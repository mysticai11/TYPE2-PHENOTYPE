# LMSIS Frontend Redesign Specification
## From Scientific Dashboard to Clinical Experience
**Version:** 2.0 — Complete Redesign  
**Date:** 2026-06-06  
**Purpose:** Make the system visually impressive, immediately understandable, and justifiable as a research contribution

---

## Preamble: What Is Wrong with the Current Frontend

The current frontend has one fundamental problem. It was designed around the model, not around the user. The 14 sliders sit next to the 2D latent space visualization next to the readout panels — all visible simultaneously. The user faces the entire scientific machinery at once. They must understand what Z₁ and Z₂ mean before they can understand what the visualization is showing them. This is the wrong order.

The correct order is:

> **Enter patient data → See where the patient stands → Understand what it means → Know what to do.**

Everything else is noise until those four moments have occurred, in that sequence.

The redesign proposed here is organized entirely around that sequence. The model's architecture never changes. Only how it is revealed to the user changes. A clinician who has never heard of a variational autoencoder should be able to use this system in under sixty seconds and walk away understanding their patient's metabolic risk in terms they already know.

---

## Part 1 — The Conceptual Framework: Clinical Cartography

The single most important design decision in this entire document is the metaphor.

The current system uses the metaphor of a **scientific dashboard** — dials, readouts, coordinates, plots. This metaphor requires the user to be a scientist.

The redesigned system uses the metaphor of a **metabolic map** — a patient has a location, the location is in a territory, the territory has a name, and there is a route from here to somewhere better.

Every adult on earth understands a map. No adult needs to be taught what it means to be in a dangerous location and to see a route back to safety. The GPS metaphor translates every abstract concept in the system into immediate human understanding:

| Abstract concept | Dashboard framing | Map framing |
|---|---|---|
| Z₁, Z₂ coordinates | "Latent space position" | "Your metabolic location" |
| Phenotypic quadrant | "Quadrant assignment" | "The territory you are in" |
| Conformal ellipse | "Prediction interval" | "Location accuracy radius" |
| Counterfactual pathway | "Intervention vector" | "The route to safety" |
| Population scatter | "Training data overlay" | "Where other people with normal BMI are" |
| Distance to safe region | "Latent space displacement" | "How far from safety" |

This reframing requires zero changes to the underlying model. It is entirely a presentation decision. But it is the decision that transforms a confusing research prototype into a system that justifies its clinical purpose.

---

## Part 2 — The Two-Phase Architecture

The current system tries to do everything on one screen. The redesign separates the experience into two distinct phases with a cinematic transition between them.

### Phase 1: Input (The Consultation)
Clean, white, calm. Feels like a modern medical intake form. The patient does not exist yet in the system — this phase is about gathering the information needed to locate them.

### Phase 2: The Map (The Diagnosis)
Full-screen, dark, immersive. The patient now has a location. This phase is entirely about understanding that location, what it means, and how to move from it. The scientific machinery is hidden. The map is everything.

The transition between Phase 1 and Phase 2 is a deliberate, cinematic animation — not a page change. It is the moment of diagnosis. It should feel like opening a window.

---

## Part 3 — Phase 1: The Input Experience

### 3.1 Layout

A single-column centered layout, maximum 680px wide, vertically centered on a white background with a very subtle warm paper texture (`noise-opacity: 3%`). This is a form, not an application — it should feel familiar and unthreatening.

At the top: the system name in a refined serif display font. Below it, one line: *"Enter routine blood biomarker values to locate the patient's metabolic state."*

No sidebars. No panels. No navigation. Just the form.

### 3.2 Form Organization

The 14 biomarkers are organized into four visually distinct groups. Each group has a heading and a thin top-rule, but no box or card border. The groups breathe into the white space rather than being contained.

**Group A — Metabolic Core**
Fasting Glucose · Fasting Insulin
(Computed below both: HOMA-IR displayed in larger text as the pair is entered)

**Group B — Lipid Profile**
Triglycerides · HDL Cholesterol
(Computed below both: TG:HDL ratio)

**Group C — Liver Markers**
AST · ALT · GGT
(Computed below all three: AST:ALT ratio)

**Group D — Body & Blood**
BMI · Waist Circumference · Platelets

**Group E — Demographics**
Age · Sex · Ancestry

### 3.3 Input Field Design

Each biomarker uses a numeric input with the following structure:

```
FASTING GLUCOSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[     94     ]   mg/dL    Normal: 70–99
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

- Label: Small caps, tracked, black
- Input box: Large, clean, generous padding, monospaced number font
- Unit: Grey, right of input
- Reference range: Muted italic, right-aligned, gives the clinician context without judgment

**Threshold coloring:** When a value leaves the normal range, the bottom rule changes color — amber for moderately elevated, crimson for significantly elevated. No alert text. No icons. Just the color of the line beneath the input. This is the only visual feedback during data entry — calm enough not to alarm, visible enough to communicate.

**Slider alternative toggle:** A small toggle at the top of the form switches between "Type values" and "Use sliders." Clinicians entering known values prefer typing. Researchers exploring the space prefer sliders. Both modes are available. The default is typing.

### 3.4 The Computed Readouts

HOMA-IR, TG:HDL ratio, and AST:ALT ratio appear as read-only computed cards between their source inputs. They use a slightly indented, cream-background inset block:

```
  ┌─────────────────────────────────┐
  │  HOMA-IR               2.8      │
  │  Borderline elevated (≥2.5)     │
  └─────────────────────────────────┘
```

These update live as values are typed. They are the bridge between raw numbers and clinical interpretation — showing the clinician that the system is already working.

### 3.5 The Analyse Button

At the bottom of the form, a single full-width button:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         LOCATE METABOLIC STATE →
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

The word "LOCATE" is deliberate. It invokes the map metaphor before the map appears. The button is not "Analyse" or "Submit" or "Run Model." It locates the patient. That verb primes the user for what they are about to see.

Button state progression:
1. Inactive (grey) while required fields are empty
2. Active (deep navy fill, white text) when all required fields are populated
3. Loading (navy with a subtle left-to-right shimmer) during inference (expected <500ms)
4. Complete (triggers the Phase 2 transition)

---

## Part 4 — The Transition: Opening the Map

This animation is the single most important moment in the entire interface. It is the moment the abstract becomes visual. It must be designed with deliberate care.

**Duration:** 1,200ms total

**Sequence:**
1. **0–200ms:** The form fades to 0% opacity smoothly
2. **200–500ms:** The background transitions from white to near-black (`#050810`) — not a flash, a slow inkwell fill from the center outward
3. **500–800ms:** The metabolic map fades in, initially showing only the four territory backgrounds and the population scatter — the full landscape before the patient's location appears
4. **800–1,000ms:** The patient's location pin drops from above onto their exact coordinate, with a brief elastic bounce (drops 20px past target, springs back 5px, settles). This is the moment of placement.
5. **1,000–1,200ms:** The phenotype banner slides in from the top, the readout panels slide in from right, the counterfactual arrow draws itself (if applicable)

**Why this specific sequence matters:** The map appears before the patient's location. The user first sees the landscape — the four territories, the population cloud, the safe zone. Then the pin drops into it. This sequence teaches the user the map before showing them the result, which means they can immediately interpret the result with context.

---

## Part 5 — Phase 2: The Map Experience

### 5.1 Overall Layout

Phase 2 is a dark full-screen layout with a very different structure from the current three-column design:

```
┌─────────────────────────────────────────────────────────────────────┐
│  PHENOTYPE BANNER — full width, 72px, bold colored background       │
├──────────────────────────────────────────┬──────────────────────────┤
│                                          │                          │
│                                          │  RIGHT PANEL             │
│           THE MAP                        │  (320px fixed)           │
│           (flex-grow, square aspect)     │                          │
│                                          │  · Location card         │
│                                          │  · Safety gauge          │
│                                          │  · Confidence ring       │
│                                          │  · Top interventions     │
│                                          │                          │
├──────────────────────────────────────────┴──────────────────────────┤
│  BOTTOM BAR — Re-enter values | Export Report | Model info (32px)   │
└─────────────────────────────────────────────────────────────────────┘
```

The map gets the majority of the space because it is the primary communication. The right panel provides interpretation. Nothing is buried.

### 5.2 The Phenotype Banner

The top 72px of the screen is a full-width color banner. It is the loudest, most immediate element in the interface. A clinician glancing at the screen for one second should see only this.

**Dual-Burden state:**
```
██████████████████████████████████████████████████████████████████████
██  ⬤  DUAL-BURDEN PHENOTYPE  ·  Thin-Fat / MUHNW  ·  Highest Risk  ██
██████████████████████████████████████████████████████████████████████
```
Background: `#e8394a` at 90% opacity. Text: white, bold, centered. The filled dot (⬤) pulses at 2s intervals — the only animation on the banner.

**Metabolically Healthy state:**
```
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░  ✓  METABOLICALLY HEALTHY  ·  Normal IR and Liver Function          ░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
```
Background: `#00c47d` at 80% opacity. No pulse. Calm.

The four phenotype banners have four distinct colors that are impossible to confuse with each other. The phenotype name is the largest text anywhere on the screen. The clinical description is eight words maximum.

### 5.3 The Map Itself

The map is a square SVG canvas that fills the available center space. It has five layers rendered back to front.

---

**LAYER 1: The Territory Backgrounds**

The four quadrants are not defined by thin axis lines. They are territories — distinct regions with their own visual character.

Each territory uses a radial gradient that originates at its outer corner and fades toward the center. The gradient starts at 15% opacity of the territory color and ends at 0% opacity at the center axis. This creates a sense that risk accumulates in the corners — which is biologically accurate.

The territory names are written directly onto the map in large, low-opacity text (8–10% opacity), like text on a real geographic map:

```
                 FATTY LIVER RISK          DUAL BURDEN ZONE
                 [cobalt watermark]         [crimson watermark]
                                   ┼
                 METABOLICALLY              INSULIN RESISTANT
                 HEALTHY                    [amber watermark]
                 [teal watermark]
```

These background territory labels are not interactive. They are atmospheric — communicating the map metaphor at a glance.

---

**LAYER 2: The Terrain Contours**

The population density of NHANES normal-BMI training data, rendered as topographic contour lines — exactly like elevation contours on a map. Three contours at the 40th, 60th, and 80th density percentile.

- Style: Very thin lines (0.5px), white at 6% opacity
- The contours cluster near the center-left (Metabolically Healthy territory), confirming that most normal-BMI adults are there
- A patient whose pin lands outside the outermost contour is in genuinely unusual metabolic territory — visible immediately

This layer is crucial. It makes the map feel inhabited and real, not abstract.

---

**LAYER 3: The Grid and Axes**

- Thin grey grid lines at regular intervals (5% opacity) — the coordinate paper beneath the map
- The two threshold lines (Z₁ = τ₁ and Z₂ = τ₂) that define the quadrant borders, in gold at 40% opacity
- Axis labels at the edges: "INSULIN RESISTANCE →" along the bottom, "LIVER FAT ↑" along the left
- The axis labels use clinical terms, not Z₁ and Z₂. Z₁ and Z₂ are never shown on the map itself. They appear only in the optional technical readout in the right panel.

---

**LAYER 4: The Population Sample**

300–400 dots representing the NHANES training cohort. These are the permanent, non-moving reference population.

- Size: 3px radius, white at 5% opacity
- Each dot colored faintly by its own phenotype quadrant (teal, amber, cobalt, crimson at 4% opacity)
- Hover: A dot tooltip shows "NHANES participant: Insulin resistance [low/moderate/high], Liver fat [low/moderate/high]" — no raw coordinates shown

The dots form a visible cloud that clusters toward the healthy quadrant with a tail extending into the risk quadrants. This immediately communicates to the user: most normal-BMI people are in the healthy zone, but many are not. The patient's pin will land somewhere relative to this cloud.

---

**LAYER 5: The Patient Data**

Everything in this layer is animated and patient-specific.

**The Confidence Halo**

Before the location pin, a soft circular glow appears at the patient's coordinate — a radial gradient in the phenotype color that extends outward 30–40px, fading to zero. This is the conformal prediction ellipse, reframed visually as an "accuracy halo" — like the blue accuracy circle around your location on Google Maps.

The halo's size communicates confidence: tight halo = high confidence, wide halo = lower confidence. No numbers are needed. The geometry does the work.

If the conformal ellipse is notably asymmetric (more uncertainty on one axis), the halo becomes an ellipse rather than a circle, oriented accordingly.

**The Location Pin**

A location pin (the standard geographic marker shape — circle with a pointed bottom) in white, 24px tall, 16px wide at the widest point.

The pin is outlined in the phenotype color with a 2px stroke. The phenotype color fills the inner circle of the pin head.

The pin casts a subtle drop shadow beneath it — the shadow is in the phenotype color at 40% opacity, giving the pin a colored "ambient light" effect that makes the entire map glow faintly in the phenotype color at the patient's location.

**The Crosshair Extension**

From the pin, two very thin dashed lines extend to both axes — allowing precise reading of the coordinate values against the grid. The lines are white at 20% opacity. They are only visible when the user hovers near the pin.

**The Counterfactual Route**

When the patient is in any risk quadrant, a route is drawn from the pin to the nearest point in the Metabolically Healthy territory.

This is not an arrow. It is a route — with the visual language of a GPS navigation line:

- A thick blue-teal path (3px, `#00c47d`) with a slight glow
- The path is a bezier curve, not a straight line — it navigates around the threshold lines naturally
- The path is animated: the color pulses forward along its direction (CSS dash-offset animation, 2s cycle), appearing to flow toward the safe zone
- At the destination, a glowing circle marks the target location with the label "Safe Zone"
- Along the path, 1–3 waypoints are marked with small diamond markers, each labeled with the primary biomarker change at that step: "↓ TG 42 mg/dL", "↓ GGT 18 U/L"

The waypoints are the counterfactuals, made geographic. Instead of "change these values," the route says "travel this path." The waypoints are the stops along the route that tell you what changes as you travel.

**The Distance Indicator**

At the midpoint of the route, a small callout shows the distance to safety in human terms — not raw latent units, but a severity framing:

```
◆ 2.1 units from safe zone
  Moderate intervention required
```

The severity framing maps latent distance to one of four clinical phrases:
- < 0.5 units: "On the boundary — minor adjustment sufficient"
- 0.5–1.5: "Mild intervention recommended"
- 1.5–3.0: "Moderate intervention required"
- > 3.0: "Significant metabolic burden"

---

### 5.4 The Right Panel

The right panel has four stacked sections separated by hairline rules. They are ordered by what the user needs first.

---

**Section 1: Location Card (top)**

```
┌─────────────────────────────────────┐
│  YOUR METABOLIC LOCATION            │
│                                     │
│  Insulin Resistance     ▓▓▓▓▓░░  68th percentile │
│  Liver Fat Risk         ▓▓▓▓▓▓░  74th percentile │
│                                     │
│  Predicted HOMA-IR          3.2     │
│  Predicted Liver Fat    261 dB/m    │
│  (Mild steatosis — S1 grade)        │
└─────────────────────────────────────┘
```

The percentile bars immediately communicate the patient's position relative to other normal-BMI adults. A clinician understands "74th percentile for liver fat" instantly without knowing what Z₂ is.

The predicted HOMA-IR and CAP values are shown below the bars in clinical units. These are the model's outputs translated from latent coordinates into the language clinicians use.

---

**Section 2: Safety Gauge**

A single large visual element — a semicircular gauge, like a speedometer:

```
         Safe      Caution    Danger
          │           │          │
     ○────────────────●──────────○
    0.0                         1.0
              Risk Score: 0.71
         [  0.58  ──────  0.83  ]
          90% confidence range
```

The gauge needle points to the current risk score. The 90% conformal interval is shown as a colored arc segment on the gauge — not as numbers alone. The arc width communicates interval width visually.

The gauge is divided into three colored zones matching the arc:
- Green (0–0.40): Safe
- Amber (0.40–0.65): Caution
- Red (0.65–1.0): Danger

The needle is in white, pointing into the appropriate zone. The arc segment representing the confidence interval spans from the lower to upper bound of the conformal interval, showing the range of possible positions.

---

**Section 3: Intervention Targets**

```
┌─────────────────────────────────────┐
│  TO REACH SAFETY — top levers:      │
│                                     │
│  1. Triglycerides   ↓ 42 mg/dL     │
│     ▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░  current    │
│     ░░░░░░░░░░░░░░░░░░░  target     │
│                                     │
│  2. GGT             ↓ 18 U/L       │
│     ▓▓▓▓▓▓▓░░░░░░░░░░░  current    │
│     ░░░░░░░░░░░░░░░░░░░  target     │
│                                     │
│  3. Fasting Insulin ↓ 4 μIU/mL     │
└─────────────────────────────────────┘
```

Two horizontal bars for each intervention: the current value and the target value, both shown proportionally on the same scale. The visual distance between the two bars communicates the magnitude of change needed.

**Critically:** The system does not say "tell the patient to reduce triglycerides." It says "reducing triglycerides by 42 mg/dL would move this patient into the safe zone, based on our model." The phrasing is always in the third person, quantitative, and framed as a model finding rather than a clinical prescription.

---

**Section 4: Model Confidence**

A compact block at the bottom of the right panel:

```
┌─────────────────────────────────────┐
│  MODEL CONFIDENCE                   │
│  Within training range     ✓        │
│  Calibration stratum   Dual-Burden  │
│  Coverage guarantee          90%    │
│  Similar patients in data     219   │
└─────────────────────────────────────┘
```

If the patient's biomarker pattern falls outside the 95th percentile convex hull of the training data, the "Within training range" line shows a warning icon instead of ✓, with the message "Extrapolation — confidence lower." This is the distribution shift warning, made visible but not alarming.

---

### 5.5 The Bottom Bar

A 40px bar at the very bottom of Phase 2:

```
← Re-enter values     |     Export Clinical Report     |     Model: DA-SS-iVAE v2.0 · NHANES 2017-18 · n=4,871
```

Three elements:
- **Re-enter values:** Returns to Phase 1 with all current values pre-populated for editing
- **Export Clinical Report:** Generates a clean single-page PDF: map screenshot, phenotype, key numbers, intervention targets, model metadata
- **Model info:** Always visible, always attributed — who built it, what it was trained on, how many patients

---

## Part 6 — The Export: Clinical Report PDF

When the clinician clicks "Export Clinical Report," a clean single-page PDF is generated with the following layout:

**Header:** System name, date, time, patient ID (if entered)

**Left half:** A cropped version of the map at the patient's location — showing the location pin, the confidence halo, the territory the patient is in, and the route to safety (if applicable). Labeled with territory names and axis labels.

**Right half:**
- Phenotype: Large, colored
- One sentence clinical description
- Predicted HOMA-IR with reference range
- Predicted Liver Fat (CAP) with steatosis grade
- Risk score with 90% interval
- Top 3 intervention targets with magnitudes

**Footer:** *"This report was generated by the Latent Metabolic State Inference System (LMSIS), a research system trained on NHANES 2017–2018 data. Results are based on a validated deep learning model (Spearman ρ=0.58 for liver fat recovery) and should be interpreted by a qualified clinician. This is not a substitute for clinical imaging or specialist evaluation."*

The disclaimer exists not to undermine the system but to position it correctly. A clinical report with a clear disclaimer is more trustworthy than one without — it signals scientific honesty.

---

## Part 7 — Research Mode (Toggle)

A small "Research View" toggle in the bottom bar switches between the default Clinical mode and a Research mode. In Research mode, additional layers appear:

**On the map:**
- Z₁ and Z₂ coordinate values shown at the pin (3 decimal places)
- Population scatter dots colored by actual phenotype quadrant
- Full ellipse boundaries for all four quadrant regions

**In the right panel:**
- Raw Z₁, Z₂ coordinates with population percentile
- Reconstruction loss for this patient ("Recon MSE: 0.087")
- KL divergence from prior
- Conformal calibration detail: stratum, n, achieved coverage

**Why keep it separate:** Clinicians need none of this. Researchers and examiners need all of it. One interface serves both audiences by layering — simple on top, technical underneath.

---

## Part 8 — Typography System

**Display / Phenotype names:** Clash Display (Variable) or DM Serif Display
- Large, authoritative, personality
- Used ONLY for the phenotype name in the banner and the section headings

**Data readouts:** JetBrains Mono (400, 500)
- All numbers: coordinates, HOMA-IR, CAP, risk score, percentiles
- The monospace grid makes columns of numbers align precisely
- Communicates measurement, not decoration

**Body / Clinical text:** Instrument Sans (400, 500, 600)
- All labels, descriptions, axis names, clinical interpretations
- Humanist sans-serif — technical but readable
- Not Inter (too generic). Not Roboto (too Android). Instrument Sans reads like a medical journal.

**Map territory labels:** Same display font at very large size, very low opacity
- Creates the "printed on the map" geographic effect

---

## Part 9 — Motion Principles

Every animation in the system follows two rules:

**Rule 1:** Animation communicates information, not decoration. The location pin drops to show placement. The route flows toward safety to show direction. The confidence halo breathes to show it is live data. If removing an animation would make the system equally understandable, the animation is removed.

**Rule 2:** Clinical contexts require restrained motion. Nothing flashes. Nothing spins. Easing is always ease-out or ease-in-out — never elastic except for the pin drop, which uses a single subtle bounce to communicate physical placement. The Dual-Burden banner pulses at 2 second intervals — slow enough to be noticeable without being alarming.

**Key animations and their timings:**

| Animation | Duration | Easing | Purpose |
|---|---|---|---|
| Phase 1→2 transition | 1,200ms | Custom (see Part 4) | The diagnostic moment |
| Pin drop | 400ms | Ease-out + single bounce | Physical placement |
| Route draw | 800ms | Ease-in-out | Journey, not teleportation |
| Right panel slide-in | 300ms | Ease-out | Interpretation arrives after location |
| Banner slide-down | 200ms | Ease-out | Phenotype revealed after position |
| Halo breathe | 3,000ms cycle | Sine | Live data is active data |
| Gauge needle move | 500ms | Ease-out | Score settling |
| Phase 2→1 (Re-enter) | 400ms | Ease-in-out | Calm return |

---

## Part 10 — Color System Refined

The map metaphor requires slightly different colors than the dashboard specification. These are the final semantic colors for Phase 2:

| Token | Value | Used for |
|---|---|---|
| `--bg-void` | `#050810` | Canvas, outer background |
| `--bg-panel` | `#0c111e` | Right panel, bottom bar |
| `--border` | `#1c2940` | Panel edges, hairlines |
| `--territory-safe` | `#00c47d` | MHNW territory, route color |
| `--territory-ir` | `#f5a623` | IR-dominant territory |
| `--territory-steatosis` | `#3d8ef8` | Steatosis territory |
| `--territory-dual` | `#e8394a` | Dual-burden territory |
| `--text-primary` | `#eef2ff` | Main readable text |
| `--text-muted` | `#4a6380` | Labels, reference text |
| `--gold-threshold` | `#c8a84b` | Quadrant threshold lines |
| `--white-data` | `#ffffff` | Location pin, crosshair |

**Phase 1 (Input) colors:**
| Token | Value | Used for |
|---|---|---|
| `--input-bg` | `#fafaf8` | Warm white background |
| `--input-text` | `#1a1a1a` | Form text |
| `--input-border` | `#d4d0c8` | Field borders |
| `--input-elevated` | `#f5a623` | Above normal range indicator |
| `--input-high` | `#e8394a` | Significantly elevated indicator |
| `--button-active` | `#0c111e` | Analyse button |

---

## Part 11 — What This Redesign Argues to an Examiner

An examiner who interacts with this system for three minutes will understand, without reading the dissertation:

1. **The clinical problem** — the form asks for routine blood values, not a FibroScan. The implicit message is: expensive imaging is not needed.
2. **The approach** — the transition to a 2D map communicates that the system places patients in a geometric space, not a risk category.
3. **The novelty** — two axes, not one. The map has X (insulin resistance) and Y (liver fat). No other system shows these simultaneously.
4. **The validation** — the right panel shows "Predicted Liver Fat: 261 dB/m" in FibroScan units that a clinician recognizes. The model is anchored to reality.
5. **The safety** — the confidence range on the gauge is always visible. The system never pretends to be more certain than it is.
6. **The actionability** — the route shows where to go. The waypoints tell you how to get there.
7. **The honesty** — the disclaimer on the export, the "within training range" indicator, the model attribution in the bottom bar.

A frontend that communicates all seven of these silently, through its visual language and structure, is a frontend that fully justifies the research behind it. The science does not need to be explained because the design explains it.

---

## Part 12 — What Changes from the Current Frontend to This One

| Current | Redesigned |
|---|---|
| All 14 sliders always visible | Two-phase: form first, map second |
| Z₁ and Z₂ labeled as coordinates | Axes labeled "Insulin Resistance" and "Liver Fat" |
| Conformal ellipse as abstract shape | Confidence halo as accuracy radius |
| Counterfactual as arrow | Counterfactual as GPS route with waypoints |
| Phenotype in right panel sidebar | Phenotype as full-width banner — first thing seen |
| Risk score as number | Risk score as gauge with colored zones |
| Three equal columns always visible | Map gets primary space, panels support it |
| Everything on one screen | Progressive disclosure: locate, then understand |
| Requires understanding of latent spaces | Requires only understanding of maps |
| One mode | Clinical mode + Research mode toggle |
| No export | Clinical report PDF |

None of the underlying model changes. Only how it is revealed.

---

*End of Document*
