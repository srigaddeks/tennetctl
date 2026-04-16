"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Badge,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@kcontrol/ui";
import type { LucideIcon } from "lucide-react";
import {
  Building2,
  Check,
  ChevronLeft,
  ChevronRight,
  Database,
  ShieldCheck,
  Target,
  TriangleAlert,
  Users,
} from "lucide-react";
import { Textarea } from "@/components/ui/textarea";

type QuestionType = "single" | "multi" | "text";

interface QuestionOption {
  value: string;
  label: string;
}

interface QuestionDefinition {
  id: string;
  label: string;
  type: QuestionType;
  required?: boolean;
  helperText?: string;
  placeholder?: string;
  subsection?: string;
  options?: QuestionOption[];
}

interface QuestionnaireSection {
  id: string;
  title: string;
  description: string;
  icon: LucideIcon;
  questions: QuestionDefinition[];
}

type QuestionnaireAnswers = Record<string, string | string[]>;

const QUESTIONNAIRE_SECTIONS: QuestionnaireSection[] = [
  {
    id: "business-profile",
    title: "Business Profile",
    description: "Industry, size, data handling, and operating geographies.",
    icon: Building2,
    questions: [
      {
        id: "industry",
        label: "What is your primary industry?",
        type: "single",
        required: true,
        options: [
          { value: "saas", label: "SaaS / Technology" },
          { value: "manufacturing", label: "Manufacturing" },
          { value: "pharma", label: "Pharma / Life Sciences" },
          { value: "food", label: "Food & Agriculture" },
          { value: "auto", label: "Auto Ancillary" },
          { value: "steel", label: "Steel / Fabrication" },
          { value: "chemical", label: "Chemicals / Petroleum" },
          { value: "medical", label: "Medical Equipment" },
          { value: "electrical", label: "Electrical / Equipment" },
          { value: "financial", label: "Financial Services" },
          { value: "retail", label: "Retail / Distribution" },
          { value: "construction", label: "Building / Construction" },
          { value: "healthcare", label: "Healthcare / Hospitals" },
          { value: "logistics", label: "Logistics / Transport" },
          { value: "other", label: "Other" },
        ],
      },
      {
        id: "size",
        label: "Organisation size (employees)",
        type: "single",
        required: true,
        options: [
          { value: "1-50", label: "1 - 50" },
          { value: "51-200", label: "51 - 200" },
          { value: "201-500", label: "201 - 500" },
          { value: "501-2000", label: "501 - 2,000" },
          { value: "2000+", label: "2,000+" },
        ],
      },
      {
        id: "personaldata",
        label: "Does your organisation collect or process personal data?",
        type: "single",
        required: true,
        options: [
          {
            value: "large",
            label: "Yes - large volume (>10,000 data subjects)",
          },
          { value: "small", label: "Yes - limited volume" },
          { value: "no", label: "No" },
        ],
      },
      {
        id: "finance",
        label: "Do you process financial transactions or hold financial data?",
        type: "single",
        options: [
          { value: "yes-payments", label: "Yes - payments processing" },
          { value: "yes-banking", label: "Yes - banking / lending" },
          { value: "yes-basic", label: "Yes - basic financial records only" },
          { value: "no", label: "No" },
        ],
      },
      {
        id: "geo",
        label: "Geographies of operation - select all that apply",
        type: "multi",
        required: true,
        options: [
          { value: "india", label: "India" },
          { value: "sea", label: "South-East Asia" },
          { value: "middleeast", label: "Middle East / GCC" },
          { value: "us", label: "United States" },
          { value: "eu", label: "Europe (EU)" },
          { value: "uk", label: "United Kingdom" },
          { value: "apac", label: "APAC (other)" },
          { value: "global", label: "Global / Multi-region" },
        ],
      },
      {
        id: "listed",
        label: "Is the organisation publicly listed or sector-regulated?",
        type: "single",
        options: [
          { value: "listed", label: "Yes - publicly listed" },
          { value: "regulated", label: "Yes - regulated sector" },
          { value: "private", label: "No - private company" },
        ],
      },
    ],
  },
  {
    id: "assets-infrastructure",
    title: "Assets & Infrastructure",
    description: "Systems, data types, vendors, and facilities.",
    icon: Database,
    questions: [
      {
        id: "infra",
        label: "Primary infrastructure model",
        type: "single",
        required: true,
        subsection: "Infrastructure",
        options: [
          { value: "cloud", label: "Cloud-first (AWS / GCP / Azure)" },
          { value: "onprem", label: "On-premise / private data centre" },
          { value: "hybrid", label: "Hybrid (cloud + on-premise)" },
          { value: "saas", label: "SaaS-only (no owned infrastructure)" },
          { value: "ot", label: "Operational Technology (OT/SCADA/ICS)" },
        ],
      },
      {
        id: "systems",
        label: "How many business-critical systems do you operate?",
        type: "single",
        subsection: "Infrastructure",
        options: [
          { value: "1-5", label: "1 - 5" },
          { value: "6-20", label: "6 - 20" },
          { value: "21-50", label: "21 - 50" },
          { value: "50+", label: "50+" },
        ],
      },
      {
        id: "data",
        label: "What types of sensitive data does your organisation hold?",
        type: "multi",
        required: true,
        subsection: "Data",
        options: [
          { value: "pii", label: "Customer PII" },
          { value: "employee", label: "Employee / HR data" },
          { value: "health", label: "Health / medical data" },
          { value: "financial", label: "Financial records" },
          { value: "ip", label: "Intellectual property / trade secrets" },
          { value: "govt", label: "Government / defence data" },
          { value: "production", label: "Production / batch records" },
          { value: "formula", label: "Formulas / recipes / proprietary specs" },
          { value: "none", label: "No sensitive data" },
        ],
      },
      {
        id: "datastorage",
        label: "Where is your data stored?",
        type: "multi",
        subsection: "Data",
        options: [
          { value: "india", label: "India only" },
          { value: "multiregion", label: "Multiple countries" },
          { value: "cloud-vendor", label: "Cloud vendor managed" },
          { value: "unknown", label: "Not fully documented" },
        ],
      },
      {
        id: "vendors",
        label:
          "Do you have third-party vendors with access to systems or data?",
        type: "single",
        required: true,
        subsection: "Third Parties & Vendors",
        options: [
          { value: "many-critical", label: "Yes - multiple critical vendors" },
          { value: "some", label: "Yes - limited service access" },
          { value: "no", label: "No external vendor access" },
        ],
      },
      {
        id: "vendorcert",
        label: "Are your critical vendors certified? (SOC 2, ISO 27001, etc.)",
        type: "single",
        subsection: "Third Parties & Vendors",
        options: [
          { value: "all", label: "All critical vendors are certified" },
          { value: "some", label: "Some are certified, some are not" },
          { value: "none", label: "None are certified" },
          { value: "unknown", label: "Do not know" },
        ],
      },
      {
        id: "facilities",
        label: "Physical facilities - select all that apply",
        type: "multi",
        subsection: "Physical Facilities",
        options: [
          { value: "office", label: "Office" },
          { value: "factory", label: "Factory / production floor" },
          { value: "warehouse", label: "Warehouse / logistics hub" },
          { value: "lab", label: "Lab / cleanroom" },
          { value: "datacenter", label: "Data centre / server room" },
          { value: "remote", label: "Fully remote / distributed" },
          { value: "retail-outlets", label: "Retail outlets / branches" },
          { value: "field", label: "Field operations / on-site teams" },
        ],
      },
    ],
  },
  {
    id: "regulatory-obligations",
    title: "Regulatory Obligations",
    description: "Frameworks, certifications, and recent findings.",
    icon: ShieldCheck,
    questions: [
      {
        id: "frameworks",
        label: "Which frameworks are you actively pursuing or maintaining?",
        type: "multi",
        required: true,
        helperText:
          "These help the agent understand your regulatory context before generating risks.",
        subsection: "Active Compliance Frameworks",
        options: [
          { value: "soc2", label: "SOC 2" },
          { value: "iso27001", label: "ISO 27001" },
          { value: "dpdp", label: "DPDP (India)" },
          { value: "gdpr", label: "GDPR" },
          { value: "hipaa", label: "HIPAA" },
          { value: "pcidss", label: "PCI DSS" },
          { value: "iso9001", label: "ISO 9001 (Quality)" },
          { value: "iso14001", label: "ISO 14001 (Environment)" },
          { value: "iso45001", label: "ISO 45001 (Safety)" },
          { value: "iatf", label: "IATF 16949 (Automotive)" },
          { value: "fssai", label: "FSSAI (Food Safety)" },
          { value: "iso13485", label: "ISO 13485 (Medical)" },
          { value: "sama", label: "SAMA CSF" },
          { value: "custom", label: "Custom (uploaded to K-Control)" },
          { value: "none", label: "None yet" },
        ],
      },
      {
        id: "certs",
        label: "Mandatory sector certifications - select all that apply",
        type: "multi",
        subsection: "Active Compliance Frameworks",
        options: [
          { value: "bis", label: "BIS / ISI Mark" },
          { value: "gmp", label: "GMP / GDP (Pharma)" },
          { value: "cdsco", label: "CDSCO / MDR 2017" },
          { value: "peso", label: "PESO (Petroleum / Explosives)" },
          { value: "ce", label: "CE Marking (Europe)" },
          { value: "fda", label: "FDA 21 CFR (US)" },
          { value: "rbi", label: "RBI / SEBI Compliance" },
          { value: "irdai", label: "IRDAI (Insurance)" },
          { value: "none", label: "None applicable" },
        ],
      },
      {
        id: "auditfindings",
        label:
          "Have you had audit findings or regulatory non-conformances in the last 24 months?",
        type: "single",
        required: true,
        subsection: "Audit History",
        options: [
          { value: "major", label: "Yes - major / critical findings" },
          { value: "minor", label: "Yes - minor findings only" },
          { value: "none", label: "No findings" },
          { value: "neveraudited", label: "Never been audited" },
        ],
      },
      {
        id: "openfindings",
        label: "Are there findings currently open or under remediation?",
        type: "single",
        subsection: "Audit History",
        options: [
          { value: "yes-overdue", label: "Yes - some are overdue" },
          { value: "yes-ontrack", label: "Yes - on track for remediation" },
          { value: "no", label: "No open findings" },
        ],
      },
      {
        id: "upcomingaudit",
        label:
          "Upcoming audits or certification renewals in the next 12 months?",
        type: "single",
        subsection: "Audit History",
        options: [
          { value: "yes-6m", label: "Yes - within 6 months" },
          { value: "yes-12m", label: "Yes - within 12 months" },
          { value: "no", label: "No upcoming audits" },
        ],
      },
    ],
  },
  {
    id: "operational-context",
    title: "Operational Context",
    description: "Dependencies, incidents, continuity, and resilience.",
    icon: TriangleAlert,
    questions: [
      {
        id: "deps",
        label: "Key operational dependencies - select all that apply",
        type: "multi",
        required: true,
        subsection: "Dependencies & Single Points of Failure",
        options: [
          { value: "single-cloud", label: "Single cloud provider" },
          {
            value: "single-supplier",
            label: "Single critical raw material supplier",
          },
          {
            value: "keyperson",
            label: "Key-person dependency (1-2 critical staff)",
          },
          { value: "legacy", label: "Legacy systems / tech debt" },
          { value: "machinery", label: "Critical machinery / equipment" },
          { value: "saas-vendor", label: "Critical SaaS vendor dependency" },
          { value: "utility", label: "Power / utilities dependency" },
          { value: "logistics", label: "Logistics / cold chain" },
          { value: "regulatory-licence", label: "Regulatory licence / permit" },
          { value: "none", label: "No significant single points of failure" },
        ],
      },
      {
        id: "incidents",
        label: "Any significant incidents in the last 24 months?",
        type: "multi",
        subsection: "Incidents & History",
        options: [
          { value: "breach", label: "Security breach / data leak" },
          { value: "outage", label: "System / production outage (>4 hrs)" },
          { value: "audit-failure", label: "Audit failure / major finding" },
          { value: "safety", label: "HSE / safety incident" },
          { value: "quality", label: "Product quality failure / recall" },
          { value: "ransomware", label: "Ransomware / malware" },
          { value: "fraud", label: "Internal fraud or misconduct" },
          { value: "regulatory", label: "Regulatory action / notice" },
          { value: "none", label: "No significant incidents" },
        ],
      },
      {
        id: "bcp",
        label: "Business Continuity Plan (BCP) status",
        type: "single",
        required: true,
        subsection: "Business Continuity",
        options: [
          { value: "tested", label: "Yes - documented and tested annually" },
          {
            value: "documented",
            label: "Yes - documented, not recently tested",
          },
          { value: "draft", label: "Draft / incomplete" },
          { value: "no", label: "No BCP in place" },
        ],
      },
      {
        id: "downtime",
        label: "Maximum tolerable downtime before business impact is severe?",
        type: "single",
        subsection: "Business Continuity",
        options: [
          { value: "minutes", label: "Minutes (<30 min)" },
          { value: "hours-4", label: "Up to 4 hours" },
          { value: "hours-24", label: "Up to 24 hours" },
          { value: "days", label: "Several days" },
        ],
      },
      {
        id: "dr",
        label: "Disaster Recovery (DR) capability",
        type: "single",
        subsection: "Business Continuity",
        options: [
          { value: "full", label: "Full DR - warm/hot standby" },
          { value: "basic", label: "Basic - backup restoration" },
          { value: "none", label: "No formal DR" },
        ],
      },
    ],
  },
  {
    id: "people-culture",
    title: "People & Culture",
    description: "Training, access, contractors, and insider risk.",
    icon: Users,
    questions: [
      {
        id: "workmodel",
        label: "Work model",
        type: "single",
        required: true,
        options: [
          { value: "office", label: "Fully office-based" },
          { value: "hybrid", label: "Hybrid (office + remote)" },
          { value: "remote", label: "Fully remote" },
          { value: "field", label: "Field / factory / distributed" },
        ],
      },
      {
        id: "training",
        label: "Security awareness training",
        type: "single",
        options: [
          {
            value: "mandatory-regular",
            label: "Mandatory - completed regularly by all staff",
          },
          {
            value: "mandatory-low",
            label: "Mandatory - but low completion rate",
          },
          { value: "voluntary", label: "Voluntary / ad-hoc" },
          { value: "none", label: "No formal training" },
        ],
      },
      {
        id: "privaccess",
        label:
          "Privileged access management - who has admin / elevated access?",
        type: "single",
        options: [
          { value: "controlled", label: "Strictly controlled - PAM in place" },
          {
            value: "some-control",
            label: "Partially controlled - informal review process",
          },
          { value: "loose", label: "Loosely managed - too many admins" },
          { value: "unknown", label: "Not formally reviewed" },
        ],
      },
      {
        id: "contractors",
        label: "Contractor / temporary staff access to systems",
        type: "single",
        options: [
          { value: "none", label: "No contractor access to systems" },
          { value: "controlled", label: "Yes - time-limited, scoped access" },
          {
            value: "uncontrolled",
            label: "Yes - same access as full-time staff",
          },
        ],
      },
      {
        id: "offboarding",
        label: "Offboarding process when staff or contractors leave",
        type: "single",
        options: [
          { value: "automated", label: "Automated - access removed same day" },
          {
            value: "manual-prompt",
            label: "Manual - usually done within a day",
          },
          { value: "delayed", label: "Manual - often delayed (days to weeks)" },
          { value: "no-process", label: "No formal offboarding process" },
        ],
      },
      {
        id: "insider",
        label: "Insider risk - select any known concerns or incidents",
        type: "multi",
        options: [
          { value: "data-exfil", label: "Suspected data exfiltration" },
          { value: "misuse", label: "System misuse / abuse" },
          { value: "fraud", label: "Internal fraud" },
          { value: "ip-theft", label: "IP theft by departing staff" },
          { value: "none", label: "No known insider incidents" },
        ],
      },
    ],
  },
  {
    id: "risk-appetite",
    title: "Risk Appetite",
    description: "Tolerance, escalation thresholds, and review cadence.",
    icon: Target,
    questions: [
      {
        id: "tolerance",
        label: "Overall risk tolerance",
        type: "single",
        required: true,
        options: [
          { value: "low", label: "Low - minimise all exposure" },
          { value: "medium", label: "Medium - balanced, some risk accepted" },
          { value: "high", label: "High - growth-first, reactive management" },
        ],
      },
      {
        id: "financialthreshold",
        label: "Maximum tolerable financial impact before board escalation",
        type: "single",
        options: [
          { value: "10L", label: "< Rs 10 Lakh" },
          { value: "1cr", label: "Rs 10 Lakh - Rs 1 Cr" },
          { value: "10cr", label: "Rs 1 Cr - Rs 10 Cr" },
          { value: "10cr+", label: "Rs 10 Cr+" },
        ],
      },
      {
        id: "downtimethreshold",
        label: "Maximum tolerable system / operational downtime",
        type: "single",
        options: [
          { value: "30min", label: "< 30 minutes" },
          { value: "4hr", label: "Up to 4 hours" },
          { value: "24hr", label: "Up to 24 hours" },
          { value: "days", label: "Several days" },
        ],
      },
      {
        id: "reputation",
        label: "Reputational risk sensitivity",
        type: "single",
        options: [
          {
            value: "high",
            label: "High - any public incident is unacceptable",
          },
          { value: "medium", label: "Medium - manageable with communication" },
          { value: "low", label: "Low - sector not consumer-facing" },
        ],
      },
      {
        id: "reviewcycle",
        label: "How often should risks be formally reviewed?",
        type: "single",
        required: true,
        options: [
          { value: "monthly", label: "Monthly" },
          { value: "quarterly", label: "Quarterly" },
          { value: "biannual", label: "Bi-annually" },
          { value: "annual", label: "Annually" },
        ],
      },
      {
        id: "riskowner",
        label: "Who is the primary risk owner in the organisation?",
        type: "single",
        options: [
          { value: "ciso", label: "CISO / Head of Security" },
          { value: "coo", label: "COO / Head of Operations" },
          { value: "compliance", label: "Compliance / GRC Lead" },
          { value: "ceo", label: "CEO / Founder" },
          { value: "quality", label: "Quality / HSE Manager" },
          { value: "none", label: "No dedicated risk owner" },
        ],
      },
      {
        id: "extra-context",
        label: "Any additional context - known risks, concerns, or deadlines",
        type: "text",
        placeholder:
          "Examples: upcoming recertification, breach follow-up, new region launch, or enforcement deadline.",
      },
    ],
  },
];

const TOTAL_QUESTIONS = QUESTIONNAIRE_SECTIONS.reduce(
  (total, section) => total + section.questions.length,
  0
);

function getStorageKey(orgId?: string, workspaceId?: string | null) {
  return `kcontrol:risk-questionnaire:${orgId ?? "global"}:${workspaceId ?? "global"}`;
}

function getMultiValue(value: string | string[] | undefined): string[] {
  return Array.isArray(value) ? value : [];
}

function isAnswered(
  question: QuestionDefinition,
  answers: QuestionnaireAnswers
) {
  const value = answers[question.id];
  if (question.type === "text")
    return typeof value === "string" && value.trim().length > 0;
  if (question.type === "multi")
    return Array.isArray(value) && value.length > 0;
  return typeof value === "string" && value.length > 0;
}

function getAnsweredCountForSection(
  section: QuestionnaireSection,
  answers: QuestionnaireAnswers
) {
  return section.questions.filter((question) => isAnswered(question, answers))
    .length;
}

function getMissingRequiredForSection(
  section: QuestionnaireSection,
  answers: QuestionnaireAnswers
) {
  return section.questions.filter(
    (question) => question.required && !isAnswered(question, answers)
  ).length;
}

function getOptionLabel(question: QuestionDefinition, value: string) {
  return (
    question.options?.find((option) => option.value === value)?.label ?? value
  );
}

export function RiskQuestionnaireDialog({
  orgId,
  workspaceId,
  onClose,
}: {
  orgId?: string;
  workspaceId?: string | null;
  onClose: () => void;
}) {
  const [currentSectionIndex, setCurrentSectionIndex] = useState(0);
  const [answers, setAnswers] = useState<QuestionnaireAnswers>({});
  const [draftReady, setDraftReady] = useState(false);

  const storageKey = useMemo(
    () => getStorageKey(orgId, workspaceId),
    [orgId, workspaceId]
  );

  useEffect(() => {
    try {
      const rawDraft = window.localStorage.getItem(storageKey);
      if (rawDraft) {
        const parsed = JSON.parse(rawDraft) as QuestionnaireAnswers;
        setAnswers(parsed);
      } else {
        setAnswers({});
      }
    } catch {
      setAnswers({});
    } finally {
      setDraftReady(true);
    }
  }, [storageKey]);

  useEffect(() => {
    if (!draftReady) return;
    try {
      window.localStorage.setItem(storageKey, JSON.stringify(answers));
    } catch {
      // Ignore local draft persistence issues and keep the questionnaire usable.
    }
  }, [answers, draftReady, storageKey]);

  const currentSection = QUESTIONNAIRE_SECTIONS[currentSectionIndex];
  const answeredCount = useMemo(
    () =>
      QUESTIONNAIRE_SECTIONS.reduce(
        (total, section) =>
          total + getAnsweredCountForSection(section, answers),
        0
      ),
    [answers]
  );
  const remainingRequired = useMemo(
    () =>
      QUESTIONNAIRE_SECTIONS.reduce(
        (total, section) =>
          total + getMissingRequiredForSection(section, answers),
        0
      ),
    [answers]
  );
  const progressPercent =
    TOTAL_QUESTIONS === 0
      ? 0
      : Math.round((answeredCount / TOTAL_QUESTIONS) * 100);
  const currentSectionAnswered = getAnsweredCountForSection(
    currentSection,
    answers
  );
  const currentSectionMissing = getMissingRequiredForSection(
    currentSection,
    answers
  );

  function setSingleAnswer(questionId: string, value: string) {
    setAnswers((current) => ({ ...current, [questionId]: value }));
  }

  function toggleMultiAnswer(questionId: string, value: string) {
    setAnswers((current) => {
      const next = getMultiValue(current[questionId]);
      const updated = next.includes(value)
        ? next.filter((item) => item !== value)
        : [...next, value];
      return { ...current, [questionId]: updated };
    });
  }

  function setTextAnswer(questionId: string, value: string) {
    setAnswers((current) => ({ ...current, [questionId]: value }));
  }

  function clearDraft() {
    setAnswers({});
    try {
      window.localStorage.removeItem(storageKey);
    } catch {
      // Ignore storage issues and still clear the in-memory state.
    }
    setCurrentSectionIndex(0);
  }

  if (!currentSection) return null;

  return (
    <Dialog
      open
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DialogContent className="h-[100dvh] w-screen max-w-none overflow-hidden rounded-none border-0 p-0 sm:h-[92dvh] sm:w-[calc(100vw-2rem)] sm:max-w-6xl sm:rounded-2xl sm:border">
        <div className="grid h-full min-h-0 grid-cols-1 lg:grid-cols-[280px_minmax(0,1fr)]">
          <aside className="hidden min-h-0 border-r border-border bg-muted/20 lg:flex lg:flex-col">
            <div className="flex h-full min-h-0 flex-col gap-4 p-4 sm:p-5">
              <div className="space-y-2">
                <div className="inline-flex items-center rounded-full border border-primary/20 bg-primary/10 px-2.5 py-1 text-[11px] font-semibold text-primary">
                  Risk Questionnaire
                </div>
                <div>
                  <p className="text-sm font-semibold text-foreground">
                    Six guided sections
                  </p>
                  <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                    These answers give the agent the context it needs to
                    generate risks that fit this organisation.
                  </p>
                </div>
              </div>

              <div className="space-y-2 rounded-xl border border-border bg-background/80 p-3">
                <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                  <span>Progress</span>
                  <span>
                    {answeredCount} / {TOTAL_QUESTIONS} answered
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-primary transition-all"
                    style={{
                      width: `${Math.max(progressPercent, answeredCount > 0 ? 6 : 0)}%`,
                    }}
                  />
                </div>
                <p className="text-[11px] text-muted-foreground">
                  Draft answers are saved locally for this org/workspace.
                </p>
              </div>

              <div className="flex snap-x snap-mandatory gap-2 overflow-x-auto overscroll-x-contain pb-2 [-webkit-overflow-scrolling:touch] [scrollbar-width:thin] touch-pan-x lg:min-h-0 lg:flex-1 lg:flex-col lg:gap-1.5 lg:overflow-y-auto lg:overflow-x-hidden lg:overscroll-contain lg:pb-0 lg:pr-1">
                {QUESTIONNAIRE_SECTIONS.map((section, index) => {
                  const Icon = section.icon;
                  const sectionAnswered = getAnsweredCountForSection(
                    section,
                    answers
                  );
                  const sectionMissing = getMissingRequiredForSection(
                    section,
                    answers
                  );
                  const active = index === currentSectionIndex;
                  return (
                    <button
                      key={section.id}
                      type="button"
                      onClick={() => setCurrentSectionIndex(index)}
                      className={`min-w-[220px] snap-start flex-shrink-0 rounded-xl border px-3 py-3 text-left transition-colors lg:w-full lg:min-w-0 ${
                        active
                          ? "border-primary/30 bg-primary/10"
                          : "border-border bg-background hover:border-primary/20 hover:bg-muted/40"
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <div
                          className={`mt-0.5 rounded-lg p-2 ${active ? "bg-primary/15 text-primary" : "bg-muted text-muted-foreground"}`}
                        >
                          <Icon className="h-4 w-4" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center justify-between gap-2">
                            <p className="truncate text-sm font-medium text-foreground">
                              {section.title}
                            </p>
                            <span className="text-[11px] text-muted-foreground">
                              {index + 1}
                            </span>
                          </div>
                          <p className="mt-1 hidden text-[11px] leading-relaxed text-muted-foreground sm:block">
                            {section.description}
                          </p>
                          <div className="mt-2 flex flex-wrap items-center gap-2">
                            <Badge variant="outline" className="text-[10px]">
                              {sectionAnswered}/{section.questions.length}{" "}
                              answered
                            </Badge>
                            {sectionMissing === 0 ? (
                              <Badge
                                variant="outline"
                                className="border-emerald-500/30 bg-emerald-500/10 text-[10px] text-emerald-600"
                              >
                                Required complete
                              </Badge>
                            ) : (
                              <Badge
                                variant="outline"
                                className="border-amber-500/30 bg-amber-500/10 text-[10px] text-amber-600"
                              >
                                {sectionMissing} required open
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </aside>

          <div className="flex min-h-0 flex-col overflow-hidden bg-background">
            <div className="border-b border-border bg-background/95 px-4 py-4 backdrop-blur lg:hidden">
              <div className="space-y-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="inline-flex items-center rounded-full border border-primary/20 bg-primary/10 px-2.5 py-1 text-[11px] font-semibold text-primary">
                    Risk Questionnaire
                  </div>
                  <Badge variant="outline" className="text-[11px]">
                    {answeredCount}/{TOTAL_QUESTIONS}
                  </Badge>
                </div>

                <div className="space-y-1">
                  <p className="text-lg font-semibold text-foreground">
                    {currentSection.title}
                  </p>
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    {currentSection.description}
                  </p>
                </div>

                <div className="rounded-2xl border border-border bg-muted/30 p-3">
                  <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                    <span>Overall progress</span>
                    <span>{progressPercent}% complete</span>
                  </div>
                  <div className="mt-2 h-2 overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-primary transition-all"
                      style={{
                        width: `${Math.max(progressPercent, answeredCount > 0 ? 6 : 0)}%`,
                      }}
                    />
                  </div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <Badge variant="outline" className="text-[10px]">
                      {currentSectionAnswered}/{currentSection.questions.length}{" "}
                      in section
                    </Badge>
                    <Badge
                      variant="outline"
                      className={
                        currentSectionMissing === 0
                          ? "border-emerald-500/30 bg-emerald-500/10 text-[10px] text-emerald-600"
                          : "border-amber-500/30 bg-amber-500/10 text-[10px] text-amber-600"
                      }
                    >
                      {currentSectionMissing === 0
                        ? "Required complete"
                        : `${currentSectionMissing} required open`}
                    </Badge>
                  </div>
                </div>

                <div className="flex gap-2 overflow-x-auto overscroll-x-contain pb-1 [-webkit-overflow-scrolling:touch] touch-pan-x">
                  {QUESTIONNAIRE_SECTIONS.map((section, index) => {
                    const Icon = section.icon;
                    const active = index === currentSectionIndex;
                    const sectionAnswered = getAnsweredCountForSection(
                      section,
                      answers
                    );
                    return (
                      <button
                        key={section.id}
                        type="button"
                        onClick={() => setCurrentSectionIndex(index)}
                        className={`min-w-[170px] flex-shrink-0 rounded-2xl border px-3 py-3 text-left transition-colors ${
                          active
                            ? "border-primary/30 bg-primary/10 shadow-sm"
                            : "border-border bg-card"
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <div
                            className={`rounded-xl p-2 ${
                              active
                                ? "bg-primary/15 text-primary"
                                : "bg-muted text-muted-foreground"
                            }`}
                          >
                            <Icon className="h-4 w-4" />
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="truncate text-sm font-medium text-foreground">
                              {section.title}
                            </p>
                            <p className="mt-1 text-[11px] text-muted-foreground">
                              {sectionAnswered}/{section.questions.length}{" "}
                              answered
                            </p>
                          </div>
                          <span className="text-[11px] text-muted-foreground">
                            {index + 1}
                          </span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            <DialogHeader className="hidden border-b px-6 py-4 text-left lg:flex">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <DialogTitle className="text-lg sm:text-xl">
                    {currentSection.title}
                  </DialogTitle>
                  <DialogDescription className="mt-1 max-w-2xl text-sm">
                    {currentSection.description}
                  </DialogDescription>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline">
                    Section {currentSectionIndex + 1} of{" "}
                    {QUESTIONNAIRE_SECTIONS.length}
                  </Badge>
                  <Badge variant="outline">{progressPercent}% complete</Badge>
                </div>
              </div>
            </DialogHeader>

            <div className="min-h-0 flex-1 overflow-y-auto overscroll-y-contain">
              <div className="space-y-4 px-4 py-4 sm:space-y-5 sm:px-6 sm:py-5">
                {currentSection.questions.map((question, index) => {
                  const previousQuestion = currentSection.questions[index - 1];
                  const showSubsection =
                    question.subsection &&
                    question.subsection !== previousQuestion?.subsection;
                  const answered = isAnswered(question, answers);

                  return (
                    <div key={question.id} className="space-y-3">
                      {showSubsection && (
                        <div className="pt-1">
                          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                            {question.subsection}
                          </p>
                        </div>
                      )}

                      <Card
                        className={
                          answered
                            ? "border-primary/20 bg-primary/[0.03] shadow-sm"
                            : "bg-card shadow-sm"
                        }
                      >
                        <CardContent className="space-y-3 p-3.5 sm:p-4">
                          <div className="space-y-1">
                            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                              <p className="text-sm font-medium leading-relaxed text-foreground sm:pr-3">
                                {question.label}
                                {question.required && (
                                  <span className="ml-1 text-destructive">
                                    *
                                  </span>
                                )}
                              </p>
                              {answered && (
                                <Badge
                                  variant="outline"
                                  className="shrink-0 self-start border-primary/30 bg-primary/10 text-primary"
                                >
                                  Answered
                                </Badge>
                              )}
                            </div>
                            {question.helperText && (
                              <p className="text-xs text-muted-foreground">
                                {question.helperText}
                              </p>
                            )}
                          </div>

                          {question.type === "text" && (
                            <Textarea
                              value={
                                typeof answers[question.id] === "string"
                                  ? (answers[question.id] as string)
                                  : ""
                              }
                              onChange={(event) =>
                                setTextAnswer(question.id, event.target.value)
                              }
                              placeholder={question.placeholder}
                              className="min-h-28 resize-y"
                            />
                          )}

                          {question.type === "single" && (
                            <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
                              {question.options?.map((option) => {
                                const selected =
                                  answers[question.id] === option.value;
                                return (
                                  <button
                                    key={option.value}
                                    type="button"
                                    onClick={() =>
                                      setSingleAnswer(question.id, option.value)
                                    }
                                    className={`flex min-h-12 items-center justify-between gap-3 rounded-xl border px-3 py-3 text-left text-sm leading-relaxed transition-colors ${
                                      selected
                                        ? "border-primary bg-primary/10 text-primary shadow-sm"
                                        : "border-border bg-background text-muted-foreground hover:border-primary/20 hover:bg-muted/40 hover:text-foreground"
                                    }`}
                                  >
                                    <span>{option.label}</span>
                                    {selected && (
                                      <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-primary/15 text-primary">
                                        <Check className="h-3.5 w-3.5" />
                                      </span>
                                    )}
                                  </button>
                                );
                              })}
                            </div>
                          )}

                          {question.type === "multi" && (
                            <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
                              {question.options?.map((option) => {
                                const selected = getMultiValue(
                                  answers[question.id]
                                ).includes(option.value);
                                return (
                                  <button
                                    key={option.value}
                                    type="button"
                                    onClick={() =>
                                      toggleMultiAnswer(
                                        question.id,
                                        option.value
                                      )
                                    }
                                    className={`flex min-h-12 items-center justify-between gap-3 rounded-xl border px-3 py-3 text-left text-sm leading-relaxed transition-colors ${
                                      selected
                                        ? "border-primary bg-primary/10 text-primary shadow-sm"
                                        : "border-border bg-background text-muted-foreground hover:border-primary/20 hover:bg-muted/40 hover:text-foreground"
                                    }`}
                                  >
                                    <span>{option.label}</span>
                                    {selected && (
                                      <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-primary/15 text-primary">
                                        <Check className="h-3.5 w-3.5" />
                                      </span>
                                    )}
                                  </button>
                                );
                              })}
                            </div>
                          )}

                          {question.type !== "text" && answered && (
                            <div className="flex flex-wrap gap-1.5">
                              {(question.type === "multi"
                                ? getMultiValue(answers[question.id]).map(
                                    (value) => getOptionLabel(question, value)
                                  )
                                : [
                                    getOptionLabel(
                                      question,
                                      String(answers[question.id])
                                    ),
                                  ]
                              ).map((label) => (
                                <Badge
                                  key={label}
                                  variant="outline"
                                  className="text-[11px]"
                                >
                                  {label}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    </div>
                  );
                })}
              </div>
            </div>

            <DialogFooter className="shrink-0 border-t bg-background/95 px-4 py-4 backdrop-blur sm:px-6">
              <div className="flex w-full flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div className="flex items-start gap-2 text-xs text-muted-foreground sm:items-center">
                  {remainingRequired === 0 ? (
                    <span>All required questions are complete.</span>
                  ) : (
                    <>
                      <TriangleAlert className="h-3.5 w-3.5 text-amber-500" />
                      <span>
                        {remainingRequired} required question(s) still need an
                        answer.
                      </span>
                    </>
                  )}
                </div>

                <div className="grid w-full grid-cols-2 gap-2 sm:flex sm:w-auto sm:flex-wrap sm:items-center sm:justify-end">
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={clearDraft}
                    className="w-full sm:w-auto"
                  >
                    Reset Answers
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={onClose}
                    className="w-full sm:w-auto"
                  >
                    Close
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    disabled={currentSectionIndex === 0}
                    onClick={() =>
                      setCurrentSectionIndex((value) => Math.max(value - 1, 0))
                    }
                    className="col-span-1 w-full gap-2 sm:w-auto"
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Previous
                  </Button>
                  {currentSectionIndex < QUESTIONNAIRE_SECTIONS.length - 1 ? (
                    <Button
                      type="button"
                      onClick={() =>
                        setCurrentSectionIndex((value) =>
                          Math.min(value + 1, QUESTIONNAIRE_SECTIONS.length - 1)
                        )
                      }
                      className="col-span-1 w-full gap-2 sm:w-auto"
                    >
                      Next
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  ) : (
                    <Button
                      type="button"
                      onClick={onClose}
                      disabled={remainingRequired > 0}
                      className="col-span-1 w-full sm:w-auto"
                    >
                      Done
                    </Button>
                  )}
                </div>
              </div>
            </DialogFooter>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
