FROM nginx:1.23.3

COPY ./run.sh /run.sh
COPY ./nginx.conf /nginx.conf
COPY ./nginx_http.conf /nginx_http.conf

USER root

RUN chmod +x /run.sh

VOLUME /vol/static
VOLUME /vol/www

ENTRYPOINT []
CMD ["/bin/bash", "-c", "/run.sh"]
