# ============================================================
# Stage 1: development — Vite dev server with HMR
# ============================================================
FROM node:22-alpine AS development

WORKDIR /app

COPY package.json ./
# npm install rather than npm ci: no lockfile exists yet.
# Switch to `npm ci` after committing package-lock.json.
RUN npm install

# Bake the build/tooling config into the image. docker-compose.dev.yml only
# volume-mounts ./src and ./index.html, so these files must be present here or
# Vite/Tailwind/TypeScript would have no configuration at dev runtime.
COPY vite.config.ts tsconfig*.json tailwind.config.js postcss.config.js ./

# Application source is volume-mounted at runtime (see docker-compose.dev.yml).
# node_modules stays inside the container so Linux binaries are not
# overwritten by any Windows-native node_modules on the host.

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]


# ============================================================
# Stage 2: builder — compile the production bundle
# ============================================================
FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .
RUN npm run build


# ============================================================
# Stage 3: production — static bundle served by nginx
# ============================================================
FROM nginx:alpine AS production

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
