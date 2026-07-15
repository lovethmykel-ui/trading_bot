import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apps.api.core.database import engine
from shared.db.models import Base

def init_db():
    print("Creating tables in SQLite...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

if __name__ == "__main__":
    init_db()
