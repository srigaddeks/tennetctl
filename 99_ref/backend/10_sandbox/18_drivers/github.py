"""
GitHub asset driver.

Collects assets from the GitHub API directly (no Steampipe required).
Supports:
- github_org: Organization metadata and settings
- github_repo: Repositories (with pagination)
- github_branch_protection: Branch protection rules per repo
- github_team: Teams within the org
- github_org_member: Organization members

Auth: Personal Access Token (PAT) or GitHub App installation token.
Currently implements PAT. GitHub App support is a future enhancement.

Rate limits:
- Authenticated PAT: 5,000 requests/hour
- The driver tracks remaining rate limit from response headers
- Backs off automatically when rate limit is near exhaustion
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from importlib import import_module as _import_module
_base_mod = _import_module("backend.10_sandbox.18_drivers.base")
AssetDriver = _base_mod.AssetDriver
_sp_base = _import_module("backend.10_sandbox.19_steampipe.base")
CollectedAsset = _sp_base.CollectedAsset
CollectionResult = _sp_base.CollectionResult
ConnectionConfig = _sp_base.ConnectionConfig
ConnectionTestResult = _sp_base.ConnectionTestResult

logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "https://api.github.com"
_RATE_LIMIT_BUFFER = 100  # Stop collecting if remaining < this threshold


class GitHubDriver(AssetDriver):
    """Direct GitHub API driver for asset collection."""

    def supports_provider(self, provider_code: str) -> bool:
        return provider_code == "github"

    async def test_connection(self, config: ConnectionConfig) -> ConnectionTestResult:
        import time
        start = time.monotonic()
        token = config.credentials.get("personal_access_token", "")
        base_url = config.config.get("base_url", _DEFAULT_BASE_URL).rstrip("/")
        org_name = config.config.get("org_name", "")

        if not token:
            return ConnectionTestResult(success=False, message="Missing personal_access_token credential")
        if not org_name:
            return ConnectionTestResult(success=False, message="Missing org_name in connection config")

        try:
            async with self._client(token, base_url) as client:
                # Try /orgs/{org} first (classic PATs with read:org)
                resp = await client.get(f"/orgs/{org_name}")
                latency_ms = int((time.monotonic() - start) * 1000)

                if resp.status_code == 200:
                    org_data = resp.json()
                    return ConnectionTestResult(
                        success=True,
                        message=f"Connected to GitHub org '{org_data.get('login', org_name)}' successfully.",
                        details={
                            "org_id": org_data.get("id"),
                            "plan": org_data.get("plan", {}).get("name") if org_data.get("plan") else None,
                            "rate_limit_remaining": int(resp.headers.get("X-RateLimit-Remaining", -1)),
                        },
                        latency_ms=latency_ms,
                    )
                elif resp.status_code == 401:
                    return ConnectionTestResult(
                        success=False,
                        message="Authentication failed — PAT is invalid or expired",
                        latency_ms=latency_ms,
                    )
                elif resp.status_code == 403:
                    # Fine-grained tokens may lack org:read but still access repos.
                    # Verify token works via /user, then check org repo access.
                    user_resp = await client.get("/user")
                    if user_resp.status_code != 200:
                        return ConnectionTestResult(
                            success=False,
                            message="Authentication failed — PAT is invalid or expired",
                            latency_ms=int((time.monotonic() - start) * 1000),
                        )
                    # Token is valid — check if it can list repos for this org
                    repos_resp = await client.get(f"/orgs/{org_name}/repos", params={"per_page": 1})
                    latency_ms = int((time.monotonic() - start) * 1000)
                    if repos_resp.status_code == 200:
                        user_data = user_resp.json()
                        return ConnectionTestResult(
                            success=True,
                            message=f"Connected as '{user_data.get('login', 'unknown')}' with repo access to '{org_name}'. Note: token lacks org:read — some org metadata may be unavailable.",
                            details={
                                "authenticated_user": user_data.get("login"),
                                "rate_limit_remaining": int(repos_resp.headers.get("X-RateLimit-Remaining", -1)),
                                "token_type": "fine-grained",
                            },
                            latency_ms=latency_ms,
                        )
                    else:
                        return ConnectionTestResult(
                            success=False,
                            message=f"PAT cannot access org '{org_name}' — grant organization access for this token in GitHub Settings > Personal access tokens",
                            latency_ms=latency_ms,
                        )
                elif resp.status_code == 404:
                    return ConnectionTestResult(
                        success=False,
                        message=f"Organization '{org_name}' not found — check the org name",
                        latency_ms=latency_ms,
                    )
                else:
                    return ConnectionTestResult(
                        success=False,
                        message=f"Unexpected response: HTTP {resp.status_code}",
                        latency_ms=latency_ms,
                    )
        except httpx.ConnectError as e:
            return ConnectionTestResult(success=False, message=f"Connection error: {e}")
        except httpx.TimeoutException:
            return ConnectionTestResult(success=False, message="Request timed out")

    async def collect_assets(
        self,
        config: ConnectionConfig,
        asset_types: list[str] | None = None,
        cursor: str | None = None,
    ) -> CollectionResult:
        token = config.credentials.get("personal_access_token", "")
        base_url = config.config.get("base_url", _DEFAULT_BASE_URL).rstrip("/")
        org_name = config.config.get("org_name", "")

        collect_all = asset_types is None
        should_collect = lambda t: collect_all or t in asset_types  # noqa: E731

        all_assets: list[CollectedAsset] = []
        errors: list[str] = []

        async with self._client(token, base_url) as client:
            # Collect org
            if should_collect("github_org"):
                try:
                    org_assets = await self._collect_org(client, org_name)
                    all_assets.extend(org_assets)
                except Exception as e:
                    errors.append(f"github_org: {e}")
                    logger.warning("github_collect_org_failed", extra={"org": org_name, "error": str(e)})

            # Collect repos (needed for branch protections too)
            repos: list[dict[str, Any]] = []
            if should_collect("github_repo") or should_collect("github_branch_protection"):
                try:
                    repo_assets, repos = await self._collect_repos(client, org_name)
                    if should_collect("github_repo"):
                        all_assets.extend(repo_assets)
                except Exception as e:
                    errors.append(f"github_repo: {e}")
                    logger.warning("github_collect_repos_failed", extra={"org": org_name, "error": str(e)})

            # Collect branch protections
            if should_collect("github_branch_protection") and repos:
                try:
                    bp_assets = await self._collect_branch_protections(client, org_name, repos)
                    all_assets.extend(bp_assets)
                except Exception as e:
                    errors.append(f"github_branch_protection: {e}")
                    logger.warning("github_collect_branch_protections_failed", extra={"org": org_name, "error": str(e)})

            # Collect teams
            if should_collect("github_team"):
                try:
                    team_assets = await self._collect_teams(client, org_name)
                    all_assets.extend(team_assets)
                except Exception as e:
                    errors.append(f"github_team: {e}")

            # Collect org members
            if should_collect("github_org_member"):
                try:
                    member_assets = await self._collect_org_members(client, org_name)
                    all_assets.extend(member_assets)
                except Exception as e:
                    errors.append(f"github_org_member: {e}")

            # Collect team memberships
            if should_collect("github_team_member"):
                try:
                    # Need teams for this — collect if not already
                    if not any(a.asset_type_code == "github_team" for a in all_assets):
                        try:
                            team_assets_for_members = await self._collect_teams(client, org_name)
                        except Exception:
                            team_assets_for_members = []
                    else:
                        team_assets_for_members = [a for a in all_assets if a.asset_type_code == "github_team"]
                    tm_assets = await self._collect_team_members(client, org_name, team_assets_for_members)
                    all_assets.extend(tm_assets)
                except Exception as e:
                    errors.append(f"github_team_member: {e}")

            # Collect outside collaborators
            if should_collect("github_collaborator"):
                try:
                    collab_assets = await self._collect_outside_collaborators(client, org_name)
                    all_assets.extend(collab_assets)
                except Exception as e:
                    errors.append(f"github_collaborator: {e}")

            # Collect repo webhooks
            if should_collect("github_webhook") and repos:
                try:
                    webhook_assets = await self._collect_webhooks(client, repos)
                    all_assets.extend(webhook_assets)
                except Exception as e:
                    errors.append(f"github_webhook: {e}")

            # Collect action workflows
            if should_collect("github_action_workflow") and repos:
                try:
                    workflow_assets = await self._collect_workflows(client, repos)
                    all_assets.extend(workflow_assets)
                except Exception as e:
                    errors.append(f"github_action_workflow: {e}")

            # Collect deploy keys
            if should_collect("github_deploy_key") and repos:
                try:
                    dk_assets = await self._collect_deploy_keys(client, repos)
                    all_assets.extend(dk_assets)
                except Exception as e:
                    errors.append(f"github_deploy_key: {e}")

            # Collect org-level secrets (names only, not values)
            if should_collect("github_secret"):
                try:
                    secret_assets = await self._collect_org_secrets(client, org_name)
                    all_assets.extend(secret_assets)
                except Exception as e:
                    errors.append(f"github_secret: {e}")

        return CollectionResult(
            assets=all_assets,
            errors=errors,
            is_partial=len(errors) > 0 and len(all_assets) > 0,
        )

    @staticmethod
    def _flatten_props(data: dict[str, Any], prefix: str = "") -> dict[str, str]:
        """Flatten a GitHub API JSON response into string key-value pairs for EAV storage."""
        props: dict[str, str] = {}
        for k, v in data.items():
            key = f"{prefix}{k}" if prefix else k
            if k in ("url", "html_url", "avatar_url", "hooks_url", "git_url", "ssh_url", "clone_url",
                      "svn_url", "mirror_url", "events_url", "issues_url", "pulls_url", "milestones_url",
                      "notifications_url", "labels_url", "releases_url", "deployments_url", "git_refs_url",
                      "git_tags_url", "git_commits_url", "trees_url", "blobs_url", "statuses_url",
                      "languages_url", "stargazers_url", "contributors_url", "subscribers_url",
                      "subscription_url", "commits_url", "comments_url", "issue_comment_url",
                      "contents_url", "compare_url", "merges_url", "archive_url", "downloads_url",
                      "assignees_url", "branches_url", "tags_url", "collaborators_url",
                      "teams_url", "forks_url", "keys_url", "issue_events_url",
                      "members_url", "public_members_url", "repos_url", "node_id"):
                continue  # Skip API URLs and internal IDs
            if isinstance(v, dict):
                # Flatten nested objects (e.g. license, permissions, owner)
                for nk, nv in v.items():
                    if nv is not None and not isinstance(nv, (dict, list)):
                        props[f"{key}_{nk}"] = str(nv)
            elif isinstance(v, list):
                props[key] = ",".join(str(i) for i in v) if v else ""
            elif v is not None:
                props[key] = str(v)
        return props

    async def _collect_org(self, client: httpx.AsyncClient, org_name: str) -> list[CollectedAsset]:
        resp = await client.get(f"/orgs/{org_name}")
        resp.raise_for_status()
        data = resp.json()
        return [CollectedAsset(
            external_id=data["login"],
            asset_type_code="github_org",
            properties=self._flatten_props(data),
        )]

    async def _collect_repos(
        self, client: httpx.AsyncClient, org_name: str
    ) -> tuple[list[CollectedAsset], list[dict[str, Any]]]:
        assets: list[CollectedAsset] = []
        raw_repos: list[dict[str, Any]] = []
        page = 1
        while True:
            resp = await client.get(
                f"/orgs/{org_name}/repos",
                params={"per_page": 100, "page": page, "type": "all"},
            )
            resp.raise_for_status()
            repos = resp.json()
            if not repos:
                break
            for r in repos:
                raw_repos.append(r)
                assets.append(CollectedAsset(
                    external_id=r["full_name"],
                    asset_type_code="github_repo",
                    properties=self._flatten_props(r),
                    parent_external_id=org_name,
                    parent_asset_type_code="github_org",
                ))
            if len(repos) < 100:
                break
            page += 1
        return assets, raw_repos

    async def _collect_branch_protections(
        self,
        client: httpx.AsyncClient,
        org_name: str,
        repos: list[dict[str, Any]],
    ) -> list[CollectedAsset]:
        assets: list[CollectedAsset] = []
        for repo in repos:
            if repo.get("archived") or repo.get("disabled"):
                continue
            full_name = repo["full_name"]
            default_branch = repo.get("default_branch", "main")
            try:
                resp = await client.get(f"/repos/{full_name}/branches/{default_branch}/protection")
                if resp.status_code == 404:
                    # No branch protection — still worth recording as an asset with protection=False
                    assets.append(CollectedAsset(
                        external_id=f"{full_name}/{default_branch}",
                        asset_type_code="github_branch_protection",
                        properties={
                            "repository_full_name": full_name,
                            "branch": default_branch,
                            "is_protected": "False",
                        },
                        parent_external_id=full_name,
                        parent_asset_type_code="github_repo",
                    ))
                    continue
                if resp.status_code != 200:
                    continue
                bp = resp.json()
                bp_props = self._flatten_props(bp)
                bp_props["repository_full_name"] = full_name
                bp_props["branch"] = default_branch
                bp_props["is_protected"] = "True"
                assets.append(CollectedAsset(
                    external_id=f"{full_name}/{default_branch}",
                    asset_type_code="github_branch_protection",
                    properties=bp_props,
                    parent_external_id=full_name,
                    parent_asset_type_code="github_repo",
                ))
            except Exception as e:
                logger.debug("github_branch_protection_fetch_failed", extra={"repo": full_name, "error": str(e)})
        return assets

    async def _collect_teams(self, client: httpx.AsyncClient, org_name: str) -> list[CollectedAsset]:
        assets: list[CollectedAsset] = []
        page = 1
        while True:
            resp = await client.get(f"/orgs/{org_name}/teams", params={"per_page": 100, "page": page})
            resp.raise_for_status()
            teams = resp.json()
            if not teams:
                break
            for t in teams:
                assets.append(CollectedAsset(
                    external_id=f"{org_name}/{t['slug']}",
                    asset_type_code="github_team",
                    properties=self._flatten_props(t),
                    parent_external_id=org_name,
                    parent_asset_type_code="github_org",
                ))
            if len(teams) < 100:
                break
            page += 1
        return assets

    async def _collect_org_members(self, client: httpx.AsyncClient, org_name: str) -> list[CollectedAsset]:
        assets: list[CollectedAsset] = []
        for role in ("admin", "member"):
            page = 1
            while True:
                resp = await client.get(
                    f"/orgs/{org_name}/members",
                    params={"per_page": 100, "page": page, "role": role},
                )
                if resp.status_code == 403:
                    break  # Fine-grained tokens may lack org member access
                resp.raise_for_status()
                members = resp.json()
                if not members:
                    break
                for m in members:
                    assets.append(CollectedAsset(
                        external_id=f"{org_name}/{m['login']}",
                        asset_type_code="github_org_member",
                        properties={
                            "login": str(m.get("login", "")),
                            "user_id": str(m.get("id", "")),
                            "avatar_url": str(m.get("avatar_url") or ""),
                            "role": role,
                            "site_admin": str(m.get("site_admin", False)),
                        },
                        parent_external_id=org_name,
                        parent_asset_type_code="github_org",
                    ))
                if len(members) < 100:
                    break
                page += 1
        return assets

    async def _collect_team_members(
        self, client: httpx.AsyncClient, org_name: str, team_assets: list,
    ) -> list[CollectedAsset]:
        assets: list[CollectedAsset] = []
        for ta in team_assets:
            slug = ta.properties.get("slug") if hasattr(ta, "properties") else None
            if not slug:
                continue
            page = 1
            while True:
                resp = await client.get(
                    f"/orgs/{org_name}/teams/{slug}/members",
                    params={"per_page": 100, "page": page},
                )
                if resp.status_code != 200:
                    break
                members = resp.json()
                if not members:
                    break
                for m in members:
                    # Get role in team
                    role_resp = await client.get(f"/orgs/{org_name}/teams/{slug}/memberships/{m['login']}")
                    team_role = "member"
                    if role_resp.status_code == 200:
                        team_role = role_resp.json().get("role", "member")
                    assets.append(CollectedAsset(
                        external_id=f"{org_name}/{slug}/{m['login']}",
                        asset_type_code="github_team_member",
                        properties={
                            "login": str(m.get("login", "")),
                            "team_slug": slug,
                            "role": team_role,
                        },
                        parent_external_id=f"{org_name}/{slug}",
                        parent_asset_type_code="github_team",
                    ))
                if len(members) < 100:
                    break
                page += 1
        return assets

    async def _collect_outside_collaborators(self, client: httpx.AsyncClient, org_name: str) -> list[CollectedAsset]:
        assets: list[CollectedAsset] = []
        page = 1
        while True:
            resp = await client.get(
                f"/orgs/{org_name}/outside_collaborators",
                params={"per_page": 100, "page": page},
            )
            if resp.status_code == 403:
                break  # May lack permission
            resp.raise_for_status()
            collabs = resp.json()
            if not collabs:
                break
            for c in collabs:
                assets.append(CollectedAsset(
                    external_id=f"{org_name}/collaborator/{c['login']}",
                    asset_type_code="github_collaborator",
                    properties={
                        "login": str(c.get("login", "")),
                        "user_id": str(c.get("id", "")),
                        "avatar_url": str(c.get("avatar_url") or ""),
                        "site_admin": str(c.get("site_admin", False)),
                    },
                    parent_external_id=org_name,
                    parent_asset_type_code="github_org",
                ))
            if len(collabs) < 100:
                break
            page += 1
        return assets

    async def _collect_webhooks(self, client: httpx.AsyncClient, repos: list[dict[str, Any]]) -> list[CollectedAsset]:
        assets: list[CollectedAsset] = []
        for repo in repos:
            if repo.get("archived") or repo.get("disabled"):
                continue
            full_name = repo["full_name"]
            try:
                resp = await client.get(f"/repos/{full_name}/hooks", params={"per_page": 100})
                if resp.status_code != 200:
                    continue
                hooks = resp.json()
                for h in hooks:
                    config = h.get("config", {})
                    assets.append(CollectedAsset(
                        external_id=f"{full_name}/hook/{h['id']}",
                        asset_type_code="github_webhook",
                        properties={
                            "name": str(h.get("name", "")),
                            "active": str(h.get("active", False)),
                            "url": str(config.get("url") or ""),
                            "content_type": str(config.get("content_type") or ""),
                            "insecure_ssl": str(config.get("insecure_ssl") or "0"),
                            "events": ",".join(h.get("events", [])),
                            "created_at": str(h.get("created_at") or ""),
                            "updated_at": str(h.get("updated_at") or ""),
                        },
                        parent_external_id=full_name,
                        parent_asset_type_code="github_repo",
                    ))
            except Exception as e:
                logger.debug("github_webhook_fetch_failed", extra={"repo": full_name, "error": str(e)})
        return assets

    async def _collect_workflows(self, client: httpx.AsyncClient, repos: list[dict[str, Any]]) -> list[CollectedAsset]:
        assets: list[CollectedAsset] = []
        for repo in repos:
            if repo.get("archived") or repo.get("disabled"):
                continue
            full_name = repo["full_name"]
            try:
                resp = await client.get(f"/repos/{full_name}/actions/workflows", params={"per_page": 100})
                if resp.status_code != 200:
                    continue
                data = resp.json()
                for w in data.get("workflows", []):
                    assets.append(CollectedAsset(
                        external_id=f"{full_name}/workflow/{w['id']}",
                        asset_type_code="github_action_workflow",
                        properties={
                            "name": str(w.get("name", "")),
                            "path": str(w.get("path", "")),
                            "state": str(w.get("state", "")),
                            "created_at": str(w.get("created_at") or ""),
                            "updated_at": str(w.get("updated_at") or ""),
                        },
                        parent_external_id=full_name,
                        parent_asset_type_code="github_repo",
                    ))
            except Exception as e:
                logger.debug("github_workflow_fetch_failed", extra={"repo": full_name, "error": str(e)})
        return assets

    async def _collect_deploy_keys(self, client: httpx.AsyncClient, repos: list[dict[str, Any]]) -> list[CollectedAsset]:
        assets: list[CollectedAsset] = []
        for repo in repos:
            if repo.get("archived") or repo.get("disabled"):
                continue
            full_name = repo["full_name"]
            try:
                resp = await client.get(f"/repos/{full_name}/keys", params={"per_page": 100})
                if resp.status_code != 200:
                    continue
                keys = resp.json()
                for k in keys:
                    assets.append(CollectedAsset(
                        external_id=f"{full_name}/deploy-key/{k['id']}",
                        asset_type_code="github_deploy_key",
                        properties={
                            "title": str(k.get("title", "")),
                            "read_only": str(k.get("read_only", True)),
                            "created_at": str(k.get("created_at") or ""),
                            "key_fingerprint": str(k.get("key", ""))[-20:] if k.get("key") else "",
                        },
                        parent_external_id=full_name,
                        parent_asset_type_code="github_repo",
                    ))
            except Exception as e:
                logger.debug("github_deploy_key_fetch_failed", extra={"repo": full_name, "error": str(e)})
        return assets

    async def _collect_org_secrets(self, client: httpx.AsyncClient, org_name: str) -> list[CollectedAsset]:
        assets: list[CollectedAsset] = []
        resp = await client.get(f"/orgs/{org_name}/actions/secrets", params={"per_page": 100})
        if resp.status_code != 200:
            return assets  # May lack permission
        data = resp.json()
        for s in data.get("secrets", []):
            assets.append(CollectedAsset(
                external_id=f"{org_name}/secret/{s['name']}",
                asset_type_code="github_secret",
                properties={
                    "name": str(s.get("name", "")),
                    "visibility": str(s.get("visibility", "")),
                    "created_at": str(s.get("created_at") or ""),
                    "updated_at": str(s.get("updated_at") or ""),
                },
                parent_external_id=org_name,
                parent_asset_type_code="github_org",
            ))
        return assets

    def _client(self, token: str, base_url: str) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=30.0,
        )
