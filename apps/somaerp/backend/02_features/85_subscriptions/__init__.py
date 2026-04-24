"""85_subscriptions sub-feature — plans + plan_items + subscriptions + events.

State machine: active <-> paused; active/paused -> cancelled | ended.
Status transitions auto-insert evt_subscription_events rows.
"""
