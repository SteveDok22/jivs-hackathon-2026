# AEGIS — Design System

The single source of truth for the AEGIS frontend look and feel. Every
component reads from these tokens (`src/styles.scss`); nothing hardcodes a
colour or font. Change it here, it changes everywhere.

**Product:** AEGIS — Trusted Enterprise AI, built for secure organizations.
(Under the hood: the Trusted Enterprise Agent — a secured AI agent over
cleansed enterprise data.)

---

## 1. Concept

The name is the Greek *aegis* — the shield of Zeus. The whole visual language
says **protection over live data**: a red data-network that pulses and scans,
guarded by clean white outlines. Not decorative red-on-black — the red *is*
the data and the threats, the white *is* the verified/safe state. Colour
carries meaning, it is not just style.

Audience is broad (not only engineers), so: striking first impression, but
every section must be understandable in one read. Wow through motion and
clarity, never through jargon.

---

## 2. Colour

Dark base, red as the signal colour, neon white for outlines and truth.
Deliberately not monotone black-and-red — white glow and graded reds keep it
alive.

| Token            | Hex        | Use                                              |
|------------------|------------|--------------------------------------------------|
| `--bg`           | `#0a0a0c`  | Page background, near-black with a cool tint     |
| `--bg-raised`    | `#121216`  | Cards, panels                                    |
| `--bg-elevated`  | `#1a1a20`  | Raised elements, code blocks                     |
| `--line`         | `#26262e`  | Borders, dividers                                |
| `--red`          | `#e5322d`  | Primary accent — the signal colour               |
| `--red-deep`     | `#7a1518`  | Gradient partner, darker red for depth           |
| `--red-glow`     | `#ff4d4d`  | Glows, hover, active network nodes               |
| `--white`        | `#ffffff`  | Key numbers, outlines, primary text highlights   |
| `--white-neon`   | `#f5f5ff`  | Neon outline glow (with box-shadow)              |
| `--text`         | `#e8e8ec`  | Body text                                        |
| `--text-dim`     | `#8a8a94`  | Secondary text, labels                           |
| `--verified`     | `#3fb950`  | Safe / passed states (kept from core semantics)  |
| `--amber`        | `#d29922`  | Redacted / caution states                        |

**Meaning mapping (never break this):**
- Red = data, threats, the thing being watched.
- White = verified, safe, trusted output.
- Green = a passed check. Amber = redacted. These stay rare and semantic.

**Signature gradient:** `--red-deep -> --red` on a black base, used behind the
hero title and CTA buttons.

**Neon-outline recipe:** a 1px `--white` border + `box-shadow: 0 0 12px
rgba(255,255,255,0.25)` gives the "outlined, glowing" look on key elements
without turning the page into neon soup. Use sparingly — hero title, primary
CTA, active nav, key metric values.

---

## 3. Typography

Three faces, three jobs. Loaded from Google Fonts.

- **Space Grotesk** — headings and the hero. Modern grotesk with technical
  character; carries the "wow". Weights 500/700.
- **Inter** — body text and UI. Clean, highly readable — matters for the broad
  audience. Weights 400/600.
- **JetBrains Mono** — numbers, metrics, SQL, citations, code. Reinforces the
  security/engineering credibility. Weights 400/600.

Scale (fluid, clamp-based so it breathes across screens):

| Token           | clamp                                   | Use              |
|-----------------|-----------------------------------------|------------------|
| `--fs-hero`     | `clamp(2.75rem, 6vw, 5.5rem)`           | Hero title       |
| `--fs-h1`       | `clamp(2rem, 4vw, 3rem)`                | Section titles   |
| `--fs-h2`       | `clamp(1.4rem, 2.5vw, 2rem)`            | Sub-sections     |
| `--fs-body`     | `1.05rem`                               | Body             |
| `--fs-small`    | `0.85rem`                               | Labels, captions |

Headings: Space Grotesk, letter-spacing `-0.02em` (tight, modern).
Labels/eyebrows: JetBrains Mono, uppercase, letter-spacing `0.08em`.

---

## 4. Spacing & layout

8px base grid. Tokens: `--space-1: 8px` up to `--space-12: 96px`.
Content max-width: `1200px`. Reading max-width (prose): `680px`.
Section vertical rhythm: `--space-12` (96px) between major sections.
Radius: `--radius: 12px` (cards), `--radius-lg: 20px` (feature panels),
`--radius-pill: 999px` (badges, buttons).

---

## 5. Motion

Balance over spectacle (agreed): a real wow moment, but it must stay smooth on
a mid laptop and respect `prefers-reduced-motion`.

- **Easing:** `--ease: cubic-bezier(0.22, 1, 0.36, 1)` (soft, decelerating).
- **Durations:** micro 150ms, standard 300ms, entrance 600ms.
- **Scroll reveals:** sections fade + rise 16px as they enter the viewport,
  staggered by ~80ms per child.
- **Counters:** numbers count up from 0 when their section is first seen.
- **The network background:** red plexus of nodes, links drawn when near,
  cursor repels/attracts nodes, a "scan" pulse travels through periodically —
  tying the motion to the product's meaning (scanning data).
- **Reduced motion:** all of the above collapse to instant/opacity-only. The
  network freezes to a static field. Nothing essential depends on motion.

**Performance guardrails:** the network caps its node count and pauses when the
tab is hidden or the hero is scrolled out of view. Target 60fps; degrade node
count on small screens.

---

## 6. Components (visual contract)

- **Buttons.** Primary: red gradient fill, white text, subtle glow on hover.
  Secondary: transparent, white 1px outline, fills on hover. Pill radius.
- **Cards.** `--bg-raised`, 1px `--line` border, 20px radius; on hover the
  border shifts toward `--red` and a faint red glow appears.
- **Badges.** Pill, mono uppercase, semantic colour (verified/amber/red).
- **Nav (Line Sidebar).** Fixed vertical rail; a white line indicator slides to
  the active section as you scroll. Solid, enterprise, not playful.
- **Custom cursor.** A small ring that softly magnetises to buttons and links.
  Restrained — enterprise, not a toy. Hidden on touch devices.
- **Metric value.** JetBrains Mono, large, white with faint neon outline; the
  label above it is dim mono uppercase.

---

## 7. Pages

- **`/` Homepage** (broad audience, understandable + visual):
  Hero (title + live 5-layer animation + live demo field + network bg)
  -> Problem -> How it works (5 layers) -> Metrics (count-up) -> Tech -> CTA.
  Line Sidebar tracks scroll. Grid-scan effect in the hero.
- **`/app` Product** (the working tool):
  the chat + metrics we already built, on the network background, themed to
  AEGIS. This is where the real agent lives.

---

## 8. Accessibility

- Contrast: body text `--text` on `--bg` exceeds WCAG AA. Red is an accent,
  never the only carrier of meaning (icons/labels accompany it).
- Focus: visible white focus ring on all interactive elements.
- Motion: full `prefers-reduced-motion` support (section 5).
- The custom cursor never replaces the real one on keyboard/touch.
