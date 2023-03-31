FROM certbot/certbot:v1.27.0

COPY certify.sh /opt/
RUN chmod +x /opt/certify.sh

ENTRYPOINT []
CMD ["certbot", "renew"]