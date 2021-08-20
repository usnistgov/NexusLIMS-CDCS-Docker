#!/bin/bash

source .env

docker exec -i "${PROJECT_NAME}_cdcs" python - <<'EOF'
# needs to run from /srv/curator
from mdcs import settings   # sets up DB connection
from core_main_app.components.data import models  # the model from ORM we want
from datetime import datetime
import xml.etree.ElementTree as ET
import pytz

# each Data object has fields such as title, xml_file, creation_date,
#  last_modification_date, last_change_date, etc. as defined in 
#  core_main_app/components/abstract_data/models.py 
#  these can be changed by reading the Document, directly modifying 
#  `last_change_date` (or whatever) and then running Document.save() to 
#  commit it to the DB
for i, doc in enumerate(models.Data.get_all('date')):
  e = ET.fromstring(doc.xml_content)
  time = e.find("acquisitionActivity/startTime")
  if time is None:
    continue
  dt = datetime.fromisoformat(time.text)
  print(f"Updating document {i+1} to {dt}")
  dt = pytz.timezone('America/New_York').localize(dt).astimezone(pytz.UTC)  
  doc.creation_date = dt
  doc.last_modification_date = dt
  doc.last_change_date = dt
  doc.save()
EOF
