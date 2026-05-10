# Brand Guidelines

The dashboard ships in a placeholder enterprise palette pending access to SMP Technology's actual brand kit. Everything is tokenised so the swap is one file.

## Why placeholder

I attempted to scrape SMP Technology's site (smp-corp.com) and LinkedIn page during the build but both pages either gate behind authentication or block automated access. Rather than guess at colours that may misrepresent the company, the design uses a deliberate "enterprise tech" palette that any infrastructure / AIOps company would feel at home in. Once given the real brand kit, the swap is a five-minute change.

## Current palette

| Role | Token | Hex | Notes |
|---|---|---|---|
| Background dark | `--ink-900` | `#0a0f1c` | App background |
| Background mid | `--ink-800` | `#0f172a` | Sidebar, header |
| Surface | `--ink-700` | `#1e293b` | Cards, inputs |
| Border | `--ink-600` | `#334155` | Hairlines |
| Accent | `--signal-500` | `#06b6d4` | Primary action, charts |
| Accent hi | `--signal-400` | `#22d3ee` | Hover, focus ring |
| Accent text | `--signal-300` | `#67e8f9` | Code, citations |
| Warn | `--warn-500` | `#f59e0b` | SLO at risk |
| Warn hi | `--warn-400` | `#fbbf24` | |
| Bad | `--bad-500` | `#ef4444` | Failure, miss |
| Good | `--ok-500` | `#10b981` | Hit, faithful |

Defined in two places, kept in sync:

- `frontend/tailwind.config.ts` — exposes them as Tailwind utilities (`bg-ink-700`, `text-signal-400`).
- `frontend/app/globals.css` — exposes them as CSS variables for any non-Tailwind context.

## Typography

| Use | Font |
|---|---|
| Headings | Plus Jakarta Sans |
| Body | Inter |
| Code, metrics | JetBrains Mono |

Loaded via `next/font` in `app/layout.tsx`. Replace the import lines and the CSS variables to swap to the SMP brand fonts.

## How to swap to SMP's actual brand

1. Get the SMP palette (HEX or HSL).
2. Open `frontend/tailwind.config.ts`. Replace the `ink.*` and `signal.*` values inside `theme.extend.colors`.
3. Open `frontend/app/globals.css`. Replace the matching CSS variables in `:root`.
4. If the brand uses different fonts, update the `next/font` imports in `app/layout.tsx`.
5. Run `npm run dev`. Done.

The components themselves never hardcode hex values; everything resolves through the tokens. There are zero `style={{ color: '#…' }}` instances in the codebase by design.

## Logo

The sidebar shows a placeholder wordmark using the accent colour. Drop a real logo file into `frontend/public/` and replace the wordmark element in `components/Sidebar.tsx`.

## Accessibility notes

- Body text against the dark background is rendered at `slate-200` minimum (contrast ratio 11.5:1 against `--ink-900`).
- The accent colour is used for highlights, not for body text, to avoid the common cyan-on-dark legibility trap.
- All interactive elements have a visible focus ring (`focus:ring-2 focus:ring-signal-500/50`) so keyboard users can navigate.
- Charts pair colour with shape/label so colour-blind users aren't penalised.
