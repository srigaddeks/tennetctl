from __future__ import annotations
import asyncio
import uuid
import datetime
from importlib import import_module
from typing import AsyncIterator
from .models import ConversationRecord, MessageRecord
from .repository import ConversationRepository
from .schemas import (ConversationListResponse, ConversationResponse,
                      CreateConversationRequest, MessageResponse, SendMessageRequest)

_telemetry_module = import_module("backend.01_core.telemetry")
_logging_module = import_module("backend.01_core.logging_utils")
_errors_module = import_module("backend.01_core.errors")
_audit_module = import_module("backend.01_core.audit")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_constants_module = import_module("backend.20_ai.constants")

get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
AuthorizationError = _errors_module.AuthorizationError
ValidationError = _errors_module.ValidationError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
AIAuditEventType = _constants_module.AIAuditEventType
require_permission = _perm_check_module.require_permission

# Lazy imports for agent pipeline (avoids circular import at module load)
_GRC_AGENT_CONTEXT_KEYS = frozenset({"framework_id", "control_id", "risk_id", "task_id"})
_GENERIC_ATTACHMENT_QUERY_TERMS = frozenset({
    "attach",
    "attached",
    "attachment",
    "image",
    "images",
    "photo",
    "photos",
    "picture",
    "pictures",
    "screenshot",
    "screenshots",
    "document",
    "documents",
    "pdf",
    "file",
    "files",
    "upload",
    "uploaded",
    "summary",
    "summarize",
    "summarise",
    "explain",
    "overview",
    "title",
    "what is in this image",
    "what is present in this image",
    "what is shown in this image",
    "what do you see",
    "describe this image",
    "describe the image",
})
_GENERIC_ATTACHMENT_RETRIEVAL_HINT = (
    "document title abstract executive summary overview purpose audience key points"
)

def _to_response(r: ConversationRecord) -> ConversationResponse:
    return ConversationResponse(id=r.id, tenant_key=r.tenant_key, user_id=r.user_id,
        org_id=r.org_id, workspace_id=r.workspace_id, agent_type_code=r.agent_type_code,
        title=r.title, page_context=r.page_context, is_archived=r.is_archived,
        created_at=r.created_at, updated_at=r.updated_at)

@instrument_class_methods(namespace="ai.conversations.service", logger_name="backend.ai.conversations.instrumentation")
class ConversationService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = ConversationRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.ai.conversations")

    @staticmethod
    def _assert_scope_match(
        *,
        conversation: ConversationRecord,
        org_id: str,
        workspace_id: str,
    ) -> None:
        if not conversation.org_id or not conversation.workspace_id:
            raise ValidationError("Conversation is missing org/workspace scope and cannot be accessed")
        if conversation.org_id != org_id or conversation.workspace_id != workspace_id:
            raise NotFoundError(f"Conversation {conversation.id} not found")

    async def create_conversation(self, *, user_id: str, tenant_key: str, request: CreateConversationRequest) -> ConversationResponse:
        if not request.org_id or not request.workspace_id:
            raise ValidationError("Conversations must be org/workspace scoped (org_id and workspace_id are required)")
        async with self._database_pool.acquire() as conn:
            await require_permission(
                conn,
                user_id,
                "ai_copilot.create",
                scope_org_id=request.org_id,
                scope_workspace_id=request.workspace_id,
            )
            record = await self._repository.create_conversation(conn, tenant_key=tenant_key, user_id=user_id,
                org_id=request.org_id, workspace_id=request.workspace_id,
                agent_type_code=request.agent_type_code, title=request.title, page_context=request.page_context)
            await self._audit_writer.write_entry(conn, AuditEntry(
                id=str(uuid.uuid4()), tenant_key=tenant_key, entity_type="conversation",
                entity_id=record.id, event_type=AIAuditEventType.CONVERSATION_CREATED,
                event_category="ai", actor_id=user_id, actor_type="user",
                properties={"agent_type_code": record.agent_type_code},
                occurred_at=datetime.datetime.utcnow()))
        return _to_response(record)

    async def list_conversations(self, *, user_id: str, tenant_key: str, is_archived: bool = False,
            org_id: str, workspace_id: str,
            agent_type_code: str | None = None, limit: int = 50, offset: int = 0) -> ConversationListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(
                conn,
                user_id,
                "ai_copilot.view",
                scope_org_id=org_id,
                scope_workspace_id=workspace_id,
            )
            records = await self._repository.list_conversations(conn, user_id=user_id,
                tenant_key=tenant_key, is_archived=is_archived, org_id=org_id,
                workspace_id=workspace_id, agent_type_code=agent_type_code,
                limit=limit, offset=offset)
        return ConversationListResponse(items=[_to_response(r) for r in records], total=len(records))

    async def get_conversation(
        self,
        *,
        conversation_id: str,
        user_id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str,
    ) -> ConversationResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_conversation(
                conn,
                conversation_id=conversation_id,
                user_id=user_id,
                tenant_key=tenant_key,
            )
            if not record:
                raise NotFoundError(f"Conversation {conversation_id} not found")
            self._assert_scope_match(
                conversation=record,
                org_id=org_id,
                workspace_id=workspace_id,
            )
            await require_permission(
                conn,
                user_id,
                "ai_copilot.view",
                scope_org_id=record.org_id,
                scope_workspace_id=record.workspace_id,
            )
        return _to_response(record)

    async def archive_conversation(
        self,
        *,
        conversation_id: str,
        user_id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str,
    ) -> None:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_conversation(
                conn,
                conversation_id=conversation_id,
                user_id=user_id,
                tenant_key=tenant_key,
            )
            if not record:
                raise NotFoundError(f"Conversation {conversation_id} not found")
            self._assert_scope_match(
                conversation=record,
                org_id=org_id,
                workspace_id=workspace_id,
            )
            await require_permission(
                conn,
                user_id,
                "ai_copilot.create",
                scope_org_id=record.org_id,
                scope_workspace_id=record.workspace_id,
            )
            ok = await self._repository.archive_conversation(
                conn,
                conversation_id=conversation_id,
                user_id=user_id,
                tenant_key=tenant_key,
            )
            if not ok:
                raise NotFoundError(f"Conversation {conversation_id} not found")
            await self._audit_writer.write_entry(conn, AuditEntry(
                id=str(uuid.uuid4()), tenant_key=tenant_key, entity_type="conversation",
                entity_id=conversation_id, event_type=AIAuditEventType.CONVERSATION_ARCHIVED,
                event_category="ai", actor_id=user_id, actor_type="user",
                properties={}, occurred_at=datetime.datetime.utcnow()))

    async def add_user_message(self, *, conversation_id: str, user_id: str, tenant_key: str,
            content: str, page_context: dict | None) -> MessageResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_conversation(
                conn,
                conversation_id=conversation_id,
                user_id=user_id,
                tenant_key=tenant_key,
            )
            if not record:
                raise NotFoundError(f"Conversation {conversation_id} not found")
            await require_permission(
                conn,
                user_id,
                "ai_copilot.execute",
                scope_org_id=record.org_id,
                scope_workspace_id=record.workspace_id,
            )
            msg = await self._repository.add_message(conn, conversation_id=conversation_id,
                role_code="user", content=content, token_count=None, model_id=None)
            await self._audit_writer.write_entry(conn, AuditEntry(
                id=str(uuid.uuid4()), tenant_key=tenant_key, entity_type="message",
                entity_id=msg.id, event_type=AIAuditEventType.MESSAGE_SENT,
                event_category="ai", actor_id=user_id, actor_type="user",
                properties={"conversation_id": conversation_id},
                occurred_at=datetime.datetime.utcnow()))
        return MessageResponse(id=msg.id, conversation_id=msg.conversation_id, role_code=msg.role_code,
            content=msg.content, token_count=msg.token_count, model_id=msg.model_id, created_at=msg.created_at)

    async def list_messages(
        self,
        *,
        conversation_id: str,
        user_id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str,
        limit: int = 100,
    ) -> list[MessageResponse]:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_conversation(
                conn,
                conversation_id=conversation_id,
                user_id=user_id,
                tenant_key=tenant_key,
            )
            if not record:
                raise NotFoundError(f"Conversation {conversation_id} not found")
            self._assert_scope_match(
                conversation=record,
                org_id=org_id,
                workspace_id=workspace_id,
            )
            await require_permission(
                conn,
                user_id,
                "ai_copilot.view",
                scope_org_id=record.org_id,
                scope_workspace_id=record.workspace_id,
            )
            messages = await self._repository.list_messages(
                conn,
                conversation_id=conversation_id,
                user_id=user_id,
                tenant_key=tenant_key,
                limit=limit,
            )
        return [MessageResponse(id=m.id, conversation_id=m.conversation_id, role_code=m.role_code,
            content=m.content, token_count=m.token_count, model_id=m.model_id, created_at=m.created_at)
            for m in messages]

    async def stream_message(
        self,
        *,
        conversation_id: str,
        user_id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str,
        content: str,
        page_context: dict | None,
    ) -> AsyncIterator[str]:
        """
        Full agent streaming pipeline:
          1. Verify ownership + persist user message
          2. Fire session name generator on first message (asyncio.create_task)
          3. Resolve agent config from DB
          4. Build ToolContext with GRC services
          5. Run GRCAgent loop — yield SSE strings
          6. If session_named SSE comes back via queue, inject it into the stream
        """
        _agent_mod = import_module("backend.20_ai.04_agents.grc_agent")
        _sng_mod = import_module("backend.20_ai.04_agents.session_name_generator")
        _dispatcher_mod = import_module("backend.20_ai.05_mcp.dispatcher")
        _ac_repo_mod = import_module("backend.20_ai.12_agent_config.repository")
        _ac_resolver_mod = import_module("backend.20_ai.12_agent_config.resolver")
        _prompt_assembler_mod = import_module("backend.20_ai.13_prompt_config.assembler")
        _prompt_repo_mod = import_module("backend.20_ai.13_prompt_config.repository")
        _memory_mod = import_module("backend.20_ai.03_memory.service")
        GRCAgent = _agent_mod.GRCAgent
        generate_session_name = _sng_mod.generate_session_name
        MCPToolDispatcher = _dispatcher_mod.MCPToolDispatcher
        ToolContext = _dispatcher_mod.ToolContext
        AgentConfigRepository = _ac_repo_mod.AgentConfigRepository
        AgentConfigResolver = _ac_resolver_mod.AgentConfigResolver
        PromptAssembler = _prompt_assembler_mod.PromptAssembler
        PromptConfigRepository = _prompt_repo_mod.PromptTemplateRepository

        # Lazy GRC service imports — avoids hard coupling at module level
        _fw_svc_mod = import_module("backend.05_grc_library.02_frameworks.service")
        _req_svc_mod = import_module("backend.05_grc_library.04_requirements.service")
        _ctrl_svc_mod = import_module("backend.05_grc_library.05_controls.service")
        _risk_svc_mod = import_module("backend.06_risk_registry.02_risks.service")
        _task_svc_mod = import_module("backend.07_tasks.02_tasks.service")

        # 1. Verify ownership + persist user message
        async with self._database_pool.acquire() as conn:
            conv = await self._repository.get_conversation(
                conn,
                conversation_id=conversation_id,
                user_id=user_id,
                tenant_key=tenant_key,
            )
            if not conv:
                raise NotFoundError(f"Conversation {conversation_id} not found")
            self._assert_scope_match(
                conversation=conv,
                org_id=org_id,
                workspace_id=workspace_id,
            )
            await require_permission(
                conn,
                user_id,
                "ai_copilot.execute",
                scope_org_id=conv.org_id,
                scope_workspace_id=conv.workspace_id,
            )
            is_first_message = conv.title is None
            await self._repository.add_message(
                conn, conversation_id=conversation_id,
                role_code="user", content=content, token_count=None, model_id=None,
            )
            # Load recent history (last 40 messages)
            history_records = await self._repository.list_messages(
                conn,
                conversation_id=conversation_id,
                user_id=user_id,
                tenant_key=tenant_key,
                limit=40,
            )

        # 2. Session name generator (fire and forget on first message)
        sse_queue: asyncio.Queue = asyncio.Queue()
        if is_first_message:
            # Resolve a fresh config for the namer (same config as main agent)
            resolver = AgentConfigResolver(
                repository=AgentConfigRepository(),
                database_pool=self._database_pool,
                settings=self._settings,
            )
            namer_config = await resolver.resolve(
                agent_type_code="copilot",
                org_id=conv.org_id,
            )
            asyncio.create_task(
                generate_session_name(
                    conversation_id=conversation_id,
                    first_message=content,
                    pool=self._database_pool,
                    config=namer_config,
                    sse_queue=sse_queue,
                )
            )

        # 3. Resolve agent config
        agent_type_code = "grc_assistant" if page_context and any(
            k in page_context for k in _GRC_AGENT_CONTEXT_KEYS
        ) else "copilot"
        resolver = AgentConfigResolver(
            repository=AgentConfigRepository(),
            database_pool=self._database_pool,
            settings=self._settings,
        )
        config = await resolver.resolve(agent_type_code=agent_type_code, org_id=conv.org_id)

        # 4. Build system prompt
        assembler = PromptAssembler(
            repository=PromptConfigRepository(),
            database_pool=self._database_pool,
        )
        system_prompt, _ = await assembler.compose(
            agent_type_code=agent_type_code,
            org_id=conv.org_id,
        )
        if not system_prompt:
            system_prompt = (
                "You are the K-Control GRC Copilot. You help compliance teams understand "
                "their framework compliance posture, identify risks, and manage tasks. "
                "Use available tools to retrieve accurate data before answering. "
                "Be concise and cite specific data points when available.\n\n"
                "## Write Operations (Approval-Gated)\n"
                "You can also help users CREATE new GRC entities. All write operations require "
                "explicit user approval before execution — never execute writes without approval.\n\n"
                "Write tools available:\n"
                "- grc_create_framework: Create a single framework\n"
                "- grc_create_requirement / grc_bulk_create_requirements: Add requirements to a framework\n"
                "- grc_create_control / grc_bulk_create_controls: Add controls to ONE framework at a time\n"
                "- grc_create_risk / grc_bulk_create_risks: Create risks for one org/workspace\n"
                "- grc_create_task / grc_bulk_create_tasks: Create tasks for ONE control or risk at a time\n"
                "- grc_map_control_to_risk: Link a control to a risk\n\n"
                "When using write tools: call the tool, which creates an approval request. "
                "Tell the user what you're proposing and that they need to approve it. "
                "Always READ existing data first (list frameworks, controls, etc.) before proposing creates "
                "so you can use correct IDs. Never guess UUIDs."
            )

        # 4b. Recall user memories — only on first message per session to avoid per-turn overhead.
        # Long messages (> 10 chars) on first turn benefit most from personalization context.
        if is_first_message and len(content) > 10:
            memory_service = _memory_mod.MemoryService(settings=self._settings)
            memories = await memory_service.recall(
                query=content,
                tenant_key=tenant_key,
                user_id=user_id,
                org_id=conv.org_id,
                top_k=3,
            )
            memory_context = _memory_mod.MemoryService.format_for_prompt(memories)
            if memory_context:
                system_prompt = system_prompt + "\n\n" + memory_context

        # 4c. Document RAG — retrieve relevant context from attachments.
        # Uses a combined strategy: PageIndex (hierarchical TOC, best for structured docs)
        # + vector RAG (Qdrant, always runs as fallback).
        # Runs on every message turn (attachments may be added mid-conversation).
        if len(content) > 5:
            doc_context = await self._retrieve_document_context_combined(
                conversation_id=conversation_id,
                query=content,
                tenant_key=tenant_key,
            )
            if doc_context:
                system_prompt = system_prompt + "\n\n" + doc_context

        # 5. Build ToolContext — pass raw asyncpg pool to dispatcher/agent
        _raw_pool = self._database_pool.pool
        _svc_kwargs = dict(settings=self._settings, database_pool=self._database_pool, cache=self._cache)
        tool_context = ToolContext(
            pool=_raw_pool,
            user_id=user_id,
            tenant_key=tenant_key,
            org_id=conv.org_id,
            workspace_id=conv.workspace_id,
            framework_service=_fw_svc_mod.FrameworkService(**_svc_kwargs),
            requirement_service=_req_svc_mod.RequirementService(**_svc_kwargs),
            control_service=_ctrl_svc_mod.ControlService(**_svc_kwargs),
            risk_service=_risk_svc_mod.RiskService(**_svc_kwargs),
            task_service=_task_svc_mod.TaskService(**_svc_kwargs),
        )

        # Convert DB history to OpenAI message format (oldest-first, for the agent).
        # list_messages returns ASC order — the last record is the user message we just
        # persisted. Exclude it ([:-1]) so it isn't duplicated: the agent appends it
        # as the current turn. Exclude system messages (shouldn't exist but defensive).
        history = [
            {"role": r.role_code, "content": r.content}
            for r in history_records[:-1]   # [:-1] excludes the message just added
            if r.role_code in ("user", "assistant")
        ]

        # 6. Run GRC agent — yield SSE
        agent = GRCAgent(
            pool=_raw_pool,
            config=config,
            settings=self._settings,
        )

        async for chunk in agent.run(
            conversation_id=conversation_id,
            user_message=content,
            history=history,
            system_prompt=system_prompt,
            tool_context=tool_context,
            page_context=page_context or {},
        ):
            yield chunk
            # Non-blocking: inject session_named SSE if it arrived
            try:
                while True:
                    named_chunk = sse_queue.get_nowait()
                    yield named_chunk
            except asyncio.QueueEmpty:
                pass

        # Final flush of any remaining session_named events.
        # Wait up to 3s for the session namer to complete — it fires a single LLM call
        # and is usually done before the main agent, but we give it a brief window.
        try:
            session_chunk = await asyncio.wait_for(sse_queue.get(), timeout=3.0)
            yield session_chunk
            # Drain any further items without waiting
            while True:
                yield sse_queue.get_nowait()
        except (asyncio.TimeoutError, asyncio.QueueEmpty):
            pass

    async def _retrieve_document_context(
        self,
        *,
        conversation_id: str,
        query: str,
        tenant_key: str,
        top_k: int = 5,
        score_threshold: float = 0.45,
    ) -> str:
        """
        Retrieve the most relevant document chunks from Qdrant kcontrol_copilot
        for the given conversation and query.
        Returns a formatted context block for injection into the system prompt,
        or empty string if Qdrant / embeddings are not configured or no chunks found.
        """
        try:
            _doc_store_mod = import_module("backend.20_ai.03_memory.document_store")
            _embed_mod = import_module("backend.20_ai.03_memory.embedder")

            if not self._settings.ai_qdrant_url:
                return ""

            embedder = _embed_mod.Embedder(settings=self._settings)
            vector = await embedder.embed(query)
            if vector is None:
                return ""

            doc_store = _doc_store_mod.CopilotDocumentStore(
                qdrant_url=self._settings.ai_qdrant_url,
                api_key=self._settings.ai_qdrant_api_key or "",
            )
            chunks = await doc_store.search(
                query_vector=vector,
                tenant_key=tenant_key,
                conversation_id=conversation_id,
                top_k=top_k,
                score_threshold=score_threshold,
            )
            if not chunks:
                return ""

            lines = ["## Attached Document Context"]
            lines.append("The user has attached documents to this conversation. "
                         "Use the following excerpts to answer their questions:\n")
            seen_files: set[str] = set()
            for chunk in chunks:
                if chunk.filename not in seen_files:
                    lines.append(f"### {chunk.filename}")
                    seen_files.add(chunk.filename)
                lines.append(chunk.chunk_text)
                lines.append("")
            return "\n".join(lines)
        except Exception as exc:
            self._logger.warning("Document RAG retrieval failed: %s", exc)
            return ""

    @staticmethod
    def _is_generic_attachment_query(query: str) -> bool:
        lowered = query.lower()
        return any(term in lowered for term in _GENERIC_ATTACHMENT_QUERY_TERMS)

    @staticmethod
    def _format_attachment_manifest(attachments: list) -> str:
        if not attachments:
            return ""

        lines = [
            "## Conversation Attachments",
            "These files are attached to the current conversation. Use them when answering file-related questions:\n",
        ]
        for attachment in attachments:
            lines.append(
                f"- {attachment.filename} "
                f"(status: {attachment.ingest_status}, chunks: {attachment.chunk_count}, "
                f"size_bytes: {attachment.file_size_bytes})"
            )
        return "\n".join(lines)

    async def _retrieve_attachment_opening_context(
        self,
        *,
        conversation_id: str,
        tenant_key: str,
        attachments: list,
        chunk_limit: int = 4,
    ) -> str:
        """
        Fallback for generic prompts when semantic retrieval misses.

        We pull the opening chunks from the newest ready attachment so prompts
        like "summarize the uploaded document" still have grounded context.
        """
        if not attachments or not self._settings.ai_qdrant_url:
            return ""

        latest_attachment = max(attachments, key=lambda attachment: attachment.created_at)
        _doc_store_mod = import_module("backend.20_ai.03_memory.document_store")
        doc_store = _doc_store_mod.CopilotDocumentStore(
            qdrant_url=self._settings.ai_qdrant_url,
            api_key=self._settings.ai_qdrant_api_key or "",
        )
        chunks = await doc_store.list_attachment_chunks(
            tenant_key=tenant_key,
            conversation_id=conversation_id,
            attachment_id=latest_attachment.id,
            limit=chunk_limit,
        )
        if not chunks:
            return ""

        lines = [
            "## Attached Document Context",
            "Semantic retrieval did not find a strong match for the user's prompt. "
            "Use the opening sections of the latest attached document as fallback context:\n",
            f"### {latest_attachment.filename} (opening context)",
        ]
        for chunk in chunks:
            lines.append(chunk.chunk_text)
            lines.append("")
        return "\n".join(lines)

    async def _retrieve_document_context_pageindex(
        self,
        *,
        conversation_id: str,
        query: str,
    ) -> str:
        """
        Phase 2 PageIndex retrieval for attachments that have a ready TOC tree.
        Returns a formatted context block, or empty string if nothing is available.
        Always safe to call — all failures are caught and logged.
        """
        try:
            _pi_mod = import_module("backend.20_ai.03_memory.pageindex")
            _att_repo_mod = import_module("backend.20_ai.19_attachments.repository")

            pageindexer = _pi_mod.PageIndexer(settings=self._settings) \
                if (self._settings.ai_pageindex_enabled and self._settings.ai_provider_url) \
                else _pi_mod.NullPageIndexer()

            repo = _att_repo_mod.AttachmentRepository()
            async with self._database_pool.acquire() as conn:
                ready_attachments = await repo.list_ready_for_pageindex(
                    conn, conversation_id=conversation_id,
                )

            if not ready_attachments:
                return ""

            results: list[str] = []
            for att in ready_attachments:
                if not att.pageindex_tree:
                    continue
                try:
                    answer = await pageindexer.retrieve(
                        query=query,
                        tree=att.pageindex_tree,
                        filename=att.filename,
                    )
                    if answer:
                        results.append(f"### {att.filename} (hierarchical analysis)\n{answer}")
                except Exception as exc:
                    self._logger.warning(
                        "PageIndex Phase 2 failed for attachment %s: %s", att.id, exc,
                    )

            if not results:
                return ""

            lines = [
                "## Document Context (Hierarchical Navigation)",
                "The following answers were derived by navigating the document's "
                "structural table of contents:\n",
            ]
            lines.extend(results)
            return "\n\n".join(lines)

        except Exception as exc:
            self._logger.warning("PageIndex retrieval pipeline failed: %s", exc)
            return ""

    async def _retrieve_document_context_combined(
        self,
        *,
        conversation_id: str,
        query: str,
        tenant_key: str,
        top_k: int = 5,
    ) -> str:
        """
        Combined retrieval strategy:
          1. PageIndex (hierarchical, best for structured documents like PDFs)
          2. Vector RAG via Qdrant (semantic chunks, always runs as fallback/supplement)

        Both run concurrently. PageIndex results are placed first in the prompt
        (they tend to be more precise for structural queries).  Vector RAG fills
        in gaps and covers non-PageIndex file types (plain text, CSV, JSON, images).
        Empty results from either path are silently skipped.
        """
        _att_repo_mod = import_module("backend.20_ai.19_attachments.repository")

        repo = _att_repo_mod.AttachmentRepository()
        async with self._database_pool.acquire() as conn:
            attachments = await repo.list_by_conversation(conn, conversation_id=conversation_id)

        ready_attachments = [
            attachment for attachment in attachments
            if attachment.ingest_status == "ready" and attachment.chunk_count > 0
        ]
        attachment_manifest = self._format_attachment_manifest(attachments)

        # Run both paths concurrently — they are independent
        pi_task = asyncio.ensure_future(
            self._retrieve_document_context_pageindex(
                conversation_id=conversation_id,
                query=query,
            )
        )
        vec_task = asyncio.ensure_future(
            self._retrieve_document_context(
                conversation_id=conversation_id,
                query=query,
                tenant_key=tenant_key,
                top_k=top_k,
            )
        )

        pi_context, vec_context = await asyncio.gather(pi_task, vec_task)

        fallback_context = ""
        if not vec_context and ready_attachments and self._is_generic_attachment_query(query):
            fallback_query = f"{query}\n\n{_GENERIC_ATTACHMENT_RETRIEVAL_HINT}"
            vec_context = await self._retrieve_document_context(
                conversation_id=conversation_id,
                query=fallback_query,
                tenant_key=tenant_key,
                top_k=top_k,
                score_threshold=0.20,
            )
            if not vec_context:
                fallback_context = await self._retrieve_attachment_opening_context(
                    conversation_id=conversation_id,
                    tenant_key=tenant_key,
                    attachments=ready_attachments,
                )

        parts = [p for p in (attachment_manifest, pi_context, vec_context, fallback_context) if p]
        return "\n\n".join(parts)
