> **Note:** This document contains the internal mechanics of the Soma Partner Program.
> For the customer-facing program design, see [partner-program.md](partner-program.md).
> In all customer-facing contexts, this is called the **Partner Program**, never "referral program."

# 31. Referral Program — Single-Level, Wallet-Based

> Every customer is a potential growth channel. The referral program makes sharing natural, rewarding, and fraud-resistant.

---

## Program Philosophy

### Why Referral, Not Advertising

| Advertising | Referral |
|-------------|----------|
| Interruptive — people ignore it | Conversational — people trust it |
| Expensive — Rs 500-2,000 CAC | Cheap — Rs 100-300 effective CAC |
| One-time impression | Ongoing relationship |
| Brand talks about itself | Customer talks about brand |
| Scales with budget | Scales with satisfaction |

### Design Principles

1. **Single-level only.** A refers B, A earns. B refers C, B earns. A does NOT earn from C. No MLM. No pyramids. Clean.
2. **Reward the behaviour, not the sign-up.** Referrer earns only after the referred customer has PAID for a full month. No gaming with free trials.
3. **Simple enough to explain in one WhatsApp message.** If you need a FAQ page to explain the program, it's too complicated.
4. **Generous but sustainable.** 10% is meaningful to the referrer and affordable for the business at 50-60% gross margins.
5. **Anti-abuse by design.** Gating, caps, and manual review make gaming unprofitable.

---

## Core Mechanics

### The Basic Loop

```
Customer A receives their unique referral code: SOMA-PRIYA
         │
         ▼
Customer A shares code with Friend B (via booklet, WhatsApp, word of mouth)
         │
         ▼
Friend B signs up using code SOMA-PRIYA
         │
         ▼
Friend B completes their first paid month (minimum 4 paid deliveries)
         │
         ▼
Customer A starts earning 10% of Friend B's total spend
         │
         ▼
Credits accumulate monthly in Customer A's Soma Wallet
         │
         ▼
Customer A uses credits for Soma orders OR withdraws cash (after Rs 500)
```

### Key Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Earn rate** | 10% of referred customer's total spend | Generous enough to motivate, sustainable at 55% gross margin |
| **Duration** | 12 months from referred customer's first paid order | Long enough to be valuable, bounded to prevent infinite liability |
| **Activation trigger** | Referred customer completes 4th paid delivery | Ensures real customer, not just a sign-up; takes ~1 week for daily subscribers |
| **Credit frequency** | Monthly (added on 1st of following month) | Simple to understand, easy to reconcile |
| **Minimum withdrawal** | Rs 500 (Starter/Advocate), Rs 300 (Champion), Rs 200 (Ambassador) | Prevents micro-transactions, encourages accumulation |
| **Withdrawal method** | UPI transfer within 7 business days | Universal in India, zero transaction cost for business |
| **Wallet expiry** | Never (while account is active) | Builds trust, no "use it or lose it" pressure |
| **Monthly earning cap** | Rs 2,000/month per referrer | Prevents gaming at scale, keeps program sustainable |

### Referral Code Format

- **Format:** `SOMA-[FIRSTNAME]` (e.g., SOMA-PRIYA, SOMA-ARUN)
- **If name conflict:** `SOMA-PRIYA2` or `SOMA-PRIYAK` (first letter of last name)
- **Case insensitive:** SOMA-PRIYA = soma-priya = Soma-Priya
- **Where assigned:** At customer sign-up, automatically generated
- **Where displayed:** In WhatsApp welcome message, on booklet (handwritten or stickered), in wallet page

---

## Tier System

### Overview

| Tier | Referrals Required | Earn Rate | Cash Withdrawal Threshold | Perks |
|------|-------------------|-----------|--------------------------|-------|
| **Starter** | 0-2 active referrals | 10% | Rs 500 (store credit only below this) | Basic program access |
| **Advocate** | 3-5 active referrals | 10% | Rs 500 (cash eligible) | 3 extra booklets to distribute |
| **Champion** | 6-10 active referrals | 12% | Rs 300 | 1 free product/month + priority WhatsApp support |
| **Ambassador** | 11+ active referrals | 15% | Rs 200 | Co-branded booklet, exclusive products, monthly wellness call with founder |

### Tier Details

#### Starter (0-2 Referrals)

Every customer starts here. They receive their referral code at sign-up.

- **Earn rate:** 10% of referred customer's spend
- **Wallet:** Credits usable for Soma orders only (no cash withdrawal)
- **Cash withdrawal:** Only after reaching Rs 500 AND upgrading to Advocate (3 referrals)
- **Communication:** Monthly wallet balance update via WhatsApp

**Example earnings:**
- Refer 1 friend who spends Rs 2,299/month
- Monthly earning: Rs 230
- After 3 months: Rs 690 in wallet (usable for ~3 free bottles per month)

#### Advocate (3-5 Referrals)

The sweet spot — these customers are genuinely enthusiastic and will distribute booklets.

- **Earn rate:** 10%
- **Wallet:** Cash withdrawal unlocked at Rs 500+
- **Bonus:** 3 extra premium booklets to hand to friends (Rs 150 value, free)
- **Communication:** Monthly wallet update + quarterly "thank you" note

**Example earnings:**
- 4 active referrals, each spending Rs 2,299/month
- Monthly earning: Rs 920
- Can withdraw Rs 920/month after first month at this tier
- Annual earning potential: Rs 11,040

#### Champion (6-10 Referrals)

Rare but powerful — these are true fans. Treat them like partners.

- **Earn rate:** 12% (upgrade from 10%)
- **Wallet:** Cash withdrawal at Rs 300+
- **Bonus:** 1 free product per month (any SKU) + priority WhatsApp support (response within 1 hour)
- **Communication:** Personal WhatsApp message from founder monthly

**Example earnings:**
- 8 active referrals, each spending Rs 2,299/month
- Monthly earning: Rs 2,207 (capped at Rs 2,000)
- Plus 1 free product worth Rs 99-129
- Annual earning potential: Rs 24,000 + Rs 1,500 in free products

#### Ambassador (11+ Referrals)

This will likely be 0-2 people in the first year. Treat them like co-founders.

- **Earn rate:** 15%
- **Wallet:** Cash withdrawal at Rs 200+
- **Bonus:**
  - Co-branded booklet (their name on cover: "Curated by [Name] x Soma Delights")
  - Exclusive products (early access to new SKUs, limited editions)
  - Monthly 15-minute wellness call with founder
  - Invitation to product development feedback sessions
- **Communication:** Direct WhatsApp line to founder, monthly call

**Example earnings:**
- 15 active referrals, each spending Rs 2,299/month
- Monthly earning: Rs 2,000 (capped)
- Plus exclusive products, personal attention, brand recognition

---

## Wallet Mechanics

### How Credits Work

```
Timeline Example — Customer Priya:

January:
  - Priya refers Arun. Arun signs up Jan 5.
  - Arun's status: "Pending" (hasn't completed 4 deliveries yet)
  - Priya's wallet: Rs 0 (no earnings yet)

January 15:
  - Arun completes his 4th paid delivery.
  - Arun's status: "Active Referral"
  - Priya's earnings start accruing from this point.

February 1:
  - Arun spent Rs 1,800 in January (from Jan 15-31).
  - Priya earns 10% = Rs 180.
  - Priya's wallet: Rs 180 (visible as "Available")
  - WhatsApp notification: "You earned Rs 180 from referrals! Wallet balance: Rs 180."

March 1:
  - Arun spent Rs 2,299 in February (full month).
  - Priya earns 10% = Rs 230.
  - Priya's wallet: Rs 410.
  - WhatsApp: "You earned Rs 230 from referrals! Wallet balance: Rs 410."

April 1:
  - Arun spent Rs 2,299 in March.
  - Priya earns Rs 230.
  - Priya's wallet: Rs 640.
  - Priya can now withdraw cash (Rs 640 > Rs 500 threshold, assuming she's Starter tier).
  - Or she can use Rs 640 toward Soma orders.

If Priya refers 2 more people (total 3), she upgrades to Advocate tier and unlocks:
  - Cash withdrawal at Rs 500+
  - 3 free booklets to distribute
```

### Wallet Visibility

**Option 1: WhatsApp Bot (Phase 1 — manual)**
Customer sends "WALLET" to Soma WhatsApp number. Founder replies with balance within 2 hours.

**Option 2: WhatsApp Bot (Phase 2 — semi-automated)**
Customer sends "WALLET" → auto-reply with balance from a Google Sheet lookup (using WhatsApp Business API or a simple Twilio integration).

**Option 3: Simple Web Page (Phase 3 — at 100+ customers)**
somadelights.in/wallet?code=SOMA-PRIYA → shows balance, transaction history, tier status.

### Wallet Display Format (WhatsApp)

```
🌿 SOMA WALLET — Priya

Tier: Advocate ⭐⭐⭐
Active Referrals: 4

This Month's Earnings:
  Arun K.     Rs 230
  Meena S.    Rs 230
  Ravi P.     Rs 180 (partial month)
  ─────────────────
  Total:      Rs 640

Wallet Balance: Rs 1,820
  Available:  Rs 1,820
  Pending:    Rs 230 (releases Apr 1)

💰 Withdraw: Reply WITHDRAW [amount]
🛒 Use for order: Mention at next delivery

Next tier: Champion (need 2 more referrals)
Champions earn 12% + free monthly product!
```

### Withdrawal Process

1. Customer sends "WITHDRAW 500" to Soma WhatsApp
2. Founder verifies wallet balance and tier eligibility
3. Founder confirms: "Processing Rs 500 withdrawal to your UPI. You'll receive it within 7 business days."
4. Transfer via UPI (Google Pay, PhonePe, or direct UPI transfer)
5. Wallet balance updated
6. Confirmation: "Rs 500 transferred to [UPI ID]. New wallet balance: Rs 1,320."

**At small scale (under 100 customers), this is 100% manual and takes 5 minutes per withdrawal.**

---

## Referral Flow — Step by Step

### Step 1: Customer Receives Code

**Trigger:** Customer completes sign-up and first paid delivery.

**WhatsApp message:**

> Welcome to Soma Delights, Priya! 🌿
>
> Your personal referral code is: **SOMA-PRIYA**
>
> Share this code with friends and family. When they subscribe and complete their first month, you'll earn 10% of everything they spend — for a full year.
>
> Use your earnings for free Soma products or cash them out.
>
> Your booklet has a space for your referral code — write it in!

### Step 2: Customer Shares Code

**Channels:**
1. **Booklet hand-off:** Customer gives their extra booklet to a friend with code written inside
2. **WhatsApp forward:** Customer sends a pre-written message (provided by Soma) to friends
3. **Word of mouth:** Customer mentions Soma in conversation — "Use my code SOMA-PRIYA"
4. **Social media:** Customer shares their routine on Instagram/WhatsApp status, tags @somadelights

**Pre-written message for customer to forward:**

> Hey! I've been starting my mornings with Soma Delights — fresh cold-pressed juice delivered to my door at 7 AM. No preservatives, made daily.
>
> Use my code **SOMA-PRIYA** when you sign up and we both benefit.
>
> Try it: [WhatsApp link]

### Step 3: New Customer Signs Up

New customer contacts Soma via WhatsApp and mentions the referral code.

**Soma's response:**

> Hi [Name]! Welcome! 👋
>
> Great to have you — Priya is one of our favourite customers!
>
> Your first week is at our introductory price. Let me know:
> 1. Your delivery address
> 2. Preferred juice (or we'll surprise you!)
> 3. Any allergies or preferences
>
> First delivery: tomorrow at 7 AM!

### Step 4: Activation (4th Paid Delivery)

After the new customer's 4th paid delivery, the referral is "activated."

**WhatsApp to referrer:**

> Great news, Priya! 🎉
>
> Arun (referred by you) just completed his first week. You'll start earning 10% of his purchases, credited monthly to your Soma Wallet.
>
> At his current plan, that's ~Rs 230/month added to your wallet.
>
> Keep sharing — you're 2 referrals away from Advocate tier!

**WhatsApp to new customer:**

> Arun, you've completed your first week! 🌿
>
> How are you feeling? We'd love to hear your feedback.
>
> PS — Priya (who referred you) just started earning wellness credits thanks to you. You'll get your own referral code too — share the wellness!

### Step 5: Monthly Credit

On the 1st of each month, calculate referral earnings and credit wallets.

**WhatsApp to referrer:**

> Monthly Soma Wallet Update 🌿
>
> You earned Rs 460 from referrals in March.
>
> Breakdown:
>   Arun K. — Rs 230
>   Meena S. — Rs 230
>
> Wallet balance: Rs 1,360
>
> Use for your next order or reply WITHDRAW to cash out.

---

## Gating & Anti-Abuse Rules

### Activation Gating

| Gate | Requirement | Why |
|------|-------------|-----|
| **Paid delivery gate** | Referred customer must complete 4 paid deliveries before referrer earns | Prevents sign-up gaming — only real, paying customers count |
| **First month gate** | Full calendar month must pass before referral earnings are withdrawable | Prevents quick churn after referral credit |
| **Household gate** | Maximum 1 referral credit per household address | Prevents family members signing up under different names |
| **Monthly cap** | Maximum Rs 2,000/month in referral earnings | Prevents scaled gaming; keeps program sustainable |

### Self-Referral Detection

**Red flags (automatic flagging):**

| Signal | Detection Method | Action |
|--------|-----------------|--------|
| Same delivery address as referrer | Address matching in order sheet | Auto-flag, manual review |
| Same phone number pattern (e.g., +91-9XXXX-XXXX1, +91-9XXXX-XXXX2) | Phone number similarity check | Auto-flag, manual review |
| Same UPI account for wallet withdrawal | UPI ID matching | Block withdrawal, manual review |
| Same device (if using web sign-up) | Cookie/fingerprint check (Phase 3) | Auto-flag |
| Referral and referred customer sign up within 1 hour | Timestamp matching | Auto-flag |

**At small scale (under 100 customers), all flags result in manual review by founder. False positives are fine — better to verify than to miss fraud.**

### Volume Flags

| Signal | Threshold | Action |
|--------|-----------|--------|
| More than 3 referrals in 24 hours | 3 | Auto-pause referral credits, founder review |
| More than 10 referrals in 7 days | 10 | Account flagged for investigation |
| Referral from a non-customer | N/A | Code disabled; must be an active subscriber to refer |
| Referred customer churns within 7 days | N/A | No credits earned; referrer notified |

### Fraud Response Protocol

1. **Flag identified:** Founder reviews within 24 hours
2. **Investigation:** Check delivery addresses, payment methods, order patterns
3. **False positive:** Unflag and apologize to customer — offer a small goodwill credit (Rs 50)
4. **Confirmed fraud:** Revoke all pending credits. Disable referral code. Send message:

> "Hi [Name], we've noticed some unusual activity on your referral account. We've paused your referral credits while we review. If this is a mistake, please WhatsApp us and we'll sort it out immediately."

5. **Repeat offender:** Ban from referral program (can still be a customer)

---

## Edge Cases

### Referrer Churns (Stops Subscribing)

- Referral earnings **continue** for the full 12-month duration
- Wallet credits accumulate even if referrer is not an active subscriber
- Incentive: referrer may re-subscribe to use credits (retention mechanism)
- Cash withdrawal still available at tier thresholds

### Referred Customer Churns After 1 Month

- Referrer earned for Month 1 — no clawback
- No further earnings until/unless referred customer reactivates
- If referred customer reactivates within the 12-month window, earnings resume

### Referred Customer Pauses Subscription

- No earnings during pause period
- 12-month clock does NOT reset — original expiry date stands
- Earnings resume when referred customer reactivates

### Referred Customer Upgrades Plan

- Referrer earns 10% of the higher plan amount
- Example: referred customer upgrades from Rs 1,999 to Rs 2,599 plan → referrer earns Rs 260/month instead of Rs 200

### Referred Customer Downgrades Plan

- Referrer earns 10% of the lower plan amount
- No clawback on previous higher-tier earnings

### Dispute Between Two Referrers

- If two people claim they referred the same customer: **first code used wins**
- The referral code entered at sign-up is the official record
- If no code was entered but customer verbally names a referrer: founder assigns manually
- If truly ambiguous: split credit 50/50 for the first month, then assign to whoever the customer confirms

### Referrer Wants to Transfer Credits to Another Customer

- Not allowed in Phase 1 (keeps system simple)
- Consider in Phase 2 if enough demand (at 200+ customers)

---

## WhatsApp Notification Templates

### Referral Sign-Up Notification

> 🌿 [Referrer Name], someone just signed up using your code!
>
> [New Customer First Name] has started their Soma journey. You'll begin earning 10% of their purchases after they complete their first 4 deliveries.
>
> We'll keep you posted!

### Referral Activation Notification

> 🎉 Great news, [Referrer Name]!
>
> [New Customer First Name] just completed their activation period. You're now earning 10% of their monthly spend.
>
> Estimated monthly earning from this referral: Rs [amount].
>
> Wallet balance: Rs [balance].

### Monthly Earnings Notification

> 🌿 SOMA WALLET — Monthly Update
>
> [Referrer Name], you earned Rs [amount] from referrals in [month].
>
> Active referrals: [count]
> This month's earnings: Rs [amount]
> Wallet balance: Rs [balance]
> Pending (releases next month): Rs [pending]
>
> 🛒 Use for orders | 💰 Reply WITHDRAW [amount]

### Tier Upgrade Notification

> ⭐ Congratulations, [Referrer Name]!
>
> You've been upgraded to [Tier Name]!
>
> What's new:
> - Earn rate: [rate]%
> - Cash withdrawal threshold: Rs [threshold]
> - [Tier-specific perk]
>
> Thank you for being a Soma champion!

### Near-Tier Notification (Engagement Nudge)

> 🌿 [Referrer Name], you're just [X] referral(s) away from [Next Tier Name]!
>
> [Tier perks preview]
>
> Share your code: SOMA-[CODE]
> Or forward this message to a friend who'd love fresh morning wellness.

### Withdrawal Confirmation

> 💰 Withdrawal Processed
>
> Amount: Rs [amount]
> To: [UPI ID]
> Expected by: [date — within 7 business days]
>
> Remaining wallet balance: Rs [balance]
>
> Thank you for being part of the Soma family!

---

## Financial Impact Model

### Referral Program Cost at Scale

| Customers | Avg. Referrals per Customer | Active Referrals | Monthly Referral Payout | As % of Revenue |
|-----------|----------------------------|------------------|------------------------|-----------------|
| 50 | 0.5 | 25 | Rs 5,750 | 5.0% |
| 100 | 0.6 | 60 | Rs 13,800 | 6.0% |
| 200 | 0.7 | 140 | Rs 32,200 | 7.0% |
| 500 | 0.8 | 400 | Rs 92,000 | 8.0% |

**Assumptions:**
- Average customer spend: Rs 2,299/month
- Referral earn rate: 10% (blended across tiers)
- Not all referrals are active simultaneously

### Why 10% is Sustainable

- Gross margin per bottle: 55-60%
- Referral payout: 10% of revenue = ~18% of gross margin
- Remaining margin after referral: ~42% (still healthy)
- Compare to: Meta ads (Rs 500-2,000 per customer, one-time) vs referral (Rs 230/month for 12 months = Rs 2,760 total, but customer was acquired at zero upfront cost)

### Break-Even Analysis

- A referred customer at Rs 2,299/month with 55% gross margin generates Rs 1,264/month in gross profit
- After 10% referral payout (Rs 230), remaining gross profit: Rs 1,034/month
- After 12 months of referral payouts: Rs 2,760 total payout against Rs 15,168 gross profit (12 months)
- **Net profit per referred customer after referral cost: Rs 12,408 over 12 months**
- This is why the program is sustainable even at 15% for Ambassadors

---

## Implementation Phases

### Phase 1: Manual (Month 1-3, 0-50 Customers)

| Component | Implementation |
|-----------|----------------|
| Referral codes | Manually assigned, tracked in Google Sheet |
| Wallet balance | Google Sheet column, updated on 1st of month |
| Notifications | Founder sends WhatsApp messages manually using templates |
| Withdrawal | Founder transfers via UPI manually |
| Fraud detection | Founder reviews all referrals personally |
| Tier tracking | Google Sheet with conditional formatting |

**Tools needed:** Google Sheets, WhatsApp Business, UPI app.
**Time required:** 2-3 hours/month for reconciliation and notifications.

### Phase 2: Semi-Automated (Month 4-6, 50-150 Customers)

| Component | Implementation |
|-----------|----------------|
| Referral codes | Auto-generated at sign-up (Google Form + Sheet) |
| Wallet balance | Google Sheet with formulas, auto-calculated |
| Notifications | WhatsApp Business API with template messages (or Twilio) |
| Withdrawal | Semi-automated — batch UPI transfers weekly |
| Fraud detection | Automated flags in Sheet (address matching, timing) |
| Tier tracking | Auto-calculated from referral count |

**Tools needed:** Google Sheets (advanced), WhatsApp Business API, Twilio (optional).
**Time required:** 1-2 hours/month.

### Phase 3: Automated (Month 7+, 150+ Customers)

| Component | Implementation |
|-----------|----------------|
| Referral codes | Auto-generated, unique URL per customer |
| Wallet balance | Web page: somadelights.in/wallet |
| Notifications | Automated WhatsApp messages via API |
| Withdrawal | Automated UPI via payment gateway (Razorpay/Cashfree) |
| Fraud detection | Rule-based automated flagging + manual review queue |
| Tier tracking | Fully automated with real-time updates |

**Tools needed:** Simple web app (or Airtable/Retool), payment gateway, WhatsApp API.
**Time required:** 30 minutes/month (exception handling only).
