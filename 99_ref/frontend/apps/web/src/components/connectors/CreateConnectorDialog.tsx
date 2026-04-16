"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  Button,
  Input,
  Label,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@kcontrol/ui";
import {
  Plus,
  ArrowLeft,
  ArrowRight,
  Cloud,
  Database,
  Server,
  Shield,
  Globe,
  Activity,
  Plug,
  Github,
  Lock,
  Settings2,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  Search,
} from "lucide-react";
import {
  listConnectorCategories,
  listConnectorTypes,
  listAssetVersions,
  getConnectorConfigSchema,
  preflightTestConnector,
  createConnector,
} from "@/lib/api/sandbox";
import type {
  DimensionResponse,
  AssetVersionResponse,
  ConnectorTestResult,
  ConnectorConfigField,
  ConnectorConfigSchemaResponse,
} from "@/lib/api/sandbox";

// ── Helpers ───────────────────────────────────────────────────────────────────

function slugify(val: string): string {
  return val
    .toLowerCase()
    .replace(/[^a-z0-9-]/g, "-")
    .replace(/--+/g, "-")
    .replace(/^-|-$/g, "");
}

const SCHEDULE_OPTIONS = [
  { value: "manual", label: "Manual" },
  { value: "realtime", label: "Real-time" },
  { value: "hourly", label: "Every hour" },
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
];

const CATEGORY_ICONS: Record<string, typeof Cloud> = {
  cloud_infrastructure: Cloud,
  cloud_provider: Cloud,
  identity_provider: Shield,
  source_control: Github,
  project_management: Activity,
  database: Database,
  container_orchestration: Server,
  "logging_&_monitoring": Activity,
  logging_monitoring: Activity,
  it_service_management: Settings2,
  communication: Globe,
  custom: Plug,
};

function getCategoryIcon(code: string) {
  const normalized = code.toLowerCase().replace(/\s+/g, "_");
  return CATEGORY_ICONS[normalized] || Plug;
}

const TYPE_ICONS: Record<string, typeof Cloud> = {
  github: Github,
  gitlab: Globe,
  bitbucket: Globe,
  aws: Cloud,
  azure: Cloud,
  azure_storage: Cloud,
  gcp: Cloud,
  postgres: Database,
  postgresql: Database,
  mysql: Database,
  kubernetes: Server,
  k8s: Server,
};

function getTypeIcon(code: string) {
  return TYPE_ICONS[code.toLowerCase()] || Plug;
}

function matchesDefaultType(
  typeCode: string,
  defaults?: { categoryCode?: string; typeCode?: string }
) {
  return defaults?.typeCode?.toLowerCase() === typeCode.toLowerCase();
}

function ConfigFieldInput({
  field,
  value,
  onChange,
  autoFocus,
}: {
  field: ConnectorConfigField;
  value: string;
  onChange: (val: string) => void;
  autoFocus?: boolean;
}) {
  const base =
    "w-full rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors";
  if (field.type === "select" && field.options) {
    return (
      <select
        className={`h-9 ${base}`}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        autoFocus={autoFocus}
      >
        <option value="">Select...</option>
        {field.options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    );
  }
  if (field.type === "textarea") {
    return (
      <textarea
        className={`min-h-[80px] py-2 ${base} resize-y`}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={field.placeholder}
        autoFocus={autoFocus}
      />
    );
  }
  return (
    <input
      type={field.type === "password" ? "password" : "text"}
      className={`h-9 ${base}`}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={field.placeholder}
      autoComplete={field.type === "password" ? "new-password" : "off"}
      autoFocus={autoFocus}
    />
  );
}

// ── Steps ─────────────────────────────────────────────────────────────────────

function StepIndicator({ current }: { current: 1 | 2 }) {
  return (
    <div className="flex items-center gap-2 mb-1">
      <div
        className={`flex items-center gap-1.5 text-xs font-medium ${current === 1 ? "text-primary" : "text-muted-foreground"}`}
      >
        <span
          className={`h-5 w-5 rounded-full flex items-center justify-center text-[10px] font-bold ${current === 1 ? "bg-primary text-primary-foreground" : "bg-primary/20 text-primary"}`}
        >
          {current > 1 ? <CheckCircle2 className="h-3.5 w-3.5" /> : "1"}
        </span>
        Select Type
      </div>
      <div className="h-px flex-1 bg-border" />
      <div
        className={`flex items-center gap-1.5 text-xs font-medium ${current === 2 ? "text-primary" : "text-muted-foreground"}`}
      >
        <span
          className={`h-5 w-5 rounded-full flex items-center justify-center text-[10px] font-bold ${current === 2 ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}
        >
          2
        </span>
        Configure
      </div>
    </div>
  );
}

// ── Component ─────────────────────────────────────────────────────────────────

export function CreateConnectorDialog({
  open,
  orgId,
  workspaceId,
  onCreated,
  onClose,
  defaults,
  initialCategories,
  initialTypesByCategory,
}: {
  open: boolean;
  orgId: string;
  workspaceId?: string;
  onCreated: () => void;
  onClose: () => void;
  defaults?: { categoryCode?: string; typeCode?: string };
  initialCategories?: DimensionResponse[];
  initialTypesByCategory?: Record<string, DimensionResponse[]>;
}) {
  const [step, setStep] = useState<1 | 2>(1);
  const [categories, setCategories] = useState<DimensionResponse[]>(
    initialCategories ?? []
  );
  const [typesByCategory, setTypesByCategory] = useState<
    Record<string, DimensionResponse[]>
  >(initialTypesByCategory ?? {});
  const [selectedCategory, setSelectedCategory] = useState("");
  const [typesLoading, setTypesLoading] = useState(false);
  const [selectedType, setSelectedType] = useState("");
  const [selectedTypeName, setSelectedTypeName] = useState("");
  const [versions, setVersions] = useState<AssetVersionResponse[]>([]);
  const [versionsLoading, setVersionsLoading] = useState(false);
  const [selectedVersion, setSelectedVersion] = useState("");
  const [instanceCode, setInstanceCode] = useState("");
  const [connectorName, setConnectorName] = useState("");
  const [description, setDescription] = useState("");
  const [schedule, setSchedule] = useState("manual");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const [testResult, setTestResult] = useState<ConnectorTestResult | null>(
    null
  );
  const [testing, setTesting] = useState(false);

  const [configSchema, setConfigSchema] =
    useState<ConnectorConfigSchemaResponse | null>(null);
  const [schemaLoading, setSchemaLoading] = useState(false);
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({});
  const [typeSearch, setTypeSearch] = useState("");
  const [hasAppliedDefaultSelection, setHasAppliedDefaultSelection] =
    useState(false);

  const nameInputRef = useRef<HTMLInputElement>(null);

  // Load categories + eagerly pre-fetch all types so empty categories are hidden
  useEffect(() => {
    const loadAll = async (cats: DimensionResponse[]) => {
      setCategories(cats);
      const entries = await Promise.all(
        cats.map(async (cat) => {
          try {
            const types = await listConnectorTypes(cat.code);
            return [cat.code, types] as const;
          } catch {
            return [cat.code, []] as const;
          }
        })
      );
      setTypesByCategory((prev) => {
        const next = { ...prev };
        for (const [code, types] of entries) {
          if (!next[code]) next[code] = [...types];
        }
        return next;
      });
    };

    if (initialCategories && initialCategories.length > 0) {
      if (
        initialTypesByCategory &&
        Object.keys(initialTypesByCategory).length > 0
      ) {
        setCategories(initialCategories);
        setTypesByCategory(initialTypesByCategory);
      } else {
        void loadAll(initialCategories);
      }
      return;
    }
    listConnectorCategories()
      .then(loadAll)
      .catch(() => setCategories([]));
  }, [initialCategories, initialTypesByCategory]); // eslint-disable-line react-hooks/exhaustive-deps

  // Reset on open
  useEffect(() => {
    if (open) {
      setStep(1);
      setSelectedCategory(
        defaults?.categoryCode ?? initialCategories?.[0]?.code ?? ""
      );
      setSelectedType("");
      setSelectedTypeName("");
      setVersions([]);
      setSelectedVersion("");
      setInstanceCode("");
      setConnectorName("");
      setDescription("");
      setSchedule("manual");
      setSaving(false);
      setError(null);
      setTestResult(null);
      setConfigSchema(null);
      setFieldValues({});
      setShowAdvanced(false);
      setTypeSearch("");
      setHasAppliedDefaultSelection(false);
    }
  }, [open, defaults, initialCategories]);

  // Load types when category changes
  useEffect(() => {
    if (!selectedCategory) {
      setSelectedType("");
      return;
    }
    if (typesByCategory[selectedCategory]) return;
    setTypesLoading(true);
    listConnectorTypes(selectedCategory)
      .then((t) => {
        setTypesByCategory((prev) => ({ ...prev, [selectedCategory]: t }));
        setSelectedType("");
      })
      .catch(() =>
        setTypesByCategory((prev) => ({ ...prev, [selectedCategory]: [] }))
      )
      .finally(() => setTypesLoading(false));
  }, [selectedCategory, typesByCategory]);

  const types = useMemo(
    () => typesByCategory[selectedCategory] ?? [],
    [selectedCategory, typesByCategory]
  );

  const filteredTypes = useMemo(() => {
    const term = typeSearch.trim().toLowerCase();
    if (!term) return types;
    return types.filter(
      (type) =>
        type.name.toLowerCase().includes(term) ||
        type.code.toLowerCase().includes(term)
    );
  }, [typeSearch, types]);

  const totalConnectorTypes = useMemo(() => {
    const visited = Object.values(typesByCategory).reduce(
      (count, group) => count + group.length,
      0
    );
    return visited > 0 ? visited : types.length;
  }, [typesByCategory, types]);

  // Only show categories that have at least one connector type
  const visibleCategories = useMemo(
    () => categories.filter((cat) => (typesByCategory[cat.code]?.length ?? 0) > 0),
    [categories, typesByCategory]
  );

  const selectedCategoryMeta =
    categories.find((category) => category.code === selectedCategory) ?? null;

  useEffect(() => {
    if (
      !open ||
      !selectedCategory ||
      !defaults?.typeCode ||
      hasAppliedDefaultSelection
    )
      return;
    const matchingType = (typesByCategory[selectedCategory] ?? []).find(
      (type) => matchesDefaultType(type.code, defaults)
    );
    if (!matchingType) return;
    setSelectedType(matchingType.code);
    setSelectedTypeName(matchingType.name);
    setStep(2);
    setHasAppliedDefaultSelection(true);
  }, [
    open,
    selectedCategory,
    defaults,
    typesByCategory,
    hasAppliedDefaultSelection,
  ]);

  // Reset test when type/fields change
  useEffect(() => {
    setTestResult(null);
  }, [selectedType, fieldValues]);

  // Load versions + schema when type selected
  useEffect(() => {
    if (!selectedType) {
      setVersions([]);
      setSelectedVersion("");
      setConfigSchema(null);
      setFieldValues({});
      return;
    }
    setVersionsLoading(true);
    setSchemaLoading(true);
    listAssetVersions(selectedType)
      .then((v) => {
        setVersions(v);
        const latest = v.find((ver) => ver.is_latest);
        setSelectedVersion(latest?.id ?? v[0]?.id ?? "");
      })
      .catch(() => setVersions([]))
      .finally(() => setVersionsLoading(false));
    getConnectorConfigSchema(selectedType)
      .then((schema) => {
        setConfigSchema(schema);
        if (schema) {
          const init: Record<string, string> = {};
          for (const f of schema.fields) init[f.key] = "";
          setFieldValues(init);
        }
      })
      .catch(() => setConfigSchema(null))
      .finally(() => setSchemaLoading(false));
  }, [selectedType]);

  // Focus name input when entering step 2
  useEffect(() => {
    if (step === 2) {
      setTimeout(() => nameInputRef.current?.focus(), 100);
    }
  }, [step]);

  useEffect(() => {
    if (!open || selectedCategory || visibleCategories.length === 0) return;
    setSelectedCategory(defaults?.categoryCode ?? visibleCategories[0].code);
  }, [open, selectedCategory, visibleCategories, defaults]);

  function setField(key: string, val: string) {
    setFieldValues((prev) => ({ ...prev, [key]: val }));
  }

  function selectType(code: string, name: string) {
    setSelectedType(code);
    setSelectedTypeName(name);
    setError(null);
    setStep(2);
  }

  function buildCredentialsAndProps() {
    const creds: Record<string, string> = {};
    const props: Record<string, string> = {};
    if (description.trim()) props.description = description.trim();
    if (configSchema) {
      for (const f of configSchema.fields) {
        const val = fieldValues[f.key]?.trim();
        if (!val) continue;
        if (f.credential) creds[f.key] = val;
        else props[f.key] = val;
      }
    }
    return { creds, props };
  }

  async function handleTestConnection() {
    if (!selectedType) {
      setError("Select a connector type first.");
      return;
    }
    setTesting(true);
    setError(null);
    setTestResult(null);
    try {
      const { creds, props } = buildCredentialsAndProps();
      const result = await preflightTestConnector({
        connector_type_code: selectedType,
        credentials: Object.keys(creds).length > 0 ? creds : undefined,
        properties: Object.keys(props).length > 0 ? props : undefined,
      });
      setTestResult(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Test failed");
    } finally {
      setTesting(false);
    }
  }

  async function doSave(isDraft: boolean) {
    if (!instanceCode.trim()) {
      setError("Name is required.");
      return;
    }
    if (!isDraft && configSchema) {
      for (const f of configSchema.fields) {
        if (f.required && !fieldValues[f.key]?.trim()) {
          setError(`"${f.label}" is required.`);
          return;
        }
      }
    }
    setSaving(true);
    setError(null);
    try {
      const { creds, props } = buildCredentialsAndProps();
      await createConnector(orgId, {
        instance_code: instanceCode.trim(),
        connector_type_code: selectedType,
        workspace_id: workspaceId || undefined,
        asset_version_id: selectedVersion || undefined,
        collection_schedule: schedule,
        name: connectorName.trim() || undefined,
        properties: Object.keys(props).length > 0 ? props : undefined,
        credentials: Object.keys(creds).length > 0 ? creds : undefined,
        is_draft: isDraft,
      });
      onCreated();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create connector");
      setSaving(false);
    }
  }

  const propertyFields =
    configSchema?.fields.filter((f) => !f.credential) ?? [];
  const credentialFields =
    configSchema?.fields.filter((f) => f.credential) ?? [];
  const TypeIcon = getTypeIcon(selectedType);
  const SelectedCategoryIcon = getCategoryIcon(selectedCategory || "custom");

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        if (!v) onClose();
      }}
    >
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-5xl">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-primary/10 p-2.5">
              {step === 2 ? (
                <TypeIcon className="h-4 w-4 text-primary" />
              ) : (
                <Plus className="h-4 w-4 text-primary" />
              )}
            </div>
            <div>
              <DialogTitle>
                {step === 1 ? "Add Connector" : `Configure ${selectedTypeName}`}
              </DialogTitle>
              <DialogDescription>
                {step === 1
                  ? "Choose a connector type to get started"
                  : "Fill in the details to connect your infrastructure"}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <StepIndicator current={step} />

        {/* ── Step 1: Choose Type ─────────────────────────────────────────── */}
        {step === 1 && (
          <div className="space-y-4 mt-2">
            <div className="rounded-xl border border-border/60 bg-card/70 p-4">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <p className="text-sm font-medium text-foreground">
                    Pick the system you want to connect
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Start with a category, then choose the exact connector type.
                    Search works on connector name and code.
                  </p>
                </div>
                <div className="flex flex-wrap gap-2 text-xs">
                  <span className="rounded-full border border-border/60 bg-muted/40 px-3 py-1 text-muted-foreground">
                    {visibleCategories.length} categories
                  </span>
                  <span className="rounded-full border border-border/60 bg-muted/40 px-3 py-1 text-muted-foreground">
                    {totalConnectorTypes} connector types
                  </span>
                </div>
              </div>

              <div className="relative mt-4">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={typeSearch}
                  onChange={(e) => setTypeSearch(e.target.value)}
                  placeholder="Search connector types..."
                  className="h-10 rounded-xl border-border/60 bg-background/70 pl-9"
                />
              </div>
            </div>

            <div className="grid gap-4 lg:grid-cols-[280px_minmax(0,1fr)]">
              <div className="rounded-xl border border-border/60 bg-card/70 p-3">
                <div className="mb-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                    Categories
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Choose the source area that best matches your tool.
                  </p>
                </div>

                <div className="space-y-2">
                  {visibleCategories.map((cat) => {
                    const CatIcon = getCategoryIcon(cat.code);
                    const isActive = selectedCategory === cat.code;
                    const count = typesByCategory[cat.code]?.length;
                    return (
                      <button
                        key={cat.code}
                        onClick={() => setSelectedCategory(cat.code)}
                        className={`flex w-full items-center gap-3 rounded-xl border px-3 py-3 text-left transition-all ${
                          isActive
                            ? "border-primary/40 bg-primary/10 shadow-sm"
                            : "border-border/50 bg-background/50 hover:border-border hover:bg-muted/30"
                        }`}
                      >
                        <div
                          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${
                            isActive
                              ? "bg-primary/15 text-primary"
                              : "bg-muted text-muted-foreground"
                          }`}
                        >
                          <CatIcon className="h-4 w-4" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <p
                            className={`text-sm font-medium ${isActive ? "text-foreground" : "text-muted-foreground"}`}
                          >
                            {cat.name}
                          </p>
                          <p className="mt-0.5 text-[11px] text-muted-foreground">
                            {count != null
                              ? `${count} connector${count === 1 ? "" : "s"}`
                              : "Click to load"}
                          </p>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="rounded-xl border border-border/60 bg-card/70 p-3">
                <div className="mb-3 flex flex-col gap-1 border-b border-border/50 pb-3 sm:flex-row sm:items-end sm:justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <SelectedCategoryIcon className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-foreground">
                        {selectedCategoryMeta?.name ?? "Connector Types"}
                      </p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {selectedCategoryMeta
                          ? "Select a connector type to continue to configuration."
                          : "Choose a category to view available connector types."}
                      </p>
                    </div>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {filteredTypes.length} result
                    {filteredTypes.length === 1 ? "" : "s"}
                  </span>
                </div>

                {typesLoading ? (
                  <div className="grid gap-3 sm:grid-cols-2">
                    {[1, 2, 3, 4].map((i) => (
                      <div
                        key={i}
                        className="h-20 rounded-xl bg-muted/50 animate-pulse"
                      />
                    ))}
                  </div>
                ) : filteredTypes.length > 0 ? (
                  <div className="grid gap-3 sm:grid-cols-2">
                    {filteredTypes.map((t) => {
                      const TIcon = getTypeIcon(t.code);
                      return (
                        <button
                          key={t.code}
                          onClick={() => selectType(t.code, t.name)}
                          className={`group flex items-center gap-3 rounded-xl border p-3 text-left transition-all ${
                            matchesDefaultType(t.code, defaults)
                              ? "border-primary/40 bg-primary/5"
                              : "border-border/50 bg-background/50 hover:border-primary/40 hover:bg-primary/5"
                          }`}
                        >
                          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-muted/70 transition-colors group-hover:bg-primary/10">
                            <TIcon className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
                          </div>
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2">
                              <p className="text-sm font-medium text-foreground group-hover:text-primary transition-colors">
                                {t.name}
                              </p>
                              {matchesDefaultType(t.code, defaults) && (
                                <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
                                  Suggested
                                </span>
                              )}
                            </div>
                            <p className="mt-1 text-[11px] text-muted-foreground truncate">
                              {t.code.replace(/_/g, " ")}
                            </p>
                          </div>
                          <ArrowRight className="ml-auto h-4 w-4 shrink-0 text-muted-foreground/40 group-hover:text-primary transition-colors" />
                        </button>
                      );
                    })}
                  </div>
                ) : (
                  <div className="flex min-h-[260px] flex-col items-center justify-center rounded-xl border border-dashed border-border/60 bg-background/30 px-6 text-center">
                    <Plug className="mb-3 h-8 w-8 text-muted-foreground/30" />
                    <p className="text-sm text-muted-foreground">
                      {typeSearch
                        ? "No connector types match your search in this category."
                        : "No connector types are available for this category yet."}
                    </p>
                    {typeSearch && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="mt-3 h-8 text-xs"
                        onClick={() => setTypeSearch("")}
                      >
                        Clear search
                      </Button>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ── Step 2: Configure ────────────────────────────────────────── */}
        {step === 2 && (
          <div className="space-y-4 mt-2">
            <div className="rounded-xl border border-primary/20 bg-primary/5 p-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="flex items-start gap-3">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary/10">
                    <TypeIcon className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      {selectedTypeName}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {selectedCategoryMeta?.name ?? "Connector"} connector. Add
                      connection details, then test before saving.
                    </p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2 text-xs">
                  <span className="rounded-full border border-border/60 bg-background/70 px-3 py-1 text-muted-foreground">
                    {propertyFields.length} config field
                    {propertyFields.length === 1 ? "" : "s"}
                  </span>
                  <span className="rounded-full border border-border/60 bg-background/70 px-3 py-1 text-muted-foreground">
                    {credentialFields.length} credential
                    {credentialFields.length === 1 ? "" : "s"}
                  </span>
                </div>
              </div>
            </div>

            {/* Connection Name (primary field) */}
            <div className="space-y-1.5">
              <Label className="text-xs font-medium">
                Connection Name <span className="text-red-500">*</span>
              </Label>
              <Input
                ref={nameInputRef}
                value={connectorName}
                onChange={(e) => {
                  setConnectorName(e.target.value);
                  setInstanceCode(slugify(e.target.value));
                }}
                placeholder={`e.g. Production ${selectedTypeName}`}
                className="h-9 text-sm"
              />
              {instanceCode && (
                <p className="text-[10px] text-muted-foreground font-mono">
                  ID: {instanceCode}
                </p>
              )}
            </div>

            {/* Schema-driven config fields */}
            {schemaLoading ? (
              <div className="space-y-3 rounded-lg border border-border/50 p-3">
                <div className="h-4 w-24 bg-muted rounded animate-pulse" />
                <div className="h-9 bg-muted rounded-md animate-pulse" />
                <div className="h-9 bg-muted rounded-md animate-pulse" />
              </div>
            ) : (
              <>
                {/* Configuration fields */}
                {propertyFields.length > 0 && (
                  <div className="rounded-lg border border-border/50 p-3 space-y-3">
                    <div className="flex items-center gap-2">
                      <Settings2 className="h-3.5 w-3.5 text-muted-foreground" />
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                        Configuration
                      </p>
                    </div>
                    {propertyFields.map((f, idx) => (
                      <div key={f.key} className="space-y-1.5">
                        <Label className="text-xs">
                          {f.label}
                          {f.required && (
                            <span className="text-red-500 ml-0.5">*</span>
                          )}
                        </Label>
                        <ConfigFieldInput
                          field={f}
                          value={fieldValues[f.key] ?? ""}
                          onChange={(v) => setField(f.key, v)}
                          autoFocus={idx === 0 && !connectorName}
                        />
                        {f.hint && (
                          <p className="text-[10px] text-muted-foreground leading-relaxed">
                            {f.hint}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Credential fields */}
                {credentialFields.length > 0 && (
                  <div className="rounded-lg border border-primary/20 bg-primary/[0.02] p-3 space-y-3">
                    <div className="flex items-center gap-2">
                      <Lock className="h-3.5 w-3.5 text-primary/60" />
                      <p className="text-xs font-medium text-primary/80 uppercase tracking-wide">
                        Credentials
                      </p>
                      <span className="text-[10px] text-muted-foreground ml-auto">
                        AES-256 encrypted
                      </span>
                    </div>
                    {credentialFields.map((f) => (
                      <div key={f.key} className="space-y-1.5">
                        <Label className="text-xs">
                          {f.label}
                          {f.required && (
                            <span className="text-red-500 ml-0.5">*</span>
                          )}
                        </Label>
                        <ConfigFieldInput
                          field={f}
                          value={fieldValues[f.key] ?? ""}
                          onChange={(v) => setField(f.key, v)}
                        />
                        {f.hint && (
                          <p className="text-[10px] text-muted-foreground leading-relaxed">
                            {f.hint}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {!configSchema && !schemaLoading && (
                  <p className="text-xs text-muted-foreground rounded-lg border border-border/50 p-3">
                    No configuration schema found for this connector type. You
                    can still save as a draft.
                  </p>
                )}
              </>
            )}

            {/* Advanced options (collapsible) */}
            <div className="rounded-lg border border-border/30">
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center justify-between w-full px-3 py-2 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
              >
                <span>Advanced Options</span>
                {showAdvanced ? (
                  <ChevronUp className="h-3.5 w-3.5" />
                ) : (
                  <ChevronDown className="h-3.5 w-3.5" />
                )}
              </button>
              {showAdvanced && (
                <div className="px-3 pb-3 space-y-3 border-t border-border/30 pt-3">
                  <div className="space-y-1.5">
                    <Label className="text-xs">Instance Code</Label>
                    <Input
                      value={instanceCode}
                      onChange={(e) => setInstanceCode(slugify(e.target.value))}
                      placeholder="auto-generated-from-name"
                      className="h-8 text-xs font-mono"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-xs">Description</Label>
                    <Input
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="Optional description..."
                      className="h-8 text-xs"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-xs">Collection Schedule</Label>
                    <select
                      className="h-8 w-full rounded-md border border-input bg-background px-3 text-xs"
                      value={schedule}
                      onChange={(e) => setSchedule(e.target.value)}
                    >
                      {SCHEDULE_OPTIONS.map((o) => (
                        <option key={o.value} value={o.value}>
                          {o.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  {selectedType && (versionsLoading || versions.length > 0) && (
                    <div className="space-y-1.5">
                      <Label className="text-xs">Asset Version</Label>
                      {versionsLoading ? (
                        <div className="h-8 bg-muted rounded-md animate-pulse" />
                      ) : (
                        <select
                          className="h-8 w-full rounded-md border border-input bg-background px-3 text-xs"
                          value={selectedVersion}
                          onChange={(e) => setSelectedVersion(e.target.value)}
                        >
                          <option value="">No version</option>
                          {versions.map((v) => (
                            <option key={v.id} value={v.id}>
                              {v.version_label}
                              {v.is_latest ? " (latest)" : ""}
                            </option>
                          ))}
                        </select>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Test result */}
            {testResult && (
              <div
                className={`flex items-center gap-2 rounded-lg border px-3 py-2.5 text-xs ${
                  testResult.health_status === "healthy"
                    ? "border-green-500/30 bg-green-500/10 text-green-600 dark:text-green-400"
                    : "border-yellow-500/30 bg-yellow-500/10 text-yellow-600 dark:text-yellow-400"
                }`}
              >
                <span
                  className={`h-2 w-2 rounded-full shrink-0 ${testResult.health_status === "healthy" ? "bg-green-500" : "bg-yellow-500"}`}
                />
                {testResult.message}
              </div>
            )}

            {error && (
              <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2.5 text-xs text-red-500">
                {error}
              </p>
            )}
          </div>
        )}

        {/* ── Footer ──────────────────────────────────────────────────── */}
        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          {step === 1 ? (
            <Button variant="outline" size="sm" onClick={onClose}>
              Cancel
            </Button>
          ) : (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setStep(1);
                  setError(null);
                }}
                disabled={saving || testing}
                className="mr-auto gap-1.5"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                Change Type
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => doSave(true)}
                disabled={saving || testing || !instanceCode.trim()}
              >
                Save Draft
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleTestConnection}
                disabled={testing || saving || !selectedType}
                className="gap-1.5"
              >
                {testing ? (
                  <span className="flex items-center gap-1.5">
                    <span className="h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent" />
                    Testing...
                  </span>
                ) : (
                  "Test Connection"
                )}
              </Button>
              <Button
                size="sm"
                onClick={() => doSave(false)}
                disabled={
                  saving ||
                  testing ||
                  !instanceCode.trim() ||
                  testResult?.health_status !== "healthy"
                }
              >
                {saving ? (
                  <span className="flex items-center gap-1.5">
                    <span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    Saving...
                  </span>
                ) : (
                  "Save Connector"
                )}
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
