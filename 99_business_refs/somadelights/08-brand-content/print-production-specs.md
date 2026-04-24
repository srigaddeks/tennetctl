# Print Production Specifications — Soma Delights

> Technical specifications for all print materials. Hand this to your printer.
> All measurements in millimeters unless stated otherwise.

---

## 1. General Print Standards (Apply to ALL Items)

### 1.1 Color

| Specification | Requirement |
|--------------|-------------|
| Color mode | **CMYK** — NOT RGB. Convert all files to CMYK before sending to printer. |
| Color profile | ISO Coated v2 (for offset) or FOGRA39 |
| Rich black | C:40 M:30 Y:30 K:100 for large black areas (headlines, backgrounds, solid bars) |
| Registration black | C:0 M:0 Y:0 K:100 for body text ONLY (never for large areas — looks grey/washed out) |
| Maximum ink coverage | 300% total (C+M+Y+K combined). Most printers reject above 320%. |
| Brand grey tones | Define specific CMYK values for each grey shade used in the design system |
| Product colors | Match actual juice colors using Pantone swatch reference if possible. At minimum, print a color proof and compare to actual juice before bulk run. |
| Overprint | Verify NO white elements are set to overprint (common mistake in design software — white overprint = invisible white) |
| Spot colors | Not needed at our stage. Full CMYK process printing for everything. |

### 1.2 Resolution and Artwork

| Specification | Requirement |
|--------------|-------------|
| Image resolution | **300 DPI minimum** at final print size (e.g., an image that prints at 100mm wide must be at least 1181 pixels wide) |
| Line art resolution | 1200 DPI for crisp vector-like lines |
| File format | **PDF/X-1a** (press-ready) preferred. Alternative: high-res PDF with all fonts embedded and images at full resolution. |
| Fonts | All fonts embedded in PDF OR converted to outlines/curves. Never rely on the printer having your fonts installed. |
| Vector artwork | Logo and text should be vector (not rasterized) for sharpest output. Keep vector elements as vector in the PDF — do not flatten to raster. |
| Color bars / crop marks | Include crop marks and color bars in the PDF. Most design tools (InDesign, Illustrator) add these automatically on PDF export. |

### 1.3 Bleed and Safe Zones

| Zone | Measurement | Purpose |
|------|------------|---------|
| **Bleed** | 3mm on all sides beyond trim line | Prevents white edges if cutting is slightly off. Extend all backgrounds and images that touch the edge into the bleed area. |
| **Trim line** | The final cut size of the document | This is the "size" of the printed piece. |
| **Safe zone** | 5mm inside trim line on all sides | Keep ALL critical content (text, logos, important image elements) inside this zone. Content in the 5mm margin risks being cut off. |

```
+-----------------------------------+
|          3mm BLEED                 |
|  +-----------------------------+  |
|  |        5mm SAFE ZONE        |  |
|  |  +-----------------------+  |  |
|  |  |                       |  |  |
|  |  |   CONTENT AREA        |  |  |
|  |  |   (safe for text,     |  |  |
|  |  |    logos, critical     |  |  |
|  |  |    elements)           |  |  |
|  |  |                       |  |  |
|  |  +-----------------------+  |  |
|  |                             |  |
|  +-----------------------------+  |
|                                   |
+-----------------------------------+
```

### 1.4 File Naming Convention

```
soma_[item]_[description]_[version]_[date].pdf

Examples:
soma_booklet_wellness-journal_v2_2026-04.pdf
soma_label_green-vitality_v1_2026-03.pdf
soma_card_beetroot-ingredient_v1_2026-03.pdf
soma_box_starter-kit_v3_2026-04.pdf
```

---

## 2. Product-Specific Specifications

### 2.1 A5 Premium Booklet (Wellness Journal / Educational Booklet — Monthly Issue)

**This is the signature print piece. Quality must be premium.**

| Specification | Detail |
|--------------|--------|
| **Trim size** | 148 x 210mm (A5) |
| **Pages** | 8 pages self-cover (smallest issue) OR 8 inner pages + 4-page cover (12 pages total for standard issue) |
| **Cover stock** | 300 GSM art card |
| **Cover finish** | Soft-touch matte lamination BOTH sides (front and back cover). This is non-negotiable — soft-touch matte is the premium tactile signal of the brand. |
| **Inner pages stock** | 170 GSM matte coated art paper |
| **Inner pages finish** | No lamination (unnecessary for inner pages, adds cost) |
| **Binding** | Saddle-stitched (2 wire staples on spine fold) |
| **Color** | 4/4 (full CMYK color, both sides, all pages) |
| **Spine** | No printed spine (saddle-stitch does not produce a visible spine for under 48 pages) |
| **File setup** | Supply as **printer spreads** with 3mm bleed on all sides. Confirm with printer whether they want reader spreads or printer spreads — most prefer to impose themselves from single pages. |
| **Grain direction** | Long grain parallel to spine (ask printer to confirm) |

**Optional Premium Upgrade:**
- Spot UV on cover logo only: gloss UV varnish applied to the Soma logo/wordmark, creating a subtle shine contrast against the matte surface. Adds Rs 5-10 per unit at 500+ quantity. Recommend adding this once budget allows — it is a significant perceived quality upgrade.
- Deboss on cover: blind deboss (no ink, just pressed into paper) of the Soma logo. Adds Rs 8-15 per unit at 500+ quantity. Premium feel, minimal visual impact.

**Page Count Considerations:**

| Page Count | Binding | Spine | Notes |
|------------|---------|-------|-------|
| 8 pages (self-cover) | Saddle-stitch | None | Minimum viable booklet. 2 staples. |
| 12 pages (8 + cover) | Saddle-stitch | None | Standard monthly issue. 2 staples. |
| 16 pages (12 + cover) | Saddle-stitch | None | Extended issue. Still 2 staples. |
| 20 pages (16 + cover) | Saddle-stitch | None | Maximum for comfortable saddle-stitch. |
| 24+ pages | Perfect binding (glued) | 3mm minimum | Switch to perfect binding. Requires separate spine artwork. Minimum spine width 3mm. |
| 48+ pages | Perfect binding | 5mm+ | Substantial spine, can print text on spine. |

**Saddle-stitch page count rule:** Total page count (including cover) must be a multiple of 4 (4, 8, 12, 16, 20, 24...).

---

### 2.2 12-16 Page Monthly Booklet (Standard Production Run)

Same specifications as 2.1 with these adjustments:

| Specification | Detail |
|--------------|--------|
| **Pages** | 12-16 pages + 4-page cover = 16-20 pages total |
| **Binding** | Saddle-stitch (up to 20 pages total) |
| **If 24+ pages** | Switch to perfect binding. Add 3mm spine. |
| **Cover** | 300 GSM, soft-touch matte lamination both sides |
| **Inner** | 170 GSM matte coated |
| **Production note** | For monthly booklets, establish a template with fixed page sizes and grid. Only content changes month to month — layout structure stays consistent. This speeds up production and reduces printer errors. |

---

### 2.3 Ingredient Cards (A6 Collectible Series)

**These are collectible — quality must make people want to keep them.**

| Specification | Detail |
|--------------|--------|
| **Trim size** | 105 x 148mm (A6) |
| **Paper** | 300 GSM art card (must feel substantial — not flimsy) |
| **Finish** | Matte lamination BOTH sides (protects against handling, moisture from being near juice bottles) |
| **Color** | 4/4 (full color both sides) |
| **Corners** | Option 1: Square corners (standard, no extra cost). Option 2: Rounded corners, 2mm radius (adds Rs 1-2 per unit, looks more premium and collectible). **Recommendation: rounded corners.** |
| **File setup** | Single card per file. Front and back as Page 1 and Page 2 in one PDF. 3mm bleed all sides. |
| **Quantity per design** | 15-20 different ingredient designs in the full collection. Print equal quantities of each. |

**Card Structure (Content Layout):**

Front:
- Hero ingredient photograph (bleeds to edge on at least 2 sides)
- Ingredient name (large, prominent)
- Tagline or one-line description

Back:
- Origin/sourcing information
- Key nutritional facts (3-5 bullet points)
- Health benefits (2-3 sentences)
- "How we use it" — which Soma juices contain this ingredient
- Card number in the collection (e.g., "04/15")
- Soma branding (small logo, consistent position)

---

### 2.4 DL Do's & Don'ts Cards / Quick Reference Cards

| Specification | Detail |
|--------------|--------|
| **Trim size** | 99 x 210mm (DL — fits in a standard DL envelope, though we won't use envelopes) |
| **Paper** | 250 GSM matte coated |
| **Finish** | Option 1: No lamination (cheaper, acceptable for an insert card). Option 2: Matte lamination both sides (more durable, recommended if card is meant to be kept). |
| **Color** | 4/4 |
| **File setup** | Front and back in one PDF, 3mm bleed |

**Card Types to Produce:**

| Card | Front | Back |
|------|-------|------|
| Storage Do's & Don'ts | How to store your juice (refrigerate immediately, consume within 24 hours, shake before drinking) | What NOT to do (don't freeze, don't leave in sun, don't mix with hot liquid) |
| Wellness Routine Guide | Suggested daily routine incorporating juice (best times to drink, empty stomach vs. with food) | Common mistakes (drinking too fast, expecting overnight results, replacing meals entirely) |
| Ingredient Quick Reference | Quick guide to which juice does what (green = detox, red = energy, etc.) | Allergy/sensitivity notes, contact info for questions |

---

### 2.5 Starter Kit Box

**This is the premium first-impression piece. The unboxing experience matters.**

| Specification | Detail |
|--------------|--------|
| **Box type** | Rigid box with separate lid (telescope style — lid slides over base) |
| **Outer dimensions** | Approximately 250 x 200 x 100mm (internal dimensions must fit: 4 x 250ml bottles standing upright + booklet + cards + welcome note) |
| **Material** | 1200 GSM greyboard (rigid board) |
| **Wrapping** | 157 GSM art paper, printed CMYK, wrapped around greyboard |
| **Exterior finish** | Soft-touch matte lamination on wrap paper (matches booklet feel) |
| **Interior** | White paper lining (clean, premium look when opened) |
| **Interior option** | Custom printed tissue paper (brand pattern) OR plain white tissue paper (more affordable). White tissue recommended initially — custom printed tissue adds Rs 5-8 per sheet at 500+ qty. |
| **Closure** | Option 1: Friction fit (lid sits snugly on base — no closure mechanism). Option 2: Magnetic closure (magnets embedded in lid and base — adds Rs 20-30 per unit, significantly more premium). **Recommendation: friction fit for initial run (cost), magnetic for future runs.** |
| **Optional extras** | Ribbon pull on lid (aids opening) — adds Rs 3-5 per unit. Foam/cardboard insert to hold bottles in place — adds Rs 10-15 per unit but prevents bottles moving during delivery. **Recommendation: cardboard insert YES (functional), ribbon NO (unnecessary).** |

**Box Engineering Notes:**

- Measure actual bottles before finalizing box dimensions — 1-2mm tolerance matters for rigid boxes
- Internal cardboard insert (die-cut) should have slots for:
  - 4 bottle positions (standing upright, snug fit)
  - 1 booklet slot (vertical, between bottles and box wall)
  - 1 card/paper pocket (flat, on top of insert or in lid)
- Order a blank sample box BEFORE committing to a print run — check fit with actual products
- Rigid box MOQ is typically 100-200 units for custom sizes

**File Setup:**

- Printer will provide a dieline (flat template showing all panels)
- Design artwork on the dieline, not on a flat rectangle
- Include 3mm bleed on all outer panels
- Interior panels: solid white or simple brand pattern
- Lid top is the hero surface — primary branding goes here
- Lid sides: minimal or plain
- Base: Soma logo/website on base bottom (often overlooked but adds completeness)

---

### 2.6 Bottle Labels

**Labels must survive cold, wet conditions (condensation on cold bottles in Hyderabad humidity).**

| Specification | Detail |
|--------------|--------|
| **Type** | Self-adhesive sticker labels |
| **Size** | Measure your specific bottle. Typical: 70 x 100mm (portrait) or 100 x 70mm (landscape). Must wrap around bottle with at least 10mm overlap for secure adhesion. Do NOT make the label the full circumference — leave a "window" of bare bottle to see juice color. |
| **Material** | **Matte white vinyl** (BOPP — biaxially oriented polypropylene). This is waterproof, tear-resistant, and handles condensation. Paper labels WILL fail on cold, sweating bottles. |
| **Print** | CMYK digital print (fine for runs under 5,000 units) |
| **Finish** | Matte overlaminate (built into vinyl material — no additional lamination needed) |
| **Adhesive** | Permanent, waterproof. Must adhere to cold, slightly damp surfaces. **TEST THIS** — request sample labels and apply to bottles pulled from the fridge. Check adhesion after 24 hours in fridge, after removal to room temperature, and after handling with wet hands. |
| **Shape** | Rectangle with rounded corners (2mm radius) — easier to apply cleanly than sharp corners which tend to peel up |
| **File setup** | Individual label artworks. One PDF per SKU. 2mm bleed. Include dieline/cut line in a separate layer. |
| **Roll vs. sheet** | For small quantities (under 500): sheet labels (cut by hand or kiss-cut sheets). For 500+: roll labels (faster application). Discuss with printer. |

**Label Content (Per SKU):**

Front of label:
- Soma Delights logo/wordmark
- Product name (e.g., "Green Vitality")
- Tagline or brief description (e.g., "Spinach + Apple + Ginger + Lemon")
- Volume: 250ml / 300ml
- "Cold-Pressed. No Sugar. No Preservatives."

Back of label (or second label on back of bottle):
- Full ingredient list (in order of quantity)
- Nutritional information per serving (optional but recommended)
- "Best consumed within 24 hours. Keep refrigerated."
- Manufacturing date: ________ (hand-stamp or write)
- FSSAI license number (REQUIRED by law for food products in India)
- Batch number (for traceability)
- Net quantity
- Manufactured by: [Name], [Address]
- Customer care: [WhatsApp number]

**FSSAI Compliance Note:**
- All food labels in India MUST include FSSAI license or registration number
- Must include: product name, ingredient list, net quantity, manufacturing date, best before, manufacturer name and address, FSSAI logo and number
- Veg/non-veg symbol (green dot for vegetarian) is MANDATORY
- Check latest FSSAI labeling requirements before finalizing label design

---

### 2.7 Business Cards

| Specification | Detail |
|--------------|--------|
| **Size** | 90 x 55mm (Indian standard) OR 85 x 55mm (international standard — either works) |
| **Paper** | Option 1: 400 GSM cotton/textured stock (premium, tactile, expensive). Option 2: 350 GSM art card (standard premium, affordable). **Recommendation: 350 GSM art card for initial run.** |
| **Finish** | Soft-touch matte lamination both sides |
| **Color** | Mostly greyscale (brand design system). 4/4 capability but design will be black/grey/white. |
| **Optional upgrade** | Deboss or letterpress on logo — adds Rs 5-10 per card at 200+ qty. Beautiful on thick cotton stock but not worth it on art card. Save this for when you upgrade to cotton stock. |
| **File setup** | Front and back in one PDF, 3mm bleed, text in safe zone |

**Card Content:**

Front:
- Soma Delights logo (centered or left-aligned)
- Tagline: "Micro-Wellness, Delivered Daily" (or current tagline)
- Clean, mostly white with grey/black typography

Back:
- Sri [Last Name], Founder
- Phone: [Number]
- WhatsApp: [Number] (if different)
- Email: [Email]
- Instagram: @somadelights
- Website: somadelights.in (or current domain)
- Small Soma logo mark

---

### 2.8 Branded Stickers / Seals

| Specification | Detail |
|--------------|--------|
| **Shape** | Circle, 40mm diameter |
| **Material** | Option 1: Kraft paper (natural brown, eco feel). Option 2: Matte white vinyl (consistent with label material). **Recommendation: kraft paper for sealing tissue/boxes, vinyl for outdoor/bottle use.** |
| **Print** | 1-2 color (Soma logo + optional tagline). Keeps costs low and looks intentional. |
| **Adhesive** | Permanent for kraft, removable option available for vinyl |
| **Use cases** | Sealing tissue paper in starter kit, sealing the starter kit box (instead of tape), gift wrapping, branded envelope seal |
| **File setup** | Circle artwork with 2mm bleed beyond the 40mm diameter. Supply as PDF with dieline. |
| **Quantity** | Order 500-1000 minimum — stickers are cheap at volume and you'll use them for everything |

---

### 2.9 Welcome Note / Thank You Card

| Specification | Detail |
|--------------|--------|
| **Size** | A6 (105 x 148mm) or custom postcard size (120 x 170mm) |
| **Paper** | 300 GSM art card OR 250 GSM textured/cotton stock |
| **Finish** | Matte lamination one side (printed side) or uncoated (if using textured stock for handwritten note feel) |
| **Color** | 4/1 (full color front, single color back OR blank back for handwritten note) |
| **Content** | Front: printed welcome message from founder, branded design. Back: blank or lightly printed lines for handwritten personal note. |
| **Recommendation** | Blank back + handwritten personal note for first 50 customers. Printed both sides once scale makes handwriting impractical. |

---

## 3. Paper Stock Reference Guide

For discussing options with the printer — know what you're asking for:

| GSM | Thickness Feel | Common Use | Soma Use |
|-----|---------------|------------|----------|
| 80-100 GSM | Standard printer paper | Office documents | NOT USED — too thin for brand materials |
| 130-150 GSM | Thick magazine page | Magazine insides, flyers | NOT USED — too thin for our materials |
| 170 GSM | Substantial page, slight stiffness | Premium magazine, booklet insides | **Booklet inner pages** |
| 250 GSM | Card-like, bends but holds shape | Postcards, flyers, inserts | **DL cards, some inserts** |
| 300 GSM | Stiff card, doesn't bend easily | Business cards, premium cards | **Booklet covers, ingredient cards, welcome cards** |
| 350 GSM | Very stiff card | Premium business cards | **Business cards** |
| 400 GSM | Board-like, rigid | Ultra-premium business cards | **Premium business cards (cotton stock)** |
| 1200 GSM | Rigid board, does not bend | Box construction | **Starter kit box (greyboard core)** |

**Coating Types:**

| Coating | Feel | Look | Best For |
|---------|------|------|----------|
| **Matte coated** | Smooth, non-glossy | Flat, elegant, no reflections | Booklet inner pages, DL cards |
| **Matte lamination** | Silky smooth, protective | Flat, protected against fingerprints and scratches | Booklet covers, cards that are handled |
| **Soft-touch matte lamination** | Velvety, almost rubbery | Same as matte but with a tactile luxury quality | **Our primary finish** — booklet covers, ingredient cards, business cards, box |
| **Gloss lamination** | Slick, shiny | Reflective, vibrant colors | NOT USED — does not match our brand aesthetic |
| **Spot UV** | Shiny only on specific areas | Contrast between matte and gloss on same surface | Logo on booklet cover (optional upgrade) |
| **Uncoated** | Papery, natural, absorbs ink | Raw, craft, authentic | Stickers (kraft paper), notes meant for handwriting |

---

## 4. Print Method Guide

| Method | Best For | MOQ | Cost per Unit | Quality | Turnaround |
|--------|---------|-----|--------------|---------|------------|
| **Digital printing** | Short runs (under 500), labels, variable data (different content per piece) | 1+ | Higher per unit | Very good (95% of offset quality) | 2-3 days |
| **Offset printing** | Long runs (500+), consistent quality, booklets, cards | 200-500 | Lower per unit at scale | Excellent (industry standard) | 5-7 days |
| **Screen printing** | Specialty items, branded bags, single/two color on unusual materials | 50+ | Medium | Depends on complexity | 3-5 days |
| **Die-cutting** | Custom shapes (round stickers, rounded corners, box blanks) | 100+ | Adds Rs 2-10/unit depending on complexity | N/A (shape, not print) | Done during or after printing |

**Recommendations for Soma Delights:**

| Item | Print Method | Reason |
|------|-------------|--------|
| Booklets | Offset (500+ qty) or Digital (under 200) | Offset gives best booklet quality at scale |
| Ingredient cards | Offset (500+) or Digital (under 200) | Need consistent color across the series |
| DL cards | Digital (under 500) or Offset (500+) | Simple item, digital is fine for small runs |
| Labels | Digital | Variable content (different SKUs), waterproof vinyl needs digital |
| Business cards | Digital (under 200) or Offset (200+) | Small quantity initially |
| Stickers | Digital | Simple, small, variable |
| Starter kit box | Specialized packaging printer | Rigid box construction is separate from flat printing |

---

## 5. Cost Reference Table

Estimated costs based on Hyderabad market rates (March 2026). Actual prices vary by vendor — always get 3 quotes.

### 5.1 Booklets (A5, 12+4 pages, saddle-stitched, 300GSM cover with soft-touch matte, 170GSM inner)

| Quantity | Per Unit Cost | Total Cost | Notes |
|----------|-------------|------------|-------|
| 100 | Rs 45-65 | Rs 4,500-6,500 | Digital print. Expensive per unit but low commitment. |
| 200 | Rs 30-45 | Rs 6,000-9,000 | Digital or short-run offset. |
| 500 | Rs 18-28 | Rs 9,000-14,000 | Offset. Best value for regular production. |
| 1,000 | Rs 12-20 | Rs 12,000-20,000 | Offset. Per-unit drops significantly. |

### 5.2 Ingredient Cards (A6, 300GSM, matte lamination both sides, rounded corners)

| Quantity (per design) | Per Unit Cost | Total Cost (per design) | Notes |
|----------------------|-------------|------------------------|-------|
| 100 | Rs 8-12 | Rs 800-1,200 | Digital. For 15 designs = Rs 12,000-18,000 total. |
| 200 | Rs 5-8 | Rs 1,000-1,600 | Digital/offset. For 15 designs = Rs 15,000-24,000 total. |
| 500 | Rs 3-5 | Rs 1,500-2,500 | Offset. For 15 designs = Rs 22,500-37,500 total. |
| 1,000 | Rs 2-3.50 | Rs 2,000-3,500 | Offset. For 15 designs = Rs 30,000-52,500 total. |

**Recommended initial order:** 200 per design x 15 designs = 3,000 cards total. Budget Rs 15,000-24,000.

### 5.3 DL Do's & Don'ts Cards (99x210mm, 250GSM, matte lamination)

| Quantity | Per Unit Cost | Total Cost | Notes |
|----------|-------------|------------|-------|
| 200 | Rs 4-7 | Rs 800-1,400 | Digital. |
| 500 | Rs 2.50-4 | Rs 1,250-2,000 | Offset. |
| 1,000 | Rs 1.50-2.50 | Rs 1,500-2,500 | Offset. |

### 5.4 Starter Kit Box (rigid, 250x200x100mm, 1200GSM board, wrapped, soft-touch matte, cardboard insert)

| Quantity | Per Unit Cost | Total Cost | Notes |
|----------|-------------|------------|-------|
| 50 | Rs 180-280 | Rs 9,000-14,000 | Small MOQ, expensive. Some box makers won't do under 100. |
| 100 | Rs 120-200 | Rs 12,000-20,000 | Standard MOQ for custom rigid boxes. |
| 200 | Rs 80-140 | Rs 16,000-28,000 | Better per-unit. Requires storage space. |
| 500 | Rs 55-90 | Rs 27,500-45,000 | Significant savings. Only if confident in design/demand. |

**Add for magnetic closure:** Rs 20-30 per unit additional.
**Add for cardboard insert:** Rs 10-15 per unit additional.

### 5.5 Bottle Labels (matte white vinyl, digital, 70x100mm, kiss-cut sheets or rolls)

| Quantity (per SKU) | Per Unit Cost | Total Cost (per SKU) | Notes |
|-------------------|-------------|---------------------|-------|
| 100 | Rs 3-5 | Rs 300-500 | Sheet labels, cut by hand. For 6 SKUs = Rs 1,800-3,000. |
| 250 | Rs 2-3.50 | Rs 500-875 | Kiss-cut sheets. For 6 SKUs = Rs 3,000-5,250. |
| 500 | Rs 1.50-2.50 | Rs 750-1,250 | Roll labels. For 6 SKUs = Rs 4,500-7,500. |
| 1,000 | Rs 1-1.80 | Rs 1,000-1,800 | Roll labels. For 6 SKUs = Rs 6,000-10,800. |

### 5.6 Business Cards (90x55mm, 350GSM, soft-touch matte both sides)

| Quantity | Per Unit Cost | Total Cost | Notes |
|----------|-------------|------------|-------|
| 100 | Rs 5-8 | Rs 500-800 | Digital. |
| 200 | Rs 3-5 | Rs 600-1,000 | Digital/offset. |
| 500 | Rs 2-3.50 | Rs 1,000-1,750 | Offset. |

### 5.7 Circle Stickers (40mm, kraft paper, 1-2 color)

| Quantity | Per Unit Cost | Total Cost | Notes |
|----------|-------------|------------|-------|
| 500 | Rs 1-2 | Rs 500-1,000 | Digital. |
| 1,000 | Rs 0.50-1.50 | Rs 500-1,500 | Digital. |
| 2,000 | Rs 0.30-0.80 | Rs 600-1,600 | Screen/offset. |

### 5.8 Total Budget Estimate (Launch Print Order)

**Minimum Viable Print Order (tight budget):**

| Item | Quantity | Estimated Cost |
|------|----------|---------------|
| Booklets (first issue) | 100 | Rs 4,500-6,500 |
| Ingredient cards (5 designs) | 100 each = 500 total | Rs 4,000-6,000 |
| DL cards (2 types) | 200 each = 400 total | Rs 1,600-2,800 |
| Labels (6 SKUs) | 100 each = 600 total | Rs 1,800-3,000 |
| Business cards | 100 | Rs 500-800 |
| Stickers | 500 | Rs 500-1,000 |
| **SUBTOTAL** | | **Rs 12,900-20,100** |
| Starter kit box (skip initially — use branded paper bag) | 0 | Rs 0 |
| **TOTAL MINIMUM** | | **Rs 12,900-20,100** |

**Recommended Print Order (proper launch):**

| Item | Quantity | Estimated Cost |
|------|----------|---------------|
| Booklets (first issue) | 200 | Rs 6,000-9,000 |
| Ingredient cards (10 designs) | 200 each = 2,000 total | Rs 10,000-16,000 |
| DL cards (3 types) | 200 each = 600 total | Rs 2,400-4,200 |
| Labels (6 SKUs) | 250 each = 1,500 total | Rs 3,000-5,250 |
| Starter kit box | 100 | Rs 12,000-20,000 |
| Business cards | 200 | Rs 600-1,000 |
| Stickers | 1,000 | Rs 500-1,500 |
| Welcome cards | 100 | Rs 800-1,200 |
| **TOTAL RECOMMENDED** | | **Rs 35,300-57,150** |

---

## 6. Print Vendor Selection

### 6.1 Types of Vendors Needed

You likely need 2-3 different vendors — no single printer does everything well:

| Vendor Type | Items | Where to Find in Hyderabad |
|-------------|-------|---------------------------|
| **Offset/digital printer** | Booklets, cards (ingredient, DL, business, welcome) | Nampally, Abids, Begumpet — traditional printing districts |
| **Packaging specialist** | Starter kit rigid box, cardboard inserts | Balanagar, Nacharam, Jeedimetla — industrial areas with packaging factories |
| **Label printer** | Bottle labels (vinyl, waterproof) | Search IndiaMART for "vinyl label printer Hyderabad" or "BOPP label manufacturer Hyderabad" |
| **Online print** | Business cards, stickers, small items (backup option) | PrintStop.in, Printo.in, ePrint.in |

### 6.2 Vendor Evaluation Checklist

Before placing an order with any vendor:

- [ ] **Request paper/material samples** — physically feel the GSM, check the matte finish quality, compare soft-touch matte from multiple vendors (quality varies significantly)
- [ ] **Request a color proof** — digital color proof (printed sample of your actual file) before bulk production. Check that greyscale tones are accurate (grey printing is surprisingly hard — many printers produce yellowish or bluish greys)
- [ ] **Confirm CMYK capability** — some small digital printers work primarily in RGB. Verify they print in CMYK with proper color management
- [ ] **Check minimum order quantities** — some offset printers won't run under 500 units
- [ ] **Confirm turnaround time** — typical: 5-7 business days for offset, 2-3 for digital. Add 2-3 days for lamination
- [ ] **Get pricing at 3 quantities** — always ask for 200, 500, and 1,000 to understand the price curve
- [ ] **Ask about storage** — can they hold stock and release in batches? (Useful for booklets where you don't want 500 sitting at your house)
- [ ] **Inspect a finished product** — ask to see a similar job they've done. Check print registration, cut accuracy, lamination quality, binding quality
- [ ] **Confirm file format requirements** — PDF/X-1a, fonts embedded, crop marks included
- [ ] **Discuss payment terms** — most Hyderabad printers expect 50% advance + 50% on delivery. Some accept full payment on delivery for repeat orders
- [ ] **Test with a small order first** — before committing to 500 booklets, order 50-100 first. Pay the higher per-unit rate for the peace of mind

### 6.3 Common Print Problems and How to Avoid Them

| Problem | Cause | Prevention |
|---------|-------|-----------|
| Colors look different from screen | RGB to CMYK conversion, uncalibrated monitor | Always proof on paper, not on screen. Request color proof before bulk. |
| White border on edges | Artwork doesn't extend to bleed | Verify all bleed areas are filled (3mm beyond trim) |
| Text cut off near edges | Text too close to trim line | Keep all text in safe zone (5mm from edge minimum) |
| Greys look warm/yellowish | CMYK grey generated with warm tones | Define exact CMYK grey values: use C:0 M:0 Y:0 K:XX for neutral greys, or add 5-10% Cyan to counteract warmth |
| Booklet pages in wrong order | Imposition error | Number all pages in the PDF. Review a folded proof before printing. |
| Lamination bubbling | Poor lamination adhesion, usually due to heavy ink coverage | Request thermal lamination (not cold lamination) for better adhesion. Ensure ink is fully dry before laminating. |
| Label peeling off cold bottles | Wrong adhesive, paper label on wet surface | Use vinyl (BOPP), not paper. Permanent waterproof adhesive. Test before bulk order. |
| Box doesn't fit products | Dimensions measured incorrectly | Order blank sample box first. Test with actual bottles. Allow 2-3mm tolerance. |
| Soft-touch matte scratches easily | Heavy handling on dark-colored surfaces | Soft-touch matte does scratch on very dark (K:100) surfaces. Design covers with lighter grey tones to minimize visible scratching. |
| Fonts missing or substituted | Fonts not embedded in PDF | Convert all fonts to outlines OR embed all fonts. Open the PDF on a different computer to verify. |

---

## 7. Pre-Print Checklist (Run Before Every Print Order)

### 7.1 File Preparation

- [ ] All files in CMYK color mode
- [ ] Resolution: 300 DPI minimum for all images
- [ ] Bleed: 3mm on all sides
- [ ] Safe zone: 5mm margin for all critical content
- [ ] Fonts embedded or converted to outlines
- [ ] No RGB images remaining (check in Acrobat Preflight)
- [ ] Rich black used for large black areas (C:40 M:30 Y:30 K:100)
- [ ] No white elements set to overprint
- [ ] Total ink coverage under 300% everywhere
- [ ] Crop marks and color bars included
- [ ] File named correctly (soma_[item]_[desc]_[version]_[date].pdf)

### 7.2 Content Verification

- [ ] All text proofread (ideally by someone other than the designer)
- [ ] Phone numbers, URLs, social handles verified and correct
- [ ] FSSAI number included on all food-related labels
- [ ] Veg symbol (green dot) present on labels
- [ ] Nutritional information verified
- [ ] No placeholder text remaining ("Lorem ipsum", "[INSERT HERE]")
- [ ] Page numbers correct and in order (booklet)
- [ ] Brand consistency: logo usage, color values, typography match brand guidelines

### 7.3 Vendor Communication

- [ ] File format confirmed with vendor
- [ ] Paper stock and GSM confirmed
- [ ] Finish (lamination type) confirmed
- [ ] Quantity confirmed
- [ ] Color proof requested (before bulk production)
- [ ] Delivery date confirmed
- [ ] Payment terms confirmed
- [ ] Sample from previous similar job reviewed

---

## 8. Reorder Schedule

Once launched, plan your print reorders to avoid running out:

| Item | Initial Order | Reorder Trigger | Reorder Quantity | Lead Time |
|------|--------------|----------------|-----------------|-----------|
| Booklets | 200 | When 50 remaining | 200-500 (based on subscriber growth) | 7-10 days |
| Ingredient cards | 200/design | When 30 remaining of any design | 200/design | 5-7 days |
| DL cards | 200/type | When 50 remaining | 200-500/type | 3-5 days |
| Labels | 250/SKU | When 50 remaining of any SKU | 500/SKU (volume discount) | 3-5 days |
| Starter kit boxes | 100 | When 20 remaining | 100 | 10-14 days (longest lead) |
| Business cards | 200 | When 30 remaining | 200 | 3-5 days |
| Stickers | 1,000 | When 200 remaining | 1,000 | 3-5 days |

**Production Calendar:**
- New booklet issue: finalize content by 15th of month, send to print by 18th, receive by 25th, ship to subscribers with 1st of next month delivery
- New ingredient cards: produce in batches of 3-5 new designs every 2-3 months
- Labels: reorder when any SKU drops below 50 — labels have the shortest acceptable runway because no labels = no product

---

*Review this document with your designer and printer before the first print run. Keep it updated as you learn what works and what needs adjustment.*
