"""95_delivery_runs sub-feature — delivery runs + stops + board.

Run lifecycle: planned -> in_transit -> completed | cancelled.
Stops generated from lnk_route_customers snapshot at generate-stops time;
per-stop status: pending -> delivered | missed | customer_unavailable |
cancelled | rescheduled. Completed/missed counters updated atomically.
"""
