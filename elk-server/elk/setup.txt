### Setup ELK & Filebeat in same server ###

- Go to the Project Directory 

- docker-compose build --no-cache

- docker-compose up -d

- docker exec -it elasticsearch /usr/share/elasticsearch/bin/elasticsearch-reset-password -u elastic (Copy the Password)

- vim .env (Paste the elastic Password in ELASTIC_PASSWORD variable)

- docker exec -it elasticsearch /usr/share/elasticsearch/bin/elasticsearch-reset-password -u kibana_system (Copy the Password)

- vim kibana/config/kibana.yml (Paste the kibana_system Password in elasticsearch.password row)

- docker-compose up -d --build (Recreate all of the containers)

- Visit https://IP:5601 --> Username: elastic --> Password: that you paste into .env file ELASTIC_PASSWORD variable.






