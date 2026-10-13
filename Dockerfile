FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY *.html robots.txt sitemap.xml feed.xml llms.txt /usr/share/nginx/html/
COPY assets /usr/share/nginx/html/assets
EXPOSE 80
