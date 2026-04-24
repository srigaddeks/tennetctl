# Soma Delights Print Marketing System

> Version 1.0 | Last Updated: 2026-03-23
> Status: Planning / Specification
> Companion: [design-system.md](./design-system.md) for all visual specifications

---

## Table of Contents

1. [Print Philosophy](#1-print-philosophy)
2. [Master Template System](#2-master-template-system)
3. [Template Specifications](#3-template-specifications)
4. [Content Calendar](#4-content-calendar)
5. [Reusability Matrix](#5-reusability-matrix)
6. [Print Production Workflow](#6-print-production-workflow)
7. [Photography Shot List](#7-photography-shot-list)
8. [Design File Organization](#8-design-file-organization)
9. [Cost Analysis](#9-cost-analysis)
10. [Vendor Requirements](#10-vendor-requirements)
11. [Quality Control](#11-quality-control)

---

## 1. Print Philosophy

### Why Print Matters for Soma Delights

In a world of disposable digital content, a beautifully printed piece of educational material
is a physical artifact of trust. When someone holds a 300 GSM matte-laminated booklet about
gut health — one that teaches them something they did not know — they do not throw it away.
They keep it on their kitchen counter, on their desk, in their bag. It becomes a reference.
It starts conversations.

This is Soma Delights' marketing strategy: replace advertising spend with educational print
materials that people want to keep and share.

### Core Principles

**Every printed piece teaches something.**
If a print piece does not educate, it does not get printed. The subscriber or reader should
learn something valuable from every item — an ingredient fact, a health tip, a morning routine
suggestion. Product promotion is secondary and confined to a maximum of 15% of any printed
piece.

**High GSM is non-negotiable.**
Cheap paper communicates cheap product. Every Soma print item uses minimum 170 GSM inner stock
and 250+ GSM for standalone cards. The tactile quality — the weight, the matte texture, the
thickness — is part of the brand experience. When someone holds a Soma booklet, it should feel
noticeably different from a flyer or pamphlet.

**Matte only. Never glossy.**
Matte finishes communicate: premium, understated, serious, keepable. Glossy finishes
communicate: promotional, disposable, loud. All Soma print materials use matte paper stock
and soft-touch matte lamination for covers and cards. No exceptions.

**Greyscale design. Product photography is the only color.**
Same principle as web and digital: the entire print piece is designed in the warm greyscale
palette. The only color that appears is in product photography and ingredient photography. This
makes the drinks pop off the page and reinforces the design system consistently across every
touchpoint.

**Reusable templates over custom one-offs.**
Every print piece is built from a template. Content changes monthly or quarterly; the layout
stays the same. This reduces design cost, maintains brand consistency, speeds up production,
and allows non-designers to prepare content for new editions.

---

## 2. Master Template System

### Template Overview

| Template | Name                       | Size          | Pages | Paper            | Primary Use          |
|----------|----------------------------|---------------|-------|------------------|----------------------|
| A        | Wellness Booklet           | A5 (148x210mm)| 12-24 | 300/170 GSM      | Flagship monthly/quarterly |
| B        | Ingredient Deep-Dive Card  | A6 (105x148mm)| 2     | 300 GSM          | Collectible series   |
| C        | Health Tips Poster         | A4 (210x297mm)| 2     | 170 GSM          | Noticeboard, insert  |
| D        | Do's & Don'ts Quick Guide  | DL (99x210mm) | 2     | 250 GSM          | Delivery insert, pocket |
| E        | Starter Kit Insert         | A5 folded to A6| 4    | 250 GSM          | Welcome material     |
| F        | Business Card              | 90x55mm       | 2     | 400 GSM          | Networking, kiosks   |
| G        | Sticker / Label            | Various       | 1     | Matte vinyl      | Bottles, packaging   |

Each template is designed once in Figma or Adobe InDesign, with defined content zones that get
swapped for each edition or variant. The layout, typography, grid, and brand elements remain
fixed.

---

## 3. Template Specifications

### 3.1 Template A: Wellness Booklet (Flagship)

The flagship print piece. A mini-magazine about wellness that happens to come from a
cold-pressed juice brand. The content is educational; the product presence is subtle.

**Physical Specifications:**

| Property         | Monthly Edition    | Quarterly Edition    |
|------------------|--------------------|----------------------|
| Size             | A5 (148 x 210mm)  | A5 (148 x 210mm)    |
| Pages            | 12-16              | 20-24                |
| Cover stock      | 300 GSM art card   | 300 GSM art card     |
| Cover finish     | Soft-touch matte lamination (both sides) | Soft-touch matte lamination (both sides) |
| Inner stock      | 170 GSM matte art paper | 170 GSM matte art paper |
| Inner finish     | Uncoated (natural matte) | Uncoated (natural matte) |
| Binding          | Saddle-stitched (2 staples) | Perfect bound (glued spine) |
| Spine width      | N/A                | 2-3mm                |
| Bleed            | 3mm all sides      | 3mm all sides        |
| Color mode       | CMYK               | CMYK                 |
| Resolution       | 300 DPI minimum    | 300 DPI minimum      |

**Page Template Structure (12-page Monthly Edition):**

```
Page 1 (Cover):
  - Soma Delights logo (top center, small, near-black)
  - Edition title (e.g., "Morning Wellness") — near-black, large
  - Edition number + date (e.g., "Edition 03 | March 2027") — warm-grey-500
  - Single product or ingredient image — the only color on the cover
  - Minimal. Premium. Mostly white/off-white space.

Page 2 (Inside Front Cover — "This Edition"):
  - Brief welcome from the founder (3-4 sentences, serif accent font)
  - Table of contents for this edition
  - Grey line illustration relevant to the theme

Pages 3-4 (Feature Article):
  - Deep-dive educational article (800-1,000 words)
  - Topic: wellness, not product-related
  - Examples: "Why Your Morning Routine Matters More Than Your Diet"
             "The Gut-Brain Connection: What Science Actually Says"
             "Hydration Myths You Still Believe"
  - Large heading, body text in 2-column layout
  - One ingredient photo (color) as article illustration
  - Pull quote in serif accent font

Pages 5-6 (Ingredient Spotlight):
  - 2-3 ingredients featured with:
    - Ingredient name and botanical illustration (grey)
    - Key nutritional highlights
    - Health benefits (3-4 bullet points each)
    - "How we source it" — one sentence on sourcing
    - Ingredient photo (color) — the page's only color
  - Layout: one ingredient per column (2 columns) or one large + two small

Pages 7-8 (Do's & Don'ts):
  - Practical health tips in clean checklist format
  - Topic matches the edition theme
  - Layout: left column = Do's (grey checkmark icons), right column = Don'ts (grey X icons)
  - 6-8 items per column
  - Each item: 1-2 sentences
  - Bottom: "Learn more at soma-delights.com/wellness-tips"

Pages 9-10 (Seasonal / Timely Content):
  - "What's in Season" (seasonal ingredients, why to eat them now)
  - OR "Daily Routine" (a practical morning/evening routine suggestion)
  - OR "Recipe" (a simple wellness recipe using featured ingredients)
  - Flexible content zone — changes based on season and theme
  - One or two photos (ingredient shots — color)

Page 11 (Community + Products):
  - Top half: community spotlight
    - Subscriber streak celebrations ("Meera completed 60 days!")
    - Testimonial (1-2 sentences, anonymous or named with permission)
  - Bottom half: product showcase
    - The only overtly promotional section in the entire booklet
    - 2-3 product photos (color) with names and one-line benefits
    - "Order via WhatsApp" or "Add to your plan"

Page 12 (Back Cover):
  - QR code linking to soma-delights.com or specific landing page
  - WhatsApp number
  - Instagram handle
  - "Share this booklet with someone who cares about their health"
  - Referral prompt: "Give a friend a free week: soma-delights.com/free-week"
  - Next edition preview: "Next month: Gut Health Essentials"
  - Soma logo, small, bottom center

```

**24-page Quarterly Edition extends with:**
- Pages 3-6: two feature articles instead of one
- Pages 7-8: expanded ingredient spotlight (4-5 ingredients)
- Pages 9-10: "The Science Corner" — deeper scientific content
- Pages 11-12: seasonal guide with more detail
- Pages 13-14: interview or Q&A (nutritionist, customer, local farmer)
- Pages 15-16: recipe section with step-by-step
- Pages 17-18: community + milestones
- Pages 19-20: full product catalog with photos
- Pages 21-22: plans overview and pricing
- Pages 23-24: back matter (QR, social, next edition)

---

### 3.2 Template B: Ingredient Deep-Dive Card

A collectible series. Each card covers one ingredient in detail. Subscribers collect them;
they become a mini-encyclopedia of wellness ingredients. Designed to be kept, not discarded.

**Physical Specifications:**

| Property         | Value                              |
|------------------|------------------------------------|
| Size             | A6 (105 x 148mm)                  |
| Pages            | 2 (front and back)                 |
| Stock            | 300 GSM art card                   |
| Finish           | Matte lamination both sides        |
| Corners          | Rounded (3mm radius) — optional    |
| Bleed            | 3mm all sides                      |
| Color mode       | CMYK                               |

**Front Side Layout:**
- Top: ingredient photo (full color, takes up top 55% of card)
- Below photo: ingredient name — near-black, large heading
- Below name: "Did you know?" fact — 1-2 sentences in dark-grey
- Bottom: card number badge "Card #04 of 24" — warm-grey-500, small text
- Soma logo: bottom-right corner, very small, warm-grey-400

**Back Side Layout:**
- Heading: "3 Key Benefits" — near-black, subhead size
- Benefit 1: grey icon + benefit title + 1-sentence explanation
- Benefit 2: grey icon + benefit title + 1-sentence explanation
- Benefit 3: grey icon + benefit title + 1-sentence explanation
- Divider line (warm-grey-200)
- "Wellness Tip:" — 1-2 sentences on how to consume this ingredient optimally
- Bottom: QR code linking to the full ingredient page on the website
- Small text: "Learn more at soma-delights.com/ingredients/[name]"

**Series Plan (24 cards):**

| Card # | Ingredient   | Primary Benefit Theme     |
|--------|--------------|---------------------------|
| 01     | Spinach      | Iron & Energy             |
| 02     | Beetroot     | Blood Health & Stamina    |
| 03     | Turmeric     | Anti-Inflammation         |
| 04     | Ginger       | Digestion & Immunity      |
| 05     | Amla         | Vitamin C Powerhouse      |
| 06     | Cucumber     | Hydration & Cooling       |
| 07     | Apple        | Fiber & Gut Health        |
| 08     | Carrot       | Vision & Skin             |
| 09     | Lemon        | Alkalizing & Detox        |
| 10     | Mint         | Digestion & Freshness     |
| 11     | Celery       | Minerals & Hydration      |
| 12     | Wheatgrass   | Chlorophyll & Cleansing   |
| 13     | Coconut Water| Electrolytes & Recovery   |
| 14     | Aloe Vera    | Gut Lining & Healing      |
| 15     | Black Pepper | Absorption & Warmth       |
| 16     | Tulsi        | Stress & Immunity         |
| 17     | Curry Leaf   | Iron & Hair Health        |
| 18     | Coriander    | Detox & Digestion         |
| 19     | Pomegranate  | Antioxidants & Heart      |
| 20     | Watermelon   | Hydration & Lycopene      |
| 21     | Papaya       | Enzymes & Digestion       |
| 22     | Pineapple    | Bromelain & Inflammation  |
| 23     | Honey        | Antimicrobial & Energy    |
| 24     | Neem         | Purification & Skin       |

**Distribution:**
- 1 new card included with each daily delivery (rotating)
- Starter kit includes 3-4 cards for the products in the kit
- Full set of 24 available as a collector's pack at kiosk events
- Encourages engagement: "Collect all 24 — complete your wellness library"

---

### 3.3 Template C: Health Tips Poster / Insert

A single-sheet, double-sided print piece. Educational on the front, product/CTA on the back.
Used as apartment noticeboard flyers, delivery inserts, and kiosk handouts.

**Physical Specifications:**

| Property         | Value                              |
|------------------|------------------------------------|
| Size             | A4 (210 x 297mm)                  |
| Pages            | 2 (front and back)                 |
| Stock            | 170 GSM matte art paper            |
| Finish           | Uncoated (natural matte feel)      |
| Bleed            | 3mm all sides                      |
| Color mode       | CMYK                               |

**Front Side Layout:**
- Heading: educational topic title (e.g., "5 Morning Habits That Actually Work") — near-black,
  large, top-third of page
- Subheading: "A quick guide from Soma Delights" — warm-grey-500
- Content: 5-7 tips or facts, each with:
  - Number or grey icon
  - Tip title: near-black, bold
  - Tip explanation: 1-2 sentences, dark-grey
- One ingredient photo or product photo (bottom-third) — the only color on this side
- Layout: single column, generous spacing, easy to read from 1 meter (for noticeboard)

**Back Side Layout:**
- Heading: "From Soma Delights" — near-black
- Product lineup: 3-4 product photos in a row (color pops here)
- Each product: name + one-line benefit
- Free week offer: "Try a free week — no payment required"
- QR code: links to /free-week
- WhatsApp number and Instagram handle
- Soma logo

**Monthly Topics (12 months):**

| Month | Front Side Topic                                    |
|-------|-----------------------------------------------------|
| Jan   | "5 Habits to Start Your Year Right"                 |
| Feb   | "Heart Health: What Actually Matters"                |
| Mar   | "Spring Cleaning for Your Body"                     |
| Apr   | "Why Your Energy Crashes at 3 PM (And How to Fix It)"|
| May   | "Summer Hydration: How Much Water Do You Need?"     |
| Jun   | "Monsoon Immunity: A Practical Guide"               |
| Jul   | "Your Gut Health Checklist"                          |
| Aug   | "The Sleep-Wellness Connection"                     |
| Sep   | "Seasonal Eating: What to Eat in Autumn"            |
| Oct   | "Healthy Festival Eating Without Guilt"             |
| Nov   | "Gratitude & Wellness: The Mind-Body Link"          |
| Dec   | "Your Year in Wellness: A Reflection Guide"         |

---

### 3.4 Template D: Do's & Don'ts Quick Guide

A slim, pocket-sized card that fits in delivery bags, wallets, pockets, and purses. Each card
covers one wellness topic in a simple do/don't format.

**Physical Specifications:**

| Property         | Value                              |
|------------------|------------------------------------|
| Size             | DL (99 x 210mm)                   |
| Pages            | 2 (front and back)                 |
| Stock            | 250 GSM art card                   |
| Finish           | Matte lamination one side (front)  |
| Bleed            | 3mm all sides                      |
| Color mode       | CMYK                               |

**Front Side Layout ("Do's"):**
- Heading: "Hydration Do's" (or topic-specific) — near-black, subhead
- 5 items, each with:
  - Grey checkmark icon (16px)
  - Do item: 1 sentence, dark-grey body text
- Layout: single column, 28-32px between items
- Bottom: Soma logo, small, warm-grey-400

**Back Side Layout ("Don'ts"):**
- Heading: "Hydration Don'ts" — near-black, subhead
- 5 items, each with:
  - Grey X icon (16px)
  - Don't item: 1 sentence, dark-grey body text
- Bottom: "Learn more: soma-delights.com/wellness-tips" — warm-grey-500, small text
- QR code: small, bottom-right, links to relevant wellness tip page

**Topic Series (12 cards):**

| Card | Topic                    | Key Do                              | Key Don't                         |
|------|--------------------------|-------------------------------------|-----------------------------------|
| 01   | Morning Routine          | Start with water + juice            | Don't check your phone first      |
| 02   | Hydration                | Drink water before meals            | Don't wait until you feel thirsty |
| 03   | Gut Health               | Eat fiber-rich whole foods          | Don't rely on probiotic supplements alone |
| 04   | Immunity                 | Sleep 7-8 hours consistently        | Don't overdose vitamin C tablets  |
| 05   | Heart Health             | Move for 30 minutes daily           | Don't ignore persistent fatigue   |
| 06   | Skin Wellness            | Hydrate internally (water + juice)  | Don't depend only on topical products |
| 07   | Energy Management        | Eat small frequent meals            | Don't use caffeine after 2 PM    |
| 08   | Seasonal Eating          | Eat what grows locally now          | Don't eat summer fruits in monsoon|
| 09   | Sleep Hygiene            | Set a consistent bedtime            | Don't eat heavy meals after 8 PM |
| 10   | Mental Clarity           | Take 10-minute breaks every hour    | Don't multitask during deep work  |
| 11   | Festival Health          | Eat before the party                | Don't skip meals to "save room"   |
| 12   | Year-End Reflection      | Set 1 health goal for next year     | Don't try to change everything at once |

---

### 3.5 Template E: Starter Kit Insert

A folded welcome piece included in every starter kit. Personal, warm, and informative.

**Physical Specifications:**

| Property         | Value                              |
|------------------|------------------------------------|
| Size             | A5 (148 x 210mm), folded to A6    |
| Pages            | 4 (folded single sheet)            |
| Stock            | 250 GSM art card                   |
| Finish           | Matte lamination outside           |
| Bleed            | 3mm all sides                      |
| Color mode       | CMYK                               |

**Page Layout:**

```
Panel 1 (Front Cover):
  - "Welcome to Soma Delights" — near-black, title size
  - Simple botanical line illustration (grey)
  - Soma logo, bottom

Panel 2 (Inside Left — Founder's Note):
  - "A note from [Founder Name]" — near-black, subhead
  - Handwritten-feel text (use the serif accent font, not actual handwriting font)
  - 4-5 sentences: welcome, what to expect, personal touch
  - Founder's first name as sign-off

Panel 3 (Inside Right — Your Free Week):
  - "Your 7-Day Guide" — near-black, subhead
  - Day-by-day mini-guide:
    - Day 1: "Start fresh. Drink on an empty stomach."
    - Day 2: "Notice the taste. Every ingredient is real."
    - Day 3: "Your body is adjusting. Stay hydrated."
    - Day 4: "Try it before breakfast. Feel the difference."
    - Day 5: "You're halfway. How do you feel?"
    - Day 6: "Share with someone you care about."
    - Day 7: "The habit is forming. Want to continue?"
  - Clean numbered list with grey step numbers

Panel 4 (Back Cover):
  - "What's in your kit:" — near-black, subhead
  - Kit contents list (product names, ingredient card count)
  - "Questions? WhatsApp us anytime." — with number
  - "Choose your plan: soma-delights.com/plans"
  - QR code
  - Soma logo
```

**Variants:**
- Standard starter kit insert (as above)
- Referral starter kit: Panel 2 adds "You were referred by [Name]. They believe in this."
- Corporate kit: Panel 2 adjusted for corporate context, wellness benefit messaging
- Festival kit: Panel 1 includes festival-appropriate greeting (Diwali, Ugadi, etc.)

Same template structure, different content for each variant.

---

### 3.6 Template F: Business Card

**Physical Specifications:**

| Property         | Value                              |
|------------------|------------------------------------|
| Size             | 90 x 55mm (standard Indian size)  |
| Stock            | 400 GSM cotton or art card         |
| Finish           | Soft-touch matte lamination (both sides) |
| Corners          | Standard (or rounded 3mm — optional)|
| Color mode       | CMYK                               |

**Front:**
- Soma Delights logo — near-black, centered or left-aligned
- Tagline: "Daily Wellness, Delivered." — warm-grey-500, small
- Generous white space

**Back:**
- Name (if personal) or "Soma Delights" (if generic brand card)
- Phone / WhatsApp number
- Email
- Instagram handle
- Website URL
- QR code (small, bottom-right)
- All text in dark-grey, small, well-spaced

---

## 4. Content Calendar

### 4.1 Monthly Production Calendar

| Week  | Activity                                           | Owner         |
|-------|----------------------------------------------------|---------------|
| Week 1| Content planning: choose theme, outline articles    | Founder       |
| Week 2| Content writing: feature article, ingredient spotlights, tips | Founder/Writer |
| Week 3 (by 15th)| Content finalized, all text approved     | Founder       |
| Week 3 (by 20th)| Design completed, print-ready PDFs exported | Designer     |
| Week 4 (by 25th)| Printing completed, delivered to warehouse | Print vendor |
| Week 4 (by 28th)| Packed with delivery materials, ready for distribution | Operations |
| Month start     | Distribution begins with deliveries      | Delivery team |

### 4.2 Annual Themes

| Month    | Booklet Theme             | Ingredient Cards    | Do's & Don'ts         | Poster Topic                          |
|----------|---------------------------|---------------------|-----------------------|---------------------------------------|
| January  | New Year Wellness Reset   | Amla, Turmeric      | Morning Routine       | "5 Habits to Start Your Year Right"   |
| February | Heart & Energy            | Beetroot, Spinach   | Heart Health          | "Heart Health: What Actually Matters" |
| March    | Ugadi + Spring Detox      | Ginger, Lemon       | Seasonal Eating       | "Spring Cleaning for Your Body"       |
| April    | Summer Prep               | Cucumber, Mint      | Hydration             | "Why Your Energy Crashes at 3 PM"     |
| May      | Summer Hydration          | Coconut Water, Watermelon | Energy Management | "Summer Hydration Guide"             |
| June     | Monsoon Immunity          | Tulsi, Black Pepper | Immunity              | "Monsoon Immunity: A Practical Guide" |
| July     | Gut Health Deep Dive      | Aloe Vera, Apple    | Gut Health            | "Your Gut Health Checklist"           |
| August   | Sleep & Recovery          | Celery, Curry Leaf  | Sleep Hygiene         | "The Sleep-Wellness Connection"       |
| September| Seasonal Eating           | Papaya, Pomegranate | Skin Wellness         | "What to Eat in Autumn"              |
| October  | Navratri / Festival Wellness | Wheatgrass, Neem | Festival Health       | "Healthy Festival Eating"            |
| November | Diwali + Gratitude        | Honey, Pineapple   | Mental Clarity        | "Gratitude & Wellness"               |
| December | Year in Review            | Coriander, Carrot  | Year-End Reflection   | "Your Year in Wellness"              |

### 4.3 Quarterly Deep Editions

| Quarter | Theme                    | Pages | Special Feature                      |
|---------|--------------------------|-------|--------------------------------------|
| Q1 (Mar)| Spring Wellness Handbook  | 20-24 | Complete seasonal ingredient guide   |
| Q2 (Jun)| Summer Survival Guide     | 20-24 | Hydration science deep-dive          |
| Q3 (Sep)| Gut Health Encyclopedia   | 20-24 | Interview with nutritionist          |
| Q4 (Dec)| Year in Wellness          | 20-24 | Community highlights, year review    |

---

## 5. Reusability Matrix

### 5.1 Template x Distribution Channel

| Template              | Subscriber Monthly | Kiosk Pop-up | Starter Kit | Ambassador | Corporate | Festival Gift |
|-----------------------|-------------------|--------------|-------------|------------|-----------|---------------|
| A: Wellness Booklet   | Monthly edition   | Quarterly    | No          | Quarterly  | Quarterly | Special edition|
| B: Ingredient Card    | 1/day rotation    | Sampler (5)  | 3-4 cards   | Set of 12  | No        | Set of 6      |
| C: Health Poster      | No                | Yes          | No          | Yes        | Yes       | No            |
| D: Do's & Don'ts      | 1/month in bag    | Yes          | 1 card      | Yes        | Yes       | No            |
| E: Kit Insert         | No                | No           | Yes         | No         | Yes (variant) | Yes (variant)|
| F: Business Card      | No                | Yes          | No          | Yes        | Yes       | No            |

### 5.2 Template x Content Swap Points

Each template has defined "content zones" that change per edition while layout stays fixed:

**Template A (Booklet):**
- Swap: cover title, feature article, ingredient spotlights, do's/don'ts topic, seasonal content, community highlights, product showcase
- Fixed: logo placement, page grid, typography, footer, QR code placement

**Template B (Ingredient Card):**
- Swap: ingredient photo, ingredient name, "did you know" fact, 3 benefits, wellness tip, card number, QR target URL
- Fixed: card layout, icon style, font sizes, logo placement, lamination

**Template C (Health Poster):**
- Swap: topic title, 5-7 tips, illustration/photo, product selection on back
- Fixed: layout structure, heading placement, QR position, product area on back

**Template D (Do's & Don'ts):**
- Swap: topic, 5 do's, 5 don'ts, QR target URL
- Fixed: icon style, layout, logo, sizing

**Template E (Kit Insert):**
- Swap: founder note text, day-by-day guide content, kit contents list, variant greeting
- Fixed: fold structure, panel layout, typography, QR position

---

## 6. Print Production Workflow

### 6.1 Monthly Production Timeline

```
Day 1-10:    CONTENT PHASE
             - Founder/writer creates content for all templates
             - Feature article draft
             - Ingredient spotlight text
             - Do's & Don'ts content
             - Health poster tips
             - Review and approval

Day 11-15:   DESIGN PHASE
             - Designer plugs content into templates
             - Photo selection and placement
             - Proofread round 1 (designer self-check)
             - Proofread round 2 (founder review)
             - Export print-ready PDFs (PDF/X-1a, CMYK, 300 DPI, 3mm bleed)

Day 16-20:   PRINT PHASE
             - Files sent to print vendor
             - Soft proof review (digital proof from vendor)
             - Hard proof review (physical sample for first run of any template)
             - Print run begins
             - Quality check on first 10 copies

Day 21-25:   DELIVERY PHASE
             - Printed materials delivered to Soma production/storage
             - Sorted into distribution stacks:
               - Subscriber monthly packs
               - Starter kit inserts
               - Kiosk/event stock
               - Ambassador distribution packs
             - Packed and ready for month start

Day 26+:     DISTRIBUTION
             - Materials included with daily deliveries
             - Booklet: included with first delivery of the month
             - Ingredient card: 1 per delivery, rotating
             - Do's & Don'ts: included with first delivery of the month
```

### 6.2 First-Run vs Reprint Workflow

**First run of any template (new template design):**
1. Design template in Figma/InDesign
2. Internal review (founder + designer)
3. Export print-ready PDF
4. Send to vendor for hard proof
5. Review physical proof in person
6. Approve or request revisions
7. Full print run
8. Quality check on first 10 copies from the run

**Monthly reprint (existing template, new content):**
1. Swap content in existing template
2. Internal review (founder quick review)
3. Export print-ready PDF
4. Send to vendor (no hard proof needed if template is unchanged)
5. Soft proof review (digital)
6. Full print run
7. Spot check on delivery

---

## 7. Photography Shot List

### 7.1 Product Photography (One-Time + Per New Product)

| Shot                          | Quantity | Notes                                  |
|-------------------------------|----------|----------------------------------------|
| Each product bottle (front)   | 1 per SKU| White bg, natural light, slight shadow |
| Each product bottle (45-degree)| 1 per SKU| Angled view showing label and drink color |
| Product lineup (all bottles)  | 2-3      | All products together, spaced evenly   |
| Product with ingredients      | 1 per SKU| Bottle surrounded by its raw ingredients|
| Bottle close-up (label detail)| 1 per SKU| Showing label design and drink color   |

**Total for 6 products: ~30 product shots**

### 7.2 Ingredient Photography (One-Time Per Ingredient)

| Shot                          | Quantity | Notes                                  |
|-------------------------------|----------|----------------------------------------|
| Macro close-up (texture)      | 1 per ingredient | Extreme close-up showing detail |
| Whole ingredient (clean)      | 1 per ingredient | On white/marble surface        |
| Overhead flat-lay             | 1 per ingredient | Natural arrangement on surface |
| Cross-section (where applicable)| 1 per ingredient | Beetroot rings, lemon segments |

**Total for 15 ingredients: ~60 ingredient shots**

### 7.3 Process / Kitchen Photography (One-Time + Quarterly Update)

| Shot                          | Quantity | Notes                                  |
|-------------------------------|----------|----------------------------------------|
| Kitchen wide shot             | 2-3      | Overall kitchen/production space       |
| Ingredient washing            | 3-5      | Hands washing produce under water      |
| Cold-press machine            | 3-5      | Machine in operation, juice flowing    |
| Bottling process              | 3-5      | Juice being poured/sealed into bottles |
| Quality check                 | 2-3      | Inspecting bottles, labeling           |
| Packing for delivery          | 3-5      | Bottles into bags, bags organized      |
| Early morning timestamp       | 2-3      | Clock showing 4 AM, window showing pre-dawn |
| Delivery handoff              | 3-5      | Rider receiving bags, loading bike     |

**Total: ~25-35 process shots**

### 7.4 Lifestyle / Delivery Photography (Quarterly Refresh)

| Shot                          | Quantity | Notes                                  |
|-------------------------------|----------|----------------------------------------|
| Bottle at doorstep            | 3-5      | Real door, morning light               |
| Person drinking (morning)     | 3-5      | By window, at breakfast, candid        |
| Bottle on desk (work)         | 2-3      | Office/home desk setting               |
| Starter kit unboxing          | 3-5      | Box opening, contents spread           |
| Ingredient flat-lay composition| 5-10    | Grouped ingredients for specific products |

**Total: ~20-30 lifestyle shots**

### 7.5 Photography Budget

**Option 1: Professional Photographer (Recommended for Launch)**

| Session              | Duration  | Estimated Cost (INR)  |
|----------------------|-----------|-----------------------|
| Product photography  | Half day  | Rs 12,000 - 18,000   |
| Ingredient photography | Half day | Rs 10,000 - 15,000  |
| Kitchen/process      | Half day  | Rs 10,000 - 15,000   |
| Lifestyle/delivery   | Half day  | Rs 10,000 - 15,000   |
| Post-processing      | Per image | Rs 100-200/image      |

**Total launch photography budget: Rs 42,000 - 63,000**
(Can reduce by combining into 2 full-day sessions: Rs 30,000 - 45,000)

**Option 2: DIY with Good Equipment (Budget-Conscious)**

| Item                 | Cost (INR)              |
|----------------------|-------------------------|
| Smartphone (if adequate camera) | Already owned |
| Lightbox / white backdrop | Rs 1,500 - 3,000  |
| Natural light diffuser   | Rs 500 - 1,000     |
| Tripod                   | Rs 1,000 - 2,500   |
| Basic editing (Lightroom mobile) | Free - Rs 800/month |

**Total DIY setup: Rs 3,000 - 7,000**
Lower quality but serviceable for initial runs. Upgrade to professional for quarterly editions.

---

## 8. Design File Organization

### 8.1 Folder Structure

```
soma-delights-print/
├── 00-brand-assets/
│   ├── logos/
│   │   ├── soma-logo-black.svg
│   │   ├── soma-logo-white.svg
│   │   ├── soma-logo-grey.svg
│   │   └── soma-logo-guidelines.pdf
│   ├── fonts/
│   │   ├── general-sans/ (or chosen heading font)
│   │   ├── inter/ (or chosen body font)
│   │   └── lora/ (or chosen serif font)
│   ├── colors/
│   │   ├── soma-palette.ase (Adobe swatch)
│   │   └── soma-palette-cmyk.pdf
│   ├── icons/
│   │   └── soma-icon-set.svg (grey line icons)
│   └── illustrations/
│       ├── ingredient-spinach.svg
│       ├── ingredient-beetroot.svg
│       └── ... (all botanical illustrations)
│
├── 01-templates/
│   ├── template-A-booklet/
│   │   ├── SOMA-A-BOOKLET-12PAGE-TEMPLATE.indd (or .fig)
│   │   └── SOMA-A-BOOKLET-24PAGE-TEMPLATE.indd
│   ├── template-B-ingredient-card/
│   │   └── SOMA-B-INGREDIENT-CARD-TEMPLATE.indd
│   ├── template-C-health-poster/
│   │   └── SOMA-C-HEALTH-POSTER-TEMPLATE.indd
│   ├── template-D-dos-donts/
│   │   └── SOMA-D-DOS-DONTS-TEMPLATE.indd
│   ├── template-E-kit-insert/
│   │   └── SOMA-E-KIT-INSERT-TEMPLATE.indd
│   └── template-F-business-card/
│       └── SOMA-F-BUSINESS-CARD-TEMPLATE.indd
│
├── 02-editions/
│   ├── 2027-01-january/
│   │   ├── content/
│   │   │   ├── feature-article.md
│   │   │   ├── ingredient-spotlight.md
│   │   │   └── dos-donts.md
│   │   ├── photos/
│   │   │   └── (selected photos for this edition)
│   │   ├── layouts/
│   │   │   ├── SOMA-A-BOOKLET-2027-01.indd
│   │   │   ├── SOMA-B-CARDS-AMLA-2027-01.indd
│   │   │   ├── SOMA-B-CARDS-TURMERIC-2027-01.indd
│   │   │   ├── SOMA-C-POSTER-2027-01.indd
│   │   │   └── SOMA-D-DOS-DONTS-2027-01.indd
│   │   └── print-ready/
│   │       ├── SOMA-A-BOOKLET-2027-01-PRINT.pdf
│   │       ├── SOMA-B-CARDS-AMLA-2027-01-PRINT.pdf
│   │       └── ...
│   ├── 2027-02-february/
│   │   └── ...
│   └── ...
│
├── 03-photography/
│   ├── products/
│   ├── ingredients/
│   ├── kitchen/
│   ├── lifestyle/
│   └── raw/ (unedited originals)
│
└── 04-archive/
    └── (completed editions moved here after 6 months)
```

### 8.2 Naming Convention

```
SOMA-[TEMPLATE]-[CONTENT]-[DATE]-[VARIANT].extension

Examples:
SOMA-A-BOOKLET-2027-03.indd          (March 2027 booklet layout)
SOMA-A-BOOKLET-2027-03-PRINT.pdf     (print-ready PDF)
SOMA-B-CARD-SPINACH.indd             (ingredient card, spinach)
SOMA-C-POSTER-2027-06.indd           (June 2027 health poster)
SOMA-D-DOSDNTS-HYDRATION.indd        (hydration do's & don'ts card)
SOMA-E-KITINSERT-STANDARD.indd       (standard starter kit insert)
SOMA-E-KITINSERT-DIWALI.indd         (Diwali variant)
```

---

## 9. Cost Analysis

### 9.1 Per-Unit Print Costs (Hyderabad Market, 2026 Estimates)

Costs are based on typical Hyderabad commercial print vendor rates. Actual costs will vary
by vendor, quantity, and market conditions. Get quotes from 3+ vendors.

**Template A: Wellness Booklet**

| Variant           | Quantity | Cost/Unit (INR) | Total (INR)      |
|-------------------|----------|-----------------|------------------|
| 12-page monthly   | 100      | Rs 70-90        | Rs 7,000-9,000   |
| 12-page monthly   | 200      | Rs 55-75        | Rs 11,000-15,000 |
| 12-page monthly   | 300      | Rs 45-65        | Rs 13,500-19,500 |
| 12-page monthly   | 500      | Rs 35-50        | Rs 17,500-25,000 |
| 24-page quarterly | 200      | Rs 90-120       | Rs 18,000-24,000 |
| 24-page quarterly | 300      | Rs 75-100       | Rs 22,500-30,000 |
| 24-page quarterly | 500      | Rs 60-85        | Rs 30,000-42,500 |

**Template B: Ingredient Card**

| Quantity | Cost/Unit (INR) | Total (INR)      |
|----------|-----------------|------------------|
| 200      | Rs 5-8          | Rs 1,000-1,600   |
| 500      | Rs 3-5          | Rs 1,500-2,500   |
| 1,000    | Rs 2-4          | Rs 2,000-4,000   |
| 2,000    | Rs 1.50-3       | Rs 3,000-6,000   |

**Template C: Health Poster (A4)**

| Quantity | Cost/Unit (INR) | Total (INR)      |
|----------|-----------------|------------------|
| 100      | Rs 8-12         | Rs 800-1,200     |
| 200      | Rs 5-8          | Rs 1,000-1,600   |
| 500      | Rs 3-5          | Rs 1,500-2,500   |

**Template D: Do's & Don'ts Card (DL)**

| Quantity | Cost/Unit (INR) | Total (INR)      |
|----------|-----------------|------------------|
| 200      | Rs 5-7          | Rs 1,000-1,400   |
| 500      | Rs 3-5          | Rs 1,500-2,500   |
| 1,000    | Rs 2-4          | Rs 2,000-4,000   |

**Template E: Starter Kit Insert**

| Quantity | Cost/Unit (INR) | Total (INR)      |
|----------|-----------------|------------------|
| 100      | Rs 8-12         | Rs 800-1,200     |
| 200      | Rs 5-8          | Rs 1,000-1,600   |
| 500      | Rs 3-5          | Rs 1,500-2,500   |

**Template F: Business Card**

| Quantity | Cost/Unit (INR) | Total (INR)      |
|----------|-----------------|------------------|
| 200      | Rs 5-8          | Rs 1,000-1,600   |
| 500      | Rs 3-5          | Rs 1,500-2,500   |

### 9.2 Monthly Budget: 100-Subscriber Stage

At 100 subscribers, monthly print needs are modest. Focus on the essentials.

| Item                           | Quantity | Cost/Unit | Monthly Cost (INR) |
|--------------------------------|----------|-----------|-------------------|
| Booklet (12-page, monthly)     | 120*     | Rs 70     | Rs 8,400          |
| Ingredient cards (2 types/month)| 3,000** | Rs 3      | Rs 9,000          |
| Do's & Don'ts card (1 topic)   | 200      | Rs 5      | Rs 1,000          |
| Health poster (for kiosks only)| 50       | Rs 8      | Rs 400            |
| Starter kit insert (new signups)| 30***   | Rs 8      | Rs 240            |

*120 = 100 subscribers + 20 buffer for kiosk/ambassador use
**3,000 = ~1 card per delivery x 100 subscribers x 30 days (print in bulk, use over month)
***30 = estimated new signups per month at this stage

**Monthly print total (100-subscriber stage): Rs 19,040**
**Rounded estimate: Rs 18,000 - 22,000 per month**
**Per subscriber: Rs 180-220 per month**

### 9.3 Monthly Budget: 300-Subscriber Stage

At 300 subscribers, economies of scale kick in. Per-unit costs drop significantly.

| Item                           | Quantity | Cost/Unit | Monthly Cost (INR) |
|--------------------------------|----------|-----------|-------------------|
| Booklet (12-page, monthly)     | 350*     | Rs 50     | Rs 17,500         |
| Ingredient cards (2 types/month)| 10,000** | Rs 2     | Rs 20,000         |
| Do's & Don'ts card (1 topic)   | 500      | Rs 3      | Rs 1,500          |
| Health poster (kiosks + apartments)| 200   | Rs 5      | Rs 1,000          |
| Starter kit insert (new signups)| 80***   | Rs 5      | Rs 400            |

*350 = 300 subscribers + 50 buffer
**10,000 = bulk print for the month (better rate), rotate through the series
***80 = estimated new signups per month at this stage

**Monthly print total (300-subscriber stage): Rs 40,400**
**Rounded estimate: Rs 38,000 - 45,000 per month**
**Per subscriber: Rs 127-150 per month**

### 9.4 Quarterly Additional Costs

| Item                           | Quantity | Cost/Unit | Quarterly Cost (INR) |
|--------------------------------|----------|-----------|---------------------|
| Quarterly deep booklet (24-page)| 400     | Rs 80     | Rs 32,000           |
| Full ingredient card set (collector pack) | 50 | Rs 100 (24-card set) | Rs 5,000 |
| Business cards (reprint)       | 200      | Rs 5      | Rs 1,000            |
| Photography session (refresh)  | 1        | —         | Rs 15,000-25,000    |

**Quarterly additional: Rs 53,000 - 63,000**
**Per quarter per subscriber (at 300): Rs 175-210**

### 9.5 Annual Budget Summary

**At 100 subscribers:**

| Category           | Annual Cost (INR)   |
|--------------------|---------------------|
| Monthly print      | Rs 2,16,000-2,64,000|
| Quarterly extras   | Rs 2,12,000-2,52,000|
| Launch photography | Rs 30,000-45,000    |
| Design tools (Figma/Canva Pro) | Rs 12,000-24,000 |
| **Annual total**   | **Rs 4,70,000-5,85,000** |
| **Per subscriber/year** | **Rs 4,700-5,850** |
| **Per subscriber/month**| **Rs 390-490**     |

**At 300 subscribers:**

| Category           | Annual Cost (INR)    |
|--------------------|----------------------|
| Monthly print      | Rs 4,56,000-5,40,000 |
| Quarterly extras   | Rs 2,12,000-2,52,000 |
| Photography refresh| Rs 60,000-100,000    |
| Design tools       | Rs 12,000-24,000     |
| **Annual total**   | **Rs 7,40,000-9,16,000** |
| **Per subscriber/year** | **Rs 2,467-3,053** |
| **Per subscriber/month**| **Rs 205-255**     |

### 9.6 Cost Reduction Strategies

1. **Bulk printing:** Print ingredient cards in large batches (5,000+) for the best per-unit rate. They don't expire — evergreen content.
2. **Reduce booklet frequency:** Booklet every other month instead of monthly once content library is established. Redistribute budget to cards and posters.
3. **DIY photography:** Use a quality smartphone + natural light for monthly process/lifestyle shots. Reserve professional photography for product and ingredient shoots.
4. **Canva Pro over Adobe:** Rs 4,000/year vs Rs 20,000/year. Sufficient for template-based work until a dedicated designer joins.
5. **Print locally:** Use Hyderabad-based print vendors (Ameerpet, Kachiguda print hub) to avoid shipping costs and enable quick turnaround.

---

## 10. Vendor Requirements

### 10.1 Print Vendor Selection Criteria

| Requirement                    | Priority | Notes                                |
|--------------------------------|----------|--------------------------------------|
| CMYK offset printing           | Must     | Not digital for booklets (quality)   |
| Soft-touch matte lamination    | Must     | Core to brand feel                   |
| 300+ GSM card stock            | Must     | Minimum for cards and covers         |
| Saddle-stitching capability    | Must     | For monthly booklets                 |
| Perfect binding capability     | Should   | For quarterly editions               |
| Within Hyderabad               | Must     | Quick turnaround, no shipping        |
| 5-7 day turnaround             | Must     | Fits the monthly production timeline |
| Hard proofing available        | Must     | For first run of new templates       |
| Minimum order: 100 copies      | Should   | Low minimum for early stage          |

### 10.2 Recommended Print Hubs in Hyderabad

- **Ameerpet printing cluster:** Multiple offset printers, competitive rates, established
- **Kachiguda / Nampally area:** Traditional print hub, good for booklets and cards
- **Kukatpally area:** Convenient proximity, digital + offset available
- **Online (backup):** PrintStop, Printo, ePrint — for when local vendor is unavailable

### 10.3 Vendor Onboarding

For the first order:
1. Request quotes from 3+ local vendors with exact specifications
2. Order a hard proof of each template (pay for the proof, it is worth it)
3. Compare: paper quality, lamination feel, color accuracy, binding quality, turnaround time
4. Select primary vendor + backup vendor
5. Establish monthly standing order terms (payment terms, delivery schedule)

---

## 11. Quality Control

### 11.1 Pre-Print Checklist

Before sending any file to the printer:

- [ ] PDF/X-1a format, CMYK color mode
- [ ] 300 DPI minimum resolution on all images
- [ ] 3mm bleed on all sides
- [ ] 5mm safe zone from trim for all critical content (text, logos)
- [ ] Fonts embedded or outlined
- [ ] No RGB images remaining
- [ ] Rich black (C40/M30/Y30/K100) for large black areas
- [ ] Greyscale elements use K-only channel
- [ ] Spell check completed
- [ ] Phone numbers and URLs verified
- [ ] QR codes tested and working
- [ ] Page count is correct (must be multiple of 4 for saddle-stitch)
- [ ] Founder/content owner has signed off on content

### 11.2 Post-Print Checklist

When printed materials arrive:

- [ ] Paper stock feels correct (weight, matte finish)
- [ ] Lamination is soft-touch matte (not glossy, not rough)
- [ ] Colors are accurate (compare to digital proof on calibrated screen)
- [ ] Product photos are vibrant and true-to-life
- [ ] Greyscale areas are clean (no color cast, no banding)
- [ ] Trim is clean and even
- [ ] Binding is secure (pages don't fall out)
- [ ] Text is sharp and legible at all sizes
- [ ] QR codes scan correctly
- [ ] No smudging, ink transfer, or printing defects
- [ ] Correct quantity delivered

### 11.3 Common Print Issues and Prevention

| Issue                     | Prevention                                      |
|---------------------------|-------------------------------------------------|
| Color shift (too warm/cool)| Use ICC profiles, request hard proof first       |
| Banding in grey gradients | Avoid gradients (design system prohibits them)   |
| Text too close to trim    | Enforce 5mm safe zone in templates               |
| Images look dark          | Brighten images 5-10% for CMYK (screens are brighter)|
| Lamination peeling        | Verify vendor uses quality lamination film + adhesive|
| QR code too small to scan | Minimum 20mm x 20mm for QR codes                |
| Pages misaligned          | Request aligned proof, check registration marks  |

---

## Appendix: Print Material at a Glance

### What Each Subscriber Receives Monthly

| Item                          | Frequency    | Included With              |
|-------------------------------|-------------|---------------------------|
| Wellness Booklet (12-page)    | 1x per month| First delivery of the month|
| Ingredient Card               | Daily       | Each delivery bag          |
| Do's & Don'ts Card            | 1x per month| First delivery of the month|

### What a New Subscriber Receives (Starter Kit)

| Item                          | Quantity    |
|-------------------------------|-------------|
| Starter Kit Insert (welcome)  | 1           |
| Ingredient Cards              | 3-4 (matching kit products) |
| Do's & Don'ts Card            | 1 (Morning Routine) |
| Products (bottles)            | 7 (one per day) |

### What is Available at Kiosks/Events

| Item                          | Quantity (per event) |
|-------------------------------|----------------------|
| Quarterly Booklet             | 50-100               |
| Health Posters                | 20-30                |
| Ingredient Card Sampler (5)   | 50-100 sets          |
| Do's & Don'ts Cards           | 100-200              |
| Business Cards                | 50-100               |

---

*This print marketing system is designed to scale. At launch (50-100 subscribers), the monthly
print commitment is manageable at Rs 18,000-22,000. As the subscriber base grows, per-unit
costs decrease while the educational content library compounds — early editions remain relevant
and can be redistributed. The key is consistency: one booklet, one card, one tip — every month,
without fail.*
