FROM nginx:alpine

COPY nginx/default.conf /etc/nginx/conf.d/default.conf

COPY index.html photos.html led-wall.html vp-sim.html robots.txt sitemap.xml 1587.gif 1885.gif /usr/share/nginx/html/
COPY th/ /usr/share/nginx/html/th/
COPY ja/ /usr/share/nginx/html/ja/
COPY css/ /usr/share/nginx/html/css/
COPY js/ /usr/share/nginx/html/js/
COPY images/ /usr/share/nginx/html/images/
COPY logo/ /usr/share/nginx/html/logo/

EXPOSE 80
