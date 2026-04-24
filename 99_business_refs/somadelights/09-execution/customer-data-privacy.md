# Customer Data Privacy & Handling Policy

> Soma Delights — Practical Data Governance for Early-Stage Food Startup
> Effective: March 2026
> Jurisdiction: India (DPDP Act 2023)
> Stage: Bootstrap (home kitchen, < 100 subscribers)

---

## 1. Philosophy

We collect the minimum data needed to deliver juice and build wellness habits. We never sell, share, or monetize customer data. Customer trust is our core asset — a data breach or privacy violation would destroy more value than any marketing campaign could build.

**Three Principles:**
1. **Collect only what you need** — if you cannot explain why you need a data point, do not collect it
2. **Protect what you collect** — reasonable security measures appropriate to our stage
3. **Delete when asked** — customers own their data, not us

---

## 2. Data Inventory — What We Collect and Why

### 2.1 Customer Profile Data

| Data Point | Why We Need It | Where Stored | Sensitivity | Retention |
|-----------|---------------|-------------|-------------|-----------|
| Full name | Delivery identification, personalization, booklet addressing | Google Sheets → CRM | Low | Until deletion request or 12 months after last order |
| Phone number (WhatsApp) | Order communication, delivery coordination, wellness tips, support | Google Sheets → CRM | Medium | Until deletion request or 12 months after last order |
| Delivery address | Physical delivery routing | Google Sheets → CRM | Medium | Until deletion request or 12 months after last order |
| Apartment/society name | Route optimization, gate access instructions | Google Sheets → CRM | Low | Until deletion request or 12 months after last order |
| Email address (optional) | Invoicing, receipts, account communication | Google Sheets → CRM | Low | Until deletion request or 12 months after last order |

### 2.2 Subscription & Order Data

| Data Point | Why We Need It | Where Stored | Sensitivity | Retention |
|-----------|---------------|-------------|-------------|-----------|
| Subscription plan | Production planning, billing | Google Sheets → CRM | Low | Indefinite (anonymized after account deletion) |
| Start date | Subscription tracking, booklet progression | Google Sheets → CRM | Low | Indefinite (anonymized) |
| Order history | Quality tracking, preference learning, dispute resolution | Google Sheets → CRM | Low | Indefinite (anonymized) |
| Delivery preferences | Timing, placement, special instructions | Google Sheets → CRM | Low | Until deletion request |
| Pause/skip requests | Subscription management | Google Sheets → CRM | Low | Until deletion request |

### 2.3 Health & Preference Data

| Data Point | Why We Need It | Where Stored | Sensitivity | Retention |
|-----------|---------------|-------------|-------------|-----------|
| Allergies/intolerances | SAFETY — prevent allergic reactions | Google Sheets → CRM, flagged prominently | **High** | Until deletion request (critical for safety) |
| Taste preferences | Product customization (sweeter/less sweet, spice tolerance) | Google Sheets → CRM | Low | Until deletion request |
| Health goals (optional) | Personalized recommendations, booklet content relevance | Google Sheets → CRM | Medium | Until deletion request |
| Dietary restrictions (vegan, etc.) | Product suitability | Google Sheets → CRM | Low | Until deletion request |

### 2.4 Payment Data

| Data Point | Why We Need It | Where Stored | Sensitivity | Retention |
|-----------|---------------|-------------|-------------|-----------|
| Payment method | Billing | **Razorpay only** — we NEVER store payment details | **Critical** | We do not store — Razorpay handles per PCI-DSS |
| Transaction records | Accounting, dispute resolution | Razorpay dashboard + our accounting sheet (amount only, no card details) | Medium | As required by tax law (typically 7 years for financial records) |
| UPI ID (if provided) | Refund processing | Google Sheets (temporary) | Medium | Delete after refund processed |

### 2.5 Referral Data

| Data Point | Why We Need It | Where Stored | Sensitivity | Retention |
|-----------|---------------|-------------|-------------|-----------|
| Referrer-referee relationship | Commission tracking | Google Sheets → CRM | Low | Duration of referral program + 12 months |
| Referral code | Attribution | Google Sheets → CRM | Low | Until deletion request |
| Commission earned | Payment to referrers | Google Sheets → accounting | Low | As required by tax law |

### 2.6 Communication Data

| Data Point | Why We Need It | Where Stored | Sensitivity | Retention |
|-----------|---------------|-------------|-------------|-----------|
| WhatsApp chat history | Support reference, feedback tracking | WhatsApp Business app (on device) | Medium | Auto-delete chats older than 6 months |
| Feedback/complaints | Quality improvement | Google Sheets → CRM | Low | Indefinite (anonymized if account deleted) |
| Opt-in/opt-out status | Communication compliance | Google Sheets → CRM | Low | Indefinite (legal record of consent) |

---

## 3. India DPDP Act 2023 — What It Means for Us

### 3.1 Overview

The Digital Personal Data Protection Act, 2023 (DPDP Act) is India's primary data protection legislation. Key provisions relevant to a small food startup:

**Scope:** Applies to processing of digital personal data collected within India or related to offering goods/services in India. This includes us — our Google Sheets, WhatsApp communication, and any digital records of customer data.

**Key Terms:**
- **Data Principal:** The customer (the person whose data it is)
- **Data Fiduciary:** Soma Delights (the entity collecting and processing data)
- **Consent Manager:** Not required at our scale, but we must obtain valid consent
- **Data Processor:** Any third party processing data on our behalf (Razorpay, Google)

### 3.2 Our Obligations Under DPDP Act

| Obligation | What It Means for Us | Our Implementation |
|-----------|---------------------|-------------------|
| **Lawful purpose** | Only collect data for a clear, stated purpose | Each data point in Section 2 has a stated "Why" |
| **Consent** | Get clear consent before collecting data | Consent checkbox on sign-up form + WhatsApp opt-in message |
| **Notice** | Tell customers what data you collect and why | Privacy policy shared at sign-up |
| **Purpose limitation** | Don't use data for purposes beyond what was stated | Never use customer data for anything beyond delivery, communication, and program management |
| **Data minimization** | Don't collect more than needed | We only collect what's in Section 2 — no unnecessary demographics, income, etc. |
| **Accuracy** | Keep data accurate and up to date | Customers can update their info anytime via WhatsApp |
| **Storage limitation** | Don't keep data longer than needed | Retention periods defined in Section 2; deletion protocol in Section 7 |
| **Security safeguards** | Reasonable security measures | Defined in Section 5 |
| **Right to access** | Customer can ask what data we have on them | We provide within 72 hours via WhatsApp or email |
| **Right to correction** | Customer can ask us to fix incorrect data | We correct within 24 hours |
| **Right to erasure** | Customer can ask us to delete their data | We delete within 7 days (Section 7) |
| **Right to grievance redressal** | Customer can complain about data handling | Founder is the point of contact (at our scale) |
| **Breach notification** | Must notify Data Protection Board of India in case of breach | Defined in Section 6 |

### 3.3 Consent Collection — How We Get It

**At Subscription Sign-Up (Google Form or WhatsApp):**

Include this consent statement (plain language):

> **Data Consent — Soma Delights**
>
> By subscribing to Soma Delights, you agree that we may collect and use the following information:
>
> - Your name, phone number, and delivery address — to deliver your subscription and communicate with you
> - Your health preferences and allergies — to ensure product safety and personalization
> - Your order history — to improve our service and personalize recommendations
> - Your referral relationships — to manage the referral program
>
> We will NOT:
> - Sell or share your personal data with anyone
> - Use your data for advertising or marketing to third parties
> - Store your payment card details (Razorpay handles all payments securely)
>
> You can ask us to show, correct, or delete your data at any time by messaging us on WhatsApp.
>
> [ ] I agree to the above data collection and use
>
> Full privacy policy: [link]

**For WhatsApp Communication Opt-In:**

First message after subscription:

> Hi [Name]! Welcome to Soma Delights. I'll send you:
> - Delivery updates (when your juice is on the way)
> - Weekly wellness tips and ingredient stories
> - Occasional product updates
>
> Reply YES to confirm, or reply STOP anytime to unsubscribe from tips (you'll still get delivery updates).

Record the YES response with timestamp as consent evidence.

---

## 4. Data Flow Map

### 4.1 Bootstrap Stage (Current — Google Sheets + WhatsApp)

```
Customer signs up (Google Form / WhatsApp)
        |
        v
Google Sheets "Master Customer List"
  - Name, phone, address, plan, start date
  - Allergies/preferences tab
  - Order history tab
  - Referral tracking tab
        |
        +---> WhatsApp Business (communication)
        |       - Delivery updates
        |       - Wellness tips
        |       - Support
        |
        +---> Daily Production Sheet
        |       - What to make, quantities
        |       - No personal data (just order counts by SKU)
        |
        +---> Delivery Route Sheet
        |       - Name, address, order details
        |       - Shared with delivery rider (if not founder)
        |       - Rider copy destroyed after delivery
        |
        +---> Razorpay
                - Payment processing
                - We send: customer email/phone for receipt
                - Razorpay stores: payment details (we never see card numbers)
```

### 4.2 Growth Stage (Future — CRM Migration)

```
Customer signs up (web form / WhatsApp)
        |
        v
CRM System (India-hosted or compliant)
  - All customer data migrated from Sheets
  - Automated consent tracking
  - Audit log of data access
        |
        +---> WhatsApp Business API (automated)
        +---> Delivery Management System
        +---> Razorpay (payment)
        +---> Accounting Software (anonymized transactions)
```

**CRM Selection Criteria (for future):**
- India-hosted servers or DPDP-compliant international provider
- Data export capability (no vendor lock-in)
- Audit logging (who accessed what data, when)
- Role-based access control
- Data deletion capability
- WhatsApp integration
- Affordable for small business (< Rs 5,000/month)

Candidates to evaluate: Zoho CRM (India-based), Freshsales (India-based), HubSpot (international but compliant).

---

## 5. Security Measures

### 5.1 Google Sheets Security (Bootstrap Stage)

| Measure | Implementation | Status |
|---------|---------------|--------|
| Google account 2FA | Enabled on all Google accounts with access | Required |
| Sheet sharing | Share only with specific email addresses, never "anyone with link" | Required |
| Access audit | Monthly review of who has access to the Master sheet | Monthly |
| Strong password | 16+ character unique password for Google account | Required |
| Device security | Screen lock on phone and laptop, auto-lock after 2 minutes | Required |
| No public Wi-Fi | Never access customer data on unsecured public Wi-Fi | Required |
| Backup | Weekly download of Sheets as CSV to encrypted local folder | Weekly |

**Access Control Matrix:**

| Person | Master Sheet | Production Sheet | Route Sheet | Payment Dashboard |
|--------|-------------|-----------------|-------------|-------------------|
| Founder (Sri) | Full access | Full access | Full access | Full access |
| Delivery rider | No access | No access | Read-only (daily, specific route) | No access |
| Future: Kitchen assistant | No access | Read-only | No access | No access |
| Future: CRM admin | Full access | Full access | Full access | View-only |

### 5.2 WhatsApp Security

| Measure | Implementation |
|---------|---------------|
| WhatsApp Business account | Use Business app, not personal WhatsApp |
| 2FA on WhatsApp | Enabled (six-digit PIN) |
| Auto-download off | Disable automatic media download (prevents accidental data on device) |
| Chat backup encryption | Enable end-to-end encrypted backup |
| No customer data in group chats | Never share customer info in any group |
| Device not shared | Phone with WhatsApp Business not used by others |

### 5.3 Physical Security

| Measure | Implementation |
|---------|---------------|
| Printed route sheets | Destroy after delivery (tear up, do not recycle visibly) |
| Rider's phone | Route info shared via temporary Google Maps link, not permanent list |
| Kitchen visitors | No access to any data — laptop/phone locked when visitors present |
| Home network | WPA3 or WPA2 encryption, strong password, no guest access to main network |

### 5.4 Payment Security

- **NEVER** store credit card numbers, CVV, or full UPI details
- **NEVER** ask customers to share payment details via WhatsApp
- **ALWAYS** use Razorpay payment links for transactions
- Keep Razorpay dashboard access limited to founder only
- Enable Razorpay 2FA
- Monthly reconciliation: verify transactions match orders

---

## 6. Data Breach Response Plan

### 6.1 What Constitutes a Breach

- Unauthorized access to customer data (Google Sheet shared accidentally, phone stolen)
- Customer data sent to wrong person (delivery details to wrong rider, email to wrong customer)
- Google account compromised
- WhatsApp account hijacked
- Laptop/phone stolen with customer data accessible
- Any third party accessing customer information without authorization

### 6.2 Immediate Response (Within 1 Hour)

1. **Contain:** Revoke access immediately
   - Google: change password, revoke shared access, sign out all sessions
   - WhatsApp: if hijacked, contact WhatsApp support for account recovery
   - Device stolen: remote wipe via Google Find My Device / Apple Find My
2. **Assess:** Determine what data was exposed
   - Which customers affected?
   - What data was accessible?
   - How long was the exposure?
3. **Document:** Record the incident
   - What happened
   - When discovered
   - What data affected
   - Immediate actions taken

### 6.3 Notification (Within 72 Hours)

**Notify affected customers:**

> Hi [Name], this is Sri from Soma Delights. I want to be transparent with you about a data incident.
>
> [Brief, honest description of what happened]
>
> What data may have been affected: [specific data points]
>
> What we've done: [containment steps taken]
>
> What you should do: [any recommended actions — e.g., be cautious of unknown contacts if phone number was exposed]
>
> I take your privacy seriously and I'm sorry this happened. If you have any questions or concerns, please message me directly.

**Notify DPBI (Data Protection Board of India):**
- Required under DPDP Act for significant breaches
- Notification format and mechanism TBD (DPBI still establishing processes as of 2026)
- Keep records of the breach and notification for 3 years

### 6.4 Post-Breach Actions

- [ ] Root cause analysis — how did this happen?
- [ ] Fix the vulnerability
- [ ] Review all security measures (Section 5)
- [ ] Consider whether additional measures are needed
- [ ] Update this document with lessons learned
- [ ] If breach was due to a process gap, add new process

---

## 7. Data Deletion Protocol

### 7.1 Customer-Requested Deletion

**Trigger:** Customer messages "Please delete my data" or any equivalent request.

**Process:**

| Step | Action | Timeline | Responsible |
|------|--------|----------|-------------|
| 1 | Acknowledge request | Within 24 hours | Founder |
| 2 | Verify identity (customer must message from registered WhatsApp number) | Same day | Founder |
| 3 | Delete from Master Google Sheet (all tabs) | Within 7 days | Founder |
| 4 | Delete from any downloaded/offline copies | Within 7 days | Founder |
| 5 | Delete WhatsApp chat history with that customer | Within 7 days | Founder |
| 6 | Notify Razorpay to delete customer record (if applicable) | Within 7 days | Founder |
| 7 | Retain anonymized order data (order count, SKUs, revenue — no name, phone, address) | Permanent | Founder |
| 8 | Confirm deletion to customer | Within 7 days | Founder |

**Confirmation message:**

> Hi [Name], your data has been deleted from all our records as requested. We've kept only anonymized order statistics (no personal information) for our business records. If you ever want to re-subscribe in the future, you're always welcome. Thank you for being a Soma customer.

**Exceptions to deletion:**
- Financial transaction records: retained as required by Indian tax law (typically 7 years) — but these contain only amounts and dates, not delivery addresses or health preferences
- Allergy information: if there is any possibility of future orders (e.g., customer paused but may return), we ask permission to retain allergy data for their safety. If they insist on full deletion, we delete and note that allergy re-collection will be required if they resubscribe.

### 7.2 Automatic Data Cleanup

| Trigger | Action |
|---------|--------|
| Customer inactive for 12+ months (no orders, no communication) | Send "should we keep your data?" WhatsApp message. If no response in 30 days, delete personal data, retain anonymized order data |
| Delivery rider ends engagement | Delete all route sheets, revoke all access within 24 hours |
| Google Sheets → CRM migration | Verify data transferred correctly, then delete Google Sheets customer data (keep Sheets as empty template) |

### 7.3 Rider Data Handling

When someone other than the founder handles delivery:

- Rider receives daily route sheet (name + address + order only — no phone, no preferences, no allergy details)
- Route sheet is a temporary Google Maps shared route OR a printed sheet
- Printed sheets are collected and destroyed after each delivery run
- Rider does NOT save customer phone numbers in personal contacts
- Rider does NOT contact customers directly — all communication through founder
- If rider calls customer (e.g., gate is locked), use the business WhatsApp number, not personal number
- When rider stops working with Soma: verify no customer data remains on their device

---

## 8. WhatsApp Communication Rules

### 8.1 Message Categories and Rules

| Category | Content | Frequency | Opt-Out? |
|----------|---------|-----------|----------|
| **Delivery updates** | "Your juice is on its way" / "Delivered at door" | Daily (operational) | No — required for service |
| **Order changes** | Pause confirmation, plan change, billing | As needed (operational) | No — required for service |
| **Wellness tips** | Ingredient facts, health tips, habit reminders | 2-3 per week (promotional) | Yes — reply STOP |
| **Product updates** | New flavors, seasonal specials, menu changes | 1-2 per month (promotional) | Yes — reply STOP |
| **Referral program** | Updates on referral earnings, program details | Monthly (promotional) | Yes — reply STOP |
| **Feedback requests** | "How was today's juice?" satisfaction checks | Weekly (operational) | Yes — reply STOP |

### 8.2 Communication Standards

**Always:**
- Use WhatsApp Business app (not personal)
- Use broadcast lists for promotional messages (each recipient sees it as an individual message)
- Include opt-out instruction in every promotional message: "Reply STOP to unsubscribe from tips"
- Respect opt-out immediately — remove from broadcast list within 24 hours
- Send during reasonable hours only (7 AM - 9 PM)
- Keep messages concise and valuable (no spam, no filler)
- Sign messages with name ("- Sri" or "- Soma Delights")

**Never:**
- Add customers to WhatsApp groups without explicit permission
- Share customer phone numbers with anyone (other customers, vendors, partners)
- Send more than 1 promotional message per day
- Send messages before 7 AM or after 9 PM (except delivery notifications)
- Forward customer messages or screenshots to others
- Use customer data for messages unrelated to Soma Delights

### 8.3 Opt-Out Management

When a customer replies STOP:

1. Acknowledge immediately: "Got it, [Name]. You won't receive tips/promotional messages from us anymore. You'll still get delivery updates for your subscription. Reply START anytime if you'd like to receive tips again."
2. Remove from all broadcast lists within 24 hours
3. Mark in Google Sheet/CRM: "Opted out of promotional messages — [date]"
4. Continue sending operational messages (delivery updates, billing) only
5. Never re-add to promotional lists without explicit re-opt-in

---

## 9. Third-Party Data Sharing

### 9.1 Current Third Parties

| Third Party | What Data They Receive | Why | Their Privacy Policy |
|------------|----------------------|-----|---------------------|
| **Google (Sheets, Forms)** | All data stored in Sheets | Data storage platform | [Google Privacy Policy](https://policies.google.com/privacy) — DPDP adequate |
| **Razorpay** | Customer phone/email (for receipts), payment details | Payment processing | [Razorpay Privacy](https://razorpay.com/privacy/) — PCI-DSS compliant |
| **WhatsApp (Meta)** | Phone numbers, message content | Communication | [WhatsApp Privacy](https://www.whatsapp.com/legal/privacy-policy) — end-to-end encrypted |
| **Delivery rider** | Name + address (daily, temporary) | Physical delivery | No formal policy — governed by our rider agreement |

### 9.2 Data Sharing Rules

- **We NEVER sell customer data** — not to advertisers, not to partners, not to anyone
- **We NEVER share customer lists** — no other business gets our subscriber list
- **Delivery data is temporary** — rider sees only what they need for today's route, nothing more
- **Aggregated/anonymized data may be shared** — e.g., "we serve 50 households in Kukatpally" in a pitch deck is fine (no personal identifiers)
- **If a future vendor or tool needs customer data** (e.g., CRM, email tool): evaluate their privacy policy, ensure DPDP compliance, and inform customers of the change

---

## 10. Privacy Policy (Plain Language Version)

> This policy is written for customers. Keep it on the website and share it at sign-up.

---

### SOMA DELIGHTS — PRIVACY POLICY

**Last updated: March 2026**

Hello! This policy explains how Soma Delights ("we", "us") handles your personal information. We wrote it in plain language because we believe privacy policies should be understood, not just agreed to.

**Who are we?**

Soma Delights is a micro-wellness brand based in Kukatpally, Hyderabad. We make and deliver cold-pressed juices and wellness products. We are a sole proprietorship operated by [Founder Name].

**What information do we collect?**

When you subscribe to Soma Delights, we collect:
- Your name (so we know who you are and can personalize your experience)
- Your phone number / WhatsApp (so we can communicate about deliveries and share wellness content)
- Your delivery address (so we can deliver your juice)
- Your allergy and dietary information (so we can keep you safe)
- Your taste preferences (so we can recommend the right products)
- Your order history (so we can improve our service)
- Your referral relationships (so we can manage the referral program)

We do NOT collect: your income, your Aadhaar number, your date of birth, or anything else that is not directly needed for our service.

**How do we use your information?**

- To deliver your juice to the right place at the right time
- To communicate with you about your subscription (delivery updates, billing, support)
- To send you wellness tips and ingredient information (if you've opted in)
- To manage the referral program (tracking referrals and commissions)
- To improve our products based on feedback and order patterns
- To keep you safe (allergy management)

We do NOT use your information for advertising. We do NOT show you targeted ads. We do NOT sell your information.

**Who do we share your information with?**

- **Razorpay** (our payment processor) — they handle your payment securely. We never see or store your card details.
- **Our delivery person** — they see your name and address for delivery purposes only. They do not keep this information.
- **Nobody else.** We do not share, sell, or rent your personal information to any other company, person, or organization.

**How do we protect your information?**

- Your data is stored in secured, password-protected systems with two-factor authentication
- Only authorized personnel (currently just the founder) can access customer data
- Delivery route sheets are destroyed after each delivery
- We follow reasonable security practices appropriate to the sensitivity of your data

We are a small business. We do not have a 500-person security team. But we take your data seriously, keep it minimal, and protect it with the tools available to us.

**What are your rights?**

Under the Digital Personal Data Protection Act, 2023, you have the right to:

- **Access:** Ask us what data we have about you. We will tell you within 72 hours.
- **Correction:** Ask us to fix any incorrect information. We will fix it within 24 hours.
- **Deletion:** Ask us to delete your data. We will delete it within 7 days. (We may keep anonymized order statistics and financial records required by tax law.)
- **Withdraw consent:** Stop receiving promotional messages anytime by replying STOP on WhatsApp. Cancel your subscription anytime.
- **Complain:** If you are unhappy with how we handle your data, contact us directly. If we cannot resolve your concern, you may contact the Data Protection Board of India.

**How long do we keep your information?**

- While you are an active subscriber: we keep all your information to provide the service.
- If you cancel: we keep your information for 12 months in case you want to resubscribe. After 12 months of inactivity, we delete personal data and keep only anonymized records.
- If you ask us to delete: we delete within 7 days (see exceptions above).
- Financial records: retained as required by Indian tax law.

**Children's data**

We do not knowingly collect personal data from anyone under 18. If a minor's data has been provided to us, a parent or guardian may contact us to request deletion.

**Changes to this policy**

If we make significant changes to this policy, we will notify you via WhatsApp before the changes take effect. Minor wording changes will be updated on our website without individual notification.

**Contact us**

For any privacy questions, requests, or concerns:
- WhatsApp: [Business Number]
- Email: [Email Address]
- In person: talk to Sri during your morning delivery

---

*End of Privacy Policy*

---

## 11. Compliance Checklist

### Before Launch

- [ ] Privacy policy written and accessible (website or shareable link)
- [ ] Consent statement added to sign-up form
- [ ] WhatsApp opt-in message drafted and ready
- [ ] Google Sheets secured (2FA, limited access, strong passwords)
- [ ] Razorpay account configured (2FA enabled)
- [ ] WhatsApp Business account set up (not personal)
- [ ] Delivery rider data handling agreement prepared (if applicable)
- [ ] Data deletion process documented and tested

### Monthly Review

- [ ] Audit who has access to Google Sheets (revoke stale access)
- [ ] Review opt-out requests — are they all honored?
- [ ] Check for any customer data stored outside approved locations (personal phone notes, paper lists, etc.)
- [ ] Verify delivery route sheets are being destroyed
- [ ] Review any new data collection — is it in the inventory (Section 2)?

### Quarterly Review

- [ ] Full read-through of this document — still accurate?
- [ ] Check for updates to DPDP Act enforcement or guidelines
- [ ] Review third-party tools — any new ones handling customer data?
- [ ] Test data deletion process (can we actually delete a record completely?)
- [ ] Review WhatsApp communication frequency — are we within our stated limits?

### When Scaling (50+ Subscribers)

- [ ] Evaluate CRM migration (Google Sheets becomes unwieldy beyond ~100 customers)
- [ ] Consider formal data processing agreement with delivery staff
- [ ] Evaluate need for dedicated data protection officer (likely not until 500+ customers)
- [ ] Review if any data processing qualifies as "significant" under DPDP Act thresholds
- [ ] Consider cyber insurance (affordable policies available for small businesses)

---

## 12. Incident Log

Maintain a running log of any data-related incidents, no matter how small.

| Date | Incident | Data Affected | Action Taken | Customers Notified? | Resolution |
|------|----------|--------------|-------------|-------------------|------------|
| — | No incidents to date | — | — | — | — |

*Update this table immediately when any incident occurs. Even minor incidents (e.g., "accidentally sent delivery update to wrong number, corrected within 5 minutes") should be logged.*

---

## 13. Template Messages

### 13.1 Data Access Request Response

> Hi [Name], thanks for asking about your data. Here's what we have on file for you:
>
> - Name: [Name]
> - Phone: [Phone]
> - Address: [Address]
> - Plan: [Plan details]
> - Subscribed since: [Date]
> - Preferences: [Listed preferences]
> - Allergies on file: [Listed allergies or "None recorded"]
> - Referral status: [Active/None]
>
> If anything is incorrect, let me know and I'll update it right away. If you'd like any of this deleted, just say the word.
>
> — Sri, Soma Delights

### 13.2 Data Correction Confirmation

> Done, [Name]. I've updated your [field] to [new value]. Let me know if anything else needs fixing. — Sri

### 13.3 Data Deletion Confirmation

> Hi [Name], your personal data has been deleted from all our records as requested. We've retained only anonymized order statistics (no personal identifiers) as required for business accounting. If you ever want to resubscribe, you're always welcome — we'd just need your details fresh. Thank you for being part of Soma. — Sri

### 13.4 Breach Notification (Template — Adapt to Situation)

> Hi [Name], this is Sri from Soma Delights. I want to be upfront with you about something.
>
> On [date], [brief description of what happened]. This may have affected [specific data — e.g., "your name and delivery address"].
>
> What I've done about it: [actions taken — e.g., "changed all passwords, revoked access, secured the system"].
>
> What you should know: [any recommended actions — or "No action needed from your end, but I wanted you to know"].
>
> I'm sorry this happened. Your trust matters more to me than anything else in this business. If you have any questions, please message me directly.
>
> — Sri

---

*This document should be reviewed quarterly and updated whenever data practices, tools, or regulations change.*
