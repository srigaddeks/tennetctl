# 09 — Subscription Plans

> Recurring revenue is the business. One-time sales are marketing. Every interaction should move a customer toward a subscription. This document designs the subscription architecture.

---

## Subscription Type Comparison

| Type | Pros | Cons | Recommendation |
|---|---|---|---|
| **Daily subscription** | Maximum habit formation, highest revenue per customer, predictable demand | Highest delivery cost, customer fatigue risk, zero flexibility | Use for core plans but allow pause days |
| **Alternate-day** | Lower commitment, customer feels less pressured | Breaks daily habit, harder to route (which days?), lower revenue | Don't offer — it signals the habit doesn't matter daily |
| **Weekly bundle** | Single delivery = low cost, customer picks up all at once | Juice quality drops over 2-3 days, defeats "fresh daily" promise | Don't offer for juice. Works for pulp products only. |
| **Monthly plan** | Maximum commitment, best pricing, predictable cash flow | High upfront ask for new customer, refund risk | Offer after customer completes a weekly plan |
| **Flexible wallet/credit** | Customer pre-pays, orders when they want | Unpredictable demand, harder to route, no habit formation | Avoid — this is anti-habit. Only for occasional buyers. |
| **Fixed plan** | Simple operations, predictable, easy to route | No choice = some customers won't join | Use for most plans — choice paralysis kills conversion |
| **Customizable plan** | Customer picks daily drink | Complex operations, inventory uncertainty | Offer limited customization: pick 2-3 favorites, we rotate |
| **Individual** | Simple | Lower AOV | Default |
| **Family** | Higher AOV, stickier (multiple people = harder to cancel) | Need variety, larger delivery | Offer from Day 1 — families are the best subscribers |

### Summary Recommendation

- **Default model:** Fixed daily delivery, 6 days/week (Mon-Sat), customer picks 2-3 preferred SKUs, you rotate
- **Flexibility:** Allow up to 2 pause days/month at no penalty
- **Billing:** Weekly billing for first 4 weeks, then monthly for committed subscribers
- **No alternate-day.** No wallet system. No weekly bundles for juice.

---

## Plan Designs

### Plan 1: Morning Glow Plan

| Attribute | Detail |
|---|---|
| **Who It's For** | Health-conscious professional, 25-40, wants a daily morning wellness ritual |
| **Products Included** | 1 x 300ml bottle daily, rotating: Green Morning (3x/week) + Citrus Immunity (2x/week) + Beetroot Recharge (1x/week) |
| **Delivery Frequency** | 6 days/week (Mon-Sat), before 7:30 AM |
| **Individual Price** | 3x Rs 99 + 2x Rs 119 + 1x Rs 99 = Rs 634/week |
| **Plan Price** | Rs 549/week |
| **Discount vs Individual** | 13.4% |
| **Monthly Price** | Rs 2,099/month (additional 4.5% monthly commitment discount) |
| **COGS/week** | Rs 222 (avg Rs 37/bottle x 6) |
| **Delivery Cost/week** | Rs 150 (Rs 25/delivery x 6) |
| **Gross Margin/week** | Rs 177 (32.2% after delivery) |
| **Monthly Net Margin** | Rs 708 per subscriber |
| **Operational Ease** | High — fixed rotation, predictable ingredients |
| **Retention Potential** | High — daily habit, visible skin/energy benefits by week 2 |
| **Churn Risk** | Medium — first 2 weeks are critical. If they survive 14 days, 70%+ stay 3 months. |

---

### Plan 2: Hydration Habit Plan

| Attribute | Detail |
|---|---|
| **Who It's For** | Anyone in Hyderabad who is chronically dehydrated (most people). Office workers, gym-goers. |
| **Products Included** | 1 x 300ml bottle daily: Hydration Cooler (4x/week) + Green Morning (2x/week) |
| **Delivery Frequency** | 6 days/week (Mon-Sat), before 7:30 AM |
| **Individual Price** | 4x Rs 89 + 2x Rs 99 = Rs 554/week |
| **Plan Price** | Rs 479/week |
| **Discount vs Individual** | 13.5% |
| **Monthly Price** | Rs 1,799/month |
| **COGS/week** | Rs 206 (avg Rs 34.3/bottle x 6) |
| **Delivery Cost/week** | Rs 150 |
| **Gross Margin/week** | Rs 123 (25.7% after delivery) |
| **Monthly Net Margin** | Rs 492 per subscriber |
| **Operational Ease** | High — Hydration Cooler is simplest to produce |
| **Retention Potential** | High in summer (March-October), drops in winter |
| **Churn Risk** | Medium-high — seasonal dependency. Winter churn could hit 40%. |

**Seasonal Note:** This plan will be the top seller from March-October. In November-February, pivot messaging to "warm lemon ginger water" or pause this plan.

---

### Plan 3: Office Energy Plan

| Attribute | Detail |
|---|---|
| **Who It's For** | IT professionals, WFH workers, anyone who crashes at 3 PM |
| **Products Included** | Mon-Fri only: Hydration Cooler (2x) + ABC Classic (2x) + Turmeric Ginger Shot (1x) |
| **Delivery Frequency** | 5 days/week (Mon-Fri), between 1:00-2:30 PM |
| **Individual Price** | 2x Rs 89 + 2x Rs 89 + 1x Rs 69 = Rs 425/week |
| **Plan Price** | Rs 369/week |
| **Discount vs Individual** | 13.2% |
| **Monthly Price** | Rs 1,399/month |
| **COGS/week** | Rs 163 |
| **Delivery Cost/week** | Rs 125 (Rs 25/delivery x 5) |
| **Gross Margin/week** | Rs 81 (21.9% after delivery) |
| **Monthly Net Margin** | Rs 324 per subscriber |
| **Operational Ease** | LOW — requires second delivery window (afternoon). Separate route. |
| **Retention Potential** | High — office routine reinforces habit |
| **Churn Risk** | Low once established — linked to work routine |

**Operational Warning:** Do NOT launch this plan until you have 50+ morning subscribers and can afford a second delivery window. The afternoon route is a separate operation. Defer to Month 3+.

---

### Plan 4: Women's Wellness Plan

| Attribute | Detail |
|---|---|
| **Who It's For** | Women 25-45, hormonal balance, skin health, iron support |
| **Products Included** | 5 days/week: Beetroot Recharge (2x) + Citrus Immunity (2x) + Green Morning (1x) |
| **Delivery Frequency** | 5 days/week (Mon-Fri), before 7:30 AM |
| **Individual Price** | 2x Rs 99 + 2x Rs 119 + 1x Rs 99 = Rs 535/week |
| **Plan Price** | Rs 459/week |
| **Discount vs Individual** | 14.2% |
| **Monthly Price** | Rs 1,749/month |
| **COGS/week** | Rs 183 |
| **Delivery Cost/week** | Rs 125 |
| **Gross Margin/week** | Rs 151 (32.9% after delivery) |
| **Monthly Net Margin** | Rs 604 per subscriber |
| **Operational Ease** | High — uses existing morning route and core SKUs |
| **Retention Potential** | Very high — wellness results compound over weeks, high emotional investment |
| **Churn Risk** | Low — women who see skin/energy results become evangelists |

**Marketing Angle:** Iron-rich beetroot + vitamin C from citrus for iron absorption. This is a science-backed pairing, not generic "women's wellness" fluff. Lead with the iron absorption story.

---

### Plan 5: Family Wellness Starter

| Attribute | Detail |
|---|---|
| **Who It's For** | Household of 2-4 people. One decision-maker (usually the person who manages family health). |
| **Products Included** | 10 bottles/week for 2 people (or 5 bottles/week each for larger families): Mixed rotation from all core SKUs based on family preferences |
| **Delivery Frequency** | 5 days/week (Mon-Fri), 2 bottles per delivery |
| **Individual Price** | 10 bottles @ avg Rs 95 = Rs 950/week |
| **Plan Price** | Rs 799/week |
| **Discount vs Individual** | 15.9% |
| **Monthly Price** | Rs 2,999/month |
| **COGS/week** | Rs 360 (avg Rs 36/bottle x 10) |
| **Delivery Cost/week** | Rs 125 (same stop, just 2 bottles instead of 1) |
| **Gross Margin/week** | Rs 314 (39.3% after delivery) |
| **Monthly Net Margin** | Rs 1,256 per subscriber |
| **Operational Ease** | Medium — 2 bottles per delivery, need to track 2 people's preferences |
| **Retention Potential** | Very high — family habit is stickiest. Social reinforcement within household. |
| **Churn Risk** | Very low — both people need to agree to cancel. One person's enthusiasm keeps it going. |

**This is the highest-value subscriber type.** Same delivery cost as individual, double the revenue. Actively market to couples and families.

---

### Plan 6: 5-Day Starter Reset (One-Time Trial)

| Attribute | Detail |
|---|---|
| **Who It's For** | Curious first-timer. Not ready for subscription. Wants to "try it out." |
| **Products Included** | 5 bottles over 5 days (Mon-Fri): 1 each of Green Morning, Beetroot Recharge, ABC Classic, Citrus Immunity, Hydration Cooler |
| **Delivery Frequency** | Daily, 5 days, before 7:30 AM |
| **Price** | Rs 449 (one-time, no subscription required) |
| **Individual Price** | Rs 495 (99+99+89+119+89) |
| **Discount** | 9.3% |
| **COGS** | Rs 180 |
| **Delivery Cost** | Rs 125 |
| **Gross Margin** | Rs 144 (32.1%) |
| **Operational Ease** | Medium — non-subscriber, may need separate route handling |
| **Retention Potential** | This IS the retention play. 60% of 5-day trial completers should convert to monthly plan. |
| **Churn Risk** | N/A — it is a trial. Churn happens if they don't convert. |

**Conversion Mechanics:**
- Day 1 delivery: Welcome card with "Your 5-Day Reset Schedule"
- Day 3 delivery: "How are you feeling? Reply to this WhatsApp" (engagement check)
- Day 5 delivery: "Your 5 days are complete! Ready to make it a habit?" + subscription offer with first-month 10% off
- Day 7 (if not converted): Follow-up WhatsApp with testimonial from another customer

---

### Plan 7: 20-Day Routine Builder

| Attribute | Detail |
|---|---|
| **Who It's For** | Committed individual who wants to build a real habit. Understands that 21 days = habit formation. |
| **Products Included** | 20 bottles over 24 days (Mon-Sat, 4 weeks, skipping 4 days for rest): Rotation of customer's top 3 preferred SKUs |
| **Delivery Frequency** | 5 days/week for 4 weeks |
| **Price** | Rs 1,699 (one-time commitment, paid upfront) |
| **Individual Price** | Rs 1,900 (20 bottles @ avg Rs 95) |
| **Discount** | 10.6% |
| **COGS** | Rs 720 (avg Rs 36 x 20) |
| **Delivery Cost** | Rs 500 (Rs 25 x 20 deliveries) |
| **Gross Margin** | Rs 479 (28.2%) |
| **Operational Ease** | High — essentially a 4-week subscription trial |
| **Retention Potential** | Very high — by day 20, the habit is formed. 75%+ should convert. |
| **Churn Risk** | Low post-completion — but dropout during the 20 days is possible (target: <20% dropout) |

**Positioning:** "It takes 21 days to build a habit. We'll deliver your wellness ritual for 20 of them. You bring day 21."

---

## Gut Reset Plan (Deferred — Month 4+)

| Attribute | Detail |
|---|---|
| **Who It's For** | Digestive health seekers, bloating/IBS sufferers |
| **Products Included** | Probiotic-focused drinks (requires fermented product development) |
| **Why Deferred** | Need fermentation setup, food safety protocols, possibly FSSAI special approval |
| **Prerequisites** | Stable operations at 80+ subscribers, fermentation R&D complete |
| **Target Launch** | Month 4-6 |

---

## Plan Comparison Summary

| Plan | Price/Month | Net Margin/Month | Bottles/Week | Operational Ease | Retention | Launch Phase |
|---|---|---|---|---|---|---|
| Morning Glow | Rs 2,099 | Rs 708 | 6 | High | High | Day 1 |
| Hydration Habit | Rs 1,799 | Rs 492 | 6 | High | Medium-High | Day 1 |
| Office Energy | Rs 1,399 | Rs 324 | 5 | Low | High | Month 3+ |
| Women's Wellness | Rs 1,749 | Rs 604 | 5 | High | Very High | Month 2 |
| Family Wellness | Rs 2,999 | Rs 1,256 | 10 | Medium | Very High | Day 1 |
| 5-Day Starter | Rs 449 (once) | Rs 144 | 5 | Medium | Conversion tool | Day 1 |
| 20-Day Builder | Rs 1,699 (once) | Rs 479 | 5/week x 4 | High | Very High | Month 2 |

---

## Launch Recommendation: Start with 3 Plans

### Phase 1 (Month 1-2): Launch these 3 only

1. **5-Day Starter Reset** — conversion funnel entry point
2. **Morning Glow Plan** — core daily subscription (weekly billing)
3. **Family Wellness Starter** — highest-value subscriber type

**Why these three:**
- Starter Reset is low commitment, captures curious buyers
- Morning Glow is the default "I want a daily juice" plan
- Family plan doubles revenue per delivery stop

### Phase 2 (Month 2-3): Add these

4. **Hydration Habit Plan** — captures summer demand, simpler production
5. **Women's Wellness Plan** — differentiated positioning, high retention

### Phase 3 (Month 3+): Add these

6. **20-Day Routine Builder** — for customers who tried Starter but aren't ready for monthly
7. **Office Energy Plan** — only after afternoon delivery capability exists

---

## Subscription Mechanics

### Billing

| Period | How It Works |
|---|---|
| **Week 1-4** | Bill weekly (lower barrier to entry). Charge every Sunday for the coming week. |
| **Month 2+** | Offer monthly billing at 5% additional discount. Charge on 1st of month. |
| **Quarterly** | Offer at Month 4+ for loyal subscribers. 10% discount vs weekly rate. |

### Payment Methods

| Method | Priority | Notes |
|---|---|---|
| UPI autopay | Primary | Most Indians are UPI-native. Set up recurring mandate. |
| Bank transfer | Secondary | For monthly/quarterly billing |
| Cash | Avoid | Creates collection overhead, no recurring capability |
| Wallet pre-load | Optional (later) | Offer bonus credits for pre-loading (e.g., load Rs 2,000, get Rs 2,200 in credits) |

### Pause & Cancellation

| Action | Policy |
|---|---|
| **Pause (up to 2 days/month)** | Free. No questions asked. Just WhatsApp "pause tomorrow" before 8 PM. |
| **Pause (3-7 days)** | Allowed, but subscription rate reverts to weekly pricing for that period. |
| **Pause (>7 days)** | Treated as cancellation. Must re-subscribe. |
| **Cancellation** | No penalty. No lock-in. But ask for feedback (mandatory 1-question survey). |
| **Reactivation** | Can restart anytime. Same pricing. No re-enrollment fee. |

### Pause Reason Tracking

Track every pause/cancel reason. Top 5 will tell you what to fix:
1. "Traveling" — normal, no action needed
2. "Too expensive" — pricing issue, offer downgrade
3. "Didn't like taste" — product issue, offer SKU swap
4. "Delivery issues" — operations problem, fix immediately
5. "Don't see results" — education gap, send benefits content

---

## Upgrade Paths

```
5-Day Starter Reset (Rs 449)
    ↓ (60% should convert)
Morning Glow Plan - Weekly (Rs 549/week)
    ↓ (after 4 weeks)
Morning Glow Plan - Monthly (Rs 2,099/month, 5% savings)
    ↓ (add family member)
Family Wellness Starter (Rs 2,999/month)
    ↓ (add pulp products)
Family + Fiber Booster add-on (Rs 3,148/month)
```

**Every plan upgrade should feel like a natural next step, not a sales push.** The delivery person, the WhatsApp tips, and the booklets should make the customer want to upgrade before you ask.

---

## Key Metrics to Track

| Metric | Target | How to Track |
|---|---|---|
| Trial-to-subscription conversion | >50% | Count 5-Day starters who become weekly subscribers within 14 days |
| Weekly-to-monthly upgrade rate | >60% | Count weekly subscribers who switch to monthly within 6 weeks |
| Monthly churn rate | <15% | Monthly cancellations / total monthly subscribers |
| Pause frequency | <3 days/month avg | Track pause requests per subscriber per month |
| Average subscriber lifetime | >4 months | Cohort analysis — track each signup month |
| Revenue per subscriber/month | >Rs 1,800 | Total subscription revenue / active subscribers |
| Family plan % of subscribers | >20% | Family plans / total plans |
