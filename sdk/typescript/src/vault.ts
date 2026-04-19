import type { Transport } from "./transport.js";

export class VaultSecrets {
  constructor(private readonly t: Transport) {}

  async list(
    filters: Record<string, string | number | boolean | undefined> = {},
  ): Promise<Array<Record<string, unknown>>> {
    const params: Record<string, string | number | boolean | undefined> = {};
    for (const [k, v] of Object.entries(filters)) if (v !== undefined) params[k] = v;
    const data = await this.t.request<Array<Record<string, unknown>>>("GET", "/v1/vault", {
      params: Object.keys(params).length ? params : undefined,
    });
    return Array.isArray(data) ? data : [];
  }

  async get(key: string): Promise<Record<string, unknown>> {
    return this.t.request("GET", `/v1/vault/${key}`);
  }

  async create(args: {
    key: string;
    value: string;
    description?: string;
  }): Promise<Record<string, unknown>> {
    const body: Record<string, unknown> = { key: args.key, value: args.value };
    if (args.description !== undefined) body.description = args.description;
    return this.t.request("POST", "/v1/vault", { body });
  }

  async rotate(key: string, args: { value: string }): Promise<Record<string, unknown>> {
    return this.t.request("POST", `/v1/vault/${key}/rotate`, { body: { value: args.value } });
  }

  async delete(key: string): Promise<void> {
    await this.t.request("DELETE", `/v1/vault/${key}`);
  }
}

export class VaultConfigs {
  constructor(private readonly t: Transport) {}

  async list(
    filters: Record<string, string | number | boolean | undefined> = {},
  ): Promise<Array<Record<string, unknown>>> {
    const params: Record<string, string | number | boolean | undefined> = {};
    for (const [k, v] of Object.entries(filters)) if (v !== undefined) params[k] = v;
    const data = await this.t.request<Array<Record<string, unknown>>>("GET", "/v1/vault-configs", {
      params: Object.keys(params).length ? params : undefined,
    });
    return Array.isArray(data) ? data : [];
  }

  async get(configId: string): Promise<Record<string, unknown>> {
    return this.t.request("GET", `/v1/vault-configs/${configId}`);
  }

  async create(body: Record<string, unknown>): Promise<Record<string, unknown>> {
    return this.t.request("POST", "/v1/vault-configs", { body });
  }

  async update(configId: string, patch: Record<string, unknown>): Promise<Record<string, unknown>> {
    return this.t.request("PATCH", `/v1/vault-configs/${configId}`, { body: patch });
  }

  async delete(configId: string): Promise<void> {
    await this.t.request("DELETE", `/v1/vault-configs/${configId}`);
  }
}

export class Vault {
  readonly secrets: VaultSecrets;
  readonly configs: VaultConfigs;
  constructor(t: Transport) {
    this.secrets = new VaultSecrets(t);
    this.configs = new VaultConfigs(t);
  }
}
