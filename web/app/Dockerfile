FROM node:22-alpine AS build

RUN corepack enable
WORKDIR /app

# Dependencies first, so this layer is cached until the lock file changes.
COPY package.json pnpm-lock.yaml ./
RUN --mount=type=cache,id=pnpm,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile

COPY . .
# Baked into the browser code at build time, so it is an argument, not a runtime setting.
ARG NEXT_PUBLIC_API_URL=https://api.jumbaq.fun
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_TELEMETRY_DISABLED=1
RUN pnpm build


FROM node:22-alpine

WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=3000

# The standalone server does not copy public/ or .next/static by itself.
COPY --from=build --chown=node:node /app/.next/standalone ./
COPY --from=build --chown=node:node /app/.next/static ./.next/static
COPY --from=build --chown=node:node /app/public ./public

# The image's own unprivileged user (uid 1000).
USER node
EXPOSE 3000
CMD ["node", "server.js"]
