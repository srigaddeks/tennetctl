# Tech Stack

## The Principle: Spreadsheets Until They Break

Do not build software until spreadsheets become painful. Do not buy tools until free tools become limiting. Do not automate until manual processes are proven.

Every hour spent building custom software at 20 customers is an hour not spent making deliveries, improving products, or talking to customers. The technology that matters most at launch is a WhatsApp Business account and a Google Sheet.

---

## Phase 1: NOW (Month 0-1, 0-30 Customers)

**Total tech cost: Rs 0-500/month**

### Orders: WhatsApp Business + Google Sheets

| Component | Detail |
|-----------|--------|
| WhatsApp Business app | Free. Set up business profile, product catalog, quick replies, labels, broadcast lists. |
| Order tracking sheet | Google Sheet with columns: Date, Customer Name, Flat/Address, Product, Quantity, Delivery Status, Payment Status, Notes |
| How orders come in | Customer sends "I want to start" on WhatsApp → you add them to the sheet → confirm on WhatsApp |
| How orders change | Customer sends "pause for 3 days" → you update the sheet → confirm |

**Google Sheet: Order Tracker**

| Column | Purpose |
|--------|---------|
| Customer Name | First name + last name |
| WhatsApp Number | Primary contact |
| Address | Flat no., building, area |
| Product | Which drink they subscribe to |
| Plan | Daily / Alternate / 3x Week |
| Start Date | When subscription began |
| Status | Active / Paused / Cancelled |
| Pause Until | If paused, return date |
| Delivery Notes | "Leave at door," "Ring bell," "After 7 AM" |

---

### Subscriptions: Google Sheets with Delivery Calendar

| Component | Detail |
|-----------|--------|
| Subscription sheet | Tab within the order tracker. Lists every active subscriber, their plan, and delivery days. |
| Daily delivery list | Filter the sheet each evening: "Who gets a delivery tomorrow?" Print or screenshot for morning reference. |
| Calendar view | Use Google Sheets conditional formatting to create a visual calendar: green = delivery day, grey = no delivery, yellow = paused. |

**Daily Delivery Prep Checklist (each evening):**
1. Open "Active Subscribers" tab
2. Filter for tomorrow's delivery day (based on plan type)
3. Remove paused subscribers
4. Count total bottles by product type → production plan
5. Sort by delivery route (area/building)
6. Screenshot delivery list → send to WhatsApp rider group (when applicable)

---

### Payments: UPI Direct + Razorpay Payment Links

| Component | Detail |
|-----------|--------|
| Month 0-1 | UPI direct transfers (Google Pay, PhonePe, Paytm). Customer pays Rs 4,500 at start of month. You send a UPI request. |
| Month 1+ | Razorpay Payment Links. Create a payment link for each plan (Rs 4,500 for Daily, Rs 3,300 for Weekday, etc.). Send via WhatsApp. 2% transaction fee. |
| Tracking | Add "Payment Date" and "Payment Amount" columns to the subscriber sheet. Mark paid/unpaid each month. |

**Why not Razorpay Subscriptions yet:** Auto-recurring payments require more setup, KYC, and have higher failure rates for small amounts. Manual payment links work fine until 50+ subscribers.

**Payment collection rhythm:**
- Monthly billing, first of the month
- Send Razorpay link via WhatsApp on the 28th of the previous month: "Hi [Name], your renewal for [Month] is Rs [X]. Here's the payment link: [link]. Please pay by the 1st so we can continue your deliveries without interruption."
- Follow up on the 2nd if unpaid
- If unpaid by the 3rd, pause deliveries and notify: "I've paused your deliveries until payment is sorted. Just pay the link when ready and I'll restart the next morning."

---

### CRM: Google Sheets

One comprehensive sheet with tabs:

| Tab | Purpose | Key Columns |
|-----|---------|------------|
| Subscribers | Master customer list | Name, WhatsApp, Address, Product, Plan, Start Date, Status, Referral Source, Notes |
| Referrals | Who referred whom | Referrer, Referred Customer, Referred Start Date, Monthly Spend, 10% Credit, Total Credits |
| Wallet | Referral + streak credits | Customer, Referral Credits, Streak Credits, Total Balance, Last Cashout Date |
| Feedback | Customer feedback log | Date, Customer, Type (product/delivery/general), Feedback, Action Taken, Resolved |
| Churn Log | Why people left | Customer, Start Date, Cancel Date, Reason, Win-back Attempted, Win-back Result |
| Pop-Up Log | Event tracking | Date, Location, Samples Given, Sign-Ups, Trials Started, Converted to Subscription |

---

### Delivery: Google Maps + WhatsApp

| Component | Detail |
|-----------|--------|
| Route planning | Open Google Maps, drop pins for all delivery addresses, arrange into logical route. Save as a named route. |
| Navigation | Google Maps turn-by-turn during delivery |
| Rider communication | WhatsApp group: "Soma Delivery Team." Share daily delivery list screenshot + route. Rider confirms each delivery with a message. |
| Delivery confirmation | Rider sends WhatsApp message after each cluster: "Aparna Sarovar done — 8 bottles delivered." You mark in the sheet. |

---

### Inventory: Google Sheet

| Column | Purpose |
|--------|---------|
| Date | Production date |
| Product | Which drink |
| Ingredients Used | Qty of each ingredient in grams/ml |
| Bottles Produced | Total bottles made |
| Bottles Delivered | Total bottles actually delivered |
| Waste | Bottles unsold, expired, or damaged |
| Ingredients Remaining | Stock level after production |
| Reorder Needed | Yes/No for each ingredient |

**Weekly ritual:** Every Sunday evening, review the inventory sheet. Calculate next week's production requirements. Place ingredient orders for Monday morning pickup from Bowenpally/Medchal market.

---

### Analytics: Manual Weekly Review

Every Sunday, 30 minutes:

| Metric | Where to Find It |
|--------|-----------------|
| Total active subscribers | Subscribers tab, filter Status = Active, count |
| New subscribers this week | Subscribers tab, filter Start Date = this week |
| Churn this week | Churn Log tab, filter Cancel Date = this week |
| Revenue collected | Sum of Payment Amount column for the month |
| Delivery success rate | Delivered / Scheduled from daily logs |
| Referral performance | Referrals tab, count new referrals this week |
| Pop-up conversion | Pop-Up Log tab, Converted / Samples ratio |
| Ingredient cost | Inventory tab, sum ingredient purchases this week |

---

### Support: WhatsApp (Founder Handles Directly)

No ticketing system. No email. No chatbot. Every customer messages the founder directly on WhatsApp. The founder responds personally.

**This is not scalable.** That's the point. At 20 customers, you WANT to hear every complaint, every suggestion, every compliment directly. This is your product research department.

**Response time targets:**
- General inquiry: within 2 hours
- Complaint/issue: within 30 minutes
- Delivery problem: within 15 minutes (during delivery hours)

---

### Marketing: Instagram + WhatsApp Status

| Channel | Tool | Cost |
|---------|------|------|
| Instagram | Phone camera + Canva Free | Rs 0 |
| Instagram scheduling | Later or Buffer free tier | Rs 0 |
| WhatsApp Status | Phone camera | Rs 0 |
| WhatsApp Broadcasts | WhatsApp Business | Rs 0 |

**Total monthly tech cost for Phase 1: Rs 0-500** (Razorpay transaction fees only)

---

## Phase 2: 3 MONTHS (50-100 Customers)

**Total tech cost: Rs 500-2,000/month**

### Orders: Simple Website with Razorpay Subscription Integration

| Component | Detail |
|-----------|--------|
| Website | Simple single-page site on Carrd.co (Rs 1,500/year) or basic WordPress (Rs 3,000-5,000 setup + Rs 200/month hosting) |
| Subscription checkout | Razorpay Subscriptions — customer selects plan, enters payment details, auto-charged monthly. 2% fee. |
| Order management | Razorpay dashboard shows active subscriptions, upcoming payments, failed payments |
| WhatsApp still active | Customers who prefer WhatsApp can still order that way. Website is an additional channel, not a replacement. |

**Website pages:**
1. Home: hero image, "What is micro-wellness?", product cards, how it works
2. Products: each product with photo, ingredients, benefits, price
3. Subscribe: plan selection + Razorpay checkout
4. Ingredient Stories: QR code destination pages for each ingredient
5. About: founder story, FSSAI info, contact

---

### CRM: Upgrade to Basic CRM

**Option A: HubSpot Free CRM**
- Free for unlimited contacts
- Track customer interactions, deals, tasks
- Email integration (if you start email)
- Mobile app for on-the-go management

**Option B: Zoho CRM Free**
- Free for up to 3 users
- Indian company — good local support
- Contact management, deals, tasks
- Integration with Zoho Payments

**Option C: Stay with Google Sheets** (honestly, this still works at 100 customers if the sheets are well-organized)

**Recommendation:** Try HubSpot Free at 50 customers. If it adds complexity without clear benefit, go back to Google Sheets. The CRM should save time, not create work.

---

### Delivery: Route Optimization Spreadsheet

At 50+ customers across 5-8 apartment complexes, route planning gets complex.

| Approach | Detail |
|----------|--------|
| Cluster-based routing | Group deliveries by apartment complex. Each complex = one stop. Order stops by proximity. |
| Google My Maps | Create a custom map with all delivery addresses plotted. Visually optimize the route. Save and share with rider. |
| Time estimation | Estimate 5 min per complex (for 5-15 bottles), plus drive time. Plan backwards from latest acceptable delivery time. |
| Route sheet | Daily sheet for rider: Stop 1 → [Complex Name, Gate info, Flat numbers, Product list]. Stop 2 → ... |

**At 100 customers:** Consider a free route optimization tool like RouteXL (free for up to 20 stops) or Circuit (free trial, then Rs 1,500/month).

---

### Wallet: Basic Wallet Tracking

Upgrade the Google Sheet wallet tracking to a more structured system:

| Component | Detail |
|-----------|--------|
| Wallet sheet | Per-customer wallet with monthly transaction log: date, type (referral/streak/cashout), amount, running balance |
| Monthly statement | Auto-generated from sheet. WhatsApp to each customer on the 15th. |
| Cashout process | Customer replies "CASH" → you verify balance ≥ Rs 500 → UPI transfer → mark in sheet |

---

### Analytics: Google Sheets Dashboard

Create a dedicated "Dashboard" tab with formulas pulling from other tabs:

| Metric | Formula Source |
|--------|--------------|
| MRR (Monthly Recurring Revenue) | =SUMPRODUCT of active subscribers × plan prices |
| Active subscriber count | =COUNTIF(Status, "Active") |
| New subscribers this month | =COUNTIFS(Start Date, this month) |
| Churn rate | =Cancelled this month / Active start of month |
| Referral rate | =New from referrals / Total new |
| Average revenue per subscriber | =MRR / Active count |
| Delivery success rate | =Delivered / Scheduled |
| Ingredient cost ratio | =Total ingredient cost / Revenue |

**Visualization:** Use Google Sheets charts — line chart for subscriber growth, bar chart for monthly revenue, pie chart for acquisition channels.

---

## Phase 3: 12 MONTHS (200-500 Customers)

**Total tech cost: Rs 5,000-15,000/month**

### Custom Ordering System

At 200+ customers, WhatsApp + spreadsheets genuinely break. Time to build a simple web application.

| Component | Detail |
|-----------|--------|
| Customer portal | Simple web app where customers log in, see their subscription, pause/modify, view wallet, see streak |
| Admin dashboard | You see all subscribers, today's delivery list, payment status, wallet balances, analytics |
| Subscription engine | Manage plans, billing cycles, auto-pause, auto-restart |
| Tech stack | Simple web app: React/Next.js frontend + Python/Node backend + PostgreSQL database. Or use a low-code platform (Retool, Appsmith) for the admin side. |
| Build vs. Buy | At 200 customers, build a custom MVP. Budget: Rs 50,000-1,00,000 (freelance developer, 4-6 weeks). Or build it yourself if you have tech skills. |

---

### Subscription Management with Pause/Modify

| Feature | Detail |
|---------|--------|
| Self-service pause | Customer pauses via portal. Auto-resumes on selected date. |
| Plan switching | Customer changes product/frequency from portal. Takes effect next delivery. |
| Payment management | Customer updates payment method. Failed payment auto-retries 3 times over 5 days. |
| Calendar view | Customer sees their delivery calendar — past deliveries, upcoming, paused dates |

---

### Wallet System with Referral Tracking

| Feature | Detail |
|---------|--------|
| Automated referral tracking | Unique referral code per customer. When a referred person subscribes using the code, system auto-tracks. |
| Auto-credit | 10% of referred customer's monthly spend auto-credited to referrer's wallet on the 1st of each month. |
| Streak auto-credit | System tracks consecutive delivery days. Auto-credits wallet at milestones (30, 60, 90 days). |
| Cashout | Customer requests cashout via portal. Admin approves. UPI transfer within 24 hours. |
| Wallet statement | Monthly email/WhatsApp with transaction details, balance, credits earned. |

---

### Route Optimization Tool

| Feature | Detail |
|---------|--------|
| Auto-route generation | Input today's delivery addresses → system outputs optimized route |
| Rider app | Simple mobile view: route map, stop-by-stop navigation, delivery confirmation at each stop |
| Capacity planning | System knows rider capacity (50 bottles per trip). Auto-splits routes if needed. |
| Performance tracking | Delivery time per stop, total route time, on-time rate |

**Options:**
- Circuit Route Planner (Rs 1,500-3,000/month) — ready-made, works well for delivery businesses
- OptimoRoute (Rs 2,000-4,000/month) — more features, better for multiple riders
- Custom build — only if the above don't fit your specific needs

---

### Inventory Management

| Feature | Detail |
|---------|--------|
| Demand forecasting | Based on active subscriptions + day of week patterns, predict tomorrow's production requirement |
| Ingredient tracking | Input ingredients purchased. System calculates consumption based on recipes. Alerts when stock is low. |
| Waste tracking | Log unsold/expired/damaged bottles. Track waste rate by product. |
| Supplier management | Track suppliers, prices, lead times. Compare costs over time. |

---

### Customer App (Maybe)

At 500 customers, a mobile app MIGHT make sense. Evaluate honestly:

| Build an app IF... | Don't build an app IF... |
|-------------------|--------------------------|
| 40%+ of customers request it | The web portal handles everything fine |
| Streak/wallet gamification would measurably improve retention | Customers are happy with WhatsApp + portal |
| You have Rs 3-5 lakhs budget for development | Budget is tight |
| You have a dedicated tech person to maintain it | You'd outsource maintenance |

**If yes, build a Progressive Web App (PWA) first.** It works like an app (home screen icon, offline capable, push notifications) but doesn't require App Store/Play Store submission. Cost: Rs 1-2 lakhs vs. Rs 3-5 lakhs for native.

---

### Analytics Dashboard

| Feature | Detail |
|---------|--------|
| Real-time metrics | Active subscribers, MRR, churn rate, NPS |
| Cohort analysis | Retention curves by monthly cohort |
| Channel attribution | Which channel did each customer come from? Which channel has best LTV? |
| Financial | Revenue, COGS, gross margin, unit economics — all auto-calculated |
| Delivery ops | On-time rate, route efficiency, rider performance |

**Options:**
- Build into the custom admin dashboard (cheapest, most customizable)
- Google Looker Studio (free, connects to Google Sheets or databases)
- Metabase (open-source, self-hosted, powerful)

---

## What NOT to Build Early

### 1. Don't Build an App Before 500 Customers

**Cost:** Rs 3-5 lakhs (native) or Rs 1-2 lakhs (PWA)
**Time:** 2-4 months of development, plus ongoing maintenance
**Who downloads it:** Nobody. Unknown brands don't get app downloads. Your customers are perfectly happy with WhatsApp.
**What to do instead:** WhatsApp (Month 0-6) → Simple website with portal (Month 6-12) → App (Month 12+, maybe)

### 2. Don't Buy Expensive CRM Software

**What you don't need:** Salesforce (Rs 10,000+/month), HubSpot paid (Rs 4,000+/month), Freshsales (Rs 2,000+/month)
**What you need:** Google Sheets (free) → HubSpot Free / Zoho Free (when sheets get messy) → Custom CRM in your web app (at 200+ customers)
**The trap:** CRM companies sell the idea that you need sophisticated customer tracking. At 30 customers, you know every customer by name. The CRM is your brain.

### 3. Don't Build Custom Software Until Spreadsheets Break

**Signs spreadsheets are breaking:**
- You're spending 30+ minutes/day on spreadsheet management
- You've made 3+ data entry errors this month
- Two people need to edit the same sheet simultaneously
- You need calculations that are too complex for formulas
- The sheet takes more than 5 seconds to load

**Until those signs appear,** Google Sheets is your tech stack. It's free, it's flexible, it's sharable, and it doesn't require a developer to maintain.

### 4. Don't Use Shopify

Shopify is for e-commerce (browse catalog → add to cart → checkout → ship). You are a subscription delivery business (subscribe → auto-deliver daily → build habit). Shopify doesn't support the subscription model natively, the delivery model at all, or the wallet/referral system you need. Shopify costs Rs 2,000+/month for features you won't use.

### 5. Don't Over-Automate WhatsApp

**What works:** WhatsApp Business with quick replies, labels, and broadcast lists.
**What to avoid:** WhatsApp API with automated chatbots. The ENTIRE value of WhatsApp for Soma Delights is that it's personal. The founder responds. A chatbot destroys the trust and warmth that differentiates the brand.
**Exception:** At 300+ subscribers, you might need a WhatsApp Business API for bulk broadcasts. But customer conversations should still be human-answered.

---

## Technology Decision Timeline

```
Month 0:    WhatsApp Business + Google Sheets + UPI payments
Month 1:    + Razorpay Payment Links
Month 2:    + Simple website (Carrd or WordPress)
Month 3:    + Razorpay Subscriptions on website
Month 4-6:  + CRM (HubSpot Free or Zoho Free, if needed)
Month 6:    + Route optimization tool (Circuit or similar)
Month 8-10: + Custom web app for ordering/admin (build or outsource)
Month 10-12:+ Automated wallet/referral system in web app
Month 12+:  + Analytics dashboard (Metabase or built-in)
Month 12+:  + Mobile app evaluation (PWA if justified)
```

---

## Monthly Tech Spend Projection

| Month | Tools | Monthly Cost (INR) |
|-------|-------|--------------------|
| 0-1 | WhatsApp Business, Google Suite, UPI | Rs 0 |
| 1-2 | + Razorpay (2% transaction fee on ~Rs 30,000-60,000 revenue) | Rs 600-1,200 |
| 2-3 | + Website hosting (Carrd or WordPress) | Rs 800-1,500 |
| 3-6 | + Razorpay Subscriptions (2% on ~Rs 1-3 lakh revenue) | Rs 2,000-6,000 |
| 6-9 | + CRM (free tier) + Route optimizer | Rs 1,500-3,000 |
| 9-12 | + Custom web app hosting + maintenance | Rs 3,000-5,000 |
| 12+ | Full stack: hosting + tools + route + analytics | Rs 8,000-15,000 |

---

## Data Ownership Checklist

Regardless of which tools you use, you MUST own your customer data:

| Data | Where It Lives | Backup Frequency |
|------|---------------|-----------------|
| Customer list (name, WhatsApp, address) | Google Sheet (now) → Database (later) | Weekly export |
| Order history | Google Sheet → Database | Weekly export |
| Payment records | Razorpay dashboard + Sheet | Monthly export |
| WhatsApp conversations | WhatsApp chat export | Monthly |
| Referral/wallet data | Google Sheet → Database | Weekly export |
| Feedback and churn reasons | Google Sheet → Database | Continuous |
| Production/inventory logs | Google Sheet → Database | Weekly |

**Never let a platform be your only copy.** If Razorpay goes down, you should have every customer's payment history in your own sheet. If WhatsApp bans your business account, you should have every customer's phone number in a separate export.

---

*The best tech stack is the one you don't think about. It works, it's reliable, it doesn't cost much, and it gets out of the way so you can focus on making great products and building real relationships with customers.*
