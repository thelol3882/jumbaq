import { getRequestConfig } from "next-intl/server";
import { defaultLocale } from "./config";

// Feature namespaces: locale files at src/features/<name>/locales/<locale>.json,
// exposed at messages.<name>.*
const FEATURE_LOCALES = ["families", "cases", "episodes", "billing"] as const;

// Widget namespaces: locale files at src/widgets/<name>/locales/<locale>.json,
// exposed at messages.widget.<name>.*
const WIDGET_LOCALES = ["landing", "setup", "family", "evening", "accuse", "billing-return", "plans", "not-found"] as const;

async function loadAll<const T extends readonly string[]>(
  names: T,
  path: (name: T[number]) => Promise<{ default: unknown }>,
) {
  return Object.fromEntries(
    await Promise.all(names.map(async (name) => [name, (await path(name)).default])),
  );
}

// One language and no locale in the URL, so the locale is fixed here.
export default getRequestConfig(async () => {
  const locale = defaultLocale;
  const isDev = process.env.NODE_ENV !== "production";

  const common = (await import(`./messages/${locale}.json`)).default;
  const features = await loadAll(
    FEATURE_LOCALES,
    (name) => import(`../features/${name}/locales/${locale}.json`),
  );
  const widget = await loadAll(
    WIDGET_LOCALES,
    (name) => import(`../widgets/${name}/locales/${locale}.json`),
  );

  return {
    locale,
    messages: { ...common, ...features, widget },
    // In dev, surface missing or broken messages instead of silently showing the key.
    onError: isDev
      ? (error: { code: string; message: string }) =>
          console.warn(`[next-intl:${error.code}] ${error.message}`)
      : undefined,
    getMessageFallback: isDev
      ? ({ namespace, key }: { namespace?: string; key: string }) =>
          `⚠️ ${namespace ? `${namespace}.` : ""}${key}`
      : undefined,
  };
});
