import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

const nextConfig: NextConfig = {
  // A small Node server (.next/standalone/server.js) in a container behind nginx. Unlike a
  // static export it serves real dynamic routes, like /cases/1/evenings/2.
  output: "standalone",
  poweredByHeader: false,
};

export default withNextIntl(nextConfig);
