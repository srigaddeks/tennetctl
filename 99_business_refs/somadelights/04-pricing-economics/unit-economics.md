# 11 — Unit Economics

> Every number here uses Hyderabad wholesale prices as of early 2026. These are first-pass estimates — update monthly as you learn real costs. The goal: know exactly how much money you make (or lose) on every bottle, every order, every route, every subscriber.
>
> **Pricing context:** Subscription revenue is now calculator-driven (₹150 ceiling → ₹100 floor per unit; same price for 300 ml drinks and 100 ml shots). See `pricing-strategy.md § Active Model: Volume-Based Dynamic Pricing` for the formula. Unit economics below should be read against that floor price to check worst-case margin.

---

## Ingredient Cost Assumptions (Hyderabad Wholesale)

Sourced from Bowenpally wholesale market and Rythu Bazaar. Prices vary by season — listed ranges reflect annual variation. Use the **mid-point** for planning.

| Ingredient | Low Season (Rs/kg) | High Season (Rs/kg) | Planning Rate (Rs/kg) | Primary Source |
|---|---|---|---|---|
| Spinach | 25 | 45 | 35 | Bowenpally / Rythu Bazaar |
| Cucumber | 15 | 35 | 25 | Bowenpally |
| Apple (Shimla variety) | 100 | 160 | 130 | Bowenpally (imported) |
| Ginger | 80 | 130 | 100 | Bowenpally |
| Lemon | 50 | 100 | 70 | Rythu Bazaar |
| Carrot | 20 | 40 | 30 | Bowenpally |
| Beetroot | 25 | 45 | 35 | Bowenpally |
| Amla | 50 | 100 | 70 | Rythu Bazaar (seasonal) |
| Turmeric (fresh) | 35 | 70 | 50 | Rythu Bazaar |
| Orange | 40 | 80 | 60 | Bowenpally |
| Mint | 30 | 60 | 40 | Local vendor |
| Coconut water | 30 | 50 | 40 | Packaged / tender coconut |
| Honey | 350 | 500 | 400 | Local apiary / retail |
| Black pepper | 500 | 700 | 600 | Retail (tiny quantities) |
| Pink salt | 150 | 200 | 175 | Retail |

### Packaging Cost Assumptions

| Item | Unit Cost (Rs) | Source |
|---|---|---|
| 300ml glass bottle | 12-18 | IndiaMart / Hyderabad glass supplier (bulk 500+) |
| Bottle cap (tamper-evident, glass-fit) | 2-3 | Same supplier |
| Label (printed, waterproof) | 3-5 | Local print shop (bulk 1000+) |
| 100ml glass bottle (shot) | 8-10 | IndiaMart |
| 100ml glass cap | 2-3 | Same |
| Shot label | 3-4 | Local print shop |
| Insulated delivery bag | 300-500 | One-time, amortized |
| Ice pack (reusable gel) | 50-80 | One-time, reusable 100+ times |
| Ingredient card | 2-3 | Printed in bulk (500+) |

> **Note:** Brand and transparency page state "glass bottles sealed immediately." PET is not used. Glass costs more (Rs 12-18 vs Rs 8-10 for PET) — the price premium is part of the brand promise and is justified by customer trust and compliance perception.

**Planning rates used below:** Bottle Rs 15 + Cap Rs 2.50 + Label Rs 4 = **Rs 21.50 per 300ml unit** (rounded to Rs 22 for COGS tables). Higher than PET but non-negotiable for the brand position.

---

## Per-SKU Economics

### Detailed COGS Breakdown

| Component | Green Morning | Beetroot Recharge | Citrus Immunity | ABC Classic | Turmeric Shot | Hydration Cooler |
|---|---|---|---|---|---|---|
| **Ingredient 1** | Spinach 80g = Rs 2.80 | Beetroot 150g = Rs 5.25 | Orange 150g = Rs 9.00 | Apple 100g = Rs 13.00 | Turmeric 15g = Rs 0.75 | Cucumber 150g = Rs 3.75 |
| **Ingredient 2** | Cucumber 120g = Rs 3.00 | Carrot 80g = Rs 2.40 | Amla 30g = Rs 2.10 | Beetroot 80g = Rs 2.80 | Ginger 15g = Rs 1.50 | Coconut water 100ml = Rs 4.00 |
| **Ingredient 3** | Apple 80g = Rs 10.40 | Apple 60g = Rs 7.80 | Carrot 60g = Rs 1.80 | Carrot 100g = Rs 3.00 | Lemon 10g = Rs 0.70 | Mint 10g = Rs 0.40 |
| **Ingredient 4** | Lemon 20g = Rs 1.40 | Lemon 15g = Rs 1.05 | Turmeric 5g = Rs 0.25 | Lemon 10g = Rs 0.70 | Honey 5g = Rs 2.00 | Lemon 20g = Rs 1.40 |
| **Ingredient 5** | Ginger 5g = Rs 0.50 | Pepper = Rs 0.20 | Lemon 15g = Rs 1.05 | — | Pepper = Rs 0.20 | Salt = Rs 0.30 |
| **Ingredient 6** | Mint 5g = Rs 0.20 | — | Pepper = Rs 0.20 | — | — | — |
| **Total Ingredients** | **Rs 18.30** | **Rs 16.70** | **Rs 14.40** | **Rs 19.50** | **Rs 5.15** | **Rs 9.85** |
| **Packaging** | Rs 15.50 | Rs 15.50 | Rs 15.50 | Rs 15.50 | Rs 15.00 (glass) | Rs 15.50 |
| **Labor (per bottle)** | Rs 3.00 | Rs 3.00 | Rs 3.50 | Rs 3.00 | Rs 3.00 | Rs 3.00 |
| **Utility (per bottle)** | Rs 2.00 | Rs 2.00 | Rs 2.00 | Rs 2.00 | Rs 1.50 | Rs 2.00 |
| **Total COGS** | **Rs 38.80** | **Rs 37.20** | **Rs 35.40** | **Rs 40.00** | **Rs 24.65** | **Rs 30.35** |
| **Selling Price** | Rs 99 | Rs 99 | Rs 119 | Rs 89 | Rs 69 | Rs 89 |
| **Gross Margin (Rs)** | Rs 60.20 | Rs 61.80 | Rs 83.60 | Rs 49.00 | Rs 44.35 | Rs 58.65 |
| **Gross Margin (%)** | 60.8% | 62.4% | 70.3% | 55.1% | 64.3% | 65.9% |

### Labor and Utility Allocation Assumptions

- **Labor:** One person producing 30 bottles in 2 hours = Rs 90 total (Rs 3/bottle). Based on Rs 15,000/month salary equivalent for production help, 4 hours/day = ~Rs 2,000/day = Rs 90 for 2-hour production block.
- **Utility:** Electricity for juicer + refrigeration + lighting = ~Rs 2,000/month. At 30 bottles/day x 26 days = 780 bottles/month = Rs 2.56/bottle, rounded to Rs 2.

---

## Per-Order Economics

### Average Order Profile

| Parameter | Assumption | Notes |
|---|---|---|
| Average bottles per order | 1.3 | Most subscribers get 1/day. Some family plans get 2. Occasional add-on shots. |
| Average order value (AOV) | Rs 125 | Weighted: 70% at Rs 99 (staples), 15% at Rs 119 (premium), 10% at Rs 89 (entry), 5% at Rs 69 (shots) |
| Average COGS per order | Rs 47 | Weighted COGS across SKU mix |

### Order-Level P&L

| Line Item | Per Order (Rs) | % of AOV |
|---|---|---|
| **Revenue (AOV)** | 125 | 100% |
| Ingredient cost | 22 | 17.6% |
| Packaging | 20 | 16.0% |
| Labor | 4 | 3.2% |
| Utility | 3 | 2.4% |
| **Total COGS** | **49** | **39.2%** |
| **Gross Profit** | **76** | **60.8%** |
| Delivery cost (in-house) | 28 | 22.4% |
| Payment processing (2%) | 3 | 2.4% |
| Ingredient card / packaging extras | 3 | 2.4% |
| **Contribution Margin** | **42** | **33.6%** |

### Subscription Order Economics (Plan Pricing)

Subscribers pay 13-15% less than individual pricing:

| Line Item | Per Subscription Order (Rs) | % of Revenue |
|---|---|---|
| **Revenue** | 108 | 100% |
| Total COGS | 47 | 43.5% |
| **Gross Profit** | 61 | 56.5% |
| Delivery cost | 28 | 25.9% |
| Payment processing | 2 | 1.9% |
| Extras | 3 | 2.8% |
| **Contribution Margin** | **28** | **25.9%** |

**Key insight:** At subscription pricing with in-house delivery, contribution margin is Rs 28/order. This is tight but viable because subscribers order 20-24 times/month, giving Rs 560-672 contribution per subscriber per month.

---

## Per-Subscriber Economics (Monthly)

### Morning Glow Plan Subscriber

| Line Item | Monthly (Rs) | Notes |
|---|---|---|
| **Revenue** | 2,099 | Monthly plan price |
| COGS (24 bottles) | 888 | Avg Rs 37 x 24 bottles |
| Delivery (24 deliveries) | 600 | Rs 25/delivery x 24 |
| Payment processing | 42 | 2% of revenue |
| WhatsApp/communication | 10 | Negligible at scale |
| Ingredient cards | 24 | Rs 1/card x 24 |
| Monthly booklet | 15 | Rs 15/booklet, 1/month |
| Referral liability (10% chance) | 21 | 10% of revenue x 10% probability subscriber was referred |
| **Total Variable Cost** | **1,600** | |
| **Net Contribution** | **499** | **23.8%** |

### Family Wellness Subscriber

| Line Item | Monthly (Rs) | Notes |
|---|---|---|
| **Revenue** | 2,999 | Monthly plan price |
| COGS (40 bottles) | 1,440 | Avg Rs 36 x 40 bottles |
| Delivery (20 deliveries) | 500 | Rs 25/delivery x 20 (same stop, 2 bottles) |
| Payment processing | 60 | 2% |
| Communication + cards | 30 | |
| Monthly booklet | 15 | |
| Referral liability | 30 | |
| **Total Variable Cost** | **2,075** | |
| **Net Contribution** | **924** | **30.8%** |

**Family subscribers are 85% more profitable per subscriber.** Same delivery stop, double the bottles.

### Subscriber Lifetime Value (LTV)

| Scenario | Avg Monthly Revenue | Net Contribution/Month | Avg Lifetime (Months) | LTV |
|---|---|---|---|---|
| Individual subscriber | Rs 2,099 | Rs 499 | 5 | Rs 2,495 |
| Family subscriber | Rs 2,999 | Rs 924 | 7 | Rs 6,468 |
| Churner (1-month) | Rs 2,099 | Rs 499 | 1 | Rs 499 |
| Power subscriber (12+ months) | Rs 2,200 (upgrades) | Rs 550 | 14 | Rs 7,700 |

**Customer Acquisition Cost (CAC):**
- Referral-based: Rs 0 upfront + Rs 210/month credit for 12 months (max Rs 2,520 but in credits worth Rs 880 to you after margins)
- Kiosk sampling: Rs 30-50/trial (COGS of sample cups) x 5 trials to convert 1 = Rs 150-250
- Booklet distribution: Rs 25/booklet x 10 booklets to get 1 customer = Rs 250
- **Target blended CAC: Rs 200-300**
- **LTV:CAC ratio: 8:1 to 25:1** — very healthy

---

## Per-Route Economics

### Single Morning Route (In-House Rider)

| Parameter | Value | Notes |
|---|---|---|
| Deliveries per route | 20 | Target 15-25 |
| Time per route | 75 min | Including loading, travel, handoffs |
| Avg revenue per delivery | Rs 108 | Subscription pricing |
| **Route revenue** | **Rs 2,160** | |
| Rider time cost | Rs 250 | Rs 15,000/month ÷ 20 working days ÷ 3 routes/day |
| Fuel cost | Rs 80 | ~15 km route, Rs 5/km |
| Ice packs / bags (amortized) | Rs 10 | Per route |
| **Route delivery cost** | **Rs 340** | |
| Route COGS (20 bottles) | Rs 740 | Avg Rs 37 x 20 |
| **Route contribution** | **Rs 1,080** | |
| **Route contribution margin** | **50.0%** | |

### Route Break-Even

| Cost Component | Monthly Cost |
|---|---|
| Rider salary | Rs 15,000 |
| Fuel | Rs 2,500 |
| Bags/ice packs (amortized) | Rs 500 |
| **Total route cost** | **Rs 18,000** |

To cover just route cost (not COGS):
- Rs 18,000 ÷ Rs 108 avg order = 167 deliveries/month
- 167 ÷ 26 working days = **6.4 deliveries/day minimum** to break even on delivery cost alone

To cover route cost + COGS and be profitable:
- Need **15+ deliveries/day** to generate Rs 28+ contribution per delivery = Rs 420/day = Rs 10,920/month route profit (after COGS and delivery cost)

**Verdict:** A route with fewer than 10 deliveries/day is unprofitable. Don't expand to a new area until you have 10+ committed subscribers there.

---

## Per-Cluster Economics

### Model: 50-Subscriber Cluster (e.g., KPHB Colony)

| Parameter | Monthly Value |
|---|---|
| **Subscribers** | 50 |
| Mix: 35 individual + 15 family | |
| **Revenue** | |
| 35 individual x Rs 2,099 | Rs 73,465 |
| 15 family x Rs 2,999 | Rs 44,985 |
| **Total Revenue** | **Rs 118,450** |
| **COGS** | |
| Individual: 35 x 24 bottles x Rs 37 | Rs 31,080 |
| Family: 15 x 40 bottles x Rs 36 | Rs 21,600 |
| **Total COGS** | **Rs 52,680** |
| **Gross Profit** | **Rs 65,770** |
| **Delivery** | |
| Individual: 35 x 24 = 840 deliveries x Rs 25 | Rs 21,000 |
| Family: 15 x 20 = 300 deliveries x Rs 25 | Rs 7,500 |
| **Total Delivery** | **Rs 28,500** |
| **Other Variable** | |
| Payment processing (2%) | Rs 2,369 |
| Cards, booklets, communication | Rs 1,500 |
| Referral credit liability | Rs 2,000 |
| **Total Other** | **Rs 5,869** |
| **Total Variable Costs** | **Rs 87,049** |
| **Cluster Contribution** | **Rs 31,401** |
| **Contribution Margin** | **26.5%** |

### Density Benefit

As cluster density increases, per-delivery cost drops:

| Subscribers in Cluster | Deliveries/Route | Routes Needed | Delivery Cost/Subscriber/Month | Improvement |
|---|---|---|---|---|
| 10 | 10/route | 1 route (underloaded) | Rs 750 | Baseline |
| 25 | 20/route | 1 route | Rs 600 | -20% |
| 50 | 22/route | 2 routes | Rs 570 | -24% |
| 100 | 25/route | 3 routes | Rs 500 | -33% |

**The cluster economics improve significantly after 25 subscribers.** That is the target density before expanding to a new cluster.

---

## Fixed Cost Structure

### Stage 1: Home Kitchen (0-30 Customers)

| Fixed Cost | Monthly (Rs) | Notes |
|---|---|---|
| Cold-press juicer (amortized 12 months) | 1,250 | Rs 15,000 unit ÷ 12 |
| Refrigerator (amortized 24 months) | 625 | Rs 15,000 ÷ 24 |
| Kitchen utilities (electricity, water) | 2,000 | Incremental |
| Packaging supplies buffer | 500 | Safety stock |
| Phone/WhatsApp Business | 500 | Dedicated number |
| Miscellaneous (cleaning, sanitizer) | 500 | |
| **Total Fixed (ex-rider)** | **Rs 5,375** | |
| Rider (1, part-time morning) | 12,000 | 6-9 AM shift |
| Rider fuel | 2,500 | |
| **Total Fixed (with rider)** | **Rs 19,875** | |

### Stage 2: Upgraded Home (30-80 Customers)

| Fixed Cost | Monthly (Rs) | Notes |
|---|---|---|
| All Stage 1 costs | 5,375 | |
| Second juicer (amortized) | 1,250 | Backup/parallel production |
| Commercial refrigerator (amortized) | 1,000 | Rs 25,000 ÷ 24 |
| Part-time helper (production) | 8,000 | 4 AM - 8 AM daily |
| Rider 1 (full morning) | 15,000 | 6-9 AM, 3 routes |
| Rider fuel | 3,000 | |
| **Total Fixed** | **Rs 33,625** | |

### Stage 3: Small Production Unit (80-200 Customers)

| Fixed Cost | Monthly (Rs) | Notes |
|---|---|---|
| Rental (small commercial space) | 15,000 | Kukatpally industrial area |
| Commercial cold-press juicer (amortized) | 3,000 | Rs 75,000 ÷ 24 |
| Walk-in cooler (amortized) | 2,500 | Rs 60,000 ÷ 24 |
| Utilities | 5,000 | |
| 2 production helpers | 20,000 | Rs 10,000 each |
| 2 riders | 30,000 | Rs 15,000 each |
| Rider fuel | 6,000 | |
| FSSAI compliance | 500 | Amortized annual fee |
| Insurance | 1,000 | |
| **Total Fixed** | **Rs 83,000** | |

---

## Break-Even Analysis

### Stage 1: Home Kitchen

| Parameter | Value |
|---|---|
| Total fixed costs | Rs 19,875/month |
| Contribution per subscriber (avg) | Rs 499/month (individual) |
| **Break-even subscribers** | **40 individual subscribers** |
| Or: 25 individual + 8 family | Rs 499 x 25 + Rs 924 x 8 = Rs 19,867 |

**Reality check:** 40 subscribers from a home kitchen is ambitious for Month 1-2. Expect 10-15 subscribers by end of Month 1, 25-30 by end of Month 2. **You will likely not break even until Month 3.**

### Months to Break-Even (Conservative)

| Month | Subscribers | Revenue | Variable Cost | Fixed Cost | Net Profit/Loss |
|---|---|---|---|---|---|
| 1 | 12 | Rs 22,200 | Rs 17,400 | Rs 19,875 | **-Rs 15,075** |
| 2 | 25 | Rs 46,250 | Rs 34,750 | Rs 19,875 | **-Rs 8,375** |
| 3 | 40 | Rs 74,000 | Rs 55,600 | Rs 19,875 | **-Rs 1,475** |
| 4 | 55 | Rs 101,750 | Rs 74,800 | Rs 33,625 | **-Rs 6,675** |
| 5 | 70 | Rs 129,500 | Rs 93,100 | Rs 33,625 | **+Rs 2,775** |
| 6 | 85 | Rs 157,250 | Rs 111,400 | Rs 33,625 | **+Rs 12,225** |

**Cash-flow positive by Month 5** with conservative subscriber growth (10-15 new/month, 85% retention).

### Cumulative Cash Required

| Month | Monthly Loss | Cumulative Cash Needed |
|---|---|---|
| 0 (Setup) | -Rs 35,000 | Rs 35,000 |
| 1 | -Rs 15,075 | Rs 50,075 |
| 2 | -Rs 8,375 | Rs 58,450 |
| 3 | -Rs 1,475 | Rs 59,925 |
| 4 | -Rs 6,675 | Rs 66,600 |
| 5 | +Rs 2,775 | Rs 63,825 |

**Total capital needed: ~Rs 70,000** to survive until profitability. Well within the Rs 2 lakh budget, leaving Rs 1.3 lakh buffer for equipment upgrades, unexpected costs, or faster scaling.

---

## Sensitivity Analysis

### Scenario 1: Delivery Cost +50% (Rs 28 → Rs 42 per delivery)

| Impact | Value |
|---|---|
| Monthly delivery cost increase (50 subs) | +Rs 16,200 |
| New contribution per individual subscriber | Rs 163/month (down from Rs 499) |
| New break-even | 122 subscribers (up from 40) |
| **Verdict** | Devastating. Delivery cost is the biggest lever. Keep in-house. |

### Scenario 2: Wastage Increases from 5% to 15%

| Impact | Value |
|---|---|
| Additional COGS per bottle | +Rs 3.70 (10% more ingredient waste) |
| Monthly impact (50 subs, 1,200 bottles) | +Rs 4,440 |
| New contribution margin | 21.8% (down from 26.5%) |
| **Verdict** | Painful but survivable. Fix by tightening prep SOPs, better forecasting. |

### Scenario 3: Retention Improves from 60% → 80% (Month-over-month)

| Impact | Value |
|---|---|
| Subscribers at Month 6 (starting from 12) | 85 → 110 |
| Revenue difference at Month 6 | +Rs 46,250 |
| **Verdict** | Retention is the second biggest lever after delivery cost. Every 5% improvement in retention = 15-20% more revenue by Month 6. |

### Scenario 4: AOV Increases by Rs 30 (Shot Add-On Adoption)

| Impact | Value |
|---|---|
| Additional revenue per order | Rs 30 |
| Monthly impact (50 subs, 1,200 orders) | +Rs 36,000 |
| Additional COGS (shots at Rs 23 each) | Rs 27,600 |
| Net contribution improvement | +Rs 8,400/month |
| **Verdict** | Shot add-ons are high margin. Push Turmeric Ginger Shot as daily add-on. |

### Lever Ranking (Most to Least Impactful)

| Rank | Lever | Impact on Monthly Profit | Controllability |
|---|---|---|---|
| 1 | Delivery cost | Rs 16,200 swing | High — keep in-house |
| 2 | Retention rate | Rs 12,000+ swing | Medium — product + service quality |
| 3 | AOV (add-ons) | Rs 8,400 swing | Medium — product design + education |
| 4 | Wastage | Rs 4,440 swing | High — process discipline |
| 5 | Price increase Rs 10/bottle | Rs 12,000 swing | Low — risk losing customers |

---

## Key Financial Rules

1. **Never operate a route with fewer than 10 deliveries/day.** Below that, you are subsidizing delivery from product margin.
2. **Target 60%+ gross margin on every SKU.** Below 55%, the SKU is a loss leader — use intentionally (ABC Classic) or kill it.
3. **Family subscribers are your gold.** Every marketing effort should prioritize converting individuals to family plans.
4. **Delivery cost is your existential risk.** If you lose in-house delivery capability and rely on Dunzo/Porter, the business model breaks.
5. **Keep Rs 50,000 cash reserve.** Never spend your last rupee. Unexpected costs will come (equipment repair, ingredient price spikes, rider quits).
