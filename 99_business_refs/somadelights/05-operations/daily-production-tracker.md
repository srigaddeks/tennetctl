# Daily Production Tracker & Batch Log
### Templates, formulas, and SOPs for tracking every batch from press to delivery

---

## 1. Why You Must Track From Day 1

At 4am, the last thing you want to think about is spreadsheets. But the batch log you fill in those first quiet minutes — before deliveries, before the day gets noisy — is the most valuable business data you will generate.

**Without data, you cannot optimize COGS.**
You will guess at which SKU is draining your margin. You will reorder ingredients by feel instead of by yield. You will price based on hope instead of numbers. Every week without a batch log is a week where problems compound invisibly.

**Spoilage compounds fast.**
At 50 bottles/day and 5% spoilage, you lose 2–3 bottles daily. That is Rs 200–300 in product gone. Over a week, that is Rs 1,750+ in lost margin — money that came from real produce, real labour, real packaging. At launch, your goal is under 3% spoilage. You cannot hit a target you are not measuring.

**Batch logs are mandatory for FSSAI traceability.**
If there is ever a quality complaint, you must be able to show: which batch, which ingredients, which supplier, which delivery date. Without logs, you are exposed. With logs, you have a defensible paper trail.

**Logs reveal which SKUs to kill before they kill your cash.**
Some SKUs will have consistently low yield, high spoilage, or poor margins. You will not feel this — you will assume it is a bad week. The log makes it undeniable. Kill the SKU or fix the recipe before it compounds into a cash problem.

---

## 2. Daily Batch Log — Google Sheets Template

### Tab Name: `Daily Log`

One row per SKU per production run. If you press Green Morning and Beet Power on the same day, that is two rows.

| Column | Header | Description |
|--------|--------|-------------|
| A | Date | Press date (not delivery date). Format: DD-MM-YYYY |
| B | SKU Name | Green Morning / Citrus Charge / Beet Power / Turmeric Shot / Ash Gourd / [6th SKU] |
| C | Planned Quantity (bottles) | How many bottles you targeted for this batch |
| D | Actual Yield (bottles) | Bottles that came out of pressing and passed initial QC |
| E | Yield % | = D / C — tells you pressing efficiency. Target: above 90% |
| F | Ingredient Cost (Rs) | Total raw material cost for this batch (produce + water + any additives) |
| G | Packaging Cost (Rs) | Bottles + caps + labels for this batch only |
| H | COGS per Bottle (Rs) | = (F + G) / D — your true cost per bottle delivered |
| I | QC Pass | Yes / No — did the batch pass colour, smell, and taste check? |
| J | QC Reject Count | Number of bottles discarded during QC |
| K | Bottles Delivered | Actual bottles that left your kitchen for customers |
| L | Bottles Returned / Unsold | Bottles that came back or were not picked up |
| M | Spoilage Count | Bottles disposed after delivery window (expired, damaged, unsellable) |
| N | Spoilage % | = M / D — keep this under 3% at launch, under 1% at scale |
| O | Selling Price (Rs) | Per bottle price for this SKU |
| P | Revenue (Rs) | = K × O |
| Q | Gross Profit (Rs) | = P - (H × K) |
| R | Gross Margin % | = Q / P — target above 60% |
| S | Notes | Any issues: ingredient substitution, equipment problem, delay, cold chain break |

---

### Sample Filled Row — Green Morning

| Column | Value |
|--------|-------|
| Date | 01-04-2025 |
| SKU Name | Green Morning |
| Planned Quantity | 20 bottles |
| Actual Yield | 18 bottles |
| Yield % | 90% |
| Ingredient Cost (Rs) | Rs 360 (spinach, cucumber, green apple, ginger, lemon) |
| Packaging Cost (Rs) | Rs 90 (18 bottles × Rs 5) |
| COGS per Bottle (Rs) | Rs 25.00 |
| QC Pass | Yes |
| QC Reject Count | 0 |
| Bottles Delivered | 17 |
| Bottles Returned / Unsold | 1 |
| Spoilage Count | 0 |
| Spoilage % | 0% |
| Selling Price (Rs) | Rs 99 |
| Revenue (Rs) | Rs 1,683 |
| Gross Profit (Rs) | Rs 1,258 |
| Gross Margin % | 74.7% |
| Notes | Cucumber slightly soft — switched to second supplier next order |

---

## 3. Weekly Summary Template

### Tab Name: `Weekly Summary`

One row per week. Fill at end of Sunday.

| Column | Header | Description / Formula |
|--------|--------|-----------------------|
| A | Week # | Week 1, Week 2, etc. |
| B | Week Ending Date | Sunday date of that week |
| C | Total Bottles Pressed | Sum of all Actual Yield from Daily Log for this week |
| D | Total Bottles Delivered | Sum of all Bottles Delivered for this week |
| E | Delivery Rate % | = D / C — target above 95% |
| F | Total Spoilage (bottles) | Sum of all Spoilage Count for this week |
| G | Weekly Spoilage % | = F / C — alert if above 3% |
| H | Total Revenue (Rs) | Sum of all Revenue for this week |
| I | Total COGS (Rs) | Sum of all (COGS per Bottle × Delivered) for this week |
| J | Gross Profit (Rs) | = H - I |
| K | Gross Margin % | = J / H |
| L | Average COGS per Bottle (Rs) | = I / D |
| M | Best SKU (highest margin) | Manual: check which SKU had the best Gross Margin % this week |
| N | Worst SKU (highest spoilage or lowest margin) | Manual: identify the SKU to review |
| O | Top Issue This Week | One sentence: what went wrong or what surprised you |
| P | Action for Next Week | One concrete fix: change supplier, adjust recipe, reduce planned qty |

---

## 4. Monthly P&L Template

### Tab Name: `Monthly P&L`

Simple cash P&L. Fill at end of month.

| Line Item | Formula / Source | Month 1 Example |
|-----------|-----------------|-----------------|
| **Revenue** | | |
| Total Bottles Delivered | From Weekly Summary totals | 540 bottles |
| Average Selling Price (Rs) | Weighted average across SKUs | Rs 104 |
| **Total Revenue** | Bottles × Avg Price | **Rs 56,160** |
| | | |
| **Cost of Goods Sold** | | |
| Total Ingredient Cost (Rs) | From Daily Log, sum of column F | Rs 10,800 |
| Total Packaging Cost (Rs) | From Daily Log, sum of column G | Rs 2,700 |
| **Total COGS** | Ingredients + Packaging | **Rs 13,500** |
| | | |
| **Gross Profit** | Revenue - COGS | **Rs 42,660** |
| **Gross Margin %** | Gross Profit / Revenue | **75.9%** |
| | | |
| **Operating Costs** | | |
| Delivery (auto/fuel/courier) | Actual spend | Rs 3,200 |
| Utilities (electricity for cold storage) | Actual spend | Rs 800 |
| Packaging extras (bags, ice packs) | Actual spend | Rs 1,200 |
| **Total Operating Costs** | Sum above | **Rs 5,200** |
| | | |
| **Net Operating Profit** | Gross Profit - Operating Costs | **Rs 37,460** |
| | | |
| Partner Program Payouts | 10–15% of referred order value | Rs 3,360 |
| | | |
| **Net Profit** | Net Operating Profit - Partner Payouts | **Rs 34,100** |
| **Net Margin %** | Net Profit / Revenue | **60.7%** |
| | | |
| **Cash Position** | | |
| Opening Cash | Cash at start of month | Rs 40,000 |
| Cash In (Revenue collected) | Assuming UPI same-day | Rs 56,160 |
| Cash Out (COGS + Ops + Partner) | Total outflows | Rs 22,060 |
| **Closing Cash** | Opening + In - Out | **Rs 74,100** |

**Month 1 Assumptions Used Above:**
- 25 active customers, average 3.6 bottles/week each
- Mix: 40% Green Morning, 20% Citrus Charge, 20% Beet Power, 10% Turmeric Shot, 10% Ash Gourd
- Price range Rs 89–129, blended average Rs 104
- COGS held at Rs 25/bottle average
- No rent (home kitchen), no salaries (solo operation)
- Partner Program: 6 active partners generating ~30% of orders

---

## 5. QC Checklist — Per Batch

Run this checklist before sealing bottles. Takes 3 minutes. Do not skip it.

### Pre-Bottling QC — Pass/Fail

| # | Check | Pass Criteria | Action if Fail |
|---|-------|--------------|----------------|
| 1 | Colour Check | Matches expected colour card for this SKU (keep a printed reference card on your wall) | Do not bottle. Investigate: wrong ratio, oxidation, wrong produce |
| 2 | Smell Check | Clean, fresh, no fermentation smell, no sourness beyond expected | Discard batch. Log in Spoilage column. Do not deliver |
| 3 | Taste Check | pH and flavour within your established range for that SKU (build this range in Week 1) | Adjust if possible (add lemon for acidity correction) or discard |
| 4 | Yield Check | Actual yield within 10% of planned quantity | If yield is below 80%, investigate: produce water content, pressing pressure, equipment issue |
| 5 | Temperature Check | Juice below 8°C before bottling | Wait. Do not bottle warm juice. It shortens shelf life and accelerates spoilage |
| 6 | Label Check | Correct SKU name, correct press date printed or written, correct batch number | Re-print label before bottling. Never deliver unlabelled or mislabelled bottles |

**QC Rule:** Any single FAIL = hold the batch. Do not deliver. Log it. Understand the cause before the next batch.

---

## 6. Ingredient Inventory Tracker

### Tab Name: `Inventory`

Update every Sunday evening for the coming week.

| Column | Header | Description |
|--------|--------|-------------|
| A | Ingredient Name | Spinach, Cucumber, Green Apple, Ginger, Lemon, Beetroot, Carrot, Orange, Turmeric, Ash Gourd, etc. |
| B | Opening Stock (kg) | Stock at start of week (carry forward from previous closing) |
| C | Purchased This Week (kg) | Total bought this week |
| D | Purchase Cost (Rs) | Total paid for purchases this week |
| E | Cost per kg (Rs) | = D / C — track this to catch price creep from suppliers |
| F | Used This Week (kg) | Total consumed in production (back-calculate from batch logs) |
| G | Closing Stock (kg) | = B + C - F - H |
| H | Wastage (kg) | Trimmings, soft/unusable produce discarded before pressing |
| I | Waste % | = H / (B + C) |
| J | Notes | Supplier change, price spike, quality issue |

**Targets:**
- Ingredient wastage under 8% at launch (home kitchen, manual trimming)
- Ingredient wastage under 5% by Month 3 (better prep technique, tighter ordering)
- If wastage exceeds 10% two weeks in a row: review your ordering quantity. You are over-buying.

**Weekly Reorder Signal:**
If Closing Stock (column G) falls below 3 days of usage for any ingredient, add to next day's market order. Never run a batch with a substituted ingredient without logging it.

---

## 7. Spoilage Analysis Protocol

**Trigger:** Any week where total Spoilage % exceeds 3%.

Work through this in order. Do not skip steps.

**Step 1 — Identify the SKU.**
Filter your Daily Log by Spoilage Count > 0. Which SKU appears most? That is your target.

**Step 2 — Diagnose the cause.**
Ask these questions:

- Cold chain broken? Was there a delivery delay? Did bottles sit unrefrigerated for more than 30 minutes?
- Delivery delay? Did the customer not receive on time, holding the bottle past safe window?
- Recipe issue? Did you change ratios recently? Did ingredient quality drop (seasonal variation in acidity or water content)?
- Label error? Was the press date correct? Did bottles from a different batch get mislabelled?
- Sealing issue? Are caps fully sealed? Any leakage in transit?

**Step 3 — Pull the last 2 weeks of batch logs for that SKU.**
Look for a pattern. Spoilage appearing only on certain days of the week (delivery day issue)? Only from certain batches (equipment or recipe issue)? Only after a specific supplier order (ingredient quality issue)?

**Step 4 — Fix and document.**
Write the fix in the Notes column of the Daily Log. Write the root cause and fix in the Weekly Summary under "Top Issue" and "Action for Next Week." Do not just fix silently — document it so you have a record.

**Step 5 — Verify.**
The following week, watch that SKU's Spoilage % closely. If it stays elevated after your fix, escalate: consider temporarily pulling that SKU from the menu while you resolve the root cause.

**Spoilage cost reality check:**
Every 1% spoilage increase on a 50-bottle/day operation is approximately Rs 50/day × Rs 350/week × Rs 1,500/month in lost gross profit. At 5% spoilage, that is Rs 7,500/month. At scale (200 bottles/day), that is Rs 30,000/month. Treat spoilage as a cash leak, not a quality inconvenience.

---

## 8. Google Sheets Setup Guide

### Sheet Structure

Create one Google Sheets file named: `Soma Delights — Production Tracker`

Create the following tabs in this exact order:

| Tab Name | Purpose |
|----------|---------|
| `Daily Log` | One row per SKU per production day |
| `Weekly Summary` | One row per week, auto-summarised from Daily Log |
| `Monthly P&L` | One row per month, mix of manual and formula fields |
| `Inventory` | One row per ingredient per week |
| `Spoilage Log` | Filtered view of Daily Log rows where Spoilage > 0 |

---

### Key Formulas (Written as Plain Text Instructions)

**COGS per Bottle (Column H in Daily Log)**
Divide the sum of Ingredient Cost (column F) and Packaging Cost (column G) by the Actual Yield (column D). In other words: add your ingredient cost and packaging cost, then divide by how many bottles you actually produced.

**Gross Margin % (Column R in Daily Log)**
Divide Gross Profit (column Q) by Revenue (column P), then multiply by 100 to get a percentage. This tells you what fraction of each rupee of revenue is actual profit after production costs.

**Spoilage % (Column N in Daily Log)**
Divide Spoilage Count (column M) by Actual Yield (column D), then multiply by 100. This is the percentage of bottles you produced that you lost — not delivered, not sold, just gone.

**Weekly Summary — Total Bottles Pressed**
Use SUMIF on the Daily Log: sum everything in the Actual Yield column where the date falls within the week you are summarising. In plain English: add up all the Actual Yield values for rows where the Date is between Monday and Sunday of that week.

**Weekly Summary — Total Spoilage %**
Divide the total Spoilage Count for the week by the total Actual Yield for the week. This is your week-level spoilage rate — the single most important weekly metric.

**Spoilage Log Tab**
Use a filter view on the Daily Log tab: show only rows where Spoilage Count (column M) is greater than zero. Do not create a separate copy of the data — use Google Sheets' built-in filter view feature so it stays automatically in sync with Daily Log.

---

### Colour Coding to Add

- Spoilage % above 3%: highlight red
- Gross Margin % below 60%: highlight orange
- Yield % below 85%: highlight yellow
- QC Pass = No: highlight red

Set these as conditional formatting rules on the Daily Log tab. At 4am, you want to scan the sheet and see problems in colour immediately.

---

### Sharing

Share the sheet view-only with yourself on a second device (phone) so you can check numbers during delivery runs without accidentally editing. Keep edit access to one device — your kitchen laptop or tablet.

---

## 9. When to Move Beyond Google Sheets

Google Sheets will carry you further than you expect. Most solo operators can manage 100+ bottles/day on a well-structured sheet. But there are clear signals to watch for.

**Move beyond Google Sheets when any of the following are true:**

- Filling in the Daily Log takes more than 30 minutes per day consistently
- You have 3 or more production staff and errors are creeping in because multiple people touch the sheet
- You are managing 6+ SKUs with different pricing tiers or partner pricing and SUMIF formulas are getting unwieldy
- You want automated low-stock alerts or reorder triggers without manual checking

**Options at that point:**

| Tool | Best For | Cost |
|------|---------|------|
| Vyapar | Simple Indian SMB inventory + billing, GST-ready | Rs 1,999–3,999/year |
| Zoho Inventory | More structured inventory + order management, integrates with Zoho Books | Rs 4,000–8,000/year |
| Google Apps Script | Automate your existing sheet (alerts, summaries, email reports) without migrating | Free (requires one-time scripting effort of ~4–6 hours) |

**Recommended path:**
Before migrating to paid software, first try Google Apps Script automation. You can add a daily summary email, automatic spoilage alerts, and low-stock flags to your existing sheet in a single afternoon. Only move to Vyapar or Zoho when the sheet itself is the bottleneck, not just the manual work around it.

**Do not migrate during a growth phase.**
If you are adding customers week over week, do not disrupt your production tracking with a tool migration at the same time. Pick a stable week (flat order volume, no new SKUs) to migrate and run both systems in parallel for two weeks before switching fully.

---

*Document owner: Operations — Sri*
*Last updated: Phase 1 launch preparation*
*Review cadence: Monthly, or after any week with spoilage above 3%*
