ARG ELASTIC_VERSION
FROM docker.elastic.co/elasticsearch/elasticsearch:${ELASTIC_VERSION}

WORKDIR /usr/share/elasticsearch/config/

USER root

COPY ./instance.yml /usr/share/elasticsearch/config/instance.yml

RUN apt-get update && apt-get install -y openssl unzip

RUN /usr/share/elasticsearch/bin/elasticsearch-certutil ca --pem --out ./ca.zip --silent

RUN unzip /usr/share/elasticsearch/ca.zip -d /usr/share/elasticsearch/config/certs/

RUN /usr/share/elasticsearch/bin/elasticsearch-certutil cert --pem \
--ca-cert /usr/share/elasticsearch/config/certs/ca/ca.crt \
--ca-key /usr/share/elasticsearch/config/certs/ca/ca.key \
--in /usr/share/elasticsearch/config/instance.yml \
--out /usr/share/elasticsearch/certs.zip \
--silent

RUN unzip /usr/share/elasticsearch/certs.zip -d ./certs/

USER elasticsearch

