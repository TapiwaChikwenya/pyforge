# UI exploration (`feature/ui-exploration`)

Expert pass on the current SPA (`app/static/index.html`, `app.css`, `app.js`, `features.js`).

## Verdict

**Learning UX: strong. Visual / first-impression system: average.**

The product flows (path → project tabs → exercises → interview) are clear and
the new learning features (first hour, review, portfolio) are discoverable.
The look still reads as a generic dark admin dashboard with Segoe UI, dense
chips, and a long wall of project cards. That undercuts “DataForged” as a brand
and makes the first session feel heavier than it is.

## What works

- Path + stage labels communicate curriculum structure.
- Progress rings and sticky header % give orientation.
- Project tabs separate brief / build / code / theory / interview cleanly.
- CodeMirror + lint + Run & Check loop is the right core interaction.
- Onboarding CTA and stack-tier chips reduce infra intimidation.
- Mentor / community solutions appear in context after struggle or pass.

## Gaps (prioritized)

### High

1. **First viewport overload** — Hero + toolbar + onboard + 34 cards. Collapse
   later stages; lead with brand + one next action + “continue”.
2. **Typography** — System/Segoe stack; pick a distinctive display + mono pair.
3. **Exercise focus mode** — Lesson chrome buries the editor; default to editor
   + run, with refresher/objectives collapsed.
4. **Mobile** — 3-column project cards and editor height need breakpoints.

### Medium

5. **Resume affordance** — Persist last project/exercise beyond first-hour.
6. **Toolbar hierarchy** — “Friction report” is an operator tool; demote it.
7. **Accessibility** — Tabs/cards are clickable `div`s; add roles, keyboard,
   focus-visible, `prefers-reduced-motion`.
8. **Motion** — Keep 2–3 intentional motions; tone down pass glow.
9. **Brand weight** — Logo/name should dominate the first paint, not the H2.

### Low

10. Emoji in chrome (hints/refresher) — optional trim for a sharper DE brand.
11. Empty/error states for review/portfolio/API failure.
12. Light theme — only if audience demands it; dark IDE feel is coherent.

## North-star composition (dashboard)

```
[ DataForged wordmark ]                    [ progress · account ]
[ Resume: Task Forge · tf-1  ▸ ]   or   [ Start first hour ▸ ]
[ Stage 1 preview — 4 projects ]
[ Show full path ▾ ]
```

Not: equal-weight tool row + every stage expanded.

## North-star composition (exercise)

```
[ title · status ]
[ editor .................. ] [ Run ]
[ result ]
[ ▸ Refresher  ▸ Hints  ▸ Mentor ]
```

## Proposed implementation slices on this branch

| Slice | Files | Outcome |
|-------|-------|---------|
| A | `app.css`, `app.js`, `features.js` | Dashboard first viewport + resume |
| B | `app.js`, `app.css` | Exercise focus / collapsible lesson |
| C | `app.css`, `index.html` | Fonts + chip diet + brand header |
| D | `app.css`, `app.js` | Mobile + a11y basics |

## Out of scope (for now)

- Rewriting to React/Vite (current SPA is fine until UX stabilizes).
- Marketing landing page separate from the learner app.
- Full design-system package.

## Implemented on this branch

| Slice | Status |
|-------|--------|
| A — Dashboard first viewport + resume | Done — brand lockup, Resume / First hour CTA, stages 2+ collapsed, Friction under More |
| B — Exercise focus mode | Done — lesson chrome in `<details>`; editor + Run first; mentor/solutions after result |
| C — Typography + brand | Done — Syne + IBM Plex Mono; brand-forward header; chip diet (2 tech chips on cards) |
| D — Mobile + a11y | Done — 720px breakpoint; tabs/cards keyboard + ARIA; `prefers-reduced-motion` |

## How to preview

```bash
docker compose up -d --build app
# http://localhost:8000
```

Sample path: open dashboard → resume or start first hour → Exercises tab → confirm editor is above the collapsed lesson panel.
