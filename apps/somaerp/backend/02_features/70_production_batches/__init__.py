"""70_production_batches sub-feature — the 4 AM tracker.

State machine: planned -> in_progress -> completed | cancelled.
Auto-generates step_logs + consumption plan on create.
Auto-emits evt_inventory_movements ('consumed') on completion.
"""
