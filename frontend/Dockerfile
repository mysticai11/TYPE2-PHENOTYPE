FROM node:20-alpine as build

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Build the frontend
COPY . .
RUN npm run build

# Serve with Nginx
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
