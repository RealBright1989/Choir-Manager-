---
name: Sovereign Admin
colors:
  surface: '#f9f9ff'
  surface-dim: '#cfdaf2'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f0f3ff'
  surface-container: '#e7eeff'
  surface-container-high: '#dee8ff'
  surface-container-highest: '#d8e3fb'
  on-surface: '#111c2d'
  on-surface-variant: '#434652'
  inverse-surface: '#263143'
  inverse-on-surface: '#ecf1ff'
  outline: '#747783'
  outline-variant: '#c4c6d3'
  surface-tint: '#345baf'
  primary: '#002868'
  on-primary: '#ffffff'
  primary-container: '#0a3d91'
  on-primary-container: '#8dadff'
  inverse-primary: '#b1c5ff'
  secondary: '#735c00'
  on-secondary: '#ffffff'
  secondary-container: '#fed65b'
  on-secondary-container: '#745c00'
  tertiary: '#521a00'
  on-tertiary: '#ffffff'
  tertiary-container: '#762900'
  on-tertiary-container: '#ff9162'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2ff'
  primary-fixed-dim: '#b1c5ff'
  on-primary-fixed: '#001947'
  on-primary-fixed-variant: '#144296'
  secondary-fixed: '#ffe088'
  secondary-fixed-dim: '#e9c349'
  on-secondary-fixed: '#241a00'
  on-secondary-fixed-variant: '#574500'
  tertiary-fixed: '#ffdbcd'
  tertiary-fixed-dim: '#ffb597'
  on-tertiary-fixed: '#360f00'
  on-tertiary-fixed-variant: '#7c2e04'
  background: '#f9f9ff'
  on-background: '#111c2d'
  surface-variant: '#d8e3fb'
typography:
  display-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 60px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.04em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  container-padding-desktop: 32px
  container-padding-mobile: 16px
  gutter: 24px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 24px
  section-gap: 48px
---

## Brand & Style
The design system is engineered for a high-stakes enterprise environment that balances administrative precision with a sense of spiritual leadership and excellence. The brand personality is authoritative yet approachable, reflecting "Sovereign Leadership" through a sophisticated digital interface.

The design style is **Corporate Modern with Glassmorphic Accents**. It utilizes a minimalist, high-end SaaS dashboard aesthetic. The core of the experience is grounded in a clean, card-based layout that uses subtle depth and translucency to organize complex data. The interface prioritizes clarity and focus, using white space as a structural tool to convey a sense of calm and order.

## Colors
The palette is rooted in a traditional "Royal" combination to evoke trust and institutional stability.
- **Primary (Royal Blue):** Used for navigation, primary actions, and brand signaling. It represents professionalism and administrative authority.
- **Secondary (Gold):** Reserved for highlights, special leadership statuses, or premium indicators. It should be used sparingly to maintain its impact.
- **Neutral (Dark Navy):** Applied to typography and iconography to ensure high legibility and a grounded feel.
- **Background (Light Gray):** A cool-toned off-white that reduces eye strain during long administrative sessions.
- **Semantic Colors:** Standardized for system feedback, ensuring immediate recognition of status changes and alerts.

## Typography
This design system utilizes a dual-font strategy to balance character with utility. 

**Plus Jakarta Sans** is used for headlines and display elements. Its slightly rounded, open terminals provide a modern, welcoming feel that softens the corporate nature of the Royal Blue palette. 

**Inter** is the workhorse for all body text, data points, and labels. It is chosen for its exceptional legibility in data-heavy environments. 

For accessibility, line heights are kept generous, and tracking is tightened slightly on large display text to maintain visual cohesion.

## Layout & Spacing
The layout follows a **Fixed-Fluid Hybrid Grid**. 
- **Desktop:** A 12-column grid with a maximum content width of 1440px. Gutters are fixed at 24px to ensure breathing room between complex data modules.
- **Sidebar:** A fixed-width collapsible sidebar (280px expanded, 80px collapsed) sits on the left, anchoring the navigation.
- **Mobile:** A single-column fluid layout with 16px side margins.

Spacing follows a strict 8px geometric scale. Components like statistics cards and data tables use internal padding of 24px to maintain a premium, spacious feel.

## Elevation & Depth
Elevation is managed through **Tonal Layering and Glassmorphism**.

1.  **Level 0 (Background):** Solid `#F5F7FA`.
2.  **Level 1 (Cards/Sidebar):** White background with a soft, diffused shadow (`0px 4px 20px rgba(10, 61, 145, 0.05)`).
3.  **Level 2 (Glassmorphic Overlays):** Used for login cards, modals, and dropdowns. These features use a semi-transparent white (`rgba(255, 255, 255, 0.8)`) with a `20px` backdrop-blur and a subtle `1px` white border to define edges against the background.

Shadows are never pure black; they are tinted with the Primary Royal Blue to maintain a cohesive, "spiritual" glow rather than a heavy, muddy appearance.

## Shapes
The shape language is **Rounded (0.5rem base)**. This moderate corner radius strikes the perfect balance between the precision of an administrative tool and the approachability of a modern SaaS product.

- **Standard Elements (Buttons, Inputs):** 8px (0.5rem).
- **Cards & Modals:** 16px (1rem).
- **Status Chips:** 100px (Pill-shaped) to distinguish them from interactive buttons.

## Components
### Data Tables
Tables should use a "Zebra-less" approach, using subtle 1px borders (`#E2E8F0`) only between rows. Headers are capitalized in `label-sm` with a light blue-gray background to distinguish the control area from the data.

### Statistics Cards
These use a white surface with a "Trend Indicator" in the bottom right corner (Success green or Danger red). Icons within these cards should be placed in a soft-tinted circular background (e.g., 10% opacity of the primary color).

### Buttons
- **Primary:** Solid Royal Blue with white text.
- **Secondary:** White background with a 1px Gold border and Gold text.
- **Ghost:** No background, Primary Blue text.

### Glassmorphic Login Card
The login container should feature a high backdrop-blur (`32px`) and a subtle gradient stroke. This creates a "High-End Admin" entry point that feels secure and premium.

### Advanced Filters
Filters should be housed in a horizontal bar above data tables, utilizing "Input Groups" that combine an icon, a label, and a dropdown chevron for a compact, efficient search experience.

### Sidebar
The sidebar uses a Dark Navy (`#1E293B`) background with active states highlighted by a Gold left-border stripe (4px) and a subtle blue-tinted background wash.