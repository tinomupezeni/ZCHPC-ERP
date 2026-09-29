# ZCHPC ERP - Employee Portal Dockerfile
# Multi-stage build for React/Vite application

# ============================================================================
# Stage 1: Dependencies
# ============================================================================
FROM node:22-alpine AS deps

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# ============================================================================
# Stage 2: Builder
# ============================================================================
FROM node:22-alpine AS builder

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Production default is the portal's own public origin (same-origin /api
# via reverse proxy needs no CORS). Matches build-and-push.sh. Local and
# staging builds MUST pass an explicit --build-arg instead - never promote
# a localhost-baked image to prod.
ARG VITE_API_URL=https://employees.zchpc.ac.zw
ENV VITE_API_URL=${VITE_API_URL}

# Build the application
RUN npm run build

# ============================================================================
# Stage 3: Production (Nginx)
# ============================================================================
FROM nginx:alpine AS production

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -q --spider http://127.0.0.1/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
