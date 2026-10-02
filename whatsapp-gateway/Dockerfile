FROM node:20-slim

WORKDIR /app

COPY package*.json ./
RUN npm install --omit=dev

COPY . .

# Persistent storage mount point for Baileys WhatsApp credentials
RUN mkdir -p /data/auth_info_baileys

ENV PORT=3001
ENV AUTH_DIR=/data/auth_info_baileys

EXPOSE 3001

CMD ["node", "gateway.js"]
