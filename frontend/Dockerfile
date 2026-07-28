# Multi-stage build: compile the Angular app with Node, serve static files
# with nginx. The final image carries no Node/npm — small and fast to deploy.
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
# Angular is a single-page app: nginx must fall back to index.html so client
# routes resolve. This config also proxies /agent, /eval etc. to the API.
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html
EXPOSE 80
