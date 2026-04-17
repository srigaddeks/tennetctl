---
source_file: "backend/02_features/06_notify/sub_features/03_templates/repository.py"
type: "code"
community: "Delivery Tracking & Retry"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Delivery_Tracking_&_Retry
---

# notify.templates repository

## Connections
- [[DB table 06_notify.12_fct_notify_templates]] - `references` [EXTRACTED]
- [[DB table 06_notify.20_dtl_notify_template_bodies]] - `references` [EXTRACTED]
- [[DB view 06_notify.v_notify_deliveries]] - `references` [EXTRACTED]
- [[DB view 06_notify.v_notify_templates]] - `references` [EXTRACTED]
- [[RenderTemplate node (notify.templates.render)]] - `calls` [EXTRACTED]
- [[notify.email channel service (rendertracksend)]] - `calls` [EXTRACTED]
- [[notify.send service (transactional)]] - `calls` [EXTRACTED]
- [[notify.templates routes]] - `calls` [EXTRACTED]
- [[notify.templates service]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Delivery_Tracking_&_Retry