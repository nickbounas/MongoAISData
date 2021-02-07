# build stage
FROM node:12 as build-stage
WORKDIR /app
COPY ./ui/package*.json ./
RUN npm install
COPY ./ui .
RUN npm run build

# production stage
FROM nginx:stable-alpine as production-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY ./.htpasswd /etc/nginx/.htpasswd
RUN rm /etc/nginx/conf.d/default.conf
COPY prod.conf /etc/nginx/conf.d
CMD ["nginx", "-g", "daemon off;"]