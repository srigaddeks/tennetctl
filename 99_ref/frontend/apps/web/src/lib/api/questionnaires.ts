import { fetchWithAuth } from "./apiClient"
import type {
  AssignmentResponse,
  CompleteResponseOutput,
  CreateQuestionnaireRequest,
  CurrentQuestionnaireResponse,
  QuestionnaireContentSchema,
  QuestionnaireResponse,
  QuestionnaireVersionResponse,
  SaveDraftResponse,
  UpsertAssignmentRequest,
} from "../types/questionnaires"

const BASE = "/api/v1/rr"

// ── Super Admin: Templates ─────────────────────────────────────────────────

export async function listQuestionnaires(): Promise<QuestionnaireResponse[]> {
  const res = await fetchWithAuth(`${BASE}/questionnaires`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list questionnaires")
  return data as QuestionnaireResponse[]
}

export async function listActiveQuestionnaires(): Promise<QuestionnaireResponse[]> {
  const res = await fetchWithAuth(`${BASE}/questionnaires/active`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list active questionnaires")
  return data as QuestionnaireResponse[]
}

export async function createQuestionnaire(
  payload: CreateQuestionnaireRequest
): Promise<QuestionnaireResponse> {
  const res = await fetchWithAuth(`${BASE}/questionnaires`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to create questionnaire")
  return data as QuestionnaireResponse
}

export async function updateQuestionnaire(
  id: string,
  payload: Partial<{ name: string; description: string | null; intended_scope: "platform" | "org" | "workspace" }>
): Promise<QuestionnaireResponse> {
  const res = await fetchWithAuth(`${BASE}/questionnaires/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to update questionnaire")
  return data as QuestionnaireResponse
}

export async function deleteQuestionnaire(id: string): Promise<void> {
  const res = await fetchWithAuth(`${BASE}/questionnaires/${id}`, {
    method: "DELETE",
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to delete questionnaire")
}

export async function publishQuestionnaireVersion(
  questionnaireId: string,
  content: QuestionnaireContentSchema
): Promise<QuestionnaireVersionResponse> {
  const res = await fetchWithAuth(`${BASE}/questionnaires/${questionnaireId}/versions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content_jsonb: content }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to publish questionnaire version")
  return data as QuestionnaireVersionResponse
}

export async function updateQuestionnaireVersionContent(
  versionId: string,
  content: QuestionnaireContentSchema
): Promise<QuestionnaireVersionResponse> {
  const res = await fetchWithAuth(`${BASE}/questionnaires/versions/${versionId}/content`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(content),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update version content")
  return data as QuestionnaireVersionResponse
}

export async function setSectionActiveStatus(
  versionId: string,
  sectionId: string,
  isActive: boolean
): Promise<QuestionnaireVersionResponse> {
  const res = await fetchWithAuth(
    `${BASE}/questionnaires/versions/${versionId}/sections/${sectionId}/active`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ is_active: isActive }),
    }
  )
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update section status")
  return data as QuestionnaireVersionResponse
}

export async function setQuestionActiveStatus(
  versionId: string,
  sectionId: string,
  questionId: string,
  isActive: boolean
): Promise<QuestionnaireVersionResponse> {
  const res = await fetchWithAuth(
    `${BASE}/questionnaires/versions/${versionId}/sections/${sectionId}/questions/${questionId}/active`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ is_active: isActive }),
    }
  )
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update question status")
  return data as QuestionnaireVersionResponse
}

export async function fetchQuestionnaireVersion(
  versionId: string
): Promise<QuestionnaireVersionResponse> {
  const res = await fetchWithAuth(`${BASE}/questionnaires/versions/${versionId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to fetch version")
  return data as QuestionnaireVersionResponse
}

export async function listQuestionnaireVersions(
  questionnaireId: string
): Promise<QuestionnaireVersionResponse[]> {
  const res = await fetchWithAuth(`${BASE}/questionnaires/${questionnaireId}/versions`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list versions")
  return data as QuestionnaireVersionResponse[]
}

// ── Super Admin: Assignments ───────────────────────────────────────────────

export async function upsertQuestionnaireAssignment(
  payload: UpsertAssignmentRequest
): Promise<AssignmentResponse> {
  const res = await fetchWithAuth(`${BASE}/questionnaire-assignments`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to assign questionnaire")
  return data as AssignmentResponse
}

// ── Workspace: Runtime ─────────────────────────────────────────────────────

export async function fetchCurrentQuestionnaire(
  orgId: string,
  questionnaireId: string,
  workspaceId?: string | null
): Promise<CurrentQuestionnaireResponse | null> {
  const params = new URLSearchParams({ org_id: orgId, questionnaire_id: questionnaireId })
  if (workspaceId) params.set("workspace_id", workspaceId)
  const res = await fetchWithAuth(`${BASE}/questionnaire-responses/current?${params}`)
  if (res.status === 404) return null
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to fetch questionnaire")
  // Backend returns null JSON when no assignment exists
  if (!data) return null
  return data as CurrentQuestionnaireResponse
}

export async function saveDraftAnswers(
  orgId: string,
  questionnaireId: string,
  answers: Record<string, string | string[]>,
  workspaceId?: string | null
): Promise<SaveDraftResponse> {
  const params = new URLSearchParams({ org_id: orgId, questionnaire_id: questionnaireId })
  if (workspaceId) params.set("workspace_id", workspaceId)
  const res = await fetchWithAuth(`${BASE}/questionnaire-responses/current/draft?${params}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers_jsonb: answers }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to save draft answers")
  return data as SaveDraftResponse
}

export async function completeQuestionnaire(
  orgId: string,
  questionnaireId: string,
  answers: Record<string, string | string[]>,
  workspaceId?: string | null
): Promise<CompleteResponseOutput> {
  const params = new URLSearchParams({ org_id: orgId, questionnaire_id: questionnaireId })
  if (workspaceId) params.set("workspace_id", workspaceId)
  const res = await fetchWithAuth(`${BASE}/questionnaire-responses/current/complete?${params}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers_jsonb: answers }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to complete questionnaire")
  return data as CompleteResponseOutput
}
