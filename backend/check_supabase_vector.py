import sys
import os
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal

def main():
    db = SessionLocal()
    try:
        # 1. Enable extension if not exists
        print("Checking/Enabling vector extension on Supabase...")
        try:
            db.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            db.commit()
            print("[SUCCESS] vector extension checked/enabled.")
        except ProgrammingError as pe:
            db.rollback()
            print(f"[FAILED] Could not run CREATE EXTENSION: {pe}")
            print("Note: In Supabase, you can also enable it from the Database > Extensions UI panel.")
        
        # 2. Check if it's in pg_extension
        result = db.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector';")).first()
        if result:
            print("[SUCCESS] vector extension is installed and active in the database!")
        else:
            print("[WARNING] vector extension is not in pg_extension.")

    except Exception as e:
        print(f"Error checking extension: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
