# =============================================================================
# AI Materials Frontend Dockerfile (React + Vite)
# =============================================================================
FROM node:20-alpine AS builder

# Build arguments for configuration
ARG VITE_API_URL=/services/aimaterials/api
ARG VITE_BASE_PATH=/services/aimaterials

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev dependencies for build)
RUN npm ci

# Copy source code
COPY . .

# Build arguments for Vite - use ARG directly in build command
# Vite will pick up these prefixed variables during build
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_BASE_PATH=${VITE_BASE_PATH}

# Print to verify (for debugging)
RUN echo "VITE_API_URL=$VITE_API_URL" && echo "VITE_BASE_PATH=$VITE_BASE_PATH"

# Build the application
RUN npm run build

# =============================================================================
# Production Stage
# =============================================================================
FROM nginx:alpine

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create healthcheck endpoint
RUN echo "OK" > /usr/share/nginx/html/health

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:3000/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
