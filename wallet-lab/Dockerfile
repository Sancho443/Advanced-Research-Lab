FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# In a real op, we'd check for 'npm run build', 
# but we are running TS directly for dev speed.
CMD ["npx", "ts-node", "src/server.ts"]