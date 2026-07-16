# Design and motion refresh - TDD evidence

## Source

Journeys and acceptance criteria were derived from the visual review of the 21 UX snapshots on 2026-07-13.

## User journeys

- As a user, I open Ajustes immediately and its data completes in the background.
- As a user, I read financial and macro charts with a restrained, coherent palette.
- As a light-theme user, I see warm off-white surfaces rather than pure white cards.
- As a user sensitive to bright screens, I see a genuinely grey light theme and a warm financial chart palette without blue, green or violet.
- As a user, I read every positive and negative financial state with the same jade and cassis semantic colors, in both themes.
- As a user, I can open a core module for the first time without waiting for its route bundle during the click.

- As a user, I can read complete financial figures without truncation.
- As a user, I see a focused primary navigation with only the five core sections.
- As a user, I see safe, actionable errors instead of internal API or mock details.
- As a user, legacy links preserve the intended Planning or Import state.
- As a motion-sensitive user, assistant scrolling and progress transitions respect reduced-motion preferences.
- As a user, the Europe market view is visibly different from the global market view.
- As a user, the Assistant explains its value before asking me to generate or start a conversation.
- As a user, empty states avoid duplicated primary actions.
- As a motion-sensitive user, press feedback remains subtle and is removed when reduced motion is enabled.
- As a user, I receive the same tactile feedback on frequent actions in Cuentas, Mercados, Economía y Ajustes.

## RED / GREEN evidence

| Behaviour | RED evidence | GREEN evidence |
| --- | --- | --- |
| Navigation, figures, safe errors and motion contracts | `npm run test:ui-quality` failed on `Objetivos debe ser accesible desde la navegacion principal` | `npm run test:ui-quality` -> `UI quality contracts: PASS` |
| Legacy URL state, Planning mock data and net-worth consistency | `npm run test:ui-quality` failed on `Las rutas antiguas deben conservar su estado al redirigir` | `npm run test:ui-quality` -> `UI quality contracts: PASS` |
| Europe market state | `npm run test:ui-quality` failed on `Mercados debe reflejar el filtro regional de la URL` | `npm run test:ui-quality` -> `UI quality contracts: PASS` |
| Phase 2 navigation and assistant hierarchy | `npm run test:ui-quality` failed on `La navegacion principal debe conservar solo cinco secciones` (`7 !== 5`) | `npm run test:ui-quality` -> `UI quality contracts: PASS` |
| Phase 3 shared press feedback | `npm run test:ui-quality` failed on `AccountsPage debe usar el feedback tactil comun en sus controles` | `npm run test:ui-quality` -> `UI quality contracts: PASS` |
| Phase 4 performance and visual palette | `npm run test:ui-quality` failed on `Las pantallas de producto deben cargarse bajo demanda` | `npm run test:ui-quality` -> `UI quality contracts: PASS` |
| Palette refinement after visual review | `npm run test:ui-quality` failed on `La paleta financiera debe usar un oro apagado para ingresos` | `npm run test:ui-quality` -> `UI quality contracts: PASS` |
| Global jade/cassis standardization | `npm run test:ui-quality` failed on `La paleta financiera debe usar el verde jade para ingresos` | `npm run test:ui-quality` -> `UI quality contracts: PASS` |
| First navigation route warming | `npm run test:ui-quality` failed because `pageLoaders.ts` did not exist | `npm run test:ui-quality` -> `UI quality contracts: PASS` |

## Test specification

| # | What is guaranteed | Test or command | Type | Result |
| --- | --- | --- | --- | --- |
| 1 | Primary navigation contains exactly five sections and excludes Goals and Insights | `test-ui-quality-contracts.ts` | UI contract | PASS |
| 2 | KPI and account metric values do not use truncation | `test-ui-quality-contracts.ts` | UI contract | PASS |
| 3 | Internal error details are sanitized | `test-ui-quality-contracts.ts` | UI contract | PASS |
| 4 | Progress bars avoid `transition-all` and layout-width animation | `test-ui-quality-contracts.ts` | UI contract | PASS |
| 5 | Assistant scrolling checks `prefers-reduced-motion` | `test-ui-quality-contracts.ts` | Accessibility contract | PASS |
| 6 | Planning and Import legacy URLs preserve nested state | `test-ui-quality-contracts.ts` | Routing contract | PASS |
| 7 | Dashboard and balance mock net worth agree | `test-ui-quality-contracts.ts` | Data contract | PASS |
| 8 | Europe market capture activates a regional filter | `test-ui-quality-contracts.ts` | Routing/UI contract | PASS |
| 9 | Existing flow catalog remains valid | `npm run test:flows` | Integration contract | PASS (33 flows) |
| 10 | Existing negative-flow catalog remains valid | `npm run test:negative-flows` | Negative contract | PASS (15 cases) |
| 11 | Desktop TypeScript and production bundle compile | `npm run build` in `apps/desktop` | Build | PASS |
| 12 | Updated principal states render successfully | `npm run snapshots` and targeted market capture | Visual E2E | PASS (21/21 + Europe review) |
| 13 | Assistant uses the shared page alignment, guided empty state and direct Chat continuation | `test-ui-quality-contracts.ts` | UI contract | PASS |
| 14 | Goals avoids a duplicate primary CTA in its empty state | `test-ui-quality-contracts.ts` | UI contract | PASS |
| 15 | Shared press feedback is transform-only and respects reduced motion | `test-ui-quality-contracts.ts` | Motion/accessibility contract | PASS |
| 16 | Frequent actions and tab controls in Accounts, Markets, Economy and Settings use the shared press feedback without `transition-all` | `test-ui-quality-contracts.ts` | Motion/accessibility contract | PASS |
| 17 | Product screens load on demand and heavy vendors are split from the initial bundle | `test-ui-quality-contracts.ts`, `npm run build` | Performance contract | PASS |
| 18 | Spending uses dedicated violet, terracotta and neutral chart colors | `test-ui-quality-contracts.ts` | Visual contract | PASS |
| 19 | Economy shares semantic violet and terracotta tokens instead of arbitrary status colors | `test-ui-quality-contracts.ts` | Visual contract | PASS |
| 20 | Settings renders without a blocking spinner and the light theme uses warm off-white cards | `test-ui-quality-contracts.ts`, snapshots | Performance/visual contract | PASS |
| 21 | Financial chart uses muted gold, burgundy and sand; the light cards use a soft grey surface | `test-ui-quality-contracts.ts`, snapshots | Visual contract | PASS |
| 22 | Positive and negative states share jade and cassis tokens across financial charts, market performance, economy and status feedback | `test-ui-quality-contracts.ts`, snapshots | Visual contract | PASS |
| 23 | Core routes preload during browser idle time and when a navigation item receives pointer, focus or press intent | `test-ui-quality-contracts.ts`, `npm run build` | Performance contract | PASS |

## Coverage and known gaps

The latest production build now splits routes and heavy vendors; the largest generated vendor chunk is 407 kB (118 kB gzip), below the previous monolithic entry bundle.

The desktop package does not declare a unit-test coverage runner, so a numeric 80% statement cannot be produced without adding a new testing stack. The repository's existing Playwright snapshot harness, flow contracts, negative-flow contracts, TypeScript build and manual image review were used instead. The build retains its pre-existing warning that the main JavaScript chunk exceeds 500 kB.

## Merge evidence

No checkpoint commits were created because the worktree already contained unrelated user changes. RED/GREEN evidence is preserved in this report without staging or rewriting those changes.
