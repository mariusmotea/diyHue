FROM marvambass/nginx-ssl-secure

RUN apt-get update && apt-get install -y python3 iproute2 && apt-get clean

ADD openssl.conf entrypoint.sh /opt/
RUN chmod a+x /opt/entrypoint.sh

EXPOSE 80/tcp
EXPOSE 443/tcp

ENTRYPOINT ["/opt/entrypoint.sh"]
CMD ["nginx"]
