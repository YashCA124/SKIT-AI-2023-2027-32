FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

EXPOSE 5173

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD node -e "require('http').get('http://127.0.0.1:5173/',(r)=>process.exit(r.statusCode>=200&&r.statusCode<400?0:1)).on('error',()=>process.exit(1))"

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5173"]
