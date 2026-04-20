"""Stub: monitoring.escalation.policy_update node."""

NODE_KEY = "monitoring.escalation.policy_update"
NODE_KIND = "effect"
NODE_TX_MODE = "caller"

async def handler(config, inputs, context):
    return {"policy_id": inputs.get("policy_id")}
