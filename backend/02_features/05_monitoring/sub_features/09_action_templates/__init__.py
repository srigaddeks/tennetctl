"""
Action Templates — reusable parameterized delivery templates for webhooks, email, and Slack.

Supports:
- Jinja2 sandboxed template rendering with allow-listed filters
- HMAC-SHA256 signing for webhook authenticity
- Retry logic with exponential backoff
- Delivery audit log with forensics
"""
