# Soma Delights Website Blueprint

> Version 1.0 | Last Updated: 2026-03-23
> Status: Planning / Information Architecture
> Companion: [design-system.md](./design-system.md) for all visual specifications

---

## Table of Contents

1. [Website Philosophy](#1-website-philosophy)
2. [Site Architecture](#2-site-architecture)
3. [Page-by-Page Specifications](#3-page-by-page-specifications)
4. [Content Requirements](#4-content-requirements)
5. [Mobile Behavior](#5-mobile-behavior)
6. [SEO Strategy](#6-seo-strategy)
7. [Technical Recommendations](#7-technical-recommendations)
8. [Mobile App Planning (Future)](#8-mobile-app-planning-future)
9. [Launch Checklist](#9-launch-checklist)

---

## 1. Website Philosophy

### What the Website IS

The Soma Delights website is a **wellness education platform** that happens to sell cold-pressed
drinks. It is not an e-commerce store with a blog bolted on. The website exists to:

1. **Prove transparency** — Every ingredient, every source, every process is documented. The
   website is evidence that Soma hides nothing.
2. **Teach first, sell second** — A visitor should learn something valuable about their health
   on every page, regardless of whether they buy anything.
3. **Make the product pages into ingredient pages** — The deepest content on the site is not
   about the products but about the raw ingredients. Each ingredient gets its own encyclopedia
   entry.
4. **Feel like a premium wellness magazine** — Reading the site should feel like paging through
   a beautifully designed print publication, not scrolling through an online store.

### What the Website is NOT

- Not an e-commerce store with cart, checkout, and payment processing (ordering happens via
  WhatsApp for now, Razorpay integration later)
- Not a blog-first content marketing play (wellness tips are educational, not SEO bait)
- Not a landing page with a single CTA (the site has depth — ingredient library, transparency,
  education)
- Not a mobile app replacement (the app comes later, at 500+ subscribers)

### Design Principles Applied to Web

All principles from `design-system.md` apply. Key reminders:

- Greyscale everything. Product photos are the only color.
- White or off-white backgrounds only. No colored sections.
- Max content width 680px for reading. Max layout width 1200px.
- One clear CTA per section. No stacking multiple CTAs.
- Body text in warm dark grey (#4A4543), never pure black.
- Near-black (#1A1816) for headings and primary CTA buttons.

---

## 2. Site Architecture

### 2.1 Complete Sitemap

```
/ (Home)
│
├── /our-story
│   Purpose: Founder narrative, brand philosophy, why Soma exists
│
├── /how-it-works
│   Purpose: Daily delivery model explained, habit formation, what to expect
│
├── /ingredients/
│   Purpose: Master ingredient library — the transparency centerpiece
│   ├── /ingredients/spinach
│   ├── /ingredients/beetroot
│   ├── /ingredients/turmeric
│   ├── /ingredients/ginger
│   ├── /ingredients/amla
│   ├── /ingredients/cucumber
│   ├── /ingredients/apple
│   ├── /ingredients/carrot
│   ├── /ingredients/lemon
│   ├── /ingredients/mint
│   ├── /ingredients/celery
│   ├── /ingredients/wheatgrass
│   └── ... (every ingredient used in any product)
│
├── /products/
│   Purpose: Product catalog — what we make and why
│   ├── /products/green-morning
│   ├── /products/beet-vitality
│   ├── /products/golden-immunity
│   ├── /products/citrus-energy
│   ├── /products/berry-restore
│   └── /products/daily-greens
│
├── /plans
│   Purpose: Subscription plans, pricing, comparison
│
├── /wellness-tips/
│   Purpose: Educational content library
│   ├── /wellness-tips/morning-routines
│   ├── /wellness-tips/gut-health-basics
│   ├── /wellness-tips/hydration-science
│   ├── /wellness-tips/seasonal-eating
│   ├── /wellness-tips/ingredient-combinations
│   └── ... (growing library)
│
├── /transparency
│   Purpose: Sourcing, kitchen, process, certifications — radical openness
│
├── /free-week
│   Purpose: Sign-up for the free starter week trial
│
├── /refer
│   Purpose: Referral program explanation and unique code lookup
│
├── /faq
│   Purpose: Common questions and answers
│
└── /contact
    Purpose: WhatsApp link, email, location information
```

### 2.2 Navigation Structure

**Primary Navigation (Desktop — top bar):**
- Logo (left)
- Ingredients | Products | Plans | Wellness Tips | Our Story
- CTA button: "Start Free Week" (right)

**Primary Navigation (Mobile — hamburger drawer):**
- Logo + Close icon (top)
- Ingredients
- Products
- Plans
- Wellness Tips
- Our Story
- Transparency
- FAQ
- Contact
- CTA button: "Start Free Week" (bottom, sticky)

**Footer Navigation:**
- Column 1: Products (links to each product page)
- Column 2: Learn (Ingredients, Wellness Tips, How It Works)
- Column 3: About (Our Story, Transparency, FAQ, Contact)
- Column 4: Connect (WhatsApp, Instagram, Email)
- Bottom: FSSAI license number, copyright, privacy policy

### 2.3 User Journeys

**Journey 1: New Visitor (Organic Search)**
Lands on ingredient page via Google ("benefits of amla") > reads ingredient content > sees
"In Our Products" section > clicks product > reads product page > clicks "Start Free Week" >
signs up.

**Journey 2: New Visitor (Referral)**
Lands on /free-week with referral code > reads what they get > signs up > explores ingredients
and wellness tips while waiting for delivery.

**Journey 3: Existing Subscriber**
Visits /wellness-tips for new educational content > reads article > shares on WhatsApp >
visits /ingredients to learn about an ingredient in their delivery.

**Journey 4: Curious Researcher**
Lands on /transparency > reads sourcing and process > visits /ingredients to verify claims >
reads 3-4 ingredient pages > trusts the brand > signs up for free week.

---

## 3. Page-by-Page Specifications

### 3.1 HOME PAGE ( / )

**Purpose:** First impression. Communicate the brand in 10 seconds: we make cold-pressed
drinks, delivered daily, with full transparency about what goes in them.

**Sections (top to bottom):**

**Hero Section**
- Background: off-white (#F5F3F0)
- Layout: text left (60%), product image right (40%)
- Headline: "Your Daily Wellness Ritual, Delivered." — near-black, hero size
- Subheadline: "Cold-pressed. Transparent. At your door by 7 AM." — warm-grey-500, body-lg
- CTA: "Start Your Free Week" — primary button (near-black)
- Secondary link: "See what goes inside" — ghost button, links to /ingredients
- Product image: a single bottle, full color — the ONLY color above the fold
- Mobile: stacked — image on top, text below, full-width

**How It Works Section**
- Background: white
- Heading: "Simple. Daily. Yours." — section heading
- Three steps, horizontal on desktop, vertical on mobile:
  1. Icon (grey leaf) + "Choose Your Plan" + 1 sentence
  2. Icon (grey clock) + "We Press Fresh at 4 AM" + 1 sentence
  3. Icon (grey truck) + "At Your Door by 7 AM" + 1 sentence
- CTA: "See Plans" — secondary button

**Product Showcase Section**
- Background: off-white (#F5F3F0)
- Heading: "What We Make" — section heading
- Layout: horizontal scroll of product cards (mobile) or 3-column grid (desktop)
- Each card: product card component (white bg, product image in color, name, one-line benefit,
  price)
- Product images are the ONLY color in this section
- CTA per card: "Learn More" — ghost button
- Section CTA: "View All Products" — secondary button

**Ingredient Showcase Section**
- Background: white
- Heading: "What Goes In Your Bottle" — section heading
- Subheading: "Every ingredient explained. Every source revealed." — warm-grey-500
- Layout: 4-column grid of ingredient cards (desktop), 2-column (mobile)
- Each card: grey botanical illustration + ingredient name
- Clicking any card navigates to the full ingredient page
- CTA: "Explore All Ingredients" — secondary button

**Transparency Section**
- Background: off-white (#F5F3F0)
- Heading: "Built on Transparency" — section heading
- Layout: 3 stat cards in a row:
  - "4:00 AM" / "Fresh-pressed every morning"
  - "6-8" / "Raw ingredients per bottle"
  - "0" / "Preservatives, added sugar, concentrates"
- Below stats: one paragraph about the sourcing and freshness commitment
- CTA: "See Our Full Process" — ghost button, links to /transparency

**Testimonials Section**
- Background: white
- Heading: "What People Say" — section heading
- Layout: 3 testimonial cards (desktop), horizontal scroll (mobile)
- Greyscale only. No photos. Quote marks in warm-grey-300.
- No CTA in this section (social proof, not a sales push)

**Plans Preview Section**
- Background: off-white (#F5F3F0)
- Heading: "Plans That Fit Your Routine" — section heading
- Layout: 2-3 plan cards side by side showing plan name, price, what's included (summary)
- CTA per card: "Choose This Plan" — primary button on recommended plan, secondary on others
- Section CTA: "Compare All Plans" — ghost button, links to /plans

**Footer**
- Background: near-black (#1A1816)
- Text: white and warm-grey-400
- Layout: 4-column grid (desktop), stacked (mobile)
- Soma logo in white, top-left of footer
- Navigation links in warm-grey-400, hover to white
- Social links: WhatsApp, Instagram icons
- Bottom bar: FSSAI number, copyright, privacy policy link

---

### 3.2 INGREDIENT PAGE ( /ingredients/{ingredient} )

**Purpose:** This is the crown jewel of the website. Every raw ingredient Soma uses gets a
dedicated, deep, educational page. This is where transparency becomes tangible. A visitor
should be able to read this page and feel they know more about this ingredient than most
nutrition websites would teach them.

**Sections (top to bottom):**

**Hero Section**
- Background: off-white (#F5F3F0)
- Layout: large ingredient photo (60% width, full color — the hero), text right (40%)
- Photo: macro or flat-lay of the raw ingredient, the ONLY color on the page above fold
- Ingredient name: near-black, title size
- Tagline: one sentence (e.g., "The iron-rich leaf that powers your morning.") — dark-grey
- Quick facts bar: 3-4 key nutrients as small pill badges (greyscale bg, dark text)
  - e.g., "Iron: 2.7mg/100g" | "Vitamin K: 483mcg" | "Folate: 194mcg"
- Mobile: photo full-width on top, text below

**"What It Is" Section**
- Background: white
- Heading: "What It Is" — section heading
- 2-3 paragraphs: what the ingredient is, where it originates, what makes it special, its role
  in Indian cuisine and Ayurvedic tradition (where relevant)
- Tone: educational, warm, not clinical
- No CTA in this section

**"Nutritional Profile" Section**
- Background: off-white (#F5F3F0)
- Heading: "Nutritional Profile" — section heading
- Subheading: "Per 100g of raw [ingredient]" — warm-grey-500
- Layout: clean data table in greyscale
  - Columns: Nutrient | Amount | % Daily Value
  - Rows: macronutrients (calories, protein, carbs, fiber, fat), then key vitamins and minerals
- Table styling: warm-grey-200 row borders, no colored cells, near-black headers
- Optional: simple bar chart visualization (greyscale bars) for top 5 nutrients
- Source citation at bottom: "Source: USDA FoodData Central" — warm-grey-500, text-xs

**"Health Benefits" Section**
- Background: white
- Heading: "Health Benefits" — section heading
- Layout: 4-5 benefit items, each with:
  - Grey line icon (24px)
  - Benefit title: near-black, subhead weight (e.g., "Supports Blood Health")
  - Benefit explanation: 2-3 sentences in dark-grey body text
  - Key compound: warm-grey-500 text ("Due to its high iron and chlorophyll content")
- Two-column layout on desktop (2 items left, 2-3 items right), single column on mobile

**"The Science" Section**
- Background: off-white (#F5F3F0)
- Heading: "The Science" — section heading
- 2-3 paragraphs explaining the biochemistry in accessible language
- How the key compounds work in the body
- Reference to relevant studies (not linked inline, but cited at bottom)
- "Studies have shown..." language with actual study references
- Citation format: Author, Journal, Year — listed at section bottom in warm-grey-500 text-xs
- This section differentiates Soma from brands that just list "benefits" without evidence

**"How We Source It" Section**
- Background: white
- Heading: "How We Source It" — section heading
- This section is the transparency differentiator:
  - Where specifically Soma gets this ingredient (market name, farm name if applicable)
  - Why this source was chosen (freshness, organic practices, proximity)
  - How often it is procured (daily, alternate days, weekly)
  - Freshness commitment: "From market to bottle in X hours"
- Optional: photo of the actual market/source (if available)
- Tone: specific and honest, not marketing-speak

**"Best Consumed" Section**
- Background: off-white (#F5F3F0)
- Heading: "Best Consumed" — section heading
- Practical wellness tips about this ingredient:
  - Morning or evening?
  - With food or empty stomach?
  - Combinations that enhance absorption (e.g., "Pair with citrus for better iron absorption")
  - Combinations to avoid (e.g., "Avoid with dairy — calcium blocks iron uptake")
  - Recommended daily amount
- Layout: Do's and Don'ts side-by-side format, grey checkmarks and X icons

**"In Our Products" Section**
- Background: white
- Heading: "In Our Products" — section heading
- Subheading: "This ingredient is a key part of:" — warm-grey-500
- Layout: horizontal row of product cards (only products containing this ingredient)
- Product cards: the standard product card component — product images are the color here
- CTA: "View All Products" — secondary button

**"Did You Know?" Section**
- Background: off-white (#F5F3F0)
- Heading: "Did You Know?" — section heading
- One interesting, memorable fact about the ingredient
- Large pull-quote style formatting using the serif accent font
- Warm-grey-500 attribution if the fact comes from a specific source

**Bottom CTA Section**
- Background: white
- Centered text block:
  - "Experience [ingredient] in your daily ritual."
  - CTA: "Start Your Free Week" — primary button
  - Secondary: "Explore More Ingredients" — ghost button

---

### 3.3 INGREDIENT INDEX PAGE ( /ingredients/ )

**Purpose:** Beautiful overview of every ingredient Soma uses. A visual library that invites
exploration.

**Sections:**

**Hero**
- Background: off-white
- Heading: "Our Ingredients" — hero size
- Subheading: "Every ingredient we use, explained in full. Because you deserve to know what
  you are drinking." — dark-grey, body-lg
- No CTA in hero (the page IS the experience)

**Ingredient Grid**
- Background: white
- Layout: 3-column grid (desktop), 2-column (tablet), 1-column (mobile)
- Each item: ingredient card (grey botanical illustration + name + one-line description)
- Cards link to full ingredient pages
- Optional: filter by nutrient type ("Rich in Iron", "High in Vitamin C", "Anti-inflammatory")
  using greyscale pill toggles

**Bottom CTA**
- "Want to experience these ingredients?" — primary CTA to /free-week

---

### 3.4 PRODUCT PAGE ( /products/{product} )

**Purpose:** Show exactly what is in this product, why these ingredients were combined, and how
to get it. The product page is essentially a curated view of ingredient pages.

**Sections (top to bottom):**

**Hero Section**
- Background: white
- Layout: product bottle photo left (40%), text right (60%)
- Product photo: full color — the bottle is the only color above fold
- Product name: near-black, title size
- One-line benefit: "Start your day with energy and clarity." — dark-grey, body-lg
- Price: near-black, section heading size
- CTA: "Add to Plan" — primary button
- Secondary: "Start Free Week" — secondary button
- Mobile: photo top, text below

**"What's Inside" Section**
- Background: off-white
- Heading: "What's Inside" — section heading
- Full ingredient list with:
  - Ingredient name (linked to ingredient page)
  - Amount per bottle (e.g., "80g fresh spinach")
  - One-line benefit (e.g., "Iron and chlorophyll for sustained energy")
- Layout: clean list with grey dividers between items
- Each ingredient name is a link — visitors can deep-dive into any ingredient

**"Why This Blend" Section**
- Background: white
- Heading: "Why This Blend" — section heading
- 2-3 paragraphs explaining the science behind this specific combination
- Which nutrients complement each other
- What the synergistic effects are
- Who benefits most from this combination
- Tone: educational, evidence-based

**"Nutritional Facts" Section**
- Background: off-white
- Heading: "Nutritional Facts" — section heading
- Clean data table: per serving (1 bottle)
  - Calories, protein, carbs, fiber, sugar (natural), fat
  - Key vitamins and minerals
  - No preservatives, no added sugar, no concentrates (explicitly stated)
- Table styling: greyscale, same as ingredient nutritional profile

**"Best For" Section**
- Background: white
- Heading: "Best For" — section heading
- Who should drink this and when:
  - Ideal for: (personas — e.g., "morning exercisers", "office workers needing afternoon energy")
  - Best time: (morning, afternoon, evening)
  - Frequency: daily recommended
  - Empty stomach or with food
- Layout: icon + text rows

**"How It's Made" Section**
- Background: off-white
- Heading: "How It's Made" — section heading
- Brief process transparency:
  - Ingredient washing and prep
  - Cold-press extraction (not centrifugal — explain why this matters)
  - Bottling and sealing
  - Cold chain to your door
  - Timeline: "From whole produce to sealed bottle in 45 minutes"
- CTA: "See our full process" — ghost button, links to /transparency

**"Part of These Plans" Section**
- Background: white
- Heading: "Part of These Plans" — section heading
- Which subscription plans include this product
- Plan cards with pricing and "Choose Plan" CTAs
- Or: "Available as a single purchase: Rs [price]/bottle"

---

### 3.5 PRODUCT INDEX PAGE ( /products/ )

**Purpose:** Browse all products.

**Hero**
- Heading: "What We Make"
- Subheading: "Every bottle, cold-pressed fresh at 4 AM."

**Product Grid**
- 2-3 column grid of product cards (standard component)
- Product images are the only color on the page

**Bottom CTA**
- "Try them all" — link to /free-week

---

### 3.6 PLANS PAGE ( /plans )

**Purpose:** Compare subscription options, understand pricing, choose a plan.

**Sections:**

**Hero**
- Heading: "Plans That Fit Your Routine"
- Subheading: "No contracts. Pause anytime. Start with a free week."

**Plan Comparison Table**
- Background: white
- Layout: side-by-side plan cards (desktop), stacked (mobile)
- For each plan:
  - Plan name
  - Price per day and per month
  - What's included (which products, how many per week)
  - Delivery schedule
  - Savings vs individual purchase (as a percentage or amount)
- Recommended plan: subtle near-black border or "Most Popular" badge in near-black pill
- CTA per plan: "Choose This Plan" — primary on recommended, secondary on others

**What's Included**
- Background: off-white
- Breakdown of each plan's contents with product photos (color pops here)

**"How Plans Work" Section**
- Background: white
- Step-by-step: choose > we deliver > adjust anytime
- Pause policy: "Pause for up to 30 days, no questions"
- Cancellation: "Cancel anytime via WhatsApp"

**Free Week Section**
- Background: off-white
- "Not sure? Start with a free week."
- What the free week includes
- CTA: "Start Free Week" — primary button

**Plan FAQ**
- Common questions about subscriptions
- Greyscale accordion component

---

### 3.7 TRANSPARENCY PAGE ( /transparency )

**Purpose:** The ultimate trust-builder. Show everything: sourcing, kitchen, process, timing,
certifications. This page proves that "transparency" is not a marketing word for Soma — it is
an operational reality.

**Sections:**

**Hero**
- Heading: "From Farm to Your Door"
- Subheading: "Every step, every source, every morning. Nothing hidden."

**"Our Kitchen" Section**
- Real photos of the production kitchen
- Not styled or staged — documentary photos
- Brief captions describing each area
- Hours of operation: "We start at 3:30 AM, 365 days a year"

**"Our Process" Timeline**
- Visual timeline (vertical, greyscale):
  - 3:30 AM — Ingredient prep begins
  - 4:00 AM — Cold-pressing starts
  - 5:00 AM — Bottling and quality check
  - 5:30 AM — Packing for delivery
  - 6:00 AM — Delivery riders dispatched
  - 6:30-7:30 AM — At your door
- Each step: grey clock icon, time, description, optional photo

**"Where We Source" Section**
- Ingredient sourcing table:
  | Ingredient | Source | Distance | Procured |
  |------------|--------|----------|----------|
  | Spinach | Kukatpally market | 2 km | Daily |
  | Beetroot | Erragadda wholesale | 5 km | Alternate days |
  - etc.
- Map visual (optional, greyscale): pin markers for sourcing locations in Hyderabad

**"What We Don't Use" Section**
- Clean list with grey X icons:
  - No preservatives
  - No added sugar
  - No concentrates
  - No artificial flavors
  - No artificial colors
  - No pasteurization (cold-pressed only)
  - No water added (100% juice and pulp)
- Each item: one sentence explaining why this matters

**"Certifications" Section**
- FSSAI license: number displayed, link to verify
- Lab reports: when available, linked as PDFs
- Future certifications planned

**"Ask Us Anything" Section**
- "We have nothing to hide. Ask us anything about our process, ingredients, or sourcing."
- WhatsApp link: direct to founder
- Email address

---

### 3.8 FREE WEEK PAGE ( /free-week )

**Purpose:** Convert interested visitors into trial subscribers. Remove all friction. Make the
offer irresistible and risk-free.

**Sections:**

**Hero**
- Heading: "Your Free Starter Week"
- Subheading: "7 days of cold-pressed wellness. No payment required."
- Starter kit photo: box + bottles + ingredient cards (color pops here)

**"What You Get" Section**
- Starter kit contents, with photos:
  - 7 bottles of cold-pressed juice (one per day, rotating products)
  - Ingredient cards for each product
  - Welcome booklet with getting-started guide
  - WhatsApp access for questions and support
- Value: "Worth Rs [amount] — yours free."

**"How It Works" Section**
- Day-by-day flow:
  - Day 1: Starter kit + first bottle delivered
  - Day 2-6: Daily delivery at your door by 7 AM
  - Day 7: Last delivery + "what's next" note
- After the free week:
  - No auto-charge. No obligation.
  - You choose: subscribe to a plan, order individual bottles, or walk away
  - "We would rather you experience it than read about it."

**Sign-Up Form**
- Fields: Name, Phone (WhatsApp), Delivery address, Preferred delivery time slot
- Submit button: "Send My Free Week" — primary button
- Trust signals below form:
  - Grey shield icon + "No payment information required"
  - Grey lock icon + "Your data stays with us only"
  - Grey check icon + "Cancel anytime via WhatsApp"
- Form submits to backend, triggers WhatsApp confirmation

**"Why Free?" Section**
- Honest explanation:
  - "We believe in the product. Once you taste it, you'll understand."
  - "Our best marketing is your first sip."
  - "We'd rather spend on your experience than on ads."
- This section builds trust by being straightforward about the business model

---

### 3.9 OUR STORY PAGE ( /our-story )

**Purpose:** Humanize the brand. Connect the visitor to the founder and the "why."

**Sections:**

**Hero**
- Heading: "Why Soma Exists"
- Subheading: "A founder's perspective on daily wellness."

**Founder Narrative**
- First-person or close-third story
- Why this brand was started
- The problem observed (unhealthy routines, opaque food industry, wellness gatekeeping)
- The belief: wellness should be simple, transparent, and habitual
- The name: "Soma" — what it means, why it was chosen
- Portrait photo of founder (real, not styled — only color is natural skin/clothing tones)

**"What We Believe" Section**
- Core beliefs as short, punchy statements:
  - "Wellness is a daily habit, not a weekend project."
  - "You should know every ingredient by name."
  - "Education is better marketing than advertising."
  - "Premium means honest, not expensive."

**Timeline**
- Key milestones (when relevant):
  - Idea stage, first prototype, first customer, first 50, first 100
  - Major decisions (no ads, free week model, transparency-first)
  - Where we are now, where we are going

---

### 3.10 HOW IT WORKS PAGE ( /how-it-works )

**Purpose:** Explain the daily delivery model and habit formation approach for people who have
never subscribed to a daily wellness delivery.

**Sections:**

**Hero**
- Heading: "How Soma Delights Works"
- Subheading: "A daily wellness habit, delivered to your door."

**"The Daily Ritual" Section**
- Step-by-step visual flow:
  1. We source fresh ingredients from local markets every morning
  2. Cold-pressed in small batches starting at 4 AM
  3. Bottled, sealed, and packed by 5:30 AM
  4. Delivered to your door between 6:30-7:30 AM
  5. You drink it as part of your morning routine
- Each step: icon, title, 1-2 sentence explanation

**"Why Daily?" Section**
- The science of habit formation
- Why daily is better than occasional
- How 7 days becomes 30 becomes a lifestyle
- The streak system: how Soma helps you stay consistent

**"What to Expect" Section**
- Week 1: "You're trying something new. Some flavors surprise you."
- Week 2-3: "It becomes part of your morning. You notice if it's missing."
- Month 2+: "Energy stabilizes. Digestion improves. It's just what you do."
- Disclaimer: "Individual results vary. We're not doctors. But we are consistent."

**"Flexibility" Section**
- Pause, skip, swap, cancel — all via WhatsApp
- No contracts, no lock-in, no penalties
- "Your plan, your rules."

---

### 3.11 WELLNESS TIPS ( /wellness-tips/ )

**Purpose:** Educational content library. Positions Soma as a knowledge source, not just a
product vendor. Each article teaches something valuable independent of Soma products.

**Index Page:**
- Magazine-style layout
- Featured article: large card at top (full-width, image + title + excerpt)
- Grid below: 2-column article cards
- Categories as greyscale pill filters:
  - Morning Routines
  - Gut Health
  - Hydration
  - Seasonal Wellness
  - Ingredient Science
  - Habit Formation
- Pagination: "Load More" button (not infinite scroll)

**Article Page:**
- Clean reading layout (680px max-width)
- Title: near-black, title size
- Author: "By [Founder Name]" — warm-grey-500
- Date: warm-grey-500
- Estimated read time: warm-grey-500
- Body: well-structured with subheadings, short paragraphs, bullet lists
- Ingredient photos as the only color in the article
- Pull quotes in serif accent font
- No product CTAs within the article body — let the content be genuinely educational
- End-of-article: subtle "Related products" section and "More articles" section
- Share: WhatsApp share button (primary), copy link (secondary)

**Launch Articles (10 needed):**
1. "Why Your Morning Routine Matters More Than Your Diet"
2. "The Complete Guide to Cold-Pressed vs. Centrifugal Juice"
3. "Understanding Gut Health: What Actually Works"
4. "Hydration Science: How Much Water Do You Really Need?"
5. "Seasonal Eating in Hyderabad: A Month-by-Month Guide"
6. "The Iron Absorption Problem (And How to Fix It)"
7. "Building a Wellness Habit: The Science of Daily Routines"
8. "Turmeric: Separating Hype from Science"
9. "What 'No Preservatives' Actually Means"
10. "The Real Cost of Cheap Juice"

---

### 3.12 REFER PAGE ( /refer )

**Purpose:** Explain the referral program and let existing subscribers look up their referral
code.

**Sections:**

**Hero**
- Heading: "Share Wellness, Earn Credits"
- Subheading: "Give a friend a free week. Get credits when they subscribe."

**How It Works**
- Step 1: Share your unique referral code
- Step 2: Friend signs up for a free week using your code
- Step 3: When friend subscribes, you earn Rs [X] in wallet credits
- Step 4: Credits apply to your next billing cycle

**Referral Code Lookup**
- Simple form: enter phone number > view your referral code + link
- Share buttons: WhatsApp (primary), copy link

**FAQ about referrals**
- What if my friend doesn't subscribe?
- How long do credits last?
- Is there a limit?

---

### 3.13 FAQ PAGE ( /faq )

**Purpose:** Answer common questions to reduce WhatsApp support volume.

**Layout:**
- Grouped by category (accordion sections):
  - About Our Products
  - Ordering & Delivery
  - Subscriptions & Plans
  - Ingredients & Nutrition
  - Free Week
  - Referral Program
- Each question: accordion (click to expand answer)
- Greyscale styling, chevron icon for expand/collapse
- Search box at top (optional, for large FAQ)
- Bottom CTA: "Still have questions? WhatsApp us" — with direct link

---

### 3.14 CONTACT PAGE ( /contact )

**Purpose:** Simple contact information.

**Content:**
- WhatsApp: link to business WhatsApp (primary contact method)
- Email: hello@soma-delights.com (or similar)
- Instagram: @somadelights
- Operating hours: "We respond within 2 hours during 6 AM - 10 PM"
- Delivery area: "Currently serving Kukatpally and surrounding areas, Hyderabad"
- Map: optional, greyscale, showing delivery coverage area

---

## 4. Content Requirements

### 4.1 Content Inventory for Launch

| Content Type         | Quantity | Priority | Status |
|----------------------|----------|----------|--------|
| Ingredient pages     | 12-15    | Critical | Needed |
| Product pages        | 5-6      | Critical | Needed |
| Wellness tip articles| 5-10     | High     | Needed |
| Our Story page       | 1        | High     | Needed |
| How It Works page    | 1        | High     | Needed |
| Transparency page    | 1        | Critical | Needed |
| FAQ entries          | 25-30    | High     | Needed |
| Plans page           | 1        | Critical | Needed |
| Free Week page       | 1        | Critical | Needed |

### 4.2 Photography Needed for Launch

| Photo Type            | Quantity | Notes                                |
|-----------------------|----------|--------------------------------------|
| Product bottle shots  | 5-6      | Each product, white/off-white bg     |
| Raw ingredient photos | 12-15    | Macro + flat-lay per ingredient      |
| Kitchen/process       | 10-15    | Documentary style                    |
| Founder portrait      | 3-5      | Natural, not styled                  |
| Ingredient flat-lays  | 5-10     | Grouped compositions                 |
| Delivery moment       | 3-5      | Real delivery at real door           |
| Starter kit           | 3-5      | Unboxing, contents spread            |

**Budget estimate:**
- Professional photographer (half-day): Rs 15,000-25,000
- Additional editing/retouching: Rs 5,000-10,000
- Total photography budget: Rs 20,000-35,000

### 4.3 Copywriting Guidelines

**Tone:** Calm, knowledgeable, warm. Never salesy. Never urgent.

**Voice:**
- First person plural ("We source..." not "Soma Delights sources...")
- Active voice preferred
- Short sentences for impact, longer sentences for explanation
- No jargon without explanation
- No exclamation marks in headings
- No superlatives without evidence

**Per-page word counts (approximate):**
- Home page: 800-1,200 words total
- Ingredient page: 1,500-2,000 words per ingredient
- Product page: 800-1,200 words per product
- Wellness tip article: 1,000-1,500 words per article
- Our Story: 1,000-1,500 words
- Transparency: 1,000-1,500 words
- How It Works: 600-800 words
- FAQ: 50-100 words per answer

---

## 5. Mobile Behavior

### 5.1 General Mobile Rules

- Mobile is the primary design target (most traffic will be mobile in Hyderabad)
- All layouts stack vertically on mobile
- Horizontal scrolling only for product card carousels (with visible scroll indicators)
- Touch targets: 44px minimum
- Navigation: hamburger with slide-in drawer
- Bottom CTA: on key conversion pages (free-week, plans), a sticky bottom bar with CTA button
  appears after scrolling past the hero

### 5.2 Mobile-Specific Adjustments

| Element              | Desktop                    | Mobile                        |
|----------------------|----------------------------|-------------------------------|
| Navigation           | Horizontal top bar         | Hamburger + drawer            |
| Product grid         | 3-column                   | 1-column or horizontal scroll |
| Ingredient grid      | 3-column                   | 2-column                      |
| Article layout       | 680px centered             | Full-width with 20px padding  |
| Plan comparison      | Side-by-side               | Stacked cards                 |
| Hero image           | Side-by-side with text     | Stacked: image top, text below|
| Footer               | 4-column grid              | Single column, stacked        |
| Section padding      | 80-120px                   | 48-64px                       |
| Body font size       | 18px                       | 16px                          |

### 5.3 Performance on Mobile

- Target: <3 second load time on 4G
- Images: lazy-loaded, responsive srcset, WebP format with JPEG fallback
- Fonts: subset to Latin characters, preloaded
- Above-fold content: no external dependencies
- Third-party scripts: loaded after interaction (not on page load)

---

## 6. SEO Strategy

### 6.1 SEO Opportunity

Ingredient pages are the primary SEO play. People search for:
- "benefits of spinach"
- "amla nutrition facts"
- "turmeric health benefits"
- "beetroot juice benefits"
- "cold pressed juice Hyderabad"

Each ingredient page is optimized to rank for these queries.

### 6.2 Page-Level SEO

**Ingredient pages:**
- Title: "[Ingredient] — Benefits, Nutrition & Science | Soma Delights"
- Meta description: "Learn about [ingredient] — nutritional profile, health benefits, the
  science behind it, and how we source it fresh in Hyderabad."
- H1: ingredient name
- Structured data: NutritionInformation schema, FAQPage schema
- Internal links: to related ingredients, products containing this ingredient, wellness tips
  mentioning this ingredient

**Product pages:**
- Title: "[Product Name] — Cold-Pressed [Key Ingredient] Juice | Soma Delights"
- Meta description: brief product description + key benefit
- Structured data: Product schema with price, availability

**Wellness tip articles:**
- Title: "[Article Title] | Soma Delights Wellness Tips"
- Meta description: article excerpt
- Structured data: Article schema, FAQPage if question-based

### 6.3 Technical SEO

- Static/SSG pages for fast load and crawlability
- Sitemap.xml generated automatically
- robots.txt: allow all public pages
- Canonical URLs on all pages
- Open Graph and Twitter Card meta tags for social sharing
- Image alt text on all images (descriptive, not keyword-stuffed)
- Internal linking strategy: ingredient pages link to products, products link to ingredients,
  articles link to both

### 6.4 Local SEO

- Google Business Profile: "Soma Delights — Cold-Pressed Juice Delivery, Kukatpally"
- NAP consistency: same name, address, phone across all platforms
- Service area: Kukatpally, KPHB, Miyapur, Kondapur, Gachibowli (initial)
- Reviews: encourage Google reviews from subscribers

---

## 7. Technical Recommendations

### 7.1 Technology Stack (Recommendations, Not Requirements)

**Static Site Generator:**
- Recommended: **Astro** or **Next.js (static export)**
- Why: fast loading, excellent SEO, markdown-based content authoring
- Astro preferred for content-heavy sites with minimal interactivity
- Next.js preferred if future e-commerce features need React

**Content Management:**
- Recommended: **Markdown files in Git** (initial) or **Headless CMS** (when team grows)
- Headless CMS options: Sanity, Strapi (self-hosted), or Contentful
- Why headless: non-technical team members can update ingredient pages, wellness tips, and
  product details without developer involvement
- Content model: Ingredient, Product, WellnessTip, FAQ, Plan — structured types

**Hosting:**
- Recommended: Vercel or Netlify (for static/SSG)
- Why: automatic deployments from Git, global CDN, fast, free tier sufficient for launch

**Ordering / Payments:**
- Phase 1 (launch): WhatsApp-based ordering. Sign-up form submits to backend, triggers
  WhatsApp confirmation message.
- Phase 2 (100+ subscribers): Razorpay integration for online payments. Subscription billing.
- Phase 3 (500+ subscribers): Full order management system.

**Analytics:**
- Recommended: Plausible or Umami (privacy-respecting, no cookie banner needed)
- Track: page views, ingredient page engagement, free-week conversions, referral code usage
- No Google Analytics (privacy-first, GDPR-like approach even without legal requirement)

**WhatsApp Integration:**
- WhatsApp Business API for automated messages
- Or: simple wa.me links for direct WhatsApp opens (Phase 1)
- Chatbot not recommended initially — keep it personal

### 7.2 Performance Budget

| Metric                     | Target          |
|----------------------------|-----------------|
| First Contentful Paint     | < 1.5s          |
| Largest Contentful Paint   | < 2.5s          |
| Total Blocking Time        | < 200ms         |
| Cumulative Layout Shift    | < 0.1           |
| Total page weight (home)   | < 800 KB        |
| Total page weight (ingredient) | < 1.2 MB   |
| Time to Interactive        | < 3.5s on 4G    |

### 7.3 Image Optimization

- Format: WebP primary, JPEG fallback
- Product photos: max 1200px wide, compressed to < 100 KB each
- Ingredient photos: max 1600px wide (hero), compressed to < 150 KB
- Thumbnails: 400px wide, < 30 KB
- Lazy loading: all images below the fold
- Responsive: srcset with 400w, 800w, 1200w, 1600w breakpoints
- Placeholder: low-quality blurred placeholder (LQIP) or solid warm-grey-50

---

## 8. Mobile App Planning (Future)

### 8.1 When to Build

- NOT at launch
- Build when subscriber count exceeds 500 AND:
  - WhatsApp ordering becomes a bottleneck
  - Subscribers request self-service plan management
  - Delivery tracking is needed
  - Streak/gamification features are validated

### 8.2 App Scope (When Built)

**Core Screens:**
1. **Home / Dashboard** — today's delivery status, streak count, next delivery
2. **My Plan** — current plan details, upcoming deliveries, swap/skip/pause
3. **Products** — browse products, request changes
4. **Ingredient Library** — same content as website, optimized for mobile reading
5. **Wellness Tips** — articles, push notification-delivered tips
6. **Wallet / Credits** — referral credits, subscription balance, payment history
7. **Referral** — unique code, share to WhatsApp, track referrals
8. **Profile / Settings** — address, delivery preferences, notification settings

**Design:**
- Same design system: greyscale + product color
- Native feel (not a wrapped website)
- Fast, minimal, not feature-bloated
- Bottom tab navigation: Home, Plan, Explore (ingredients + tips), Profile

**Push Notifications:**
- Delivery: "Your [product] is on its way" (with product color accent)
- Streak: "Day 14! Your wellness streak is building."
- Tips: "Morning tip: Pair your juice with a handful of nuts for better absorption."
- Weekly: summary of what you consumed, nutrient highlights

### 8.3 Technology Recommendation

- React Native or Flutter for cross-platform (iOS + Android)
- Or: Progressive Web App (PWA) as an intermediate step before native
- PWA advantage: no app store, instant deployment, shareable via link
- PWA disadvantage: limited push notification support on iOS

---

## 9. Launch Checklist

### 9.1 Pre-Launch (Must Have)

- [ ] Home page complete with all sections
- [ ] 12+ ingredient pages with full content and photography
- [ ] 5+ product pages with complete ingredient lists and nutritional data
- [ ] Plans page with accurate pricing
- [ ] Free Week page with working sign-up form
- [ ] Transparency page with real kitchen photos
- [ ] Our Story page
- [ ] How It Works page
- [ ] FAQ with 20+ questions
- [ ] Contact page with WhatsApp link
- [ ] Mobile responsive across all pages
- [ ] Performance budget met (< 3s load on 4G)
- [ ] SEO: title tags, meta descriptions, structured data on all pages
- [ ] Open Graph images for social sharing
- [ ] FSSAI number displayed in footer
- [ ] Privacy policy page (basic)
- [ ] 404 error page (greyscale, helpful)
- [ ] Domain configured and SSL active
- [ ] Analytics installed

### 9.2 Post-Launch (First 30 Days)

- [ ] 5 wellness tip articles published
- [ ] Google Business Profile created
- [ ] Social media profiles linked
- [ ] First round of SEO performance data reviewed
- [ ] User feedback collected on content and usability
- [ ] Form submission flow tested end-to-end
- [ ] Page speed audit on real mobile devices

### 9.3 Post-Launch (60-90 Days)

- [ ] 10+ wellness tip articles published
- [ ] Additional ingredient pages as new products launch
- [ ] Referral page activated
- [ ] A/B test: free week CTA placement
- [ ] Content calendar established for ongoing wellness tips
- [ ] Consider headless CMS migration if content updates become frequent

---

*This blueprint is a planning document. It defines WHAT the website should be, not HOW to build
it. Implementation decisions (framework, hosting, CMS) should be validated against current
capabilities and budget before development begins.*
