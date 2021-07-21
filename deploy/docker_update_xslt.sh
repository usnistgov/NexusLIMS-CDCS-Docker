#!/bin/bash
source .env
if [ $# -ge 2 ]
  then
    user=$1
    pass=$2
  else
    user="admin"
    pass="admin"
fi

docker cp ./cdcs/list.xsl "${PROJECT_NAME}_cdcs":/srv/curator/static/list.xsl
docker cp ./cdcs/detail.xsl "${PROJECT_NAME}_cdcs":/srv/curator/static/detail.xsl
docker cp ./cdcs/update_xslt.py "${PROJECT_NAME}_cdcs":/srv/curator/update_xslt.py
docker exec -u root "${PROJECT_NAME}_cdcs" chown -R cdcs:cdcs /srv/curator/static/list.xsl /srv/curator/static/detail.xsl /srv/curator/update_xslt.py

# wait until server gives a 200 response (in case it's restarting)
SERVER_URI=${SERVER_URI} bash -c 'while [[ "$(curl -s -k -o /dev/null -w ''%{http_code}'' ${SERVER_URI})" != "200" ]]; do echo "waiting 5 seconds for ${SERVER_URI} to be available"; sleep 5; done'
docker-compose exec cdcs python /srv/curator/update_xslt.py --url ${SERVER_URI} --username ${user} --password ${pass} --list ./static/list.xsl --detail ./static/detail.xsl
