"""Stub: monitoring.escalation.policy_delete node."""

NODE_KEY = "monitoring.escalation.policy_delete"
NODE_KIND = "effect"
NODE_TX_MODE = "caller"

async def handler(config, inputs, context):
    return {"deleted": True}
