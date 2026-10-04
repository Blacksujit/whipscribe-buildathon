# Frontend Dockerfile - builds and serves Next.js app
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./
RUN npm ci

# Copy source
COPY frontend/ .

# Build
RUN npm run build

# Production image
FROM node:20-alpine AS runner

WORKDIR /app

# Copy build artifacts
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/next.config.ts ./
COPY --from=builder /app/tsconfig.json ./

# Install only production dependencies
RUN npm ci --omit=dev

# next start does not need the SWC toolchain or cross-env
ENV NODE_OPTIONS=--max-old-space-size=2048
EXPOSE 3000

CMD ["npx", "next", "start"]