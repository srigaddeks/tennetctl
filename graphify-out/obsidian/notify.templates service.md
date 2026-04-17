---
source_file: "backend/02_features/06_notify/sub_features/03_templates/service.py"
type: "code"
community: "Delivery Tracking & Retry"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Delivery_Tracking_&_Retry
---

# notify.templates service

## Connections
- [[Concept Jinja2 template rendering (subject + html + text)]] - `implements` [EXTRACTED]
- [[Concept SMTP password stored in vault, fetched at send time]] - `references` [EXTRACTED]
- [[notify.smtp_configs repository]] - `calls` [EXTRACTED]
- [[notify.template_variables repository]] - `calls` [EXTRACTED]
- [[notify.template_variables routes]] - `calls` [EXTRACTED]
- [[notify.templates repository]] - `calls` [EXTRACTED]
- [[notify.templates routes]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Delivery_Tracking_&_Retry