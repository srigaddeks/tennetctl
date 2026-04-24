# Delivery Zones — Soma Delights

> Version 1.0 | Hyderabad Launch Zones | Updated: April 2026
> Source of truth for the pincode checker on /free-week and for rider route planning.

---

## Zone Structure

Delivery is organized into two tiers:

| Tier | Label | Delivery SLA | Notes |
|------|-------|-------------|-------|
| **Zone A** | Core delivery area | Before 7:00 AM guaranteed | Kukatpally kitchen ≤ 8 km radius |
| **Zone B** | Extended area | Before 8:30 AM | Slightly longer route; rider starts earlier |

---

## Zone A — Core (Guaranteed before 7 AM)

| Area | Pincodes |
|------|---------|
| Kukatpally (kitchen base) | 500072 |
| KPHB Colony | 500085 |
| Miyapur | 500049 |
| Chandanagar | 500050 |
| Lingampally | 500019 |
| Nizampet | 500090 |
| Bachupally | 500090 |
| Hafeezpet | 500049 |
| Madhapur | 500081 |
| Hitech City | 500081 |
| Kondapur | 500084 |
| Gachibowli | 500032 |
| Nanakramguda | 500032 |
| Manikonda | 500089 |
| Kokapet | 500075 |
| Financial District | 500032 |

---

## Zone B — Extended (Before 8:30 AM)

| Area | Pincodes | Status |
|------|---------|--------|
| Banjara Hills (partial) | 500034 | Active |
| Jubilee Hills (partial) | 500033 | Active |
| Tellapur | 502032 | Active |
| Nallagandla | 500019 | Active |
| Gopanpally | 500084 | Active |
| Puppalaguda | 500089 | Pilot |
| Narsingi | 500075 | Pilot |

---

## Out of Zone (Not Served)

The following areas are explicitly not served at launch. Outside this range, freshness
cannot be guaranteed within the 3-hour post-press window.

- Secunderabad / Begumpet (too far east)
- LB Nagar / Dilsukhnagar (too far south-east)
- Uppal / ECIL (too far east)
- Ameerpet / Punjagutta (possible Zone B expansion in Q3 2026)

---

## How the Pincode Checker Works

On /free-week, the user enters their 6-digit pincode. The checker:

1. Looks up the pincode in the Zone A and Zone B lists above
2. If Zone A → shows "Delivery guaranteed before 7 AM" CTA
3. If Zone B → shows "Delivery before 8:30 AM — available" CTA
4. If not found → shows "We don't deliver here yet — join the waitlist" with a WhatsApp
   button that pre-fills "I'd like Soma Delights to deliver to [pincode]"

---

## Route Planning

Rider departs kitchen at **06:30 AM**. Target: all Zone A deliveries complete by 07:00,
Zone B by 08:30.

| Route | Approx. stops | Sequence |
|-------|--------------|---------|
| Route 1 — North | Kukatpally → KPHB → Miyapur → Bachupally → Nizampet | ~15 stops |
| Route 2 — West | Kukatpally → Lingampally → Chandanagar → Hafeezpet | ~12 stops |
| Route 3 — South | Kukatpally → Kondapur → Gachibowli → Nanakramguda → Manikonda → Kokapet | ~18 stops |
| Route 4 — East | Kukatpally → Madhapur → Hitech City → Financial District | ~14 stops |

Routes 1-4 are served from day one as volume grows. At launch (5-30 customers),
the founder drives a single combined route covering Zone A only.

---

## Zone Expansion Timeline

| Phase | New Zones |
|-------|----------|
| Phase 1 (now) | Zone A only |
| Phase 2 (~Month 3) | Zone B active for full list |
| Phase 3 (~Month 6) | Ameerpet / Punjagutta / Banjara Hills full coverage |
| Phase 4 (~Month 12) | Second kitchen enables east Hyderabad |

---

## Data Maintenance

Update this file when:
- A new pincode is added after a successful test delivery
- A pincode is removed because of consistent freshness failures
- Route sequencing changes due to traffic patterns
- A new zone tier is opened

The /free-week pincode checker imports zone data from this canonical list.
If the website checker and this doc diverge, this doc wins — update the checker.
