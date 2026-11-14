# jumbaq brand

Logo v1.0 "Evidence tag", direction "Field notebook". Light theme only.

A manila evidence tag, the kind a detective ties to a clue, carries a bold graphite question mark. The dot of the question mark is red pencil: the answer is the thing the kids find. The wordmark is typed in Courier Prime, like a case file, and the dot of the **j** is the same red.

The name is always written lower-case in Latin: **jumbaq** (Kazakh for "riddle"), never "Jumbaq" or "JUMBAQ", even at the start of a sentence.

## Folder

```
brand/
├── logo/
│   ├── svg/            vector logo files (wordmark outlined, no font needed)
│   ├── png/            app icons, large mark and lockup
│   └── favicon.ico     16 + 32 + 48 (all from the small cut)
├── tokens/
│   ├── jumbaq-tailwind.css   Tailwind v4: @theme block (use this in Next.js)
│   ├── jumbaq-tokens.css     plain CSS variables, no Tailwind
│   └── jumbaq-tokens.json    nested tokens + every contrast check
└── nextjs-app/         copy these three files into the Next.js `app/` folder
    ├── favicon.ico
    ├── icon.svg
    └── apple-icon.png
```

## Logo files

| File | Use |
|---|---|
| `jumbaq-mark.svg` | Main mark: tag, punched hole, question mark, red dot. 24 px and up |
| `jumbaq-mark-small.svg` | Small cut for 16–20 px: plain manila tile with one clipped corner, no hole, pixel-aligned stem |
| `jumbaq-mark-black.svg` / `-white.svg` | One colour: solid tag, hole and question mark cut out |
| `jumbaq-app-icon.svg` | Full-bleed graphite square; iOS and Android apply their own corner mask |
| `jumbaq-lockup.svg` | Mark + wordmark, default |
| `jumbaq-lockup-black.svg`, `-white.svg` | One-colour lockups (the j dot is the same colour as the rest) |
| `jumbaq-lockup-stacked.svg` | Mark above wordmark: posters, the printed certificate |
| `png/icon-192.png`, `icon-512.png` | Web app manifest |
| `png/apple-touch-icon-180.png` | iOS home screen (same file as `nextjs-app/apple-icon.png`) |
| `png/mark-1024.png`, `lockup-1600.png` | Slides, social posts, press |

## Colours

| Role | Hex |
|---|---|
| Paper (page) | `#F4F3EC` |
| Paper dots (dot grid) | `#C2C5CB` |
| Graphite (ink, question mark) | `#2B2B2B` |
| Red pencil (accent, dot, primary action) | `#B3261E` |
| Ballpoint blue (second accent, grown-up notes) | `#24478A` |
| Manila (evidence tag) | `#E3C98F` |
| Manila edge (hole ring in the mark) | `#9A8350` |
| Muted ink / faint ink | `#55555A` / `#6E6E73` |

Main contrast ratios (WCAG):

| Pair | Ratio |
|---|---|
| Graphite on paper (read-aloud text) | 12.73:1 |
| Red pencil on paper (primary action, labels) | 5.88:1 |
| Ballpoint blue on paper (grown-up note) | 8.06:1 |
| Graphite on manila (evidence text) | 8.78:1 |
| Manila label `#5A4A22` on manila | 5.34:1 |
| Muted ink on paper | 6.66:1 |
| Faint ink on paper / on the suspect table | 4.56:1 / 4.85:1 |
| Red dot on manila (logo shape) | 4.05:1 |

Every text and UI pair passes WCAG AA; the full list is in `tokens/jumbaq-tokens.json` → `$meta.contrast`.

One change from the design: the faint grey for cleared suspects and unfinished evenings was `#75757A`. It gave 4.12:1 on paper, which fails AA for small text. It is now `#6E6E73`, the lightest grey of the same hue that passes (4.56:1). The translucent tape colour is now the flat colour `#EBE1A9`, which looks the same on paper.

No gradients, glows, soft shadows or glossy effects. The dot grid and the riddle lines are flat SVG patterns.

## Type

| Role | Font | Size / line height | Weight |
|---|---|---|---|
| Read-aloud story text (`aloud`) | Literata | 22 px / 1.6 | 400 |
| Riddle (`riddle`) | Literata italic | 24 px / 1.5 (36 px lines) | 500 |
| Body (`body`) | Literata | 20 px / 1.5 | 400 |
| Titles (`title`, `display`) | Literata | 28 px / 1.15, 34 px / 1.12 | 700 |
| Grown-up note (`note`) | Kalam | 19 px / 1.35 | 400, bold lead-in 700 |
| Labels and case data (`label`, `case`) | Courier Prime | 13–15 px / 1.4 | 400, 700 |
| Suspect names, picks (`suspect`, `pick`) | Courier Prime | 18 px, 21 px | 700 |
| Main button (`button`) | Courier Prime | 23 px, tracking 0.02em | 700 |
| Wordmark (`wordmark`) | Courier Prime | 46 px, tracking −0.01em | 700 |

All three fonts are free (SIL Open Font License). The UI is in English only. Kalam is used only for short notes of one or two sentences, never for story text, buttons or anything a child must read.

## Logo rules

- Clear space: ¼ of the tag height on every side.
- Minimum size: mark 24 px; small cut 16–20 px; lockup 120 px wide; print 6 mm / 28 mm.
- Below 24 px always use `jumbaq-mark-small.svg`.
- Don't rotate or tilt the mark, even though the notebook UI tilts its cards. The logo stays straight.
- Don't recolour the dot: it is red pencil or the one-colour ink, nothing else.
- Don't add gradients, shadows, glows, outlines or 3D effects, or stretch the mark.
- Don't set the wordmark in another font or with a capital letter.
- Don't put the colour mark on mid-tone or busy backgrounds; use the one-colour version there.

## Using the tokens in Next.js (Tailwind v4)

```css
/* app/globals.css */
@import "tailwindcss";
@import "../brand/tokens/jumbaq-tailwind.css";
```

- Class examples: `bg-dot-grid`, `bg-paper`, `text-ink`, `font-story text-aloud`, `font-hand text-note text-note-fg`, `bg-evidence-bg`, `border-3 border-primary-border`, `rounded-sm`, `p-4` (= `space.4` = 16 px).
- The theme file removes Tailwind's default shadows and radii, so `shadow-md` and `rounded-lg` do nothing. Use `rounded-none`, `rounded-sm` (2 px) or `rounded-md` (4 px).
- Fonts: the site is a static export, so load the fonts locally, not with a Google Fonts `@import`. Install them with `npm i -D @fontsource/courier-prime @fontsource-variable/literata @fontsource/kalam`, copy the `.woff2` files you need into `app/fonts/`, and load them with `next/font/local`:

```tsx
// app/layout.tsx
import localFont from "next/font/local";

const courier = localFont({
  src: [
    { path: "./fonts/courier-prime-latin-400-normal.woff2", weight: "400" },
    { path: "./fonts/courier-prime-latin-700-normal.woff2", weight: "700" },
  ],
  variable: "--font-courier-prime",
});
const literata = localFont({
  src: [
    { path: "./fonts/literata-latin-opsz-normal.woff2", style: "normal" },
    { path: "./fonts/literata-latin-opsz-italic.woff2", style: "italic" },
  ],
  weight: "200 900",
  variable: "--font-literata",
});
const kalam = localFont({
  src: [
    { path: "./fonts/kalam-latin-400-normal.woff2", weight: "400" },
    { path: "./fonts/kalam-latin-700-normal.woff2", weight: "700" },
  ],
  variable: "--font-kalam",
});

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${courier.variable} ${literata.variable} ${kalam.variable}`}>
      <body className="bg-dot-grid text-ink font-story">{children}</body>
    </html>
  );
}
```

- The variables `--font-courier-prime`, `--font-literata` and `--font-kalam` feed the utilities `font-type`, `font-story` and `font-hand`.
- Without `next/font`, you can import the fontsource CSS instead (`import "@fontsource/kalam/400.css"` and so on); the token stacks also name `'Courier Prime'`, `'Literata'` and `'Kalam'` directly.
- Without Tailwind, use `jumbaq-tokens.css`: variables such as `--color-aloud-fg` and `--type-aloud-size`, and the classes `.jq-dot-grid`, `.jq-aloud` and `.jq-note`.

## Two voices

Every episode screen has two voices, and they must never look alike.

| | Read-aloud text | Grown-up note |
|---|---|---|
| Who reads it | The parent, out loud, to the kids | The parent only, silently |
| What it is | The story and the riddle | Tips: what counts as an answer, what to say if they are stuck |
| Font | Literata 22 px / 1.6 (riddle: italic 24 px) | Kalam 19 px / 1.35, short |
| Colour | Graphite on paper (`color.aloud.*`) | Ballpoint blue on paper (`color.note.*`) |
| Marker | Red "read aloud" label in the margin (`color.aloud.label`) | Bold lead-in "grown-ups only, don't read out:" |
| Tokens | `font-story text-aloud text-aloud-fg`; riddle card `bg-riddle-lines text-riddle text-riddle-fg` | `font-hand text-note text-note-fg` |

If a sentence should be read to the kids, it is read-aloud text. If reading it out would spoil the riddle, it is a grown-up note.

## State colours

Each state has `-fg` (text) and `-bg` (background), some also a border or a note colour. Always show a word as well, never colour alone.

- `primary`: the stamp button. Red pencil text and a 3 px red double border on paper; pressed: paper on red.
- `secondary`: graphite Courier text with a dotted underline ("Need a hint").
- `evidence`: graphite on manila, label `#5A4A22`, tag hole edge `#9A8350`.
- `suspect`: graphite name on the suspect table, blue note "still a suspect".
- `cleared`: faint name `#6E6E73` with a red pencil strike line, blue note "cleared".
- `success`: red pencil on paper, like the red ticks and the "case closed" stamp.
- `gentle-error`: ballpoint blue on card paper. A wrong accusation is never red: it is a calm note ("the clues don't match, look again"). There is no losing.
