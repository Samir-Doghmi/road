#!/bin/bash

set -e

echo "==> Creating (if not exist) raw_measurement table in PostgresSQL using SQLAlchemy..."
python -c "
import os
from sqlalchemy import create_engine
from models import Base

db_url = os.environ['DATABASE_URL']
engine = create_engine(db_url)
Base.metadata.create_all(engine, checkfirst=True)
print('Done!')
"

# Launch the Flask app (api) using gunicorn, because the integrated Flask server
# is not secure and can't manage ~150 IoT devices. gunicorn can leverage concurrency
# and therefore is more performant.
echo "==> Starting api with Gunicorn..."
exec gunicorn --workers 2 --bind 0.0.0.0:8000 api:app
