# Frontend image — multi-stage, Next standalone output (build_plan §3/§7 P0).
#
# NEXT_PUBLIC_* is inlined into the CLIENT bundle at BUILD time, not read at runtime, so the
# API base URL has to arrive as a build arg. It defaults to `/api` because production is
# same-origin behind Caddy — required, not stylistic: the seat cookie is
# HttpOnly; SameSite=Lax; Path=/games/{id} with no domain, so the frontend must be same-site
# with the API or the cookie is simply never sent (build_plan §5).

FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
# `npm ci` needs the lockfile to match package.json exactly — that is the point.
RUN npm ci

FROM node:22-alpine AS builder
WORKDIR /app
ARG NEXT_PUBLIC_API_BASE_URL=/api
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

# Non-root: nothing here needs to write to the filesystem.
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001

# `standalone` output ships its own minimal node_modules; static/ and public/ are the two
# things it does NOT copy in and must be placed by hand.
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
