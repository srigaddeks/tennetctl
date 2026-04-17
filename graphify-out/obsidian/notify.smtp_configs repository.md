---
source_file: "backend/02_features/06_notify/sub_features/01_smtp_configs/repository.py"
type: "code"
community: "Delivery Tracking & Retry"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Delivery_Tracking_&_Retry
---

# notify.smtp_configs repository

## Connections
- [[DB table 06_notify.10_fct_notify_smtp_configs]] - `references` [EXTRACTED]
- [[DB view 06_notify.v_notify_smtp_configs]] - `references` [EXTRACTED]
- [[notify.email channel service (rendertracksend)]] - `calls` [EXTRACTED]
- [[notify.smtp_configs service]] - `calls` [EXTRACTED]
- [[notify.templates service]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Delivery_Tracking_&_Retry