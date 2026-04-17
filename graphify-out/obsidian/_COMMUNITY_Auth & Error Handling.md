---
type: community
cohesion: 0.03
members: 116
---

# Auth & Error Handling

**Cohesion:** 0.03 - loosely connected
**Members:** 116 nodes

## Members
- [[.__init__()_21]] - code - backend/01_core/errors.py
- [[.__init__()_24]] - code - backend/01_core/errors.py
- [[.__init__()_25]] - code - backend/01_core/errors.py
- [[.__init__()_22]] - code - backend/01_core/errors.py
- [[.__init__()_26]] - code - backend/01_core/errors.py
- [[.__init__()_23]] - code - backend/01_core/errors.py
- [[AppError]] - code - backend/01_core/errors.py
- [[BouncePayload]] - code - backend/02_features/06_notify/sub_features/07_email/routes.py
- [[Called by channel workers (11-040506) to advance delivery status.]] - rationale - backend/02_features/06_notify/sub_features/06_deliveries/service.py
- [[Create a 6-digit OTP and enqueue email delivery. Always returns (no enumeration)]] - rationale - backend/02_features/03_iam/sub_features/12_otp/service.py
- [[DeliveryPatchBody]] - code - backend/02_features/06_notify/sub_features/06_deliveries/routes.py
- [[DeliveryRow]] - code - backend/02_features/06_notify/sub_features/06_deliveries/schemas.py
- [[GET v1notifypreferences      Returns all 16 (channel × category) combinations]] - rationale - backend/02_features/06_notify/sub_features/09_preferences/routes.py
- [[Insert or skip on conflict (org_id, email). Returns the row or None if dup.]] - rationale - backend/02_features/06_notify/sub_features/16_suppression/repository.py
- [[Internal — called by the worker and the transactional API. No audit emit.     Re]] - rationale - backend/02_features/06_notify/sub_features/06_deliveries/service.py
- [[Mark a delivery as read, across any channel.      Only `status opened` is sup]] - rationale - backend/02_features/06_notify/sub_features/06_deliveries/routes.py
- [[PATCH v1notifypreferences      Upsert one or more preference rows. Each item]] - rationale - backend/02_features/06_notify/sub_features/09_preferences/routes.py
- [[Push expires_at out by the configured TTL. Session must be owned + still live.]] - rationale - backend/02_features/03_iam/sub_features/09_sessions/service.py
- [[RFC 8058 one-click unsubscribe — token on query string, form-encoded body.]] - rationale - backend/02_features/06_notify/sub_features/16_suppression/routes.py
- [[Record a bounce received from an SMTP provider.      Hard bounces (any bounce hi]] - rationale - backend/02_features/06_notify/sub_features/07_email/routes.py
- [[Record a link click and redirect to the original URL.]] - rationale - backend/02_features/06_notify/sub_features/07_email/routes.py
- [[Record an email open and return a 1px transparent GIF.]] - rationale - backend/02_features/06_notify/sub_features/07_email/routes.py
- [[Recursive condition evaluator. Supports       {op andor, children ...}]] - rationale - backend/02_features/09_featureflags/sub_features/05_evaluations/service.py
- [[Return all 16 (channel × category) preference rows for the user.     Missing row]] - rationale - backend/02_features/06_notify/sub_features/09_preferences/service.py
- [[Return count of unread deliveries for a user across all channels.      Unread =]] - rationale - backend/02_features/06_notify/sub_features/06_deliveries/service.py
- [[Return most-recent unconsumed, unexpired OTP for email.]] - rationale - backend/02_features/03_iam/sub_features/12_otp/repository.py
- [[Returns stored is_opted_in, or None if no preference row exists.     Callers sho]] - rationale - backend/02_features/06_notify/sub_features/09_preferences/repository.py
- [[Server-computed unread notification count for the current user.      Unread = st]] - rationale - backend/02_features/06_notify/sub_features/06_deliveries/routes.py
- [[Upsert one preference row. Raises ValidationError for unknown codes.     Critica]] - rationale - backend/02_features/06_notify/sub_features/09_preferences/service.py
- [[Validate token, flip preferences, add to suppression list. Returns (email, categ]] - rationale - backend/02_features/06_notify/sub_features/16_suppression/routes.py
- [[ValidationError]] - code - backend/01_core/errors.py
- [[Verify OTP code; return (session_token, user, session) on success.]] - rationale - backend/02_features/03_iam/sub_features/12_otp/service.py
- [[_apply_unsubscribe()]] - code - backend/02_features/06_notify/sub_features/16_suppression/routes.py
- [[_cache_get()]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/service.py
- [[_cache_put()]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/service.py
- [[_category_by_code()]] - code - backend/02_features/06_notify/sub_features/09_preferences/service.py
- [[_channel_by_code()]] - code - backend/02_features/06_notify/sub_features/09_preferences/service.py
- [[_emit_cardinality_failure()]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/service.py
- [[_hash_code()]] - code - backend/02_features/03_iam/sub_features/12_otp/service.py
- [[_resolve_metric()]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/service.py
- [[_resolve_resource()]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/service.py
- [[_validate_labels()]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/service.py
- [[add_suppression()_1]] - code - backend/02_features/06_notify/sub_features/16_suppression/repository.py
- [[add_suppression_route()]] - code - backend/02_features/06_notify/sub_features/16_suppression/routes.py
- [[bounce_webhook_route()]] - code - backend/02_features/06_notify/sub_features/07_email/routes.py
- [[click_tracking_route()]] - code - backend/02_features/06_notify/sub_features/07_email/routes.py
- [[count_recent_otp_by_email()]] - code - backend/02_features/03_iam/sub_features/12_otp/repository.py
- [[create_delivery()_1]] - code - backend/02_features/06_notify/sub_features/06_deliveries/repository.py
- [[create_delivery()]] - code - backend/02_features/06_notify/sub_features/06_deliveries/service.py
- [[create_delivery_event()]] - code - backend/02_features/06_notify/sub_features/06_deliveries/repository.py
- [[create_otp_code()]] - code - backend/02_features/03_iam/sub_features/12_otp/repository.py
- [[create_totp_credential()]] - code - backend/02_features/03_iam/sub_features/12_otp/repository.py
- [[delete_suppression_route()]] - code - backend/02_features/06_notify/sub_features/16_suppression/routes.py
- [[delete_totp()]] - code - backend/02_features/03_iam/sub_features/12_otp/service.py
- [[delete_totp_credential()]] - code - backend/02_features/03_iam/sub_features/12_otp/repository.py
- [[delete_totp_route()]] - code - backend/02_features/03_iam/sub_features/12_otp/routes.py
- [[errors.py_1]] - code - backend/01_core/errors.py
- [[get_active_otp()]] - code - backend/02_features/03_iam/sub_features/12_otp/repository.py
- [[get_delivery()_1]] - code - backend/02_features/06_notify/sub_features/06_deliveries/repository.py
- [[get_delivery()]] - code - backend/02_features/06_notify/sub_features/06_deliveries/service.py
- [[get_delivery_route()]] - code - backend/02_features/06_notify/sub_features/06_deliveries/routes.py
- [[get_metric()]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/service.py
- [[get_metric_by_id()]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/repository.py
- [[get_metric_by_key()]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/repository.py
- [[get_opt_in()]] - code - backend/02_features/06_notify/sub_features/09_preferences/repository.py
- [[get_totp_credential()]] - code - backend/02_features/03_iam/sub_features/12_otp/repository.py
- [[increment()]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/service.py
- [[increment_otp_attempts()]] - code - backend/02_features/03_iam/sub_features/12_otp/repository.py
- [[is_opted_in()]] - code - backend/02_features/06_notify/sub_features/09_preferences/service.py
- [[list_deliveries()_1]] - code - backend/02_features/06_notify/sub_features/06_deliveries/repository.py
- [[list_deliveries()]] - code - backend/02_features/06_notify/sub_features/06_deliveries/service.py
- [[list_deliveries_route()]] - code - backend/02_features/06_notify/sub_features/06_deliveries/routes.py
- [[list_metrics()_1]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/repository.py
- [[list_metrics()]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/service.py
- [[list_preferences()_1]] - code - backend/02_features/06_notify/sub_features/09_preferences/repository.py
- [[list_preferences()]] - code - backend/02_features/06_notify/sub_features/09_preferences/service.py
- [[list_preferences_route()]] - code - backend/02_features/06_notify/sub_features/09_preferences/routes.py
- [[list_suppressions_route()]] - code - backend/02_features/06_notify/sub_features/16_suppression/routes.py
- [[list_totp()]] - code - backend/02_features/03_iam/sub_features/12_otp/service.py
- [[list_totp_credentials()]] - code - backend/02_features/03_iam/sub_features/12_otp/repository.py
- [[list_totp_route()]] - code - backend/02_features/03_iam/sub_features/12_otp/routes.py
- [[mark_otp_consumed()]] - code - backend/02_features/03_iam/sub_features/12_otp/repository.py
- [[mark_read()]] - code - backend/02_features/06_notify/sub_features/06_deliveries/service.py
- [[mark_totp_used()]] - code - backend/02_features/03_iam/sub_features/12_otp/repository.py
- [[metrics_store()]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/repository.py
- [[observe_histogram()]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/service.py
- [[open_tracking_route()]] - code - backend/02_features/06_notify/sub_features/07_email/routes.py
- [[patch_delivery_route()]] - code - backend/02_features/06_notify/sub_features/06_deliveries/routes.py
- [[patch_preferences_route()]] - code - backend/02_features/06_notify/sub_features/09_preferences/routes.py
- [[register_metric()]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/service.py
- [[remove_suppression()_1]] - code - backend/02_features/06_notify/sub_features/16_suppression/repository.py
- [[repository.py_20]] - code - backend/02_features/03_iam/sub_features/12_otp/repository.py
- [[repository.py_23]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/repository.py
- [[repository.py_6]] - code - backend/02_features/06_notify/sub_features/06_deliveries/repository.py
- [[repository.py_10]] - code - backend/02_features/06_notify/sub_features/09_preferences/repository.py
- [[request_otp()]] - code - backend/02_features/03_iam/sub_features/12_otp/service.py
- [[resources_store()]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/repository.py
- [[routes.py_7]] - code - backend/02_features/06_notify/sub_features/06_deliveries/routes.py
- [[routes.py_10]] - code - backend/02_features/06_notify/sub_features/07_email/routes.py
- [[routes.py_12]] - code - backend/02_features/06_notify/sub_features/09_preferences/routes.py
- [[routes.py_3]] - code - backend/02_features/06_notify/sub_features/16_suppression/routes.py
- [[service.py_20]] - code - backend/02_features/03_iam/sub_features/12_otp/service.py
- [[service.py_24]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/service.py
- [[service.py_5]] - code - backend/02_features/06_notify/sub_features/06_deliveries/service.py
- [[service.py_10]] - code - backend/02_features/06_notify/sub_features/09_preferences/service.py
- [[set_gauge()]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/service.py
- [[unread_count()]] - code - backend/02_features/06_notify/sub_features/06_deliveries/service.py
- [[unread_count_route()]] - code - backend/02_features/06_notify/sub_features/06_deliveries/routes.py
- [[unsubscribe_one_click_route()]] - code - backend/02_features/06_notify/sub_features/16_suppression/routes.py
- [[unsubscribe_preview_route()]] - code - backend/02_features/06_notify/sub_features/16_suppression/routes.py
- [[update_delivery_status()_1]] - code - backend/02_features/06_notify/sub_features/06_deliveries/repository.py
- [[update_delivery_status()]] - code - backend/02_features/06_notify/sub_features/06_deliveries/service.py
- [[upsert_preference()_1]] - code - backend/02_features/06_notify/sub_features/09_preferences/repository.py
- [[upsert_preference()]] - code - backend/02_features/06_notify/sub_features/09_preferences/service.py
- [[verify_otp()]] - code - backend/02_features/03_iam/sub_features/12_otp/service.py
- [[verify_totp()]] - code - backend/02_features/03_iam/sub_features/12_otp/service.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Auth_&_Error_Handling
SORT file.name ASC
```

## Connections to other communities
- 68 edges to [[_COMMUNITY_Service & Repository Layer]]
- 47 edges to [[_COMMUNITY_API Routes & Response Handling]]
- 12 edges to [[_COMMUNITY_Session Auth & Middleware]]
- 9 edges to [[_COMMUNITY_Node Catalog & Feature Implementations]]
- 7 edges to [[_COMMUNITY_Notify Templates & Email Delivery]]
- 7 edges to [[_COMMUNITY_Admin Routes & DLQ]]
- 4 edges to [[_COMMUNITY_Monitoring Dashboards Backend]]
- 3 edges to [[_COMMUNITY_Audit Emit Pipeline]]
- 3 edges to [[_COMMUNITY_Core Infrastructure]]
- 3 edges to [[_COMMUNITY_Monitoring Query DSL]]
- 3 edges to [[_COMMUNITY_Alert Evaluator Worker]]
- 3 edges to [[_COMMUNITY_Monitoring Stores & Workers]]
- 2 edges to [[_COMMUNITY_Feature Flag Evaluations Node]]
- 1 edge to [[_COMMUNITY_Audit Events & Saved Views]]

## Top bridge nodes
- [[AppError]] - degree 67, connects to 9 communities
- [[register_metric()]] - degree 10, connects to 6 communities
- [[ValidationError]] - degree 31, connects to 4 communities
- [[errors.py_1]] - degree 7, connects to 4 communities
- [[list_suppressions_route()]] - degree 7, connects to 4 communities