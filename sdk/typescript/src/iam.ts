import type { Transport } from "./transport.js";

class ReadResource {
  constructor(
    private readonly t: Transport,
    private readonly path: string,
  ) {}

  async list(filters: Record<string, string | number | boolean | undefined> = {}): Promise<
    Array<Record<string, unknown>>
  > {
    const params: Record<string, string | number | boolean | undefined> = {};
    for (const [k, v] of Object.entries(filters)) {
      if (v !== undefined) params[k] = v;
    }
    const data = await this.t.request<Array<Record<string, unknown>>>(
      "GET",
      this.path,
      { params: Object.keys(params).length ? params : undefined },
    );
    return Array.isArray(data) ? data : [];
  }

  async get(id: string): Promise<Record<string, unknown>> {
    return this.t.request("GET", `${this.path}/${id}`);
  }
}

export class IAM {
  readonly users: ReadResource;
  readonly orgs: ReadResource;
  readonly workspaces: ReadResource;
  readonly roles: ReadResource;
  readonly groups: ReadResource;

  constructor(t: Transport) {
    this.users = new ReadResource(t, "/v1/users");
    this.orgs = new ReadResource(t, "/v1/orgs");
    this.workspaces = new ReadResource(t, "/v1/workspaces");
    this.roles = new ReadResource(t, "/v1/roles");
    this.groups = new ReadResource(t, "/v1/groups");
  }
}
