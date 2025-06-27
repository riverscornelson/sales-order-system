# Build stage
FROM node:20-alpine AS build

# Set environment variables
ENV NODE_ENV=production
ENV CI=true

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apk add --no-cache python3 make g++

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install
RUN npm install @rollup/rollup-linux-arm64-musl
RUN npm rebuild esbuild

# Copy source code (excluding node_modules)
COPY src ./src
COPY public ./public
COPY index.html .
COPY vite.config.ts .
COPY tsconfig*.json .
COPY tailwind.config.js .
COPY postcss.config.js .
COPY eslint.config.js .

# Build the application without type checking
RUN npx vite build

# Test stage (optional, can be skipped in production)
FROM build AS test
RUN npm run test -- --run

# Production stage
FROM nginx:alpine AS production

# Install security updates
RUN apk update && apk upgrade && apk add --no-cache curl

# Nginx user already exists, just ensure proper setup

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create nginx directories and set permissions
RUN mkdir -p /var/cache/nginx /var/log/nginx /var/run && \
    chown -R nginx:nginx /var/cache/nginx /var/log/nginx /var/run /usr/share/nginx/html && \
    chmod -R 755 /var/cache/nginx /var/log/nginx /var/run

# Switch to non-root user
USER nginx

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Expose port
EXPOSE 8080

# Start nginx
CMD ["nginx", "-g", "daemon off;"]