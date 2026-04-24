# 10 — Pricing Strategy

> Price is a signal. Too low = commodity juice shop. Too high = Rawpressery pretension. Soma Delights sits in the "affordable daily wellness" zone — more expensive than street juice, cheaper than premium national brands, justified by freshness + daily delivery + education.

---

## Active Model: Volume-Based Dynamic Pricing (v2, 2026)

**As of April 2026, subscription pricing is calculator-driven, not tier-driven.** The old fixed tiers (Morning Glow, Hydration Habit, etc.) further down in this document are deprecated for subscriber acquisition but kept for reference and one-off bundle economics.

### Design Tenets

1. **Same per-unit price for drinks and shots.** One number for the customer to remember. No "which is cheaper" decision friction.
2. **Customer enters household totals.** "How many drinks does the family drink a week?" is how real households plan groceries — not "how many per person". Per-person is shown as a derived hint in the UI.
3. **Delivery frequency is auto-determined, never user-chosen.** More deliveries cost us more. The cadence scales with household volume so each drop stays within the 3-day freshness window — without ever letting small subscribers drag ops economics into the red.

### Inputs (from the customer)

- `people` — household size, 1–8 (stepper)
- `drinks` — total 300 ml cold-pressed drinks per week for the household (slider 0–42)
- `shots` — total 100 ml fermented shots per week for the household (slider 0–42)

### Per-Unit Price Formula

```
perUnitPrice(totalUnitsPerMonth) =
    max(100, round5(150 − 0.625 × (totalUnitsPerMonth − 1)))
```

- **Ceiling:** ₹150 per unit (1 unit/month — effectively trial)
- **Floor:** ₹100 per unit (hits floor at ~80 units/month)
- Rounded to nearest ₹5 for clean display
- **Applies identically to drinks and shots** — see "Why shots cost the same" below

### Auto Deliveries-Per-Week Formula

Delivery frequency is **revenue-gated, not volume-gated**. Extra rider trips are only unlocked once the plan's absolute revenue clears a household-size-adjusted threshold — so delivery cost never drags ops economics into the red, and larger households don't get a free ride because they naturally order more.

```
BASE_REVENUE         = ₹2,000         // everyone starts with 2 deliveries/week
threshold(people)    = ₹2,000 + (people − 1) × ₹1,000
                       // 1p = ₹2,000 · 2p = ₹3,000 · 3p = ₹4,000 · 4p = ₹5,000
                       // 5p = ₹6,000 · 6p = ₹7,000 · 7p = ₹8,000 · 8p = ₹9,000

extraDeliveries      = max(0, floor((monthlySpend − ₹2,000) / threshold(people)))
deliveries/week      = clamp(2, 7, 2 + extraDeliveries)
```

**Matches three brand anchors exactly:**

| Anchor | Formula | Deliveries |
|---|---|---|
| 1 person @ ₹4,000 | `2 + floor((4000−2000)/2000)` = 2+1 | **3** |
| 1 person @ ₹6,000 | `2 + floor((6000−2000)/2000)` = 2+2 | **4** |
| 2 persons @ ₹6,000 | `2 + floor((6000−2000)/3000)` = 2+1 | **3** |

#### Why the threshold grows with household size

A single-person household that doubles from ₹2k → ₹4k represents a genuine behaviour change: they are drinking significantly more, every bottle needs to stay fresh, a third delivery obviously helps. For them, the ₹2,000 per-step is comfortable.

A four-person household that doubles from ₹2k → ₹4k is barely above one-drink-per-person-per-week — the four share a single drop easily, and jumping to three deliveries would waste the rider trip. So we set their threshold higher (₹5,000 per extra delivery): bigger revenue bumps before we commit more rider time.

This is the inverse of what a naïve "more people = more deliveries" rule would do, and it's correct: more people share carry capacity per drop, so the marginal delivery is worth less to them until spend scales meaningfully.

#### Extended threshold table (every step is an extra delivery)

| People → | Base (2/wk) | 3/wk unlocks at | 4/wk | 5/wk | 6/wk | 7/wk |
|---|---|---|---|---|---|---|
| 1 | < ₹4k | ₹4,000 | ₹6,000 | ₹8,000 | ₹10,000 | ₹12,000 |
| 2 | < ₹5k | ₹5,000 | ₹8,000 | ₹11,000 | ₹14,000 | ₹17,000 |
| 3 | < ₹6k | ₹6,000 | ₹10,000 | ₹14,000 | ₹18,000 | ₹22,000 |
| 4 | < ₹7k | ₹7,000 | ₹12,000 | ₹17,000 | ₹22,000 | ₹27,000 |
| 5 | < ₹8k | ₹8,000 | ₹14,000 | ₹20,000 | ₹26,000 | ₹32,000 |
| 6 | < ₹9k | ₹9,000 | ₹16,000 | ₹23,000 | ₹30,000 | ₹37,000 |
| 7 | < ₹10k | ₹10,000 | ₹18,000 | ₹26,000 | ₹34,000 | ₹42,000 |
| 8 | < ₹11k | ₹11,000 | ₹20,000 | ₹29,000 | ₹38,000 | ₹47,000 |

Read as: *"a household of N people unlocks k+1 deliveries/week once their monthly spend reaches the value in the k-th column."* A 3-person household hitting ₹10,000/month = 4 deliveries/week. A 4-person household hitting ₹22,000/month = 6 deliveries/week. Etc.

#### Sustainability math

Each extra delivery/week costs us 4 × ₹60 = **₹240/month** in rider + vehicle + coordination. The threshold is set so that every unlocked delivery is covered by more than its marginal cost:

| Step | Revenue added | Extra delivery cost | Contribution left over |
|---|---|---|---|
| 1→2 extra (1p, +₹2,000) | +₹2,000 | ₹240 | ₹1,760 |
| 1→2 extra (4p, +₹5,000) | +₹5,000 | ₹240 | ₹4,760 |

The "contribution left over" funds the product itself (COGS, packaging, kitchen labour). At the floor ₹100 per unit, blended margin is ~₹55/unit. Every threshold crossing therefore adds comfortably more margin than cost.

#### Hard limits

- **Minimum 2 deliveries / week** — any subscriber, any tier. Below that, freshness and routing both degrade.
- **Maximum 7 deliveries / week** — the cap. Corporate / catering accounts that need more go through a separate quote, not the calculator.
- **Soft minimum subscription: 4 weekly units / ₹1,999 spend.** Below that, delivery cost ratio exceeds 30% and we review/off-board monthly.

### Monthly Price

```
totalUnitsPerMonth = (drinks + shots) × 4
monthlyPrice       = totalUnitsPerMonth × perUnitPrice(totalUnitsPerMonth)
```

No separate delivery fees inside the Hyderabad serving zone.

### Reference Table

| Household | Weekly units | Monthly units | Per-unit | Monthly ₹ | Deliveries/wk | Delivery cost ratio* |
|---|---|---|---|---|---|---|
| 1 person, 4 drinks | 4 | 16 | ₹140 | ₹2,240 | 2 | 21% |
| 1 person, 7 drinks | 7 | 28 | ₹135 | ₹3,780 | 2 | 13% |
| 1 person, 4 drinks + 2 shots | 6 | 24 | ₹135 | ₹3,240 | 2 | 15% |
| 2 people, 8 drinks + 4 shots | 12 | 48 | ₹120 | ₹5,760 | 2 | 8% |
| 2 people, 14 drinks + 4 shots | 18 | 72 | ₹105 | ₹7,560 | 3 | 10% |
| 4 people, 28 drinks + 8 shots | 36 | 144 | ₹100 | ₹14,400 | 6 | 10% |
| Office, 48 units/week | 48 | 192 | ₹100 | ₹19,200 | 7 | 9% |

\* Delivery cost ratio = `(deliveries/wk × 4 × ₹60) / monthlyPrice`. Target: under 15% for sustainability. The only tier that runs above is the 16-unit starter, which is an acceptable subsidy — it's our acquisition funnel and the absolute loss is small.

### Why Drinks and Shots Cost the Same

Shots are smaller in volume (100 ml vs 300 ml) but:
- **Ingredient density is higher** — concentrated roots, ferments, functional botanicals
- **Live-culture production is slower and lossier** than pressing
- **Consumer perceives them as equal or higher value** ("one shot replaces a multivitamin")
- **Operational parity** — same glass, same batch labour, same cold chain

Pricing them identically **simplifies the calculator, removes "which should I pick" friction, and lets us rebalance the actual product mix over time without changing the pricing story.**

### Why Customers Don't Pick the Delivery Cadence

Letting a low-volume customer choose 5/week makes delivery cost balloon to 60%+ of revenue — a plan we cannot honour without cross-subsidy from higher tiers. Letting a high-volume customer choose 1/week means 3–4 day-old bottles in their fridge, which kills retention. The formula gives both sides the right answer by default. Customers who want specific drop days get to choose *when* (Mon/Thu vs Tue/Fri), not *how many*.

### Free-Week Math

The free week is 2 deliveries × (2 cold-pressed + 2 shots) = **4 drinks + 4 shots**. Costed at the floor price (₹100/unit), that's ₹800 of product value. Real COGS is lower (~₹45/unit blended average), so actual cost to serve is ~₹360 product + 2 × ₹60 delivery = **~₹480 per free-week prospect.** Conversion economics in `unit-economics.md § Trial Conversion`.

### Minimum Viable Subscription

The calculator enforces a soft minimum: below 4 weekly units the delivery cost ratio blows past 30% and we lose money on the plan. The UI doesn't block it (some trial/ad-hoc use is fine) but the product team should review any active subscriber under 4 weekly units monthly — convert or gracefully off-board.

---

## Hyderabad Market Context

### Competitive Pricing Landscape

| Competitor Type | Price Range (300ml) | What They Offer | Our Position |
|---|---|---|---|
| **Street juice shop** | Rs 30-60 | Fresh but unpasteurized, sugar added, no consistency, no delivery | We are NOT competing here. Different product entirely. |
| **Juice bar (Fresho, Naturals)** | Rs 80-150 | Good quality, dine-in/takeaway, no daily delivery | We match their price but deliver to your door daily. |
| **Rawpressery / Alo / RAW** | Rs 150-300 | Cold-pressed, premium packaging, retail shelf | We are 30-40% cheaper, fresher (same-day vs 3-day shelf), local. |
| **Local cold-press startups** | Rs 100-180 | Similar product, usually Instagram-based, inconsistent | We differentiate on consistency + subscription + education. |

### Sweet Spot: Rs 89-149 per 300ml bottle

This range is:
- Above street juice (signals quality)
- At par with juice bars (but we deliver)
- Below national premium brands (accessible daily spend)
- Psychologically under Rs 150 (important threshold in Hyderabad mid-premium)

---

## Standalone SKU Pricing

### Price Ladder

| Tier | Price Range | SKUs | Psychology |
|---|---|---|---|
| **Entry** | Rs 89 | ABC Classic, Hydration Cooler | "Less than Rs 100" — impulse-friendly, trial-friendly |
| **Standard** | Rs 99 | Green Morning, Beetroot Recharge | Just under Rs 100 — daily staple positioning |
| **Premium** | Rs 119 | Citrus Immunity | Above Rs 100 but justified by functional ingredients (amla, turmeric) |
| **Shot** | Rs 69 | Turmeric Ginger Shot (100ml) | Small volume, high perceived value per ml |

### Pricing Rules

1. **Never price a core 300ml SKU below Rs 89.** Below that, customers perceive it as street juice quality.
2. **Never price above Rs 149 for daily staples.** Above Rs 150 triggers "expensive" framing for daily purchase.
3. **Shots can be Rs 49-99.** Small volume = different mental accounting. Rs 69 for a 100ml shot feels fair.
4. **Seasonal/limited editions: Rs 129-169.** Premium pricing justified by special ingredients (mango season, monsoon immunity).
5. **Round to Rs 9 endings.** Rs 89, Rs 99, Rs 119, Rs 149, Rs 169. Not Rs 90, Rs 100. The Rs 9 ending signals a considered price, not a round-up.

---

## Bundle Pricing

### Discount Structure

| Bundle Type | Discount vs Individual | Rationale |
|---|---|---|
| **3-Day Trial** | 10-13% | Low discount — trial is about discovery, not savings |
| **5-Day Bundle** | 12-15% | Moderate — enough to feel like a deal, not enough to devalue |
| **Family Bundle (6 bottles)** | 15-17% | Higher discount justified by lower per-delivery cost |

### Bundle Pricing Table

| Bundle | Individual Total | Bundle Price | Savings | Savings % |
|---|---|---|---|---|
| 3-Day Starter Trial | Rs 287 | Rs 249 | Rs 38 | 13.2% |
| 5-Day Morning Ritual | Rs 515 | Rs 449 | Rs 66 | 12.8% |
| 5-Day Office Wellness | Rs 425 | Rs 369 | Rs 56 | 13.2% |
| Family Variety (6 bottles) | Rs 594 | Rs 499 | Rs 95 | 16.0% |

### Bundle Pricing Rules

1. **Show the "individual price" crossed out.** Anchoring is everything. "~~Rs 287~~ Rs 249" is more compelling than just "Rs 249."
2. **Round bundle prices to Rs 49 or Rs 99 endings.** Rs 249, Rs 449, Rs 499. These feel like deliberate value prices.
3. **Never discount more than 20% on bundles.** Beyond that, it trains customers to wait for deals.
4. **Bundle must include at least one premium/functional SKU.** Don't bundle only entry-tier products — it lowers perceived brand value.

---

## Subscription Pricing (Legacy — see Active Model above)

> **Deprecated as of April 2026.** New subscribers are priced via the calculator formula in "Active Model: Volume-Based Dynamic Pricing" above. The tables below remain for contractual grandfathering of early subscribers and for side-by-side economic analysis.

### Commitment Discount Tiers (Legacy)

| Commitment Level | Discount vs Individual | Billing Frequency | Lock-in |
|---|---|---|---|
| **Weekly billing** | 13-15% | Charged every Sunday | None — can cancel anytime |
| **Monthly billing** | 18-20% | Charged 1st of month | None — can cancel with 3-day notice |
| **Quarterly billing** | 22-25% | Charged quarterly | Refund pro-rata if cancelled mid-quarter |

### Subscription Pricing Table

| Plan | Individual/Week | Weekly Plan | Monthly Plan | Quarterly Plan |
|---|---|---|---|---|
| Morning Glow (6/week) | Rs 634 | Rs 549 | Rs 2,099 | Rs 5,699 |
| Hydration Habit (6/week) | Rs 554 | Rs 479 | Rs 1,799 | Rs 4,899 |
| Women's Wellness (5/week) | Rs 535 | Rs 459 | Rs 1,749 | Rs 4,749 |
| Office Energy (5/week) | Rs 425 | Rs 369 | Rs 1,399 | Rs 3,799 |
| Family Starter (10/week) | Rs 950 | Rs 799 | Rs 2,999 | Rs 8,199 |

### Subscription Pricing Psychology

**Frame as daily cost, not monthly.**

| Plan | Monthly Price | Daily Cost | Framing |
|---|---|---|---|
| Morning Glow | Rs 2,099 | Rs 70 | "Less than your daily chai + samosa" |
| Hydration Habit | Rs 1,799 | Rs 60 | "What you spend on a water bottle at the office" |
| Family Starter | Rs 2,999 | Rs 100 | "Rs 50 per person — cheaper than one juice bar visit" |

People can rationalize Rs 70/day. People hesitate at Rs 2,099/month. Always lead with the daily framing.

---

## Trial Offers

### First-Time Trial Pricing

| Offer | Price | COGS + Delivery | Margin | Purpose |
|---|---|---|---|---|
| **3-Day Starter Trial** | Rs 249 | Rs 190 | Rs 59 (23.7%) | Low-risk entry. Breakeven is fine. |
| **5-Day Starter Reset** | Rs 449 | Rs 305 | Rs 144 (32.1%) | Slightly better margin but still a conversion play. |
| **First-week-free with monthly signup** | Rs 0 (week 1) + Rs 2,099 (month) | Rs 372 (free week cost) | Recover over 3 weeks | AGGRESSIVE — only use if conversion from trials is below 40% |

### Trial Rules

1. **Never offer a trial for free outright.** Free = no commitment = no habit = no conversion.
2. **Minimum trial price: Rs 199.** Below that, people sign up casually and don't drink the juice.
3. **Trial must include a conversion ask on the last day.** No trial should end without a subscription offer.
4. **One trial per customer.** No repeat trials. If they didn't convert after 5 days, follow up but don't re-trial.

---

## Referral Pricing

### Structure (Single-Level Only)

| Participant | Benefit |
|---|---|
| **Referrer** | 10% of referred person's spend for 12 months (as wallet credit, not cash) |
| **Referred person** | 10% off their first order (any order — trial, bundle, or subscription) |

### Economics of Referral

| Scenario | Referred Person's Monthly Spend | Referrer Gets (Monthly) | Annual Referrer Benefit |
|---|---|---|---|
| Morning Glow subscriber | Rs 2,099 | Rs 210/month credit | Rs 2,520 |
| Family subscriber | Rs 2,999 | Rs 300/month credit | Rs 3,600 |
| One-time buyer (Rs 249) | Rs 249 | Rs 24.90 credit (one-time) | Rs 24.90 |

### Referral Economics Reality Check

At 10% referral payout:
- **Cost to you:** 10% of referred revenue as credit (not cash — they spend it on your products)
- **Effective cost:** ~3.5-4% of revenue (because credit redeemed against products with 60%+ margin)
- **Customer acquisition cost equivalent:** Rs 0 upfront, Rs 210/month for a Rs 2,099/month subscriber
- **Payback:** Immediate. The referred subscriber is profitable from month 1.

### Referral Rules

1. **Single level only.** No MLM. No "your referral's referrals." Simple.
2. **Credit, not cash.** Referral earnings are wallet credits, redeemable on orders.
3. **12-month cap.** After 12 months, referral benefit expires. Prevents indefinite liability.
4. **Minimum order to redeem.** Credits can be applied against orders of Rs 200+ only (prevents gaming).
5. **Both sides benefit.** Referrer gets ongoing 10%, referred person gets one-time 10% off.

---

## Wallet Credit Incentives (Month 3+)

### Pre-Loading Bonuses

| Top-Up Amount | Bonus Credits | Effective Discount |
|---|---|---|
| Rs 1,000 | Rs 50 bonus | 4.8% |
| Rs 2,000 | Rs 150 bonus | 7.0% |
| Rs 5,000 | Rs 500 bonus | 9.1% |

### Why Wallet Credits Work

1. **Cash flow advantage:** You get Rs 2,000 today, deliver products over 4 weeks.
2. **Switching cost:** Credits on your platform = reason not to try competitor.
3. **Behavioral lock-in:** "I have Rs 500 credit, might as well order."
4. **No-refund policy on credits:** Non-refundable once loaded (state this clearly).

### When to Introduce

Not at launch. Wallet credits add complexity. Introduce at Month 3 when you have 50+ active subscribers and need to improve retention/cash flow.

---

## Premium Pricing Logic

### When to Price Higher

| Signal | Action |
|---|---|
| **Functional ingredient with known benefit** | +Rs 20-30 (e.g., amla, turmeric, ashwagandha) |
| **Seasonal scarcity** | +Rs 20-50 (e.g., mango season = premium mango blend) |
| **Special packaging** | +Rs 10-20 (glass bottle instead of PET) |
| **Limited edition** | +Rs 30-50 (monthly special, not available year-round) |
| **Concentrated format (shots)** | Price per ml can be 3-5x juice (Rs 69 for 100ml vs Rs 99 for 300ml) |

### Premium SKU Pricing Examples

| SKU | Format | Price | Rs/ml | Justification |
|---|---|---|---|---|
| ABC Classic | 300ml PET | Rs 89 | Rs 0.30/ml | Entry tier |
| Green Morning | 300ml PET | Rs 99 | Rs 0.33/ml | Standard tier |
| Citrus Immunity | 300ml PET | Rs 119 | Rs 0.40/ml | Functional (amla + turmeric) |
| Turmeric Ginger Shot | 100ml glass | Rs 69 | Rs 1.15/ml | Concentrated functional |
| Seasonal Mango Glow | 300ml PET | Rs 149 | Rs 0.50/ml | Seasonal limited edition |
| Ashwagandha Calm Shot | 100ml glass | Rs 89 | Rs 1.48/ml | Premium functional (future) |

Customers accept 3-5x higher per-ml pricing for shots because shots are "medicine" (functional), not "drinks" (pleasure). This is the highest-margin format.

---

## When NOT to Discount

### Hard Rules

| Situation | Rule |
|---|---|
| **Below COGS** | NEVER. Even for trials, price must cover at least ingredient cost. |
| **"50% off" or higher** | NEVER. Trains customers to wait for sales. Destroys brand perception. |
| **Competing on price with street juice** | NEVER. You are not a Rs 40 juice. Don't act like one. |
| **Discounting to win back churned customers** | NEVER. Offer a free bottle as a "welcome back" gesture, not a discount. |
| **Festival/holiday sales** | AVOID. You're a daily wellness brand, not a retail store. Instead, offer a festive-themed limited edition at premium price. |
| **Matching a competitor's lower price** | NEVER. Compete on freshness, delivery, education — not price. |

### What to Do Instead of Discounting

| Situation | Alternative to Discount |
|---|---|
| Customer hesitant on price | Offer 3-Day Trial at Rs 249 (not a discount, a trial) |
| Customer wants to cancel | Offer SKU swap or plan downgrade, not price reduction |
| Slow acquisition week | Double referral credit for the week (10% → 20% for referrer) |
| New apartment cluster | Free trial day for first 10 signups (limit, not open-ended) |
| Customer birthday | Free shot add-on (Rs 23 COGS) — personal touch, not a discount |

---

## Pricing Psychology Playbook

### 1. Anchor Pricing

Always show the individual/higher price first.

```
Morning Glow Plan
Individual bottles: Rs 634/week
Your plan price: Rs 549/week — Save Rs 85 every week!
```

### 2. Daily Cost Framing

```
Rs 70/day. Less than your evening chai + biscuit.
That's what your daily wellness ritual costs.
```

### 3. Price Ladder

Present three options. The middle one should be the target:

```
Choose your plan:
  Hydration Habit   Rs 1,799/month  [Good]
  Morning Glow      Rs 2,099/month  [Best Value] ← target
  Family Starter    Rs 2,999/month  [Best for Families]
```

Most people pick the middle option. Make sure the middle option is your highest-margin core plan.

### 4. Loss Aversion

```
"You've already completed 5 days. Don't lose your momentum.
Continue with Morning Glow Plan — same juice, same time, every day."
```

### 5. Social Proof Pricing

```
"47 families in KPHB are on the Family Wellness Plan.
Join them — Rs 100/day for your whole household."
```

### 6. Sunk Cost for Retention

```
"You've been on Morning Glow for 3 months. That's 72 bottles of
pure nutrition. Your body is thanking you. Keep going."
```

---

## Price Testing Plan

### Month 1: Set Baseline

- Launch at stated prices. Don't change for 30 days.
- Track: conversion rate from trial to subscription, bundle vs individual preference.

### Month 2: Test One Variable

- A/B test: Rs 89 vs Rs 99 for ABC Classic (entry SKU)
- Split by apartment cluster (Cluster A gets Rs 89, Cluster B gets Rs 99)
- Measure conversion rate and revenue per customer

### Month 3: Evaluate and Adjust

| Signal | Action |
|---|---|
| Trial conversion >60% | Prices are good. Don't touch. |
| Trial conversion 40-60% | Try bundling a free shot with trial (add value, not discount) |
| Trial conversion <40% | Lower trial price to Rs 199, but keep subscription prices |
| Subscription churn <15% | Prices are sustainable. |
| Subscription churn 15-25% | Survey churned customers. If "too expensive" is top reason, consider plan restructuring (fewer days/week) rather than price cuts. |
| Subscription churn >25% | Something is wrong beyond pricing. Check product quality, delivery consistency. |

---

## Metrics to Watch

| Metric | Target | Frequency |
|---|---|---|
| Average Order Value (AOV) | >Rs 180 | Weekly |
| Average Revenue Per Subscriber (ARPS) | >Rs 1,800/month | Monthly |
| Price sensitivity by cluster | <20% variation in conversion across clusters | Monthly |
| Bundle attachment rate | >30% of orders include add-on (shot, pulp) | Monthly |
| Discount redemption rate | <15% of revenue from discounted orders | Monthly |
| Referral credit liability | <5% of monthly revenue | Monthly |
