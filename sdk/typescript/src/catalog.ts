import type { Transport } from "./transport.js";

export class Catalog {
  constructor(private readonly t: Transport) {}

  async listNodes(
    filters: Record<string, string | number | boolean | undefined> = {},
  ): Promise<Array<Record<string, unknown>>> {
    const params: Record<string, string | number | boolean | undefined> = {};
    for (const [k, v] of Object.entries(filters)) if (v !== undefined) params[k] = v;
    const data = await this.t.request<Array<Record<string, unknown>>>(
      "GET",
      "/v1/catalog/nodes",
      { params: Object.keys(params).length ? params : undefined },
    );
    return Array.isArray(data) ? data : [];
  }

  async listFeatures(
    filters: Record<string, string | number | boolean | undefined> = {},
  ): Promise<Array<Record<string, unknown>>> {
    const params: Record<string, string | number | boolean | undefined> = {};
    for (const [k, v] of Object.entries(filters)) if (v !== undefined) params[k] = v;
    const data = await this.t.request<Array<Record<string, unknown>>>(
      "GET",
      "/v1/catalog/features",
      { params: Object.keys(params).length ? params : undefined },
    );
    return Array.isArray(data) ? data : [];
  }

  async listSubFeatures(feature?: string): Promise<Array<Record<string, unknown>>> {
    const params = feature ? { feature } : undefined;
    const data = await this.t.request<Array<Record<string, unknown>>>(
      "GET",
      "/v1/catalog/sub-features",
      { params },
    );
    return Array.isArray(data) ? data : [];
  }

  async getFlow(key: string): Promise<Record<string, unknown>> {
    return this.t.request("GET", `/v1/catalog/flows/${key}`);
  }
}
