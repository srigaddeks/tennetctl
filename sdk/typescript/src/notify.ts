import type { Transport } from "./transport.js";

export class Notify {
  constructor(private readonly t: Transport) {}

  async send(args: {
    template_key: string;
    recipient_user_id: string;
    variables?: Record<string, unknown>;
    channel?: string;
    idempotency_key?: string;
  }): Promise<Record<string, unknown>> {
    const body: Record<string, unknown> = {
      template_key: args.template_key,
      recipient_user_id: args.recipient_user_id,
    };
    if (args.variables !== undefined) body.variables = args.variables;
    if (args.channel !== undefined) body.channel = args.channel;

    const headers = args.idempotency_key
      ? { "Idempotency-Key": args.idempotency_key }
      : undefined;

    return this.t.request("POST", "/v1/notify/send", { body, headers });
  }
}
