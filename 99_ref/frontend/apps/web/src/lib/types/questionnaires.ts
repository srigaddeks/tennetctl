// Questionnaire types matching backend Pydantic schemas

export interface QuestionOptionSchema {
  value: string
  label: string
}

export interface QuestionSchema {
  id: string
  label: string
  type: "single" | "multi" | "text"
  required: boolean
  options: QuestionOptionSchema[] | null
  helperText: string | null
  placeholder: string | null
  subsection: string | null
  is_active: boolean
}

export interface SectionSchema {
  id: string
  title: string
  description: string | null
  icon: string | null
  is_active: boolean
  questions: QuestionSchema[]
}

export interface QuestionnaireContentSchema {
  sections: SectionSchema[]
}

// Master template
export interface QuestionnaireResponse {
  id: string
  questionnaire_code: string
  name: string
  description: string | null
  intended_scope: "platform" | "org" | "workspace"
  current_status: "draft" | "published" | "archived"
  latest_version_number: number
  active_version_id: string | null
  is_active: boolean
}

// Version
export interface QuestionnaireVersionResponse {
  id: string
  questionnaire_id: string
  version_number: number
  version_status: "draft" | "published" | "archived"
  content_jsonb: QuestionnaireContentSchema
  version_label?: string | null
  change_notes?: string | null
}

// Assignment
export interface AssignmentResponse {
  id: string
  assignment_scope: "platform" | "org" | "workspace"
  org_id: string | null
  workspace_id: string | null
  questionnaire_version_id: string
  is_active: boolean
}

// Runtime: what a Workspace user sees
export interface CurrentQuestionnaireResponse {
  questionnaire_version_id: string
  version_number: number
  content_jsonb: QuestionnaireContentSchema
  response_status: "draft" | "completed" | null
  answers_jsonb: Record<string, string | string[]>
}

export interface SaveDraftResponse {
  response_id: string
  response_status: "draft"
}

export interface CompleteResponseOutput {
  response_id: string
  response_status: "completed"
  missing_required_question_ids: string[] | null
}

// Request bodies
export interface CreateQuestionnaireRequest {
  questionnaire_code: string
  name: string
  description?: string | null
  intended_scope: "platform" | "org" | "workspace"
}

export interface UpsertAssignmentRequest {
  assignment_scope: "platform" | "org" | "workspace"
  org_id?: string | null
  workspace_id?: string | null
  questionnaire_version_id: string
}
