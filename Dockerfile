# ─── Build Stage ──────────────────────────────────────────────────────────────
FROM node:22-alpine AS builder

WORKDIR /app

# Copy package files first to leverage Docker layer caching
COPY package*.json ./

# Install ALL dependencies (including devDependencies needed for build)
RUN npm ci

# Copy source code
COPY . .

# Run svelte-kit sync explicitly first, then build
RUN npx svelte-kit sync && npm run build

# ─── Runtime Stage ────────────────────────────────────────────────────────────
FROM node:22-alpine AS runtime

WORKDIR /app

COPY package*.json ./

# Only install production dependencies at runtime
RUN npm ci --omit=dev

# Copy the built output from builder stage
COPY --from=builder /app/build ./build

ENV HOST=0.0.0.0
ENV PORT=3000
ENV NODE_ENV=production
EXPOSE 3000

CMD ["node", "build/index.js"]
