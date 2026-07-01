# Stage 1: Build React Client
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency configuration
COPY package.json ./
RUN npm install

# Copy source code and build project
COPY . ./
# Inject production environment variable before build
ENV VITE_API_URL=http://localhost:8000
RUN npm run build

# Stage 2: Serve Client via Nginx
FROM nginx:1.25-alpine

# Copy build artifacts to default public directory
COPY --from=builder /app/dist /usr/share/nginx/html

# Apply SPA routing configs
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose Nginx web server port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
