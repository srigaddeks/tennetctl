# Notify Deployment Guide — SMTP providers, DKIM, SPF, DMARC

TennetCTL is SMTP-provider agnostic. These are the practical steps to actually land in inboxes.

## Picking an SMTP provider

| Provider | Good for | Notes |
|---|---|---|
| **Postmark** | Transactional (magic links, password resets, receipts) | Very high inbox placement; low tolerance for marketing content. |
| **SendGrid** | Mixed transactional + marketing | Dedicated IPs available; careful with reputation on shared. |
| **Mailgun** | Developer-first, EU region available | Good suppression management out of the box. |
| **Amazon SES** | Cheapest at scale; VPC-native | Requires production-access approval; cold start on reputation. |
| **Resend** | Very simple API; new but growing | Limits per domain tier. |

Pick one; the config surface in TennetCTL is identical across them.

## SMTP config fields

From the Notify Settings page (or `POST /v1/notify/smtp-configs`):

- **Host / Port** — `smtp.sendgrid.net / 587`, `smtp.postmarkapp.com / 587`, `smtp.mailgun.org / 587`, `email-smtp.us-east-1.amazonaws.com / 587`.
- **TLS** — on for all modern providers (STARTTLS on 587).
- **Username** — usually an **API key** or a generic literal like `apikey` (SendGrid). **Not** the From address.
- **Vault auth key** — the vault secret key that stores the password / API key. E.g. `notify.smtp.primary.password`. Create the secret first via Vault → Secrets.
- **From email** — the mailbox that appears in the From header. **Must** be on a domain you own and have configured SPF/DKIM for.
- **From name** — display string. Optional but recommended.

## DNS for deliverability

To land in Gmail/Yahoo/Outlook without the spam folder, configure three DNS records on the domain you send from. Your provider's docs show the exact values — this is the lay-of-the-land:

### SPF

```
yourdomain.com.  TXT  "v=spf1 include:sendgrid.net ~all"
```

(Or `include:spf.mtasv.net` for Postmark, `include:mailgun.org` for Mailgun, etc.)

**One** SPF record per domain. If you have multiple senders, combine them into one record:

```
v=spf1 include:sendgrid.net include:mailgun.org ~all
```

### DKIM

Provider-specific — they give you one or two CNAME (or TXT) records to add, e.g.:

```
s1._domainkey.yourdomain.com  CNAME  s1.domainkey.u1234.wl.sendgrid.net.
s2._domainkey.yourdomain.com  CNAME  s2.domainkey.u1234.wl.sendgrid.net.
```

Without DKIM your mail gets flagged as unauthenticated — Gmail and Yahoo **require** it for any bulk volume since 2024.

### DMARC

```
_dmarc.yourdomain.com.  TXT  "v=DMARC1; p=none; rua=mailto:dmarc@yourdomain.com"
```

Start with `p=none` to observe — you'll get weekly reports. After a few weeks with 95%+ DKIM + SPF alignment, move to `p=quarantine` then `p=reject`.

### Verification

```
dig TXT yourdomain.com | grep spf
dig TXT _dmarc.yourdomain.com
dig CNAME s1._domainkey.yourdomain.com
```

Use [mail-tester.com](https://www.mail-tester.com/) or [mxtoolbox.com](https://mxtoolbox.com/SuperTool.aspx) to verify before going live.

## Custom tracking domain (optional)

pytracking URLs today point at your TennetCTL host (`https://your-tenant.example/v1/notify/email/track/o/...`). For marketing-volume sends it's worth serving tracking URLs off your own branded domain (e.g., `t.yourdomain.com`). That requires:

1. A CNAME for `t.yourdomain.com` → your TennetCTL host.
2. TLS cert on that hostname.
3. Setting `base_tracking_url` to `https://t.yourdomain.com` in your TennetCTL env.

Not yet exposed in the UI — land it as a per-org config in a later plan.

## Suppression list maintenance

Bounces auto-populate `17_fct_notify_suppressions`. Manually suppress an address via the API:

```bash
curl -X POST http://host:51734/v1/notify/suppressions \
  -H "Cookie: tennetctl_session=..." \
  -d '{"org_id": "019d...", "email": "x@example.com", "reason_code": "manual", "notes": "user requested"}'
```

Never rely on the user unsubscribing — monitor your suppression list and clean up false positives. Compliant senders keep bounce rates under 2% and complaint rates under 0.1%.

## Webhook setup

Point your provider's bounce webhook at:

```
POST https://your-host:51734/v1/notify/email/webhooks/bounce
```

Body: `{"delivery_id": "<delivery_id>", "reason": "<reason>"}`. You'll likely need a thin adapter between your provider's webhook format and this shape — until per-provider adapters ship, keep the adapter in your app or an API gateway.

Set the delivery_id by embedding it in the `X-Delivery-Id` SMTP header or Message-ID when sending. pytracking already puts delivery_id in the open/click tokens — for bounces you embed it yourself.

## Environment checklist before going live

- [ ] DNS: SPF, DKIM, DMARC set for sending domain — verified in `dig`.
- [ ] DMARC record includes a `rua=` email address that you actually read.
- [ ] Vault holds the SMTP password; never in env vars or code.
- [ ] SMTP config's `from_email` is on the same domain as DKIM.
- [ ] At least one test-send lands in Gmail's Inbox (not Promotions/Spam).
- [ ] Bounce webhook URL registered with the provider.
- [ ] Suppression list reviewed weekly.
- [ ] Critical alerts use the `critical` category (always-delivered, user cannot opt out).
- [ ] Transactional/marketing distinction reflected in template groups.
- [ ] `List-Unsubscribe` working — click the link in a delivered email and verify suppression adds a row.
