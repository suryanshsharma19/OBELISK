FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source
COPY . .

# Ensure runtime user can write webpack/eslint cache under node_modules
RUN chown -R node:node /app

# Drop root privileges
USER node

# Expose port
EXPOSE 3000

# Start app
CMD ["npm", "start"]
