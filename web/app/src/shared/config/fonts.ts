import localFont from "next/font/local";

// Local files, not Google Fonts: the build makes no network call for them (brand/README.md).
const courier = localFont({
  src: [
    { path: "../../app/fonts/courier-prime-latin-400-normal.woff2", weight: "400" },
    { path: "../../app/fonts/courier-prime-latin-700-normal.woff2", weight: "700" },
  ],
  variable: "--font-courier-prime",
});

const literata = localFont({
  src: [
    { path: "../../app/fonts/literata-latin-opsz-normal.woff2", style: "normal" },
    { path: "../../app/fonts/literata-latin-opsz-italic.woff2", style: "italic" },
  ],
  weight: "200 900",
  variable: "--font-literata",
});

const kalam = localFont({
  src: [
    { path: "../../app/fonts/kalam-latin-400-normal.woff2", weight: "400" },
    { path: "../../app/fonts/kalam-latin-700-normal.woff2", weight: "700" },
  ],
  variable: "--font-kalam",
});

/** The classes `<html>` needs: --font-courier-prime, --font-literata, --font-kalam. */
export const fontVariables = `${courier.variable} ${literata.variable} ${kalam.variable}`;
