# ── Stage 1: build ────────────────────────────────────────────────────────────
FROM node:22-alpine AS build

WORKDIR /app

# Install dependencies (separate layer — cached unless package.json changes)
COPY package.json package-lock.json* ./
RUN npm ci

# Expose docker-compose file's public url to frontend here
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Copy source and build
COPY . .
RUN npm run build

# ── Stage 2: serve ────────────────────────────────────────────────────────────
FROM nginx:1.27-alpine

# Replace the default nginx config with ours
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the built assets from the build stage
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
