# 25 — KPI Dashboard

> Metrics that matter for Soma Delights. Daily, weekly, and monthly dashboards with targets by growth stage. What to measure, how to calculate it, and what the numbers should look like.

---

## Measurement Philosophy

Three rules:

1. **Measure what you'll act on.** If a metric won't change your behavior this week, don't track it yet.
2. **Daily metrics are operational.** They answer: "Did today go well?"
3. **Weekly and monthly metrics are strategic.** They answer: "Is the business working?"

---

## Daily Metrics (Check Every Day)

Track these in a Google Sheet row, one per day. Takes 5 minutes at 8 AM after the delivery round.

| Metric | How to Track | What "Good" Looks Like |
|--------|-------------|----------------------|
| **Orders produced** | Count bottles before dispatch | Within 5% of target (no overproduction, no shortfall) |
| **Orders delivered on time** | Count deliveries within stated window | 100% on time (95% minimum acceptable) |
| **Delivery issues** | Note any: wrong order, missed delivery, damaged bottle, late | 0 issues. Any issue = investigate same day. |
| **Wastage count** | Bottles produced but not delivered (spoiled, excess, returned) | 0–1 per day at < 50 customers. Max 5% of production. |
| **New sign-ups** | New customers who placed first order or signed up for trial | 1+ per day at Phase 1. Varies by stage. |
| **Customer messages requiring response** | WhatsApp unread messages at end of day | 0 unread by 9 PM. Response time < 2 hours during business hours. |
| **Ingredient stock status** | Quick check: anything running low for tomorrow? | Never run out. 2-day buffer on all key ingredients. |
| **Temperature log** | Morning fridge temp + dispatch temp | Fridge: 2–6 deg C. Dispatch bag: < 10 deg C. |

### Daily Log Template (Google Sheet)

| Date | Produced | Delivered | On-Time % | Issues | Wasted | New Sign-ups | Open Messages | Fridge Temp AM | Notes |
|------|----------|-----------|-----------|--------|--------|-------------|---------------|---------------|-------|
| 15/03 | 32 | 31 | 97% | 1 late (traffic) | 1 | 2 | 0 | 4 deg C | Late to Aparna complex |

---

## Weekly Dashboard

Review every Sunday evening. Takes 20 minutes. This is your strategic pulse check.

### Phase 1 Targets (Month 1–2, 20–50 Customers)

| Metric | Formula | Week 1-2 Target | Week 3-4 Target | Month 2 Target |
|--------|---------|----------------|----------------|---------------|
| **New trials** | Count of first-time orders | 3–5/week | 5–8/week | 5–10/week |
| **Trial to subscriber conversion** | Subscribers / Trials (trailing 2 weeks) | 30%+ | 35%+ | 40%+ |
| **Active subscribers** | Customers with active weekly/monthly plan | 10–15 | 20–30 | 35–50 |
| **Total deliveries** | Sum of daily deliveries | 60–90 | 120–180 | 200–300 |
| **On-time delivery %** | On-time / Total deliveries | 95%+ | 95%+ | 95%+ |
| **Wastage %** | Wasted bottles / Produced bottles | < 10% | < 8% | < 7% |
| **Gross revenue** | Sum of all payments received | Rs 10,000–15,000 | Rs 25,000–40,000 | Rs 50,000–80,000 |
| **COGS** | Ingredients + packaging + labor (production) | Track actual | Track actual | Track actual |
| **Gross margin %** | (Revenue - COGS) / Revenue | 45%+ | 50%+ | 55%+ |
| **Referral sign-ups** | New customers from referral code | 0–1 | 2–3 | 3–5 |

### Phase 2 Targets (Month 3–5, 50–150 Customers)

| Metric | Formula | Month 3 Target | Month 4 Target | Month 5 Target |
|--------|---------|---------------|---------------|---------------|
| **New trials** | Count | 8–12/week | 10–15/week | 10–15/week |
| **Trial to subscriber conversion** | | 40%+ | 40%+ | 45%+ |
| **Active subscribers** | | 60–80 | 90–120 | 120–150 |
| **Total deliveries** | | 350–500 | 500–700 | 700–900 |
| **On-time delivery %** | | 95%+ | 96%+ | 96%+ |
| **Wastage %** | | < 7% | < 6% | < 5% |
| **Gross revenue** | | Rs 1.5–2L | Rs 2–3L | Rs 3–4L |
| **Gross margin %** | | 50%+ | 52%+ | 55%+ |
| **Referral sign-ups** | | 5–8/week | 6–10/week | 8–12/week |
| **Route density** | Deliveries / Active routes | 50+ | 55+ | 60+ |

### Phase 3+ Targets (Month 6+, 150+ Customers)

| Metric | Formula | Month 6 | Month 9 | Month 12 |
|--------|---------|---------|---------|----------|
| **Active subscribers** | | 150–200 | 250–300 | 350–500 |
| **Monthly churn rate** | Churned / Start-of-month subscribers | < 8% | < 5% | < 4% |
| **Referral-driven acquisition %** | Referral new / Total new | 50%+ | 70%+ | 70%+ |
| **Gross margin %** | | 55%+ | 55%+ | 55%+ |
| **Contribution margin %** | (Revenue - COGS - delivery - team) / Revenue | 25%+ | 28%+ | 30%+ |
| **Cash flow** | Revenue - All operating expenses | Breakeven | Positive | Positive |

---

## Monthly Dashboard

Review on the 1st of each month. Takes 1 hour. This is your P&L and strategic health check.

### Subscriber Metrics

| Metric | Formula | How to Calculate |
|--------|---------|-----------------|
| **Total active subscribers** | Count of customers with active plan | Spreadsheet filter: status = active |
| **New subscribers** | Customers who started a plan this month | Count new entries this month |
| **Churned subscribers** | Customers who cancelled or didn't renew | Count cancellations + non-renewals |
| **Net subscriber growth** | New - Churned | Should be positive every month |
| **Subscriber retention rate** | (Start - Churned) / Start | 85%+ monthly |
| **Reactivations** | Previously churned customers who returned | Track separately — these are gold |

### Financial Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| **Revenue** | Total payments received | Growing month-over-month |
| **COGS** | Ingredients + packaging + direct labor | < 45% of revenue |
| **Gross margin** | Revenue - COGS | 55%+ |
| **Delivery cost** | Rider salary + fuel | < 10% of revenue |
| **Contribution margin** | Revenue - COGS - delivery | 45%+ |
| **Operating expenses** | Rent, admin, marketing materials, booklets, etc. | < 15% of revenue |
| **Net operating income** | Contribution margin - operating expenses | Positive by Month 6 |
| **AOV (Average Order Value)** | Revenue / Total orders | Rs 110–140 per order |
| **ARPU (Avg Revenue Per User)** | Revenue / Active subscribers | Rs 2,200–2,800/month |

### Unit Economics

| Metric | Formula | Target |
|--------|---------|--------|
| **Subscriber LTV (12-month projected)** | ARPU x Gross margin % x Avg lifetime months | Rs 15,000–25,000 |
| **CAC** | (Referral credits paid + kiosk/pop-up costs + samples) / New customers | Rs 200–500 |
| **LTV:CAC ratio** | LTV / CAC | 10x+ (because zero ad spend) |
| **CAC payback period** | CAC / (Monthly ARPU x Gross margin %) | < 30 days |
| **Subscriber breakeven** | Fixed cost per subscriber / Monthly contribution per subscriber | < 2 months |

### Referral & Growth Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| **Referral rate** | New customers from referrals / Total new customers | 30%+ (Phase 1), 70%+ (Phase 3+) |
| **Referral activation rate** | Referrers who referred 1+ person / Total referrers | 15%+ |
| **Wallet credits outstanding** | Total uncashed referral credits | Track liability |
| **Wallet cashouts this month** | Credits cashed out | Track cash impact |
| **Pop-ups conducted** | Count | 2–4/month |
| **Pop-up conversion rate** | Trials from pop-up / Samples given | 15%+ |

### Operational Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| **Route density** | Total deliveries / Number of routes | 50+ per route |
| **Route efficiency** | Revenue generated per route | Rs 5,000+ per route per day |
| **Production efficiency** | Bottles per production hour | 20+ |
| **Wastage %** | Wasted / Produced | < 5% |
| **On-time delivery rate** | Monthly average | 96%+ |
| **Customer complaints** | Count | < 2% of deliveries |
| **Complaint resolution time** | Avg hours to resolve | < 4 hours |

### Product Metrics

| Metric | How to Track | Action |
|--------|-------------|--------|
| **Top 3 SKUs by volume** | Count orders per SKU | Double down on production efficiency for these |
| **Bottom 3 SKUs by volume** | Count orders per SKU | Evaluate: improve, rotate, or kill |
| **SKU contribution margin** | Revenue - COGS per SKU | Kill any SKU below 40% margin |
| **New SKU trial adoption** | % of subscribers who try new SKU in first week | 50%+ means good product-market fit |

### Engagement Metrics

| Metric | How to Track | Target |
|--------|-------------|--------|
| **Booklets distributed** | Count | 1 per subscriber per month |
| **QR code scans** | URL shortener analytics | 20%+ of subscribers scan monthly |
| **WhatsApp message response rate** | Messages read / Messages sent | 70%+ |
| **Community event attendance** | Count (Phase 3+) | 15–25 per event |
| **Customer satisfaction (NPS proxy)** | Monthly WhatsApp poll: "Would you recommend us?" | 8+ out of 10 average |

---

## First 90 Days — The 5 KPIs That Matter Most

Everything else is noise until these 5 are healthy. Ranked by importance.

### 1. Week 1 to Week 2 Retention

**The question:** Do people reorder after trying?

| Signal | Meaning | Action |
|--------|---------|--------|
| 70%+ reorder | Product-market fit exists | Push growth |
| 50–70% reorder | Decent but something's off | Survey non-reorderers, improve |
| < 50% reorder | Product or price problem | Stop growing, fix the product |

**How to measure:** Of the people who ordered in Week 1, how many ordered again in Week 2? Simple spreadsheet filter.

### 2. Referral Rate

**The question:** Is word of mouth working?

| Signal | Meaning | Action |
|--------|---------|--------|
| 30%+ from referrals | Strong organic growth engine | Optimize referral UX, reward referrers |
| 15–30% from referrals | Decent but needs nudging | Actively ask happy customers to refer, simplify referral process |
| < 15% from referrals | Product isn't remarkable enough | Improve product, packaging, unboxing experience, education materials |

**How to measure:** Ask every new customer: "How did you hear about us?" Track in spreadsheet.

### 3. Delivery Consistency

**The question:** Does the bottle arrive at the same time every day?

| Signal | Meaning | Action |
|--------|---------|--------|
| 98%+ on time | Habit formation working | Maintain |
| 90–98% on time | Acceptable but watch closely | Identify late delivery causes, fix route |
| < 90% on time | Habit breaks, churn incoming | Route redesign, rider performance review, or founder does delivery |

**How to measure:** Log delivery completion time per customer daily. "On time" = within the stated delivery window.

### 4. Unit Economics Per Order

**The question:** Do we make money on each bottle delivered?

| Component | Target |
|-----------|--------|
| Revenue per order | Rs 99–149 |
| COGS per order | Rs 35–50 |
| Delivery cost per order | Rs 8–15 |
| Packaging per order | Rs 15–18 |
| **Contribution per order** | **Rs 30–70** |

**How to measure:** Total revenue / total orders vs. total variable costs / total orders. Must be positive. If negative at any point, stop and fix pricing or COGS.

### 5. Wastage Percentage

**The question:** Are we producing the right amount?

| Signal | Meaning | Action |
|--------|---------|--------|
| < 5% | Excellent production planning | Maintain |
| 5–10% | Acceptable at early stage | Tighten order confirmation process |
| 10–15% | Margin erosion | Switch to produce-to-order only |
| > 15% | Serious problem | Over-producing, bad forecasting, or spoilage in storage |

**How to measure:** (Bottles produced - Bottles delivered) / Bottles produced. Track daily, review weekly.

---

## Dashboard Tools

### Phase 0–2 (Under 150 Customers): Google Sheets

Set up 4 tabs:
1. **Daily Log** — one row per day, all daily metrics
2. **Customer List** — name, apartment, plan, start date, referral source, status
3. **Weekly Summary** — auto-calculated from daily log
4. **Monthly P&L** — revenue, costs, margins

Total setup time: 2 hours. Template structure:

**Daily Log columns:** Date | Produced | Delivered | On-Time | Issues | Wasted | New Signups | Revenue | COGS | Notes

**Customer List columns:** Name | Phone | Apartment | Flat | Plan | Start Date | Referral Source | Referrer Name | Status | Notes

### Phase 3+ (150+ Customers): Consider Simple Tools

| Tool | Purpose | Cost |
|------|---------|------|
| Google Sheets (continue) | Core tracking | Free |
| Razorpay Dashboard | Payment tracking, subscription management | Transaction fees only |
| Zoho Books | Accounting, GST filing | Rs 750/month |
| Notion | SOPs, team documentation | Free |
| WhatsApp Business API | Broadcast, auto-replies at scale | Rs 500–1,000/month |

Do NOT build custom dashboards or apps until you have 300+ customers. Google Sheets handles everything until then.

---

## Weekly Review Template

Every Sunday, 20 minutes. Answer these 7 questions:

1. **How many active subscribers?** (vs. last week)
2. **How many new trials and conversions?** (is the funnel healthy?)
3. **What was on-time delivery %?** (any issues to fix?)
4. **What was wastage %?** (are we producing right?)
5. **What was this week's revenue vs. cost?** (are we profitable per unit?)
6. **Did any customer churn? Why?** (pattern or one-off?)
7. **What's the one thing to improve next week?** (pick ONE, not five)

Write answers in the weekly summary tab. Review the trend over 4 weeks — single-week dips are noise, 4-week trends are signal.

---

## Monthly Review Template

Every 1st of the month, 1 hour. Answer these 10 questions:

1. **Net subscriber growth this month?** (new minus churned)
2. **What was monthly revenue and gross margin?** (P&L summary)
3. **What was CAC this month?** (all acquisition costs / new customers)
4. **What is projected 12-month LTV?** (ARPU x margin x avg lifetime)
5. **Is LTV:CAC ratio above 5x?** (healthy growth economics?)
6. **What % of new customers came from referrals?** (organic growth engine health)
7. **Top 3 SKUs?** (double down on these)
8. **Bottom 3 SKUs?** (improve, rotate, or kill)
9. **What was the biggest operational problem?** (fix it this month)
10. **What's the biggest opportunity for next month?** (prioritize one thing)

---

## Red Flags — Metrics That Demand Immediate Action

| Red Flag | Threshold | Action |
|----------|-----------|--------|
| Week-over-week subscriber decline | 2 consecutive weeks | Stop all growth, investigate churn |
| On-time delivery below 90% | Any single week | Route redesign or rider change |
| Wastage above 15% | Any single week | Switch to strict order-only production |
| Gross margin below 40% | Any single month | Ingredient cost audit + pricing review |
| Zero referrals in a week | 2 consecutive weeks | Product/experience problem, not referral system |
| Customer complaint spike | 5%+ of deliveries | Quality issue — audit production process |
| Cash balance below Rs 30,000 | Any day | Emergency mode — cut non-essentials, collect receivables |
| Founder working 7 days/week | 3 consecutive weeks | Hire kitchen helper immediately |

---

*Metrics are medicine, not vitamins. Take them regularly, read them honestly, and act on what they tell you. The businesses that succeed aren't the ones with the most data — they're the ones that act on 5 numbers every week instead of ignoring 50.*
