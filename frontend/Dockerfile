# Adapted from simpler-grants-gov's frontend Dockerfile, which is itself based on
# the Next.js Docker example:
# https://github.com/vercel/next.js/blob/canary/examples/with-docker-compose
#
# Differences from the simpler-grants-gov version: this app has no Storybook
# (no `stories/` or `.storybook/`), so the dev stage does not copy them.
# =============================================================================
FROM node:24-bookworm-slim AS base
WORKDIR /frontend

# Install dependencies.
# public/ and scripts/ are needed at install time because package.json's
# postinstall hook runs scripts/postinstall.js.
COPY package.json package-lock.json ./
COPY public ./public
COPY scripts ./scripts
ENV PUPPETEER_SKIP_DOWNLOAD=true
RUN npm ci --no-audit

# =============================================================================
# Development stage
# =============================================================================
FROM base AS dev
WORKDIR /frontend

COPY tsconfig.json .
COPY *.config.js .
COPY *.d.ts .
COPY src ./src

ENV NEXT_TELEMETRY_DISABLED=1

CMD ["npm", "run", "dev"]

# =============================================================================
# Release stage
# =============================================================================

# Build the Next.js front end
# =====================================
FROM base AS builder
WORKDIR /frontend

COPY tsconfig.json .
COPY *.config.js .
COPY *.d.ts .
COPY src ./src

ENV NEXT_TELEMETRY_DISABLED=1

# Let the application know that it is being built
ENV NEXT_BUILD=true

# Skip lint — CI already runs it
RUN npm run build

# Run the Next.js server
# =====================================
FROM builder AS release
WORKDIR /frontend

# Pick up OS security updates. Left unpinned deliberately: pinning exact
# versions (as simpler-grants-gov does) means the build breaks whenever Debian
# publishes a new patch, and the base image is already rebuilt regularly.
RUN apt-get update \
  && apt-get upgrade -y --no-install-recommends \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /frontend/.next/cache/images/
VOLUME ["/frontend/.next/cache/images/"]

# Remove dev dependencies after the build
RUN npm prune --production
# The release stage has no need for npm, so remove it along with yarn to avoid
# vulnerabilities in tooling that never runs in production.
# https://github.com/nodejs/docker-node/issues/777
RUN npm uninstall -g npm \
  && rm -rf /opt/yarn-v*

# Don't run production as root
RUN addgroup --system --gid 1001 nodejs \
  && adduser --system --uid 1001 nextjs \
  && chown nextjs:nodejs /frontend/.next/cache/images/
USER nextjs

COPY --from=builder /frontend/public ./public

# Leverage Next.js output tracing to keep the image small.
# Requires `output: "standalone"` in next.config.js.
# https://nextjs.org/docs/advanced-features/output-file-tracing
COPY --from=builder --chown=nextjs:nodejs /frontend/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /frontend/.next/static ./.next/static

ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV NEXT_BUILD=false

EXPOSE 3000

CMD ["node", "server.js"]
