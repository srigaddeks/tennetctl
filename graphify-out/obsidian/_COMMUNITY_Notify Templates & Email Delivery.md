---
type: community
cohesion: 0.04
members: 63
---

# Notify Templates & Email Delivery

**Cohesion:** 0.04 - loosely connected
**Members:** 63 nodes

## Members
- [[.run()_1]] - code - backend/02_features/06_notify/sub_features/03_templates/nodes/render_template.py
- [[Aggregate counts for a template's deliveries + delivery events.      Returns {by]] - rationale - backend/02_features/06_notify/sub_features/03_templates/repository.py
- [[Atomically claim queued webpush deliveries.      Uses FOR UPDATE SKIP LOCKED so]] - rationale - backend/02_features/06_notify/sub_features/08_webpush/repository.py
- [[Atomically claim up to `limit` queued email deliveries (status=queued, channel=e]] - rationale - backend/02_features/06_notify/sub_features/07_email/repository.py
- [[Background loop drain queued email deliveries every 5 seconds when idle.]] - rationale - backend/02_features/06_notify/sub_features/07_email/service.py
- [[Exception]] - code
- [[Exponential backoff 60s, 120s, 240s, 480s, ...]] - rationale - backend/02_features/06_notify/sub_features/06_deliveries/repository.py
- [[Input_1]] - code - backend/02_features/06_notify/sub_features/03_templates/nodes/render_template.py
- [[Insert or update a browser push subscription keyed on endpoint.      If the endp]] - rationale - backend/02_features/06_notify/sub_features/08_webpush/repository.py
- [[Insert template fct row, return id.]] - rationale - backend/02_features/06_notify/sub_features/03_templates/repository.py
- [[Output_1]] - code - backend/02_features/06_notify/sub_features/03_templates/nodes/render_template.py
- [[Poll + send queued email deliveries. Returns number successfully sent.     Each]] - rationale - backend/02_features/06_notify/sub_features/07_email/service.py
- [[Poll and send up to `limit` queued webpush deliveries. Returns count processed.]] - rationale - backend/02_features/06_notify/sub_features/08_webpush/service.py
- [[Record a retryable send error.      Increments attempt_count. If the new count r]] - rationale - backend/02_features/06_notify/sub_features/06_deliveries/repository.py
- [[Render + track + send a single email delivery.     Raises on any failure — calle]] - rationale - backend/02_features/06_notify/sub_features/07_email/service.py
- [[RenderTemplate]] - code - backend/02_features/06_notify/sub_features/03_templates/nodes/render_template.py
- [[Resolve email address for a delivery recipient.     Looks up 03_iam.v_users]] - rationale - backend/02_features/06_notify/sub_features/07_email/service.py
- [[Return all active webpush subscriptions for a recipient user.]] - rationale - backend/02_features/06_notify/sub_features/08_webpush/repository.py
- [[Return an active subscription matching the given endpoint URL.]] - rationale - backend/02_features/06_notify/sub_features/08_webpush/repository.py
- [[Soft-delete a subscription. Returns True if a row was actually deleted.]] - rationale - backend/02_features/06_notify/sub_features/08_webpush/repository.py
- [[Start the background email sender task. Call from app lifespan.]] - rationale - backend/02_features/06_notify/sub_features/07_email/service.py
- [[Start the webpush background sender as an asyncio Task.]] - rationale - backend/02_features/06_notify/sub_features/08_webpush/service.py
- [[Upsert per-channel body rows (INSERT ... ON CONFLICT DO UPDATE).]] - rationale - backend/02_features/06_notify/sub_features/03_templates/repository.py
- [[Wrap all links with click-tracking redirects and add an open-tracking pixel]] - rationale - backend/02_features/06_notify/sub_features/07_email/service.py
- [[_email_sender_loop()]] - code - backend/02_features/06_notify/sub_features/07_email/service.py
- [[_get_recipient_email()]] - code - backend/02_features/06_notify/sub_features/07_email/service.py
- [[_row_to_dict()]] - code - backend/02_features/06_notify/sub_features/03_templates/repository.py
- [[_send_one()]] - code - backend/02_features/06_notify/sub_features/07_email/service.py
- [[_webpush_sender_loop()]] - code - backend/02_features/06_notify/sub_features/08_webpush/service.py
- [[apply_email_tracking()]] - code - backend/02_features/06_notify/sub_features/07_email/service.py
- [[backoff_seconds_for_attempt()]] - code - backend/02_features/06_notify/sub_features/06_deliveries/repository.py
- [[create_template()_1]] - code - backend/02_features/06_notify/sub_features/03_templates/repository.py
- [[delete_template()_1]] - code - backend/02_features/06_notify/sub_features/03_templates/repository.py
- [[get_reason()]] - code - backend/02_features/06_notify/sub_features/16_suppression/repository.py
- [[get_subscription_by_endpoint()]] - code - backend/02_features/06_notify/sub_features/08_webpush/repository.py
- [[get_template()_1]] - code - backend/02_features/06_notify/sub_features/03_templates/repository.py
- [[get_template_analytics()]] - code - backend/02_features/06_notify/sub_features/03_templates/repository.py
- [[get_template_by_key()_1]] - code - backend/02_features/06_notify/sub_features/03_templates/repository.py
- [[get_user_webpush_subscriptions()]] - code - backend/02_features/06_notify/sub_features/08_webpush/repository.py
- [[is_suppressed()_1]] - code - backend/02_features/06_notify/sub_features/16_suppression/repository.py
- [[list_suppressions()_1]] - code - backend/02_features/06_notify/sub_features/16_suppression/repository.py
- [[list_templates()_1]] - code - backend/02_features/06_notify/sub_features/03_templates/repository.py
- [[mark_delivery_failed()]] - code - backend/02_features/06_notify/sub_features/08_webpush/repository.py
- [[mark_delivery_sent()]] - code - backend/02_features/06_notify/sub_features/08_webpush/repository.py
- [[mark_retryable_error()]] - code - backend/02_features/06_notify/sub_features/06_deliveries/repository.py
- [[notify.templates.render — Jinja2 StrictUndefined template rendering node.  Contr]] - rationale - backend/02_features/06_notify/sub_features/03_templates/nodes/render_template.py
- [[poll_and_claim_email_deliveries()]] - code - backend/02_features/06_notify/sub_features/07_email/repository.py
- [[poll_and_claim_webpush_deliveries()]] - code - backend/02_features/06_notify/sub_features/08_webpush/repository.py
- [[process_queued_email_deliveries()]] - code - backend/02_features/06_notify/sub_features/07_email/service.py
- [[process_queued_webpush_deliveries()]] - code - backend/02_features/06_notify/sub_features/08_webpush/service.py
- [[render_template.py]] - code - backend/02_features/06_notify/sub_features/03_templates/nodes/render_template.py
- [[repository.py_5]] - code - backend/02_features/06_notify/sub_features/03_templates/repository.py
- [[repository.py_8]] - code - backend/02_features/06_notify/sub_features/07_email/repository.py
- [[repository.py_3]] - code - backend/02_features/06_notify/sub_features/08_webpush/repository.py
- [[repository.py_2]] - code - backend/02_features/06_notify/sub_features/16_suppression/repository.py
- [[service.py_8]] - code - backend/02_features/06_notify/sub_features/07_email/service.py
- [[service.py_2]] - code - backend/02_features/06_notify/sub_features/08_webpush/service.py
- [[soft_delete_subscription()]] - code - backend/02_features/06_notify/sub_features/08_webpush/repository.py
- [[start_email_sender()]] - code - backend/02_features/06_notify/sub_features/07_email/service.py
- [[start_webpush_sender()]] - code - backend/02_features/06_notify/sub_features/08_webpush/service.py
- [[update_template()_1]] - code - backend/02_features/06_notify/sub_features/03_templates/repository.py
- [[upsert_bodies()_1]] - code - backend/02_features/06_notify/sub_features/03_templates/repository.py
- [[upsert_subscription()]] - code - backend/02_features/06_notify/sub_features/08_webpush/repository.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Notify_Templates_&_Email_Delivery
SORT file.name ASC
```

## Connections to other communities
- 18 edges to [[_COMMUNITY_Service & Repository Layer]]
- 13 edges to [[_COMMUNITY_API Routes & Response Handling]]
- 7 edges to [[_COMMUNITY_Auth & Error Handling]]
- 5 edges to [[_COMMUNITY_Audit Emit Pipeline]]
- 4 edges to [[_COMMUNITY_Core Infrastructure]]
- 3 edges to [[_COMMUNITY_Session Auth & Middleware]]
- 2 edges to [[_COMMUNITY_Alert Evaluator Worker]]
- 2 edges to [[_COMMUNITY_Monitoring Stores & Workers]]
- 2 edges to [[_COMMUNITY_Node Catalog & Feature Implementations]]
- 1 edge to [[_COMMUNITY_Monitoring Query DSL]]

## Top bridge nodes
- [[Exception]] - degree 11, connects to 6 communities
- [[_send_one()]] - degree 21, connects to 4 communities
- [[repository.py_3]] - degree 10, connects to 2 communities
- [[repository.py_2]] - degree 6, connects to 2 communities
- [[.run()_1]] - degree 6, connects to 2 communities