# Cloud Field Theme: Integration Spec for Firebreak (v2)

**Target project:** `firebreak-cordon` (Cyber Incident Response Planner), frontend only
**Component:** `CloudField` (variant `cloud-field`) from `@designcodeio/threeui` v1.2.0 (MIT)
**Replaces:** the generic `CLOUD-FIELD-INTEGRATION.md`. That file is still the reference for what the effect looks like, but where the two disagree, **this file wins**.

---

## 0. Prime directive

Add the Cloud Field animated night-mountain background behind the existing dashboard **without changing any dashboard, API, algorithm, or test behavior.**

1. Do not rewrite, simplify, or "improve" the effect. Use the package component as shipped.
2. Make the smallest diff that works. Presentation changes only.
3. If something here is wrong or conflicts with what you find in the repo, **stop and report it** instead of working around it silently.
4. Before relying on any "Verified fact" in section 2, re-check it yourself in the repo or `node_modules`.

---

## 1. Goal and default decisions

**Goal:** the dashboard keeps its current layout and features, and gains the animated Cloud Field behind it, with panels turned into translucent "glass" so the background is visible and all text stays readable.

The owner may override any of these. Without an override, use the defaults:

| # | Decision | Default |
|---|---|---|
| D1 | Scope | **Background only**, behind the existing dashboard |
| D2 | Landing page (nav, hero, reveal text, cards, footer from the source HTML) | **Out of scope.** It is SaaS marketing content ("Strata", "Start Migration") and needs a scrolling page; the dashboard is a fixed 100vh app shell |
| D3 | Colors and fonts | **Keep the dashboard palette** (cyan, rose, slate) and fonts (Outfit, JetBrains Mono). Do not recolor to violet. Do not add Inter |
| D4 | Tailwind, GSAP, iconify | **Do not add.** The effect runs in an iframe and brings its own copies |
| D5 | Effect grade | `hue={0} saturation={1} brightness={1}`, `mode="dark"` (neutral) |
| D6 | Mouse parallax | **Not required** (see 2.3). Static centered parallax is acceptable |

---

## 2. Verified facts

### 2.1 About the project (read from the uploaded zip)

- Frontend: **Vite ^8, React ^19, plain JavaScript (`.jsx`)**. No TypeScript, no Tailwind. Scripts: `dev`, `build`, `lint` (oxlint), `preview`.
- `frontend/src/main.jsx` renders `<App />` inside **`<StrictMode>`**.
- `App.jsx` (~1100 lines) styles almost everything with **inline style objects** (~144). Global CSS is only `index.css` (Outfit and JetBrains Mono imports, CSS variables, `body` background `var(--bg-primary)`).
- Opaque backgrounds that will hide any background effect:
  - the root wrapper `<div style={{display:'flex', flexDirection:'column', height:'100vh', backgroundColor:'#090d16', ...}}>`
  - `<header>` (`#0c1220`)
  - `<aside>` right sidebar (`#0a0f1d`)
  - cards and panels inside the tabs (`#111827`, `#172554`, and so on)
- The graph is Cytoscape in `<div ref={containerRef} style={{width:'100%',height:'100%'}}/>`, inside a `position:'relative'` wrapper. Cytoscape's canvas is transparent by default.
- Backend (Flask, port 5000) and its tests (`pytest`, **61 tests** per `HANDOFF.md`) must stay untouched.
- Project convention: `HANDOFF.md` is updated at the end of each phase and decisions go in `docs/DECISIONS.md` (ADR-001 to ADR-008 exist).

### 2.2 About the package (checked on npm and in the tarball)

- `@designcodeio/threeui@1.2.0`, license **MIT** (© Meng To).
- Package `exports` include `"."`, `"./style.css"`, and **`"./components/*"`**. `./components/CloudField` exists and re-exports `CloudField` from `NeuformIsolatedEffects`.
- `PortalFieldCollection` also supports `variant="cloud-field"`, but it pulls in the whole collection. **Prefer the `CloudField` subpath import.**
- Props accepted by `CloudField`: `mode` (`"light" | "dark"`, default `"dark"`), `hue`, `saturation`, `brightness`, `className`, `style`.
- Peer dependencies: `react >=18 <20`, `react-dom >=18 <20`, **`three >=0.149 <1`** (not currently installed in this project). The package also depends on two aliased copies of three. `lib-dist` is about 55 MB on disk. This affects `node_modules` size, not the browser bundle, as long as you import only the subpath and lazy-load it.

### 2.3 How `CloudField` actually renders (read from the source bundle)

- It renders **`<iframe srcDoc=... sandbox="allow-scripts">`** with `display:block; width:100%; height:100%; border:0`. It is **not** raw WebGL mounted into your DOM, and it does **not** use your Tailwind or GSAP.
- Inside the iframe, the source page (`strata-cloud.html`) loads scripts from CDNs: `cdn.tailwindcss.com`, `code.iconify.design`, `cdnjs.cloudflare.com` (GSAP and ScrollTrigger), plus Google Fonts. The component isolates only the `#c` canvas and hides the rest of that page.
- The page's single inline script starts with `gsap.registerPlugin(ScrollTrigger)` and only then sets up WebGL. **If the GSAP CDN is unreachable, that line throws and the shader never starts** (you see only the fallback color). So the effect needs internet access at demo time. *(Inferred from reading the source; confirm by testing with the network off.)*
- An iframe **captures pointer events** by default, so the host must set `pointer-events: none` on it. With that set, the page inside never receives mouse movement, so the shader's mouse parallax stays at its default center position. This is expected (D6). Do not try to forward mouse events; that would require editing the source.
- The bundle URL `threeui.com/source-code/cloud-field.json` redirects to a Supabase storage URL. Treat remote content as changeable: **pin the npm version exactly** and do not fetch code at runtime.

### 2.4 Problems with the generic spec that this file corrects

- It assumed Tailwind, a `.shader-frame` wrapper, and GSAP lifecycle cleanup. None apply here (iframe, no Tailwind in the project).
- "Path B, copy the three registered files" does not build: `NeuformIsolatedEffects.tsx` imports about 30 sibling `*.html?raw` files and only one of them is listed. Use the npm package instead.
- The listed SHA-256 hashes describe the raw source files. The npm package is compiled, so hashes will **not** match. Use an exact version pin plus the lockfile as the regression check.
- It had no mounting plan for an app with opaque panels, and did not name this project's build, lint, or test commands.

---

## 3. Scope: what you may and may not touch

**May create or modify**
- `frontend/package.json` and `frontend/package-lock.json` (add `@designcodeio/threeui` and `three`).
- New files under `frontend/src/theme/`, for example `CloudBackdrop.jsx` and `theme.css`.
- `frontend/src/main.jsx`: import `theme.css` and mount `<CloudBackdrop />` as a sibling of `<App />`.
- `frontend/src/App.jsx`: **style-only edits to these elements and nothing else** (re-locate them by content, not line number):
  1. root wrapper: `backgroundColor: '#090d16'` becomes `'transparent'`
  2. `<header>`: translucent background
  3. `<aside>`: translucent background
  4. the graph panel wrapper (the `position:'relative'` div that contains `containerRef`): add a semi-opaque backing so nodes, edges and labels stay legible
  5. tab panels and cards: only if a specific one is unreadable in testing
- `README.md` (short "UI theme" note), `HANDOFF.md` (append a section), `docs/DECISIONS.md` (add ADR-009).

**Must not touch:** `backend/**`, tests, mock JSON, `docs/mock/**`, Cytoscape configuration or styles, API calls, state, handlers, props, routing, or any logic in `App.jsx`. Do not add Tailwind, GSAP, iconify, or new fonts. Do not edit anything inside `node_modules`.

---

## 4. Implementation

### 4.1 Install (exact versions)

```bash
cd frontend
npm install --save-exact @designcodeio/threeui@1.2.0
npm install three            # required peer dependency
```

If the install fails or `CloudField` is not exported as described, stop and report. Do not substitute another package or shader.

### 4.2 `frontend/src/theme/CloudBackdrop.jsx`

Requirements:
- **Lazy-load** the component so it is not in the main bundle: `React.lazy(() => import('@designcodeio/threeui/components/CloudField').then(m => ({ default: m.CloudField })))` inside `<Suspense fallback={null}>`.
- Wrapper element: `position: fixed; inset: 0; z-index: -1; pointer-events: none; overflow: hidden; background: #071010` (the component's own loading color; avoids a flash).
- Render `<CloudField mode="dark" hue={0} saturation={1} brightness={1} style={{ pointerEvents: 'none' }} />`.
- Add `aria-hidden="true"` on the wrapper. It is decorative.
- **StrictMode:** the dev double-mount must still leave exactly **one** iframe in the DOM. Verify.
- **Reduced motion:** if `window.matchMedia('(prefers-reduced-motion: reduce)').matches`, do not mount the iframe; render only a static CSS gradient with the same dark violet tones (`#050510` to `#14102a`). This is a host-boundary addition and does not change default visuals.
- Optional: if `document.hidden`, unmount the iframe and remount on visibility (the animation restarts; that is acceptable).

### 4.3 Stacking (this is the part most likely to go wrong)

The dashboard root is a normal-flow block with its own background. A fixed iframe at `z-index: 0` would paint **over** the header and root, covering the whole UI. Use this arrangement:

- `#root { isolation: isolate; }` in `theme.css`, so the backdrop's `z-index: -1` stays inside the app and above `body`'s background.
- Backdrop wrapper at `z-index: -1` (above).
- The root wrapper in `App.jsx` must have a **transparent** background, otherwise it paints over the backdrop.
- Keep `body { background: var(--bg-primary) }` as the last-resort fallback behind everything.

### 4.4 Glass panels (readability)

In `theme.css` or via the style-only edits in section 3:
- Header and sidebar: dark translucent fill (around `rgba(12,18,32,0.72)`) with `backdrop-filter: blur(12px)`.
- Graph panel backing: around `rgba(9,13,22,0.62)`.
- Do not lower the opacity of text. Do not change borders, spacing, font sizes, or layout.
- Required: normal text and labels meet **WCAG AA contrast (4.5:1)** against the *brightest* part of the background (the horizon glow), not just the darkest.

### 4.5 Performance guard (optional, only if needed)

The shader is full-screen with layered noise, and the Cytoscape canvas redraws on top. If the dashboard feels sluggish on an integrated GPU, add a `?lite=1` URL flag that renders the iframe at half size and scales it up with CSS (`width:50%; height:50%; transform: scale(2); transform-origin: 0 0`). This is softer but about 4x cheaper. Do not edit the shader or its resolution cap.

---

## 5. Things to preserve exactly

- Do not edit or "fix" anything inside the package. Quirks such as `preserveDrawingBuffer: true` and silent shader-compile failure are intentional.
- Defaults `hue 0, saturation 1, brightness 1` are the neutral, ungraded look. Use exactly those.
- The dashboard's existing look (colors, fonts, spacing, node and edge styling) must stay recognisably the same apart from the translucent panels.

---

## 6. Verification checklist (report each item with evidence)

**Commands** (from the project)
- [ ] `cd frontend && npm run lint` passes with no new warnings
- [ ] `cd frontend && npm run build` succeeds; report the size of the new lazy chunk and confirm the main chunk did not grow by the package size
- [ ] `cd backend && pytest -q` still reports **61 passed** (nothing in backend changed)

**Dashboard behavior unchanged**
- [ ] Scenario switcher (Worked Example and Enterprise) works
- [ ] All five tabs work: Topology, Priority Queue, Attack Paths, Restore Plan, Simulation
- [ ] Node click, path highlight, and isolate toggle work; Cytoscape still resizes correctly
- [ ] API connected indicator and live data still work with the Flask server running
- [ ] **Clicks are never blocked** by the backdrop (try clicking everywhere, including the graph)

**Visual**
- [ ] Night sky, five mountain ridges, stars, and an occasional meteor visible around and behind the panels
- [ ] All text is readable (AA contrast), including small labels in the sidebar and legend
- [ ] Graph nodes, edges and labels are as legible as before
- [ ] No white flash or layout shift on load
- [ ] Resize and rotate: background stays full-bleed

**Lifecycle and robustness**
- [ ] With React StrictMode on, exactly one iframe exists in the DOM
- [ ] Reloading and switching tabs does not create duplicate iframes or console errors
- [ ] **Network off:** the dashboard works fully; the backdrop shows only its dark fallback, with no errors that affect the app
- [ ] `prefers-reduced-motion: reduce` shows the static gradient and no iframe

---

## 7. Documentation to add

1. `docs/DECISIONS.md`: **ADR-009 "Cloud Field background"** with the decisions D1 to D6, the iframe and CDN trade-off, and the stacking approach.
2. `HANDOFF.md`: append a **"UI Theme: Cloud Field"** section with files changed, commands run with real output, verification results, known limits (needs internet; no mouse parallax), and how to remove it (delete `src/theme/`, revert the style-only edits, uninstall the two packages).
3. `README.md`: one short note, plus credit: *Background effect: ThreeUI Cloud Field (MIT, © Meng To).*

---

## 8. Hackathon demo safety

- Open the dashboard on the **venue network** before presenting. If the effect does not appear, the fallback must still look clean.
- Keep a screenshot of the finished look as a backup.
- The effect needs internet because its CDN scripts load inside the iframe. If you cannot guarantee a connection, tell the owner so they can decide whether to accept the fallback or approve a deliberate source edit (which would change the "use as shipped" rule and should be recorded in ADR-009).

---

## 9. Prompt to hand your agent

> Read `CLOUD-FIELD-INTEGRATION.firebreak.md` fully, then inspect `frontend/` to confirm section 2.1. Install the pinned packages, build `src/theme/CloudBackdrop.jsx` and `theme.css`, and make only the style-only edits listed in section 3. Do not change any logic, backend code, tests, or Cytoscape settings. If anything in the spec conflicts with the repo or the installed package, stop and tell me. When finished, run lint, build, and pytest, work through the checklist in section 6 with evidence for every item, and update `HANDOFF.md` and `docs/DECISIONS.md` as described in section 7.
