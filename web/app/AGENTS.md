<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

# jumbaq web app

The web app at `jumbaq.fun`: the landing, the one-minute setup and the evenings of a case. A parent reads it from a phone, so mobile comes first. These rules are for everyone working on it, people and coding agents. The backend rules and the commit style are in [backend/AGENTS.md](../../backend/AGENTS.md).

## Stack

Next.js 16 (App Router, `output: "standalone"`), React 19, TypeScript strict, Tailwind v4 with the brand tokens, RTK Query (`baseApi.injectEndpoints()`), next-intl (one locale, no locale in the URL), lexen (translation extraction and checks). pnpm only.

## Layers

```
app/       routes: thin wrappers that render ONE widget, no data fetching, no feature imports
widgets/   screens and blocks: compose features, the only layer app/ may import
features/  domain modules: API, types, hooks, services, components. Never import another feature
shared/    reusable primitives with no domain logic: ui, api core, session hint, config, hooks
```

- Dependencies go one way: `app → widgets → features → shared`. ESLint (`eslint.config.mjs`) enforces it.
- `app/` imports only from `widgets/` (and `@/providers`, `shared/config`, `next`, `next-intl`). A route renders one widget.
- A shell that several screens share goes in a `layout.tsx`, never in a page, so it stays mounted across navigations. Use a route group for the screens that share it. Like a route, the layout renders one widget.
- A widget composes features: it imports any feature's public `index.ts` and wires them together with props. It decides the layout.
- A feature never imports another feature or a widget. When two features must work together, a widget connects them. Inside a feature, import with relative paths.
- Everything outside a feature imports only its `index.ts` (`@/features/families`), never a file inside it.

`families` is the reference feature and `landing` the reference widget. Copy their shape.

## A feature

```
src/features/families/
├── index.ts              public API: components, hooks, `export type * from "./types"`; not the api object
├── api/familiesApi.ts    baseApi.injectEndpoints()
├── types/                aliases of the generated API types
├── hooks/                useSetupForm, useFamily, useStartHref
├── components/           smart components (use the feature's hooks) and plain ones (props only)
├── services/             pure logic with tests: setupForm.ts + setupForm.test.ts
└── locales/en.json       register it in FEATURE_LOCALES in src/i18n/request.ts
```

No `pages/` folder: a page is a widget.

## A widget

```
src/widgets/landing/
├── index.ts              the widget component(s) app/ renders
├── Landing.tsx           the wrapper: loads the data, picks the layout
├── LandingMobile.tsx     only renders
├── LandingDesktop.tsx    only renders
├── parts.tsx             pieces both layouts share
└── locales/en.json       namespace widget.landing; register it in WIDGET_LOCALES in src/i18n/request.ts
```

## Mobile and desktop

- A widget `X.tsx` picks `XMobile` or `XDesktop` with `useIsMobile()` (`shared/hooks`) only when the two UIs truly differ; otherwise Tailwind breakpoints in one component (`Setup` is one column everywhere).
- The wrapper `X.tsx` loads the data and passes it down; `XDesktop` and `XMobile` only render. Form state and submit go into a feature hook (`useSetupForm`), shared by both.
- `useIsMobile()` is true on the server and during hydration: the first HTML is the phone layout, and desktop swaps in right after. (Sheber does the opposite, because its users work at a desk.)
- Mobile is design row D, desktop is row F of the design canvas ("jumbaq - page designs v2"). Desktop is the same notebook opened flat, never a different look:
  - `NotebookSpread`: the main page on the left, the parent's page on the right, with a dashed fold. Story text stays at reading width (about 34em); the extra width goes to the parent's tools, never to longer lines.
  - The main action stays in view on the right page (`sticky`), and has a key: `useSubmitShortcut` (⌘↵ or Ctrl+↵) with a `KeyHint` next to it. Only one shortcut per screen, so it never clashes with typing.
  - Nothing to click inside the read-aloud text: buttons on the reading page pull the kids' attention.
  - The form state lives in the wrapper (`Setup.tsx`), so turning a tablet or resizing keeps what was typed.

## Look

- The brand is in `brand/` at the repository root: colours, type, logo rules and the two voices. `src/app/jumbaq-tailwind.css` is a copy of `brand/tokens/jumbaq-tailwind.css` (the Docker build sees only `web/app`); change both together.
- Use the token utilities (`bg-dot-grid`, `text-ink`, `font-story text-aloud`, `font-hand text-note text-note-fg`, `border-primary-border`), never raw hex in a component.
- The notebook pieces are in `shared/components/notebook`: `NotebookPage`, `StampButton`/`StampLink` (the main action), `TypedButton` (the second action), `HandNote` (grown-ups only), `EvidenceTag`, `Wordmark`. They take texts as props, already translated. Reach for them before writing your own.
- Two voices never look alike: read-aloud text is Literata in graphite, a grown-up note is Kalam in ballpoint blue. A wrong answer is a calm blue note, never red: there is no losing.
- Fonts are local files in `src/app/fonts`, loaded by `shared/config/fonts.ts`. No Google Fonts at runtime.

## Services

Logic from hooks over about 100 lines goes to `services/<name>.ts`: pure functions only, no `react`, `next`, `@reduxjs/toolkit` or `next-intl` imports, no classes. The hook owns RTK, state and `useTranslations`. Validation returns literal-union error keys, not localized text. Services get vitest tests.

## API

- Types are generated: `pnpm api:types` writes `src/shared/api/schema.d.ts` from the backend OpenAPI (needs `uv`, no database; never edit the file). Features alias what they use in `types/` (`type Family = Schemas["FamilyOut"]`); no hand-written copies of API shapes. Run it after every backend change of a schema, and commit the file.
- Always `baseApi.injectEndpoints()` in a feature, never a new `createApi`, with the tags of `baseApi` (add a new one to `TAG_TYPES`) and the helpers `listTags` and `itemTags` (`shared/api/tags.ts`).
- The API is on another host (`api.jumbaq.fun`, `NEXT_PUBLIC_API_URL`, baked in at build time). Requests use `credentials: "include"` and send `X-Requested-With: jumbaq`, which the API asks for on every change (CSRF).
- The family session is the HttpOnly `family_session` cookie of the API host. The web app never sees it: `useFamily()` asks `GET /family`, and 401 `family.no_session` means this browser has no family. `shared/session/familyHint` remembers in `localStorage` that a family was made, only so an anonymous visitor makes no API call; it is a hint, never proof.
- Errors: show text by the error code, never the API `message`. `useApiErrorMessage()` gives `(error) => text`, `useFormErrorMessage()` the code of the first wrong field (`shared/api/useApiErrorMessage.ts`). A new backend error code goes to `shared/api/errorCodes.ts` and `common.errors` in `src/i18n/messages/en.json`; `backend/tests/test_error_codes.py` fails until all three agree.

## i18n

- Namespaces: `common` (global, `src/i18n/messages/en.json`), `<feature>` (`features/<name>/locales/en.json`), `widget.<name>` (`widgets/<name>/locales/en.json`).
- Always `useTranslations("<namespace>")`, never a bare `useTranslations()`.
- A dot in a key means nesting, also for error codes: `common.errors.family.no_session` is `{"errors": {"family": {"no_session": …}}}`.
- Arrays of texts become keyed objects, iterated with an `as const` key list (`ROOM_PRESETS`, `STEPS`). Non-text data stays in code.
- Dynamic values use ICU arguments (`{count}`, plurals), not string concatenation.
- After changing texts: `pnpm i18n extract`, then `pnpm i18n:check`. The name is always lower case: jumbaq.

## Standalone server

`pnpm build` makes `.next/standalone/server.js`; the Dockerfile copies `.next/static` and `public` next to it, and nginx sends `jumbaq.fun` to it. Dynamic routes like `/cases/[number]/evenings/[evening]` work as real paths, with no `generateStaticParams`. Data from the API is still fetched in the browser with RTK Query. Unknown URLs render `src/app/not-found.tsx`.

## Running it

`make up` in the repository root builds and starts the web app with the backend, on http://localhost:3000, as the server runs it. Rebuild it with `make up` after a change.

For hot reload, stop that container and run the dev server on the same port, so CORS (`JUMBAQ_CORS_ORIGINS` in `infra/.env`) still matches:

```sh
docker compose -f ../../infra/docker-compose.yml stop web
pnpm install
pnpm dev        # http://localhost:3000, the API on http://localhost:8000
```

## Checks before a commit

`pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm i18n:check`, `pnpm build`. Comments only where they explain why. Commit messages are one line, `type: title`, no body and no trailers (backend/AGENTS.md).
