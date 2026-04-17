---
type: community
cohesion: 0.07
members: 40
---

# Delivery Tracking & Retry

**Cohesion:** 0.07 - loosely connected
**Members:** 40 nodes

## Members
- [[Concept Jinja2 template rendering (subject + html + text)]] - document - backend/02_features/06_notify/sub_features/03_templates/nodes/render_template.py
- [[Concept RFC 8058 one-click unsubscribe header (List-Unsubscribe)]] - document - backend/02_features/06_notify/sub_features/07_email/service.py
- [[Concept SMTP password stored in vault, fetched at send time]] - document - backend/02_features/06_notify/sub_features/01_smtp_configs/schemas.py
- [[Concept delivery status lifecycle (queued → sent → openedclickedfailed)]] - document - backend/02_features/06_notify/sub_features/06_deliveries/service.py
- [[Concept dynamic_sql variable safelist (SELECT-only, DMLDDL blocked, allowed context keys)]] - document - backend/02_features/06_notify/sub_features/03_templates/nodes/safelist.py
- [[Concept email suppression list check before send]] - document - backend/02_features/06_notify/sub_features/07_email/service.py
- [[Concept exponential backoff retry for delivery failures (60s, 120s, 240s...)]] - document - backend/02_features/06_notify/sub_features/06_deliveries/repository.py
- [[Concept fallback channel chain (scheduled deliveries on alternate channels)]] - document - backend/02_features/06_notify/sub_features/11_send/service.py
- [[Concept idempotency key dedup for transactional sends]] - document - backend/02_features/06_notify/sub_features/06_deliveries/repository.py
- [[Concept in-app delivery auto-advances to delivered on creation]] - document - backend/02_features/06_notify/sub_features/06_deliveries/service.py
- [[Concept pytracking open pixel + click wrapping for email]] - document - backend/02_features/06_notify/sub_features/07_email/service.py
- [[Concept variable resolution pipeline (static + dynamic_sql + caller override)]] - document - backend/02_features/06_notify/sub_features/04_variables/repository.py
- [[DB table 06_notify.10_fct_notify_smtp_configs]] - code - backend/02_features/06_notify/sub_features/01_smtp_configs/repository.py
- [[DB table 06_notify.12_fct_notify_templates]] - code - backend/02_features/06_notify/sub_features/03_templates/repository.py
- [[DB table 06_notify.13_fct_notify_template_variables]] - code - backend/02_features/06_notify/sub_features/04_variables/repository.py
- [[DB table 06_notify.15_fct_notify_deliveries]] - code - backend/02_features/06_notify/sub_features/06_deliveries/repository.py
- [[DB table 06_notify.20_dtl_notify_template_bodies]] - code - backend/02_features/06_notify/sub_features/03_templates/repository.py
- [[DB table 06_notify.61_evt_notify_delivery_events]] - code - backend/02_features/06_notify/sub_features/06_deliveries/repository.py
- [[DB view 06_notify.v_notify_deliveries]] - code - backend/02_features/06_notify/sub_features/06_deliveries/repository.py
- [[DB view 06_notify.v_notify_smtp_configs]] - code - backend/02_features/06_notify/sub_features/01_smtp_configs/repository.py
- [[DB view 06_notify.v_notify_template_variables]] - code - backend/02_features/06_notify/sub_features/04_variables/repository.py
- [[DB view 06_notify.v_notify_templates]] - code - backend/02_features/06_notify/sub_features/03_templates/repository.py
- [[RenderTemplate node (notify.templates.render)]] - code - backend/02_features/06_notify/sub_features/03_templates/nodes/render_template.py
- [[SendTransactional node (notify.send.transactional)]] - code - backend/02_features/06_notify/sub_features/11_send/nodes/send_transactional.py
- [[notify.deliveries repository]] - code - backend/02_features/06_notify/sub_features/06_deliveries/repository.py
- [[notify.deliveries routes]] - code - backend/02_features/06_notify/sub_features/06_deliveries/routes.py
- [[notify.deliveries service]] - code - backend/02_features/06_notify/sub_features/06_deliveries/service.py
- [[notify.email channel service (rendertracksend)]] - code - backend/02_features/06_notify/sub_features/07_email/service.py
- [[notify.send routes (POST v1notifysend)]] - code - backend/02_features/06_notify/sub_features/11_send/routes.py
- [[notify.send service (transactional)]] - code - backend/02_features/06_notify/sub_features/11_send/service.py
- [[notify.smtp_configs repository]] - code - backend/02_features/06_notify/sub_features/01_smtp_configs/repository.py
- [[notify.smtp_configs routes]] - code - backend/02_features/06_notify/sub_features/01_smtp_configs/routes.py
- [[notify.smtp_configs schemas]] - code - backend/02_features/06_notify/sub_features/01_smtp_configs/schemas.py
- [[notify.smtp_configs service]] - code - backend/02_features/06_notify/sub_features/01_smtp_configs/service.py
- [[notify.template_variables repository]] - code - backend/02_features/06_notify/sub_features/04_variables/repository.py
- [[notify.template_variables routes]] - code - backend/02_features/06_notify/sub_features/04_variables/routes.py
- [[notify.templates repository]] - code - backend/02_features/06_notify/sub_features/03_templates/repository.py
- [[notify.templates routes]] - code - backend/02_features/06_notify/sub_features/03_templates/routes.py
- [[notify.templates service]] - code - backend/02_features/06_notify/sub_features/03_templates/service.py
- [[notify.templates.nodes.safelist — SQL safelist validator]] - code - backend/02_features/06_notify/sub_features/03_templates/nodes/safelist.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Delivery_Tracking_&_Retry
SORT file.name ASC
```
