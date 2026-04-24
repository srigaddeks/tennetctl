# Soma Delights Design System

> Version 1.0 | Last Updated: 2026-03-23
> Status: Planning / Specification

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [Color System](#2-color-system)
3. [Typography](#3-typography)
4. [Photography & Imagery Style](#4-photography--imagery-style)
5. [Grid & Layout System](#5-grid--layout-system)
6. [Component Library](#6-component-library)
7. [Print Material Specifications](#7-print-material-specifications)
8. [Iconography & Illustration Style](#8-iconography--illustration-style)
9. [Spacing & Sizing Scale](#9-spacing--sizing-scale)
10. [Motion & Interaction](#10-motion--interaction)
11. [Accessibility](#11-accessibility)
12. [Anti-Patterns](#12-anti-patterns)
13. [Brand Voice in Design](#13-brand-voice-in-design)
14. [Application Guidelines](#14-application-guidelines)
15. [Design Token Reference](#15-design-token-reference)

---

## 1. Design Philosophy

### Core Principle

**"Quiet luxury meets radical transparency."**

The design system for Soma Delights serves one purpose: to make the product the hero of every
visual context. Everything around the product — the layout, typography, backgrounds, navigation,
print materials — steps back deliberately so the drinks themselves carry all the energy, color,
and life on the page.

### Guiding Beliefs

**The product is the only color.**
Greyscale creates a premium calm. The muted environment is not a limitation — it is a deliberate
stage. When a deep ruby beet juice or a vivid green morning blend appears on that stage, it
commands attention without competing with anything around it.

**White space communicates confidence.**
Generous margins, breathing room between sections, and low information density per page are not
wasted space. They signal that Soma Delights has nothing to cram in, nothing to shout about.
The brand is confident enough to let silence speak.

**Every element earns its place.**
No decorative gradients, no ornamental borders, no "just because" illustrations. Every visual
element must serve one of two purposes: education or trust. If it does neither, it does not
belong.

**Education feels like a calm conversation.**
The design must support long-form reading without fatigue. Typography, spacing, and hierarchy
are tuned for sustained engagement — the goal is that someone reads an entire ingredient page
or wellness booklet without feeling sold to.

**Premium comes from restraint, not embellishment.**
High GSM paper, matte finishes, generous white space, and a limited palette — these choices
cost more in production but signal quality through what is absent, not what is added.

### Design Mood

If Soma Delights were a physical space, it would be:
- A clean, well-lit kitchen with white marble countertops and wooden cutting boards
- Fresh produce arranged simply on the counter — no styling, no props
- Morning light coming through a window
- A single cookbook open to a well-worn page
- Quiet. Intentional. Real.

---

## 2. Color System

### 2.1 Primary Palette (Brand / UI / Print)

These are the ONLY colors used for interface elements, text, backgrounds, borders, buttons,
navigation, and all non-product visual elements.

| Token Name      | Hex       | RGB             | Usage                                        |
|-----------------|-----------|-----------------|----------------------------------------------|
| `white`         | `#FFFFFF` | 255, 255, 255   | Primary background, breathing space           |
| `warm-grey-50`  | `#F5F3F0` | 245, 243, 240   | Secondary background, cards, alternating sections |
| `warm-grey-100` | `#EBE8E4` | 235, 232, 228   | Card backgrounds, hover states on white       |
| `warm-grey-200` | `#E8E5E0` | 232, 229, 224   | Borders, dividers, subtle separators          |
| `warm-grey-300` | `#D4D0CB` | 212, 208, 203   | Disabled states, placeholder text borders     |
| `warm-grey-400` | `#B5B0AA` | 181, 176, 170   | Disabled text, inactive icons                 |
| `warm-grey-500` | `#9B9590` | 155, 149, 144   | Secondary text, captions, labels, timestamps  |
| `warm-grey-600` | `#7A756F` | 122, 117, 111   | Tertiary text, helper text                    |
| `warm-grey-700` | `#5C5753` | 92, 87, 83      | Body text alternative (compact contexts)      |
| `dark-grey`     | `#4A4543` | 74, 69, 67      | Primary body text (warm, easy on eyes)        |
| `near-black`    | `#1A1816` | 26, 24, 22      | Headings, emphasis, navigation, CTA buttons   |

**True Black (`#000000`) is NEVER used.** It creates too much contrast against white backgrounds
and feels harsh. `near-black` at `#1A1816` has the same visual authority with a warmer, more
approachable character.

### 2.2 Product Accent Colors

These colors exist ONLY to represent the actual products. They are derived from the natural
colors of the drinks themselves.

| Token Name       | Hex       | RGB            | Product Association                    |
|------------------|-----------|----------------|----------------------------------------|
| `vitality-green` | `#6B8F3C` | 107, 143, 60   | Green juice products (spinach, kale)   |
| `beet-ruby`      | `#8B2252` | 139, 34, 82    | Beetroot-based products                |
| `turmeric-gold`  | `#C4972A` | 196, 151, 42   | Turmeric / golden milk products        |
| `citrus-amber`   | `#D4882B` | 212, 136, 43   | Citrus-forward products (orange, lemon)|
| `berry-deep`     | `#5C2D50` | 92, 45, 80     | Berry blend products                   |
| `earth-brown`    | `#6B5344` | 107, 83, 68    | Pulp / dehydrated / nutty products     |

### 2.3 Color Usage Rules

**Product colors are ONLY permitted in:**
- Product photography and product bottle imagery
- SKU color indicator dots (small, 8-12px circles next to product names)
- Ingredient highlight accents on individual ingredient pages (subtle, e.g., a thin colored
  bar at the top of an ingredient hero section)
- Product category badges (small, pill-shaped, on product listing pages)

**Product colors are NEVER used for:**
- Buttons (primary, secondary, or tertiary)
- Backgrounds (section, card, page, or modal)
- Navigation elements (links, active states, hover states)
- Text of any kind
- Borders or dividers
- Icons
- Form elements (inputs, selects, checkboxes)
- Alert or notification states

**The entire point of this restriction:**
When a user scrolls through a greyscale page and encounters a product image, the natural color
of the drink is the most vibrant thing on screen. This creates an involuntary focus on the
product without any design tricks, animations, or attention-grabbing UI. The product sells
itself by being the only living color in a calm, muted environment.

### 2.4 Semantic Colors (Functional)

For functional UI states, use greyscale variations rather than traditional red/green/blue:

| State     | Approach                                                           |
|-----------|--------------------------------------------------------------------|
| Success   | `near-black` text + grey checkmark icon + "Done" / "Confirmed"    |
| Error     | `near-black` text + grey alert icon + descriptive error message    |
| Warning   | `dark-grey` text + grey warning icon + contextual guidance         |
| Info      | `warm-grey-500` text + grey info icon                              |

No colored alerts. No red error states. No green success banners. Use clear language and
iconography to communicate state — the copy does the work, not the color.

### 2.5 Dark Mode

Not planned for initial launch. If implemented later:
- Invert the greyscale (near-black becomes background, warm-grey-50 becomes text)
- Product accent colors remain unchanged — they still pop, now against dark instead of light
- Maintain the same contrast ratios in reverse

---

## 3. Typography

### 3.1 Type Families

**Primary Sans-Serif (Headings + UI):**
Recommended: **General Sans** or **Outfit**
- Geometric, clean, modern without being cold
- Strong at large sizes for headings
- Clear at small sizes for UI labels
- Fallback stack: `'General Sans', 'Outfit', 'Montserrat', system-ui, sans-serif`

**Secondary Sans-Serif (Body Text):**
Recommended: **Inter** or **DM Sans**
- Humanist warmth for sustained reading
- Excellent legibility at body sizes (16-18px)
- Clear number tables for nutritional data
- Fallback stack: `'Inter', 'DM Sans', 'Source Sans 3', system-ui, sans-serif`

**Accent Serif (Pull Quotes + Wellness Tips):**
Recommended: **Lora** or **Libre Baskerville**
- Used sparingly for pull quotes, wellness tip callouts, and founder notes
- Adds warmth and editorial quality without disrupting the clean feel
- NEVER used for body text or headings
- Fallback stack: `'Lora', 'Libre Baskerville', 'Georgia', serif`

### 3.2 Type Scale — Web / App

Based on a 1.250 ratio (major third), anchored at 16px body.

| Token             | Size (Mobile) | Size (Desktop) | Weight     | Family   | Usage                          |
|-------------------|---------------|----------------|------------|----------|--------------------------------|
| `text-xs`         | 12px          | 12px           | 400        | Body     | Captions, timestamps, legal    |
| `text-sm`         | 14px          | 14px           | 400        | Body     | Labels, helper text, metadata  |
| `text-body`       | 16px          | 18px           | 400        | Body     | Body text, paragraphs          |
| `text-body-lg`    | 18px          | 20px           | 400        | Body     | Lead paragraphs, intros        |
| `text-subhead`    | 18px          | 20px           | 600        | Heading  | Subheadings, card titles       |
| `text-section`    | 22px          | 28px           | 600        | Heading  | Section headings               |
| `text-title`      | 28px          | 36px           | 700        | Heading  | Page titles                    |
| `text-hero`       | 36px          | 52px           | 700        | Heading  | Hero headlines                 |
| `text-display`    | 44px          | 64px           | 700        | Heading  | Marketing hero (single use)    |
| `text-quote`      | 20px          | 24px           | 400 italic | Serif    | Pull quotes, wellness tips     |

### 3.3 Type Scale — Print

| Token             | Size    | Leading  | Weight     | Family   | Usage                          |
|-------------------|---------|----------|------------|----------|--------------------------------|
| `print-caption`   | 8pt     | 11pt     | 400        | Body     | Photo credits, legal, footnotes|
| `print-small`     | 9pt     | 13pt     | 400        | Body     | Table data, small labels       |
| `print-body`      | 10pt    | 15pt     | 400        | Body     | Body text, paragraphs          |
| `print-body-lg`   | 11pt    | 16pt     | 400        | Body     | Lead paragraphs                |
| `print-subhead`   | 12pt    | 16pt     | 600        | Heading  | Subheadings                    |
| `print-section`   | 16pt    | 20pt     | 600        | Heading  | Section headings               |
| `print-title`     | 24pt    | 28pt     | 700        | Heading  | Page titles                    |
| `print-hero`      | 36pt    | 40pt     | 700        | Heading  | Cover titles, hero text        |
| `print-quote`     | 14pt    | 20pt     | 400 italic | Serif    | Pull quotes                    |

### 3.4 Line Height & Measure

| Context        | Line Height | Max Characters/Line | Notes                              |
|----------------|-------------|---------------------|------------------------------------|
| Body text      | 1.6         | 65-75 characters    | Optimal readability                |
| Headings       | 1.2         | No limit            | Tight for visual impact            |
| Captions       | 1.4         | 50-60 characters    | Compact but legible                |
| Pull quotes    | 1.5         | 45-55 characters    | Generous for emphasis              |
| Print body     | 1.5 (15pt)  | 55-65 characters    | Slightly tighter for print density |

**Max content width for reading:** 680px (web), 130mm (print on A5).
This ensures body text never exceeds comfortable reading measure.

### 3.5 Typography Rules

- NEVER use more than 2 type families on a single page (heading + body; serif is reserved for
  occasional pull quotes within body text)
- ALL CAPS is permitted ONLY for: navigation labels, button text, and section overline labels.
  Never for body text or long headings.
- Letter spacing for ALL CAPS text: +0.05em (slight expansion for readability)
- No underlined text except hyperlinks
- Bold used sparingly — for emphasis within body, not for entire paragraphs
- Italic used only for: pull quotes, ingredient scientific names, and subtle emphasis

---

## 4. Photography & Imagery Style

### 4.1 Product Photography

**Setting:** Always on white (`#FFFFFF`) or off-white (`#F5F3F0`) background.
**Lighting:** Natural light, soft, directional (mimicking morning window light). Slight shadow
cast to the bottom-right for grounding — shadow color should be warm grey, not black.
**Composition:** Product centered or positioned on the rule-of-thirds. Never tilted, never
floating. Grounded and real.
**Post-processing:** Minimal. True-to-life color of the drink. No artificial saturation boost.
The drink's natural color is already vibrant enough against the muted background.

### 4.2 Ingredient Photography

**Setting:** White or light grey surface (marble, light wood, clean white plate).
**Style:** Overhead flat-lay OR macro close-up.
**Flat-lay:** Raw ingredients arranged naturally — not art-directed into geometric patterns.
Scattered as if someone just unpacked them from the market. Real, not styled.
**Macro:** Extreme close-up showing texture — the pores of a lemon, the veins of a spinach
leaf, the rough skin of turmeric root. These shots showcase freshness and rawness.
**Lighting:** Natural, soft, slightly warm.
**Post-processing:** Slightly desaturated environment (surface, props if any), full saturation
on the ingredient itself. The ingredient pops naturally.

### 4.3 Process / Kitchen Photography

**Setting:** The actual production kitchen. Real equipment, real surfaces, real hands.
**Style:** Documentary. Not staged, not art-directed. Capture the process as it happens.
**Key shots needed:**
- Hands washing ingredients
- Cold-press machine in operation
- Juice flowing into bottles
- Bottles being sealed
- Bottles packed into delivery bags
- Early morning timestamp visible (clock, phone, window light)
**Lighting:** Whatever the kitchen actually has + supplemental soft light if needed.
**Post-processing:** Light color correction only. No filters.

### 4.4 Lifestyle Photography

**Setting:** Real homes, real mornings, real people. Hyderabad context.
**Style:** Candid, not posed. Someone drinking juice by a window. A bottle on a work desk.
A morning routine in progress.
**Subjects:** Real customers (with permission) or founder. Never models. Never stock.
**Lighting:** Morning light preferred. Natural always.
**Post-processing:** Slightly desaturated environment, product color preserved.

### 4.5 Photography Anti-Patterns

- No stock photos. Ever. For any purpose.
- No artificial studio lighting that makes food look plastic
- No props that don't belong in a real kitchen (exotic flowers, designer towels, etc.)
- No filters that distort natural color
- No images where the background is more interesting than the subject
- No people looking at the camera and smiling with a product (infomercial aesthetic)
- No flat-lay arrangements that look like they took 2 hours to set up

---

## 5. Grid & Layout System

### 5.1 Web Grid

**Container:**
- Max width: 1200px
- Centered with auto margins
- Padding: 24px (mobile), 32px (tablet), 0 (desktop, content within max-width)

**Column System:**
- 12-column grid
- Gutter: 24px (mobile), 32px (desktop)
- Common layouts:
  - Full-width: 12 columns (hero sections, full-bleed images)
  - Content + sidebar: 8 + 4 columns
  - Two-column: 6 + 6 columns
  - Three-column: 4 + 4 + 4 columns (product cards, feature grids)
  - Reading content: 8 columns centered (680px max-width for body text)

**Breakpoints:**
| Name     | Min Width | Columns | Gutter | Container Padding |
|----------|-----------|---------|--------|-------------------|
| Mobile   | 0         | 4       | 16px   | 20px              |
| Tablet   | 768px     | 8       | 24px   | 32px              |
| Desktop  | 1024px    | 12      | 32px   | 32px              |
| Wide     | 1440px    | 12      | 32px   | auto (centered)   |

### 5.2 Print Grid

**A5 Booklet (148 x 210mm):**
- Margins: top 15mm, bottom 20mm, outer 15mm, inner 18mm (for binding)
- Columns: 2-column for body text, full-width for images and headings
- Gutter: 5mm between columns
- Text block: 115mm wide x 175mm tall
- Baseline grid: 15pt (matching body leading)

**A4 Poster/Insert:**
- Margins: 15mm all sides (20mm bottom)
- Columns: 3-column grid
- Gutter: 6mm
- Bleed: 3mm on all sides

**A6 Ingredient Card:**
- Margins: 8mm all sides
- Single column
- Bleed: 3mm on all sides

**DL Do's & Don'ts Card (99 x 210mm):**
- Margins: 8mm sides, 10mm top/bottom
- Single column
- Bleed: 3mm

### 5.3 Section Spacing (Web)

Consistent vertical rhythm between page sections:

| Context           | Desktop  | Tablet  | Mobile  |
|-------------------|----------|---------|---------|
| Between sections  | 120px    | 80px    | 64px    |
| Within sections   | 64px     | 48px    | 40px    |
| Between cards     | 32px     | 24px    | 20px    |
| Paragraph spacing | 24px     | 20px    | 16px    |

---

## 6. Component Library

### 6.1 Cards

**Product Card**
- Background: `white`
- Border: 1px `warm-grey-200`
- Border radius: 12px
- Padding: 0 (image area) + 24px (text area)
- Image: product photo (full color — this is where color appears)
- Title: `near-black`, `text-subhead`
- Description: `dark-grey`, `text-sm`
- Price: `near-black`, `text-body`, font-weight 600
- Hover: border shifts to `warm-grey-300`, subtle 2px translateY(-2px) lift
- No shadow on rest. On hover: `0 4px 12px rgba(26, 24, 22, 0.06)`

**Ingredient Card**
- Background: `warm-grey-50`
- Border: none
- Border radius: 12px
- Padding: 0 (image area) + 20px (text area)
- Image: ingredient photo (full color, top of card, rounded top corners)
- Title: `near-black`, `text-subhead`
- Subtitle: `warm-grey-500`, `text-sm` (e.g., "Rich in Vitamin C, Iron")
- Link behavior: entire card is clickable, navigates to ingredient page

**Testimonial Card**
- Background: `warm-grey-50`
- Border: none
- Border radius: 12px
- Padding: 32px
- Quote mark: oversized `"` in `warm-grey-300`, positioned top-left, decorative
- Quote text: `dark-grey`, `text-body`, italic (body sans, not serif)
- Attribution: `warm-grey-500`, `text-sm`, preceded by em dash
- No customer photo (privacy-first approach)

**Wellness Tip Card**
- Background: `white`
- Border: 1px `warm-grey-200`
- Border radius: 12px
- Padding: 24px
- Icon: grey line icon (24px), top-left
- Title: `near-black`, `text-subhead`
- Body: `dark-grey`, `text-sm`, max 3 lines
- Link: `dark-grey`, `text-sm`, underline, "Read more"

**Stat Card (for transparency page)**
- Background: `warm-grey-50`
- Border radius: 12px
- Padding: 32px, center-aligned
- Number: `near-black`, `text-hero`, font-weight 700
- Label: `warm-grey-500`, `text-sm`, uppercase, letter-spaced
- Example: "4:00 AM" / "Juicing starts" or "6" / "Raw ingredients per bottle"

### 6.2 Buttons

**Primary Button**
- Background: `near-black` (`#1A1816`)
- Text: `white`, `text-sm`, font-weight 600, uppercase, letter-spacing +0.05em
- Padding: 14px 28px
- Border radius: 8px
- Hover: background shifts to `dark-grey` (`#4A4543`)
- Active: background shifts to `near-black`, scale(0.98)
- Disabled: background `warm-grey-300`, text `warm-grey-500`
- No colored buttons. Ever.

**Secondary Button**
- Background: `white`
- Border: 1.5px `dark-grey`
- Text: `dark-grey`, `text-sm`, font-weight 600
- Padding: 14px 28px
- Border radius: 8px
- Hover: background `warm-grey-50`, border `near-black`, text `near-black`

**Ghost Button**
- Background: transparent
- Border: none
- Text: `dark-grey`, `text-sm`, font-weight 500
- Underline on hover
- Used for tertiary actions, "Learn more" links, navigation-like CTAs

**Button Rules:**
- Max one primary button per viewport/section
- Buttons always have minimum 44px tap target on mobile
- No icon-only buttons without accessible labels
- Button text is action-oriented: "Start Free Week", "View Ingredients", "Subscribe Now"

### 6.3 Navigation

**Desktop Navigation**
- Position: sticky top
- Background: `white` with subtle bottom border (`warm-grey-200`)
- Height: 72px
- Logo: left-aligned, `near-black`
- Links: center or right-aligned, `dark-grey`, `text-sm`, font-weight 500
- Active link: `near-black`, 2px bottom border (`near-black`)
- Hover: `near-black`
- CTA button: rightmost item, primary button style but smaller padding (10px 20px)

**Mobile Navigation**
- Hamburger icon: `near-black`, right-aligned, 24px
- Drawer: slides in from right, white background, full height
- Links: stacked, `text-body`, `dark-grey`, 56px row height
- Close: X icon, top-right
- Overlay: `near-black` at 40% opacity behind drawer

### 6.4 Forms

**Text Input**
- Background: `warm-grey-50`
- Border: 1.5px `warm-grey-200`
- Border radius: 8px
- Padding: 14px 16px
- Text: `dark-grey`, `text-body`
- Placeholder: `warm-grey-400`
- Focus: border `near-black`, subtle shadow `0 0 0 3px rgba(26, 24, 22, 0.08)`
- Error: border `dark-grey`, error icon (grey) + error message in `dark-grey` text below
- No colored validation states

**Select / Dropdown**
- Same styling as text input
- Custom chevron icon in `warm-grey-500`
- Dropdown panel: white, shadow `0 8px 24px rgba(26, 24, 22, 0.1)`, border-radius 8px

**Checkbox / Radio**
- Custom styled: `warm-grey-200` border, white fill
- Checked: `near-black` fill, white checkmark
- Size: 20px
- Label: `dark-grey`, `text-body`, 8px gap

### 6.5 Dividers

**Preferred approach:** Use vertical spacing (white space) to separate sections. No visible
dividers needed in most cases.

**When a divider is needed:**
- Hairline: 1px `warm-grey-200`, full-width or content-width
- Section divider: 1px `warm-grey-200`, with 48-64px margin above and below
- Never use both a divider AND generous spacing — pick one

### 6.6 Icons

**Style:** Line icons only. Consistent 1.5px stroke weight.
**Colors:** `dark-grey` (primary) or `warm-grey-500` (secondary/decorative)
**Sizes:**
- Small: 16px (inline with text, labels)
- Standard: 24px (navigation, cards, features)
- Large: 32px (feature highlights, section icons)
- Display: 48px (hero features, empty states)

**Icon set recommendation:** Lucide Icons or Phosphor Icons (light weight variant).
Both offer clean, consistent line-style icons.

**Rules:**
- No filled icons
- No colored icons
- No emoji as icons (web and print — WhatsApp is the only emoji-permitted channel)
- Every icon used functionally must have an accessible text label
- Decorative icons (in cards, features) do not need labels but must have aria-hidden

---

## 7. Print Material Specifications

### 7.1 Paper Stock Standards

| Material                    | Stock          | Finish                    | Weight |
|-----------------------------|----------------|---------------------------|--------|
| Booklet cover               | Art card       | Soft-touch matte lam      | 300 GSM|
| Booklet inner pages         | Art paper      | Matte (uncoated feel)     | 170 GSM|
| Ingredient cards            | Art card       | Matte lamination (2-side) | 300 GSM|
| DL Do's & Don'ts cards      | Art card       | Matte lamination (1-side) | 250 GSM|
| A4 health posters/inserts   | Art paper      | Uncoated matte            | 170 GSM|
| Starter kit insert          | Art card       | Matte lamination (1-side) | 250 GSM|
| Business cards              | Cotton/art card| Soft-touch matte lam      | 400 GSM|
| Stickers / labels           | Matte vinyl    | Matte (no gloss)          | 80-100 micron |
| Starter kit box             | Rigid board    | Soft-touch matte lam      | 350 GSM|

### 7.2 Print Finish Rule

**MATTE ONLY. Never glossy.**

Matte communicates: premium, understated, tactile, keepable.
Glossy communicates: cheap, promotional, disposable.

Soft-touch matte lamination is preferred for any material that will be handled frequently
(cards, booklet covers, business cards). It adds a velvety tactile quality that reinforces
the premium positioning.

### 7.3 Print Color Mode

- All print files: CMYK color mode
- Resolution: 300 DPI minimum (600 DPI for text-heavy documents)
- Bleed: 3mm on all sides
- Safe zone: 5mm from trim edge for all critical content
- Export format: PDF/X-1a:2001 for commercial printing
- Rich black for large black areas: C:40 M:30 Y:30 K:100 (NOT 0/0/0/100)
- Greyscale elements: use single-channel K (black) only for cleaner printing

### 7.4 Booklet Binding

| Page Count | Binding Method  | Spine    | Notes                              |
|------------|-----------------|----------|------------------------------------|
| 8-20 pages | Saddle-stitched | No spine | Stapled through fold, cost-effective|
| 20-48 pages| Perfect bound   | 2-4mm    | Glued spine, more premium feel     |

For monthly editions (12-16 pages): saddle-stitched.
For quarterly deep editions (20-24 pages): perfect bound.

---

## 8. Iconography & Illustration Style

### 8.1 Ingredient Illustrations

**Style:** Botanical line illustration. Single-weight line (1.5-2px at standard size).
Think: scientific illustration meets minimal modern line art.

**Color:** Grey only (`dark-grey` or `warm-grey-500`). Never colored.

**Subjects:** Each core ingredient gets an illustration:
- Spinach leaf (single leaf, veins visible)
- Beetroot (cross-section showing rings)
- Turmeric root (knobbly, with a small cross-section showing orange interior — shown in grey)
- Ginger root (characteristic shape, skin texture)
- Amla (round fruit, characteristic segments)
- Cucumber (partial cross-section)
- Apple (side view, stem, single leaf)
- Carrot (whole, with greens)
- Lemon (half-cut, segments visible)
- Mint leaves (sprig, 4-5 leaves)

**Usage contexts:**
- Ingredient cards (print)
- Website ingredient index page
- Booklet ingredient spotlight sections
- WhatsApp message headers (simplified versions)
- Occasional social media (minimal use)

### 8.2 UI Iconography

Functional icons for navigation, features, and UI elements. Sourced from Lucide or Phosphor
icon sets — never custom-drawn for UI (consistency matters more than uniqueness).

**Core icon set needed:**
- Navigation: menu, close, back, search, user, cart/bag, heart
- Features: leaf (wellness), clock (time/freshness), truck (delivery), shield (trust),
  droplet (hydration), sun (morning), moon (evening)
- Actions: plus, minus, check, x, chevron, arrow, external-link
- Social: WhatsApp, Instagram (brand icons)
- Utility: phone, mail, map-pin, calendar, download

### 8.3 Illustration Anti-Patterns

- No cartoonish or childish illustration styles
- No filled/colored illustrations
- No clip art
- No 3D renders
- No gradients in illustrations
- No hand-drawn/sketchy style (too casual for the brand)
- No illustrations of people (use photography for people)

---

## 9. Spacing & Sizing Scale

### 9.1 Base Spacing Scale

Built on a 4px base unit. All spacing values are multiples of 4.

| Token      | Value | Common Usage                                          |
|------------|-------|-------------------------------------------------------|
| `space-1`  | 4px   | Tight inline gaps, icon-to-label spacing              |
| `space-2`  | 8px   | Compact element spacing, small card internal padding  |
| `space-3`  | 12px  | List item spacing, form field gaps                    |
| `space-4`  | 16px  | Standard gap, paragraph spacing (mobile)              |
| `space-5`  | 20px  | Card internal padding (mobile), mobile margins        |
| `space-6`  | 24px  | Card internal padding (desktop), paragraph spacing    |
| `space-8`  | 32px  | Section internal padding, large card padding          |
| `space-10` | 40px  | Sub-section spacing                                   |
| `space-12` | 48px  | Section padding (mobile), between-section spacing     |
| `space-16` | 64px  | Section padding (desktop light)                       |
| `space-20` | 80px  | Section padding (desktop standard)                    |
| `space-24` | 96px  | Large section gaps                                    |
| `space-30` | 120px | Major section separation (desktop)                    |

### 9.2 Border Radius Scale

| Token        | Value | Usage                                      |
|--------------|-------|--------------------------------------------|
| `radius-sm`  | 4px   | Small elements, tags, badges               |
| `radius-md`  | 8px   | Buttons, inputs, small cards               |
| `radius-lg`  | 12px  | Cards, modals, dropdowns                   |
| `radius-xl`  | 16px  | Large cards, image containers              |
| `radius-full`| 9999px| Pills, avatars, circular elements          |

### 9.3 Shadow Scale

Shadows are used extremely sparingly. Most elements have no shadow.

| Token          | Value                                   | Usage                    |
|----------------|-----------------------------------------|--------------------------|
| `shadow-sm`    | `0 1px 3px rgba(26, 24, 22, 0.04)`     | Subtle card lift         |
| `shadow-md`    | `0 4px 12px rgba(26, 24, 22, 0.06)`    | Hover states on cards    |
| `shadow-lg`    | `0 8px 24px rgba(26, 24, 22, 0.08)`    | Dropdowns, modals        |
| `shadow-xl`    | `0 16px 48px rgba(26, 24, 22, 0.10)`   | Dialogs, overlays        |

Note: shadow color is always warm near-black at low opacity — never pure black.

---

## 10. Motion & Interaction

### 10.1 Principles

- Motion should be barely noticeable — functional, not decorative
- No animations that delay access to content
- No parallax scrolling
- No animated backgrounds
- No loading animations beyond a simple spinner

### 10.2 Timing

| Type              | Duration  | Easing                  | Usage                          |
|-------------------|-----------|-------------------------|--------------------------------|
| Micro-interaction | 150ms     | ease-out                | Button hover, focus states     |
| Transition        | 250ms     | ease-in-out             | Card hover, accordion open     |
| Navigation        | 300ms     | ease-in-out             | Page transitions, drawer slide |
| Complex           | 400ms     | cubic-bezier(0.4,0,0.2,1)| Modal open, overlay fade     |

### 10.3 Hover States

- Cards: subtle 2px upward lift + `shadow-md`
- Buttons: background color shift (defined in button specs)
- Links: underline appears (transition 150ms)
- Images: no hover effect (no zoom, no overlay, no filter change)

---

## 11. Accessibility

### 11.1 Color Contrast Compliance

All text must meet WCAG 2.1 AA minimum (4.5:1 for normal text, 3:1 for large text).

| Combination                              | Ratio  | Passes |
|------------------------------------------|--------|--------|
| `near-black` on `white`                  | 17.4:1 | AAA    |
| `dark-grey` on `white`                   | 8.6:1  | AAA    |
| `warm-grey-500` on `white`               | 3.9:1  | AA-lg  |
| `warm-grey-600` on `white`               | 5.1:1  | AA     |
| `near-black` on `warm-grey-50`           | 15.8:1 | AAA    |
| `dark-grey` on `warm-grey-50`            | 7.8:1  | AAA    |
| `white` on `near-black`                  | 17.4:1 | AAA    |

**Note:** `warm-grey-500` on `white` (3.9:1) does NOT pass AA for body text. Use it only for:
- Large text (18px+ or 14px+ bold) where 3:1 is sufficient
- Non-essential decorative labels
- Always pair with a darker text alternative for critical information

For captions and labels that must be accessible at small sizes, use `warm-grey-600` (#7A756F)
which passes AA at 5.1:1.

### 11.2 Non-Color Indicators

Product accent colors are never the sole indicator of information:
- SKU color dots always have a text label ("Green Morning", not just a green dot)
- Error states use icons + text, not color
- Links are underlined (not just colored differently — they are all greyscale anyway)

### 11.3 Focus States

- Visible focus ring: 2px solid `near-black`, 2px offset
- Focus ring on white backgrounds: clearly visible
- Focus ring on dark backgrounds: switch to white
- Never remove focus outlines without replacement

### 11.4 Touch Targets

- Minimum touch target: 44 x 44px (mobile)
- Buttons: minimum height 44px
- Navigation links: minimum 44px tall tap area
- Form inputs: minimum 44px height

---

## 12. Anti-Patterns

These are absolute prohibitions. No exceptions, no edge cases, no "just this once."

### Visual

- **No gradients** — not on backgrounds, buttons, text, or any element
- **No drop shadows** — except the defined subtle shadow scale for interactive states
- **No colored backgrounds** — sections are white or warm-grey-50, nothing else
- **No colored text** — all text is from the greyscale palette
- **No colored borders** — all borders are warm-grey-200 or similar greyscale
- **No colored icons** — all icons are greyscale
- **No glossy finishes** — all print is matte
- **No stock photography** — every image is original

### Typographic

- **No more than 2 type families per page** (heading + body; occasional serif quote)
- **No ALL CAPS body text** (headings only, sparingly, always letter-spaced)
- **No decorative/display fonts** (no script, no handwriting, no novelty)
- **No text smaller than 12px on web, 8pt in print**
- **No centered body paragraphs** (left-aligned always for readability)

### Layout

- **No parallax scrolling**
- **No infinite scroll** (paginate or load-more)
- **No auto-playing media** (video, audio, carousels)
- **No pop-ups or modals for marketing** (modals only for functional UI: confirmations, forms)
- **No sticky elements besides navigation** (no floating CTAs, no chat bubbles)
- **No carousel/slider for hero content** (single hero, no rotation)

### Content

- **No emojis in print or web** (WhatsApp and casual social media are exceptions)
- **No exclamation marks in headings** (calm confidence, not excitement)
- **No superlatives without evidence** ("best", "most", "#1" — never)
- **No urgency language** ("Limited time!", "Act now!", "Only X left!")
- **No comparison to competitors** (Soma stands on its own)

---

## 13. Brand Voice in Design

### How the Design Speaks

The visual design IS the brand voice made visible. Every design decision communicates:

| Design Choice                | What It Communicates                        |
|------------------------------|---------------------------------------------|
| Greyscale palette            | Confidence, calm, premium restraint          |
| Product color pops           | "The drink is the star, not the marketing"   |
| Generous white space         | "We have nothing to cram in or hide"         |
| Large ingredient pages       | "We are transparent about everything"        |
| Matte print finishes         | "Quality over flash"                         |
| No gradients or effects      | "We don't need tricks"                       |
| One CTA per section          | "No pressure, your choice"                   |
| Educational content focus    | "We teach, we don't sell"                    |
| Simple, clean forms          | "We respect your time"                       |
| No stock photos              | "Everything here is real"                    |

### Information Density

- One idea per section on web
- One topic per spread in print
- Never more than 3 bullet points without a visual break
- Paragraphs: 3-5 sentences maximum
- Pages should feel "airy" — if it feels dense, it needs more space or fewer words

### Hierarchy of Communication

On any page, the user should understand within 5 seconds:
1. Where they are (page title / heading)
2. What they can learn (section overview)
3. What they can do (single clear CTA)

Nothing else should compete for attention.

---

## 14. Application Guidelines

### 14.1 Web Application

Follow this design system for all pages. Key pages are specified in the website blueprint
(`website-blueprint.md`). Design tokens translate directly to CSS custom properties or
Tailwind theme configuration.

### 14.2 Print Application

Follow this design system for all print materials. Templates and specifications are detailed
in the print marketing system (`print-marketing-system.md`). Design tokens translate to
InDesign/Figma paragraph and character styles.

### 14.3 Social Media

**Instagram:**
- Grid aesthetic: alternating greyscale text posts and color product/ingredient photos
- Stories: simple text on off-white or near-black backgrounds, product photos with minimal
  text overlay
- No busy graphics, no heavy text overlays, no colored backgrounds

**WhatsApp:**
- Plain text messages (no formatting tricks)
- Emojis permitted sparingly (this is the one exception)
- Product photos as-is (no branded frames or borders)
- Voice notes for personal touch

**Future channels (YouTube, etc.):**
- Same greyscale aesthetic for thumbnails and overlays
- Clean white/off-white backgrounds for video
- Product as the only color on screen

### 14.4 Packaging

- Bottle labels: matte finish, minimal text, product name + key ingredients
- Label color: white/off-white background with near-black text
- Product color appears ONLY as the drink visible through the bottle
- Starter kit box: kraft or white, soft-touch matte, minimal branding

---

## 15. Design Token Reference

### Quick-Reference Token Map

All tokens in one place for implementation:

```
// Colors
--color-white: #FFFFFF;
--color-warm-grey-50: #F5F3F0;
--color-warm-grey-100: #EBE8E4;
--color-warm-grey-200: #E8E5E0;
--color-warm-grey-300: #D4D0CB;
--color-warm-grey-400: #B5B0AA;
--color-warm-grey-500: #9B9590;
--color-warm-grey-600: #7A756F;
--color-warm-grey-700: #5C5753;
--color-dark-grey: #4A4543;
--color-near-black: #1A1816;

--color-vitality-green: #6B8F3C;
--color-beet-ruby: #8B2252;
--color-turmeric-gold: #C4972A;
--color-citrus-amber: #D4882B;
--color-berry-deep: #5C2D50;
--color-earth-brown: #6B5344;

// Typography
--font-heading: 'General Sans', 'Outfit', system-ui, sans-serif;
--font-body: 'Inter', 'DM Sans', system-ui, sans-serif;
--font-serif: 'Lora', 'Libre Baskerville', Georgia, serif;

// Spacing
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;
--space-10: 40px;
--space-12: 48px;
--space-16: 64px;
--space-20: 80px;
--space-24: 96px;
--space-30: 120px;

// Border Radius
--radius-sm: 4px;
--radius-md: 8px;
--radius-lg: 12px;
--radius-xl: 16px;
--radius-full: 9999px;

// Shadows
--shadow-sm: 0 1px 3px rgba(26, 24, 22, 0.04);
--shadow-md: 0 4px 12px rgba(26, 24, 22, 0.06);
--shadow-lg: 0 8px 24px rgba(26, 24, 22, 0.08);
--shadow-xl: 0 16px 48px rgba(26, 24, 22, 0.10);

// Motion
--duration-micro: 150ms;
--duration-standard: 250ms;
--duration-nav: 300ms;
--duration-complex: 400ms;
--ease-standard: ease-in-out;
--ease-out: ease-out;
--ease-complex: cubic-bezier(0.4, 0, 0.2, 1);
```

---

## Appendix: Design System Checklist

Before any design deliverable ships (web page, print file, social post), verify:

- [ ] Only greyscale used for UI/layout (no colored backgrounds, buttons, text)
- [ ] Product photography is the only source of color
- [ ] Max 2 type families on the page
- [ ] Body text meets WCAG AA contrast (4.5:1 minimum)
- [ ] White space is generous — nothing feels cramped
- [ ] One clear CTA per section/viewport
- [ ] No stock photos
- [ ] No gradients, no glossy, no drop shadows (except defined scale)
- [ ] No emojis (except WhatsApp)
- [ ] Print files: CMYK, 300 DPI, 3mm bleed, matte finish specified
- [ ] Mobile responsive (if web)
- [ ] Touch targets 44px minimum (if interactive)
- [ ] All images have alt text (if web)

---

*This design system is a living document. Updates should be versioned and communicated to all
design and development stakeholders.*
