import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apps.api.core.database import SessionLocal
from shared.db.models import Balance, Position, Order, Trade

def wipe_data():
    db = SessionLocal()
    try:
        print("Wiping trades...")
        db.query(Trade).delete()
        print("Wiping orders...")
        db.query(Order).delete()
        print("Wiping positions...")
        db.query(Position).delete()
        print("Wiping balances...")
        db.query(Balance).delete()
        
        db.commit()
        print("Successfully wiped all portfolio data.")
    except Exception as e:
        db.rollback()
        print(f"Error wiping data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    wipe_data()
