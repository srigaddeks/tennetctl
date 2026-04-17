---
source_file: "backend/02_features/06_notify/sub_features/04_variables/repository.py"
type: "code"
community: "Delivery Tracking & Retry"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Delivery_Tracking_&_Retry
---

# notify.template_variables repository

## Connections
- [[Concept variable resolution pipeline (static + dynamic_sql + caller override)]] - `implements` [EXTRACTED]
- [[DB table 06_notify.13_fct_notify_template_variables]] - `references` [EXTRACTED]
- [[DB view 06_notify.v_notify_template_variables]] - `references` [EXTRACTED]
- [[RenderTemplate node (notify.templates.render)]] - `calls` [EXTRACTED]
- [[notify.send service (transactional)]] - `calls` [EXTRACTED]
- [[notify.template_variables routes]] - `calls` [INFERRED]
- [[notify.templates service]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Delivery_Tracking_&_Retry