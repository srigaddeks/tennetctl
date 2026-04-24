"""90_delivery_routes sub-feature — delivery routes + IMMUTABLE customer link.

Routes are tenant-scoped, anchored to a kitchen, with a fixed customer
sequence. Reorder = atomic DELETE all + INSERT new positions per the
lnk_ immutability rule.
"""
