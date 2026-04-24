# Shelf Life & Freshness Policy

**Version:** 1.0
**Status:** Operational Standard — Non-Negotiable
**Scope:** All Soma Delights products, production, cold chain, delivery, and kiosk operations

---

## 1. Core Philosophy: Short Shelf Life Is a Feature

Every other beverage brand treats shelf life as a problem to be solved through chemistry. Longer is better. Six months is good. Two years is great. The goal is to defeat time.

Soma treats shelf life differently. Short shelf life is not a production failure. It is a production success. It is the proof — visible, measurable, concrete — that nothing was added to the product to make it survive longer than it naturally would.

When a customer picks up a Soma bottle and sees "Pressed: Mon 24 Mar, 4:30am. Best consumed by: Tue 25 Mar, 4:30am," they are holding evidence. Evidence that their juice was made this morning, that it contains no preservatives, that the only thing in it is what is listed on the label. The expiry is not a warning. It is a warranty.

**The marketing language is: "Ours lasts 48 hours because it's alive. Theirs lasts 6 months because it's dead."**

This is factually accurate, brand-consistent, and — crucially — verifiable by the customer. It is the kind of claim that builds trust because anyone can test it. Compare what a 48-hour juice tastes like versus a 6-month packaged juice. The difference is not subtle.

Every operational decision in this document flows from this principle: **freshness is the product**. Cold chain, timestamps, delivery windows, kiosk protocols, spoilage targets, seasonal adjustments — all of it exists to protect the aliveness of the product from press to consumption.

---

## 2. Per-Product Shelf Life Reference Table

All shelf life windows assume proper refrigeration at 2–8°C from the moment of pressing. Any temperature deviation reduces the window.

| Product Category | Shelf Life (Refrigerated) | Shelf Life (Unrefrigerated) | Notes |
| --- | --- | --- | --- |
| Cold-pressed juice — citrus-heavy (lemon, orange, grapefruit base) | 24–48 hours | 2–4 hours max | Citric acid provides some natural antimicrobial protection but does not extend refrigerated window meaningfully |
| Cold-pressed juice — green/vegetable (spinach, cucumber, wheatgrass, celery base) | 24–48 hours | 1–2 hours max | Most oxidation-sensitive category; consume within 12 hours of delivery for peak nutrition |
| Cold-pressed juice — turmeric/ginger shots (high-concentration extracts) | 48–72 hours refrigerated | 3–4 hours max | Higher natural antimicrobial load from ginger and curcumin allows slight extension; always refrigerate |
| Wellness shots — amla, neem, giloy (future) | 48–72 hours refrigerated | 2–3 hours max | Similar profile to turmeric/ginger shots |
| Fermented shots — kombucha, kvass, lacto-fermented (future, Phase 2) | 5–7 days refrigerated | 4–6 hours max | Live culture drinks have different spoilage profile; CO2 is normal; quality degrades rather than becoming unsafe |
| Nut milk — almond, coconut (future, Phase 2) | 24–48 hours refrigerated | 1–2 hours max | Highest spoilage risk category; strictest cold chain required |
| Dehydrated pulp products — fruit leather, dried powder blends (future, Phase 2) | 6–12 months dry storage | Same — no refrigeration required | Completely different category; no cold chain; store at room temperature below 30°C, away from moisture |

### Shelf Life vs. Nutrition Window

Shelf life is the food safety boundary. The nutrition window is shorter.

| Time After Pressing | Nutrient Retention (Approximate) | Soma's Position |
| --- | --- | --- |
| 0–6 hours | 95–100% | Optimal — consume if possible |
| 6–12 hours | 85–95% | Peak window — morning delivery consumed by afternoon |
| 12–24 hours | 75–85% | Still high — within stated shelf life |
| 24–48 hours | 60–75% | Safe to consume, reduced nutrition |
| Beyond 48 hours | Below 60% | Do not consume — discard |

We communicate this to customers not as alarming information but as education: "Drink it in the morning when it arrives. That is when it is best. The label says 48 hours so you have flexibility, but your body benefits most from the first 12."

---

## 3. Timestamp System: "Pressed On," Not "Best Before"

The language on the bottle matters. "Best Before" is an industry standard that implies the product was made some time ago and is counting down. It is correct for products that sit in warehouses. It is the wrong frame for Soma.

Soma uses "Pressed On" labeling. This reframes the relationship with time: the label tells you when the juice was born, not when it expires.

### Label Format

```
Pressed:  Mon 24 Mar, 4:30am
Best by:  Tue 25 Mar, 4:30am
```

Both fields always appear. The "Pressed" field is the proof of freshness — a customer who receives their juice by 7am can verify that it was made three hours ago. The "Best by" field gives the safety boundary.

### Labeling Rules

- **Always use day + date + time**, not just date. "Mon 24 Mar, 4:30am" is more transparent than "24/03/2025."
- **"Best by" is always exactly 24 hours after press time for juices.** Do not use 48 hours on the label even though the safety window extends to 48 hours. Labeling the conservative window pushes customers to consume earlier and reduces spoilage at the customer end.
- **Shots (turmeric, ginger, amla):** label "Best by" at 48 hours after press time given their extended window.
- **Never pre-print date labels.** Every batch of labels is printed the morning of production with that day's press time. No pre-dated labels stored in advance.
- **The label is a daily production artifact.** If a bottle has yesterday's press time on it, it should not leave the kitchen.

### Batch Numbering (Internal)

In addition to the customer-facing timestamp, each production batch has an internal batch number for traceability:

```
Format:  YYYYMMDD-[PRODUCT CODE]-[BATCH NUMBER]
Example: 20260324-SG-001  (Soma Green, Batch 1, 24 March 2026)
```

Batch numbers are logged in the daily production record alongside: press time, quantity pressed, QC outcome, delivery allocation, and any incidents. This enables rapid traceability if a customer reports a quality issue.

---

## 4. Production-to-Delivery Timeline

The production timeline is the cold chain's spine. Every deviation from this sequence is a freshness compromise. The timeline is not a target — it is the standard operating procedure.

```
04:00am   Produce arrival and produce inspection
           — Reject any produce showing bruising, mold, or off-smell
           — Weigh and sort by product batch

04:15am   Pressing begins
           — Cold-press juicer operating at optimal RPM for juice category
           — Juice flows directly into chilled glass bottles (pre-chilled in refrigerator)
           — No room temperature staging; bottle goes from press to sealed immediately

05:00am   Quality check
           — Taste test: each batch tasted by production team member
           — Visual check: correct color, no separation issues beyond normal
           — Temperature check: juice temperature at seal must be below 10°C
           — Reject protocol: any batch failing taste or temperature check is discarded, not delivered

05:30am   Pack and label
           — Labels printed with that morning's press time
           — Bottles placed in insulated delivery bags with ice packs
           — Each bag labeled by route and customer name

06:00am   Delivery begins
           — Earliest delivery departure: 6:00am
           — Delivery riders briefed on cold chain protocol (bag stays sealed until handoff)

06:00–08:00am   Delivery window
           — Target: all deliveries complete by 8:00am
           — Acceptable outer limit: 8:30am in peak traffic conditions
           — Deliveries beyond 8:30am: customer notified, offered next-day credit

08:00am   Customer refrigerates
           — Customer education: "Put it in the fridge the moment it arrives. Drink it before noon."

Morning–afternoon   Consumption window
           — Optimal: within 4 hours of delivery (6–10am)
           — Acceptable: within 12 hours of delivery (by 8pm)
           — Maximum: within 24 hours of press time (by 4:30am next morning)
```

---

## 5. Cold Chain Requirements

Cold chain is not optional and it is not negotiable. Every minute spent at room temperature shortens the effective nutrition window and accelerates microbial risk.

### Temperature Standards

| Stage | Temperature Requirement | Duration Limit at Non-Standard |
| --- | --- | --- |
| Post-press (bottle just sealed) | Below 10°C | Must reach below 8°C within 15 minutes |
| In refrigeration (pre-delivery) | 2–8°C | Unlimited within shelf life window |
| In delivery bag (transit) | Below 12°C | Maximum 90 minutes before delivery |
| At kiosk (cold display) | 2–8°C | Maximum 6 hours on display, then discard |
| Customer refrigerator | 2–8°C | Until "Best by" time |

### Delivery Bag Protocol

- Every delivery bag contains: 2 ice packs minimum, insulated inner lining, sealed top
- Ice packs are refrozen every night; never reuse a partially-melted ice pack for next day
- Bag stays sealed from pack time until the customer opens it at their door
- Rider does not open bags to check orders in transit — all verification happens at pack time

### Route Time Limits

- Routes over 60 minutes total: add a third ice pack
- Routes in summer (April–June, Hyderabad temperatures above 38°C): shorten route maximum from 90 to 60 minutes; consider pre-chilling delivery bags in cold room before packing

### Temperature Failure Protocol

If a delivery bag temperature is found to have exceeded 15°C at any point (checked by customer or discovered on return):
1. Do not accept the juice back — dispose of it safely
2. Issue immediate full replacement for the next day
3. Log the cold chain failure with time, route, and probable cause
4. Investigate within 24 hours: was it an ice pack failure, a bag seal issue, a route delay?
5. If a pattern emerges (same route, same rider, same time of year), fix the root cause before the next delivery cycle

---

## 6. Customer Education on Freshness

Every Soma customer receives an ingredient card inside their delivery. One side explains the ingredients in their specific juice. The other side explains the freshness model.

### The Freshness Card (Inside Every Bottle Box)

**Front:**

> **Why does your Soma juice expire so fast?**
>
> Because it is real.
>
> The orange juice in a tetra pack at your local store lasts 6 months. That is because it was pasteurized (heated to kill everything alive in it), then preserved (chemicals added to stop any remaining biological activity).
>
> Your Soma juice lasts 48 hours because we did none of that. It is exactly what it was when it left the press at 4am: raw, cold-pressed, alive.
>
> Short shelf life is not a flaw. It is the proof that nothing was done to it.

**Back:**

> **How to get the most from your juice:**
>
> — Refrigerate immediately when it arrives. Do not leave it on the counter.
>
> — Drink it before noon for maximum nutritional benefit. The enzymes are most active in the first 6–8 hours after pressing.
>
> — Shake gently before opening. Natural separation is normal — it means there are no emulsifiers.
>
> — If your juice smells off or tastes strange within 12 hours of delivery, message us on WhatsApp immediately. We will replace it. No questions asked.

This card is not a terms-and-conditions notice. It is the brand speaking directly, as a neighbor who wants you to get the most out of what you paid for.

---

## 7. Delayed Delivery Protocol

Delays happen. Hyderabad traffic on a Monday morning between Miyapur and Kukatpally can stretch a 20-minute route to 50 minutes. The policy must be clear and communicated in advance.

### Delay Categories and Responses

| Situation | Customer Communication | Resolution |
| --- | --- | --- |
| Delivery between 8:00–8:30am | No communication needed; within acceptable window | Deliver normally |
| Delivery between 8:30–9:00am | Proactive WhatsApp message: "Slight delay today — arriving by 9am" | Deliver with ice pack check; if bag temperature acceptable, deliver normally |
| Delivery after 9:00am | Call or WhatsApp before delivery | Offer: deliver with credit for next order, OR skip today and credit full amount to subscription |
| Juice arrives warm (customer reports bag temperature above 15°C) | Immediate apology + replacement | Next-day replacement guaranteed; investigate cold chain failure |
| Customer not home at delivery time | Leave in a cool spot (shaded corridor, near building entrance) only if under 8:30am and temperature allows | If after 8:30am or hot day: do not leave unrefrigerated; message customer to coordinate next-day |

### Credit Policy for Delays

- Delivery after 9am with customer inconvenience: Rs 29 credit (equivalent to roughly 20% of order value)
- Cold chain failure confirmed: full replacement next day, no charge
- Delivery missed (customer not home, juice not safely leaveable): full credit for that day's delivery to subscription account

Credit is issued proactively — before the customer has to ask. A customer who receives a credit before they file a complaint is more loyal than a customer who had to ask three times to get one.

---

## 8. Spoilage Rate Targets

Spoilage is the operational measure of how well the freshness model is working. Every unit that spoils before consumption represents wasted produce, wasted production cost, and a failed delivery on the freshness promise.

### Spoilage Definition

A bottle is counted as spoiled if:

- It is discarded at production due to QC failure (taste, temperature, visual)
- It is discarded by the delivery team due to cold chain failure in transit
- The customer reports it as off, sour, or visually compromised within the freshness window
- It is returned unsold from a kiosk after the kiosk display limit

### Targets

| Phase | Spoilage Rate Target | Notes |
| --- | --- | --- |
| Launch (first 3 months) | Under 5% | Higher acceptable rate as operations calibrate; focus on understanding failure causes |
| Stabilization (months 4–6) | Under 3% | Standard industry target for direct fresh delivery |
| Mature operations | Under 1% | Achieved through route optimization, better produce sourcing, tighter cold chain |

### Daily Spoilage Log

Every morning, the production lead records:

- Total units pressed
- Units discarded at QC
- Units discarded in transit (reported by riders)
- Customer spoilage reports (from previous day's delivery)
- Running daily spoilage rate

This is a 5-minute daily exercise. If the 7-day rolling average exceeds the phase target, it triggers a root cause review before the next production cycle.

---

## 9. Kiosk and Pop-Up Freshness Standards

Kiosk sales have a different freshness profile than direct delivery. Juice sits in a public display, handled by multiple people, exposed to ambient conditions, for an unknown period before purchase.

### Kiosk Cold Display Requirements

- All juice must be displayed in an active refrigerated display unit or ice bath with visible ice throughout display hours
- Display temperature must be maintained at 2–10°C; a visible thermometer in the display unit is required
- Juice bottles are labeled with press time before leaving the kitchen — the kiosk does not add labels

### Kiosk Time Limits

| Condition | Maximum Display Time |
| --- | --- |
| Refrigerated display unit (2–8°C) | 6 hours from press time |
| Ice bath display (temperature maintained below 10°C) | 4 hours from press time |
| Ambient display (no refrigeration — not permitted) | Not permitted under any circumstances |

**Discard rule:** any bottle that has been in kiosk display for 6 hours (refrigerated) or 4 hours (ice bath) must be discarded, regardless of how it looks or smells. Do not sell beyond these windows. Do not discount it. Discard it.

This is a non-negotiable policy. The kiosk team is not empowered to extend display windows for any reason — not to recover cost, not because the juice looks fine, not because a customer requests it.

### Kiosk Staffing for Freshness

- Every kiosk shift has one person responsible for time-tracking all bottles on display
- A simple clock-face label on each batch (e.g., "6-hour limit expires at 12:30pm") makes this operationally simple
- The responsible person replaces ice every 90 minutes during summer months

### Kiosk Restocking

- New bottles from the kitchen arrive at the kiosk chilled (from refrigerated transport)
- Bottles are placed in display in FIFO order — oldest batch in front, newest batch behind
- The arrival time of each restocking batch is logged on the kiosk time-tracking sheet

---

## 10. Seasonal Adjustments: Hyderabad Summers

Hyderabad summers (March–June) are operationally significant. Average daytime temperatures of 38–44°C mean that ambient temperature failures are not edge cases — they are the baseline risk condition for four months of the year.

### Summer Protocol Adjustments

**Production:**
- Pre-chill glass bottles in refrigerator for 1 hour before pressing (not just at room temperature)
- Target juice temperature at seal: below 8°C (tightened from standard 10°C)
- Increase production QC ice bath for finished bottles to ensure rapid temperature stabilization

**Packaging:**
- Three ice packs per delivery bag (versus standard two) from April 1 through June 30
- Larger insulated bags for longer routes
- Consider biodegradable gel ice sachets for high-density apartment routes where bags are opened more frequently

**Delivery timing:**
- Move delivery window earlier: 5:30–7:30am instead of standard 6:00–8:00am
- Delivery cutoff: all deliveries complete by 7:30am from April through June
- Routes exceeding 45 minutes (standard 60-minute limit) must be restructured or handled with additional cold chain support

**Kiosk:**
- Reduce kiosk display window to 4 hours (refrigerated) and 2.5 hours (ice bath) during April–June
- Add a dedicated ice resupply to kiosk every 60 minutes during peak afternoon heat
- Consider no-kiosk operations during peak summer heat (12pm–4pm); early morning and evening kiosk only

**Customer communication:**
- Summer advisory message (April 1): "Hyderabad summers mean we deliver earlier — your juice arrives by 7:30am. Put it straight in the fridge. Drink it before 10am for peak freshness."
- Reminder weekly in May and June

---

## 11. The Alive Guarantee

Soma's guarantee is simple, unconditional, and communicated clearly before purchase and at delivery.

**The Alive Guarantee:**

> If your juice has turned, smells off, or tastes wrong within 12 hours of delivery, we will replace it. Full bottle. No questions asked. Message us on WhatsApp.

### What "No Questions Asked" Means Operationally

- Customer messages us on WhatsApp with the complaint
- Team responds within 30 minutes during operating hours (6am–10pm)
- Replacement scheduled for next morning delivery
- The only thing we ask: "Can you tell us roughly what you noticed?" — not to challenge the claim, but to gather data for quality improvement

We do not ask for photos. We do not ask for the bottle back. We do not ask them to prove the claim. We trust the customer and we replace immediately.

Internally:
- Every claim is logged: date, customer, product, issue described, batch number
- If the same batch number generates more than one complaint, immediate investigation of that batch's cold chain and production record
- If the same customer generates more than three claims in 30 days, a gentle conversation to understand whether the issue is product-side or customer-side (for example: customer leaving juice on counter for several hours before drinking)

### What the Alive Guarantee Covers

- Juice that smells sour, fermented, or off within 12 hours of delivery
- Juice that has separated in a way that does not resolve with gentle shaking (some separation is normal; complete phase separation with color change is not)
- Juice that tastes significantly different from prior deliveries of the same product
- Juice delivered warm (bag temperature failure)

### What the Alive Guarantee Does Not Cover

- Customer leaving juice unrefrigerated for more than 2 hours after delivery (this is disclosed in the freshness card)
- Juice consumed beyond the "Best by" timestamp on the label
- Normal tartness or bitterness from specific ingredients (amla, neem, bitter gourd) — these are taste characteristics, not spoilage indicators; they are disclosed at point of sale

---

## 12. Marketing Integration: The 48-Hour Window as Content

The short shelf life is not just an operational fact. It is one of Soma's most honest and effective marketing tools.

### Content Approaches

**Daily Instagram / WhatsApp story:**
"Pressed this morning at 4:30am. Expires tomorrow at 4:30am. If you want yours, order now."
This is honest urgency. The scarcity is real. The timestamp is real. It is the opposite of manufactured FOMO.

**Comparison graphic (weekly):**
Side-by-side: Soma bottle (pressed today, expires tomorrow) vs. a packaged juice (manufactured date vs. best before — often 3–6 months apart). No commentary needed. The dates speak.

**The "Alive" series:**
Short weekly posts explaining what "alive" means for a specific ingredient. "This week's amla was pressed this morning. Amla's Vitamin C content drops 20% within 24 hours of pressing. That is why we deliver it fresh and why you should drink it before noon."

**The "Expired" post (occasional):**
Document a batch being discarded because it could not be delivered in time. "We pressed 40 extra bottles today. 40 customers did not order. These went to compost, not to a customer. Here is what we did with them: [recipe for pulp use, or composting partner]. This is what happens when you do not compromise on freshness."

This kind of content is disarming. It shows that the commitment is real, operational, and costly — not a marketing slogan.

### What Not to Do

- Do not use the short shelf life as pressure sales. "Order in the next 2 hours or it is gone" language is manipulative. The shelf life is a fact, not a countdown clock for sales conversion.
- Do not apologize for the short shelf life in marketing. Never write "unfortunately, our juice only lasts 48 hours." Write "our juice only lasts 48 hours — here is why that is good news."
- Do not claim specific nutritional percentages for the freshness benefit without verified data. Say "enzymes are most active in the first 6–8 hours" because that is the established science. Do not say "our juice has 40% more Vitamin C than packaged juice" unless you have the lab test to support it.

---

## 13. Summary: Freshness as Operating Standard

The shelf life and freshness policy is not a customer service document. It is an operational standard that governs every decision from produce procurement to bottle discard.

The standard is:

1. Press at 4am, deliver by 7am, consume by noon. That is the optimal chain.
2. Label every bottle with its birth time, not just its expiry.
3. Never extend shelf life through chemistry. Solve capacity problems with more kitchens, not more preservatives.
4. Cold chain is non-negotiable. A warm delivery is a failed delivery. Replace it.
5. Spoilage under 3% is the operational target. Investigate every deviation.
6. Kiosk display windows are hard limits. Discard, do not discount.
7. Summer requires earlier delivery windows and more ice. Plan for it from February.
8. The Alive Guarantee is unconditional. Trust the customer, replace without argument.
9. Use the 48-hour window in marketing — it is Soma's most honest differentiator.
10. Short shelf life is the proof of no preservatives. That proof is what customers are paying for.

---

*Soma Delights. Pressed at 4am. Expires tomorrow. That is not a problem. That is the product.*
