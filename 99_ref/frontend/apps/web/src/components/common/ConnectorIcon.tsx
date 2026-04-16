import {
  Github,
  Cloud,
  Database,
  Shield,
  Plug,
  Server,
  Globe,
} from "lucide-react";

interface ConnectorIconProps {
  typeCode: string;
  className?: string;
}

export function ConnectorIcon({ typeCode, className }: ConnectorIconProps) {
  const cls = className ?? "h-4 w-4";
  const lower = typeCode.toLowerCase();

  if (lower.includes("github")) return <Github className={cls} />;
  if (lower.includes("aws")) return <Cloud className={cls} />;
  if (lower.includes("azure")) return <Cloud className={cls} />;
  if (lower.includes("gcp") || lower.includes("google")) return <Cloud className={cls} />;
  if (
    lower.includes("postgres") ||
    lower.includes("postgresql") ||
    lower.includes("mysql") ||
    lower.includes("database") ||
    lower.includes("db")
  ) {
    return <Database className={cls} />;
  }
  if (lower.includes("kubernetes") || lower.includes("k8s")) return <Shield className={cls} />;
  if (lower.includes("server") || lower.includes("host") || lower.includes("endpoint")) return <Server className={cls} />;
  if (lower.includes("global") || lower.includes("library") || lower.includes("world")) return <Globe className={cls} />;

  return <Plug className={cls} />;
}

const CONNECTOR_LABELS: Record<string, string> = {
  github: "GitHub",
  aws: "AWS",
  azure: "Azure",
  azure_storage: "Azure Storage",
  gcp: "Google Cloud",
  postgres: "PostgreSQL",
  postgresql: "PostgreSQL",
  mysql: "MySQL",
  kubernetes: "Kubernetes",
  k8s: "Kubernetes",
  okta: "Okta",
  entra: "Entra ID",
};

export function getConnectorLabel(typeCode: string): string {
  if (!typeCode) return "Unknown";
  const lower = typeCode.toLowerCase();
  return (
    CONNECTOR_LABELS[lower] ??
    typeCode.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
  );
}
