from __future__ import annotations

from enum import StrEnum


class ReportType(StrEnum):
    EVIDENCE_REPORT = "evidence_report"
    FRAMEWORK_COMPLIANCE = "framework_compliance"
    CONTROL_STATUS = "control_status"
    RISK_SUMMARY = "risk_summary"
    TASK_HEALTH = "task_health"
    AUDIT_TRAIL = "audit_trail"
    EXECUTIVE_SUMMARY = "executive_summary"
    FRAMEWORK_READINESS = "framework_readiness"
    FRAMEWORK_GAP_ANALYSIS = "framework_gap_analysis"
    BOARD_RISK_REPORT = "board_risk_report"
    REMEDIATION_PLAN = "remediation_plan"
    COMPLIANCE_POSTURE = "compliance_posture"
    VENDOR_RISK = "vendor_risk"
    MANUAL_UPLOAD = "manual_upload"


class ReportStatus(StrEnum):
    QUEUED = "queued"
    PLANNING = "planning"
    COLLECTING = "collecting"
    ANALYZING = "analyzing"
    WRITING = "writing"
    FORMATTING = "formatting"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportExportFormat(StrEnum):
    PDF = "pdf"
    DOCX = "docx"
    MD = "md"


REPORT_TYPE_LABELS: dict[str, str] = {
    ReportType.EVIDENCE_REPORT: "Evidence Check Report",
    ReportType.FRAMEWORK_COMPLIANCE: "Framework Compliance Report",
    ReportType.CONTROL_STATUS: "Control Status Report",
    ReportType.RISK_SUMMARY: "Risk Summary Report",
    ReportType.TASK_HEALTH: "Task Health Report",
    ReportType.AUDIT_TRAIL: "Audit Trail Report",
    ReportType.EXECUTIVE_SUMMARY: "Executive Summary Report",
    ReportType.FRAMEWORK_READINESS: "Framework Readiness Report",
    ReportType.FRAMEWORK_GAP_ANALYSIS: "Framework Gap Analysis",
    ReportType.BOARD_RISK_REPORT: "Board Risk Report",
    ReportType.REMEDIATION_PLAN: "Remediation Plan",
    ReportType.COMPLIANCE_POSTURE: "Compliance Posture Report",
    ReportType.VENDOR_RISK: "Vendor Risk Assessment",
    ReportType.MANUAL_UPLOAD: "Manual Report Submission",
}

REPORT_SECTIONS: dict[str, list[str]] = {
    ReportType.FRAMEWORK_COMPLIANCE: [
        "executive_summary", "framework_overview", "control_coverage",
        "risk_exposure", "compliance_gaps", "recommendations",
    ],
    ReportType.CONTROL_STATUS: [
        "executive_summary", "controls_by_category", "controls_needing_attention",
        "test_coverage", "owner_assignment", "action_items",
    ],
    ReportType.RISK_SUMMARY: [
        "executive_overview", "risk_landscape", "risk_by_category",
        "treatment_status", "residual_risk", "recommendations",
    ],
    ReportType.TASK_HEALTH: [
        "overview", "overdue_tasks", "unassigned_tasks",
        "by_priority", "by_type", "resolution_trends",
    ],
    ReportType.EXECUTIVE_SUMMARY: [
        "compliance_score", "top_risks", "control_health",
        "open_items", "key_metrics", "next_steps",
    ],
    ReportType.AUDIT_TRAIL: [
        "period_summary", "event_timeline", "key_events", "anomalies",
    ],
    ReportType.EVIDENCE_REPORT: [
        "executive_summary", "criteria_evaluation", "gap_analysis", "methodology",
    ],
    ReportType.FRAMEWORK_READINESS: [
        "executive_summary", "readiness_scorecard", "trust_criteria_coverage",
        "control_gaps", "evidence_status", "remediation_roadmap",
    ],
    ReportType.FRAMEWORK_GAP_ANALYSIS: [
        "executive_summary", "annex_a_coverage", "implemented_controls",
        "gap_analysis", "risk_treatment", "certification_readiness",
    ],
    ReportType.BOARD_RISK_REPORT: [
        "executive_headline", "risk_posture_summary", "top_risks_board",
        "compliance_health", "key_decisions_required", "outlook",
    ],
    ReportType.REMEDIATION_PLAN: [
        "executive_summary", "critical_items", "high_priority_items",
        "control_gaps_plan", "risk_remediation", "timeline_and_owners",
    ],
    ReportType.COMPLIANCE_POSTURE: [
        "executive_summary", "framework_coverage_matrix", "cross_framework_gaps",
        "risk_posture_overview", "task_backlog_health", "improvement_recommendations",
    ],
    ReportType.VENDOR_RISK: [
        "executive_summary", "third_party_risk_overview", "high_risk_vendors",
        "control_coverage_gaps", "treatment_status", "recommendations",
    ],
}
