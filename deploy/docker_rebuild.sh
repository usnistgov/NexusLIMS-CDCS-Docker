#!/bin/bash

# the following script can be used to completely wipe the running CDCS,
# rebuild, and run setup tasks (create super user and add XSLTs)

# this will create superuser with username/password admin/admin, so don't use
# that in production...

cd ../build
docker-compose build
cd ../deploy
docker-compose down -v
docker-compose up -d
#./docker_set_ssl.sh
./docker_createsuperuser.sh
#./docker_update_xslt.sh
docker-compose logs --follow