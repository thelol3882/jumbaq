import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";
import i18next from "eslint-plugin-i18next";

function layer(files, patterns, message) {
  return [
    {
      files: Array.isArray(files) ? files : [files],
      rules: {
        "no-restricted-imports": ["error", { patterns: [{ group: patterns, message }] }],
      },
    },
  ];
}

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    plugins: { i18next },
    rules: {
      // Hardcoded user-facing strings belong in locales/*.json.
      "i18next/no-literal-string": [
        "warn",
        {
          mode: "jsx-text-only",
          "jsx-attributes": {
            include: ["label", "placeholder", "title", "alt", "aria-label"],
          },
          ignoreAttribute: [
            "className",
            "style",
            "type",
            "id",
            "key",
            "data-testid",
            "href",
            "src",
            "fill",
            "stroke",
            "d", // SVG paths
            "viewBox",
            "xmlns",
          ],
          ignore: [
            "^[0-9]+$",
            "^[0-9]+\\.[0-9]+$",
            "^\\s*$",
            "—",
            "-",
            "/",
            "•",
          ],
          ignoreCallee: ["require", "console.log", "console.error", "console.warn"],
        },
      ],
    },
  },
  // Layers (AGENTS.md): app -> widgets -> features -> shared, and features never import
  // each other. Outside a feature only its index.ts is imported.
  ...layer("src/app/**", ["@/features", "@/features/*"], "Routes render a widget; compose features in src/widgets."),
  ...layer("src/widgets/**", ["@/features/*/*"], "Import a feature only through its index.ts."),
  ...layer("src/features/**", ["@/features", "@/features/*", "@/widgets", "@/widgets/*"], "A feature never imports another feature or a widget; inside a feature use relative imports."),
  ...layer(
    ["src/shared/**", "src/store/**", "src/i18n/**", "src/providers.tsx"],
    ["@/features", "@/features/*", "@/widgets", "@/widgets/*"],
    "shared has no domain logic and imports no feature or widget.",
  ),
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
