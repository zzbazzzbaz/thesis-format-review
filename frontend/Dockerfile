# Product frontend Dockerfile.
#
# Built by `.gitea/workflows/uno-docker.yml` and published as
# `git.gqt.plus/gqt/thesis-review-frontend`.
FROM node:22-alpine AS build

ARG VITE_PUBLIC_BASE_PATH=/thesis_reviews/frontend/
ARG VITE_API_BASE_URL=/thesis_reviews/backend

ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build -- --base ${VITE_PUBLIC_BASE_PATH} \
    && base="${VITE_PUBLIC_BASE_PATH%/}/" \
    && sed -i "s|<head>|<head><base href=\"${base}\">|" dist/index.html

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html/thesis_reviews/frontend

EXPOSE 80
