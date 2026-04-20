"""Stub: monitoring.escalation.policy_create node."""

NODE_KEY = "monitoring.escalation.policy_create"
NODE_KIND = "effect"
NODE_TX_MODE = "caller"

async def handler(config, inputs, context):
    return {"policy_id": inputs.get("name")}
