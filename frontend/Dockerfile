# syntax=docker/dockerfile:1.7

FROM node:22-bookworm-slim AS base

WORKDIR /app

ENV PATH="/app/node_modules/.bin:$PATH"

FROM base AS deps

COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

FROM deps AS dev

COPY . .

EXPOSE 4000

CMD ["sh", "-c", "npm run start -- --host 0.0.0.0 --port 4000"]

FROM deps AS build

COPY . .
RUN npm run build

FROM node:22-bookworm-slim AS prod

WORKDIR /app
ENV NODE_ENV=production \
    PATH="/app/node_modules/.bin:$PATH"

COPY --from=build /app/dist ./dist
COPY --from=build /app/server.mjs ./server.mjs
COPY --from=build /app/package.json ./package.json
COPY --from=build /app/package-lock.json* ./

RUN if [ -f package-lock.json ]; then npm ci --omit=dev; else npm install --omit=dev; fi

EXPOSE 4000

CMD ["npm", "run", "serve", "--", "--host", "0.0.0.0", "--port", "4000"]
