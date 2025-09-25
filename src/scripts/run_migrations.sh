#!/bin/bash
set -e

cd /code/src
export PYTHONPATH=/code/src:$PYTHONPATH

echo "Running migrations..."
alembic upgrade head

echo "Creating initial tier..."
python3 << END
from app.core.config import settings
from app.models.tier import Tier
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import datetime

engine = create_engine(f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    result = db.execute(text("SELECT COUNT(*) FROM tier WHERE name = 'free'")).scalar()
    if result == 0:
        tier = Tier(name="free", created_at=datetime.datetime.now())
        db.add(tier)
        db.commit()
        print("Created 'free' tier successfully")
    else:
        print("'free' tier already exists")
except Exception as e:
    print(f"Error creating tier: {e}")
    db.rollback()
finally:
    db.close()
END 