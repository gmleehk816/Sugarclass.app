FROM node:20-slim

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Environment variable for API URL (can be overridden at runtime)
ENV NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Run in dev mode for hot reloading
CMD ["npm", "run", "dev"]
