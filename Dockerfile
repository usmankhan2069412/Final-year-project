# Use an official Node.js runtime as the base image
FROM node:20-slim

# Install pnpm using corepack
RUN corepack enable && corepack prepare pnpm@latest --activate

# Set working directory
WORKDIR /app

# Copy package.json and pnpm-lock.yaml
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy the rest of the application
COPY . .

# Expose the Vite default port
EXPOSE 5173

# Start the dev server
CMD ["pnpm", "run", "dev"]
