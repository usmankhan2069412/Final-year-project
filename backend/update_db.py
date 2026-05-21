import sys
import os
from sqlalchemy import create_engine, text

# Add current directory to path
sys.path.append(os.getcwd())

from app.core.config import settings

def update():
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.begin() as conn:
        print("Checking deployments table columns...")
        # Get columns of deployments table
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'deployments';
        """))
        columns = [row[0] for row in result.fetchall()]
        print("Existing columns in deployments:", columns)
        
        # Alter deployments
        if 'whatsapp_phone_number_id' not in columns:
            print("Adding whatsapp_phone_number_id to deployments...")
            conn.execute(text("ALTER TABLE deployments ADD COLUMN whatsapp_phone_number_id VARCHAR(50);"))
        if 'whatsapp_business_account_id' not in columns:
            print("Adding whatsapp_business_account_id to deployments...")
            conn.execute(text("ALTER TABLE deployments ADD COLUMN whatsapp_business_account_id VARCHAR(50);"))
        if 'is_active' not in columns:
            print("Adding is_active to deployments...")
            conn.execute(text("ALTER TABLE deployments ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT FALSE;"))
        if 'webhook_verified_at' not in columns:
            print("Adding webhook_verified_at to deployments...")
            conn.execute(text("ALTER TABLE deployments ADD COLUMN webhook_verified_at TIMESTAMP WITH TIME ZONE;"))
            
        print("Checking conversations table columns...")
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'conversations';
        """))
        conv_columns = [row[0] for row in result.fetchall()]
        print("Existing columns in conversations:", conv_columns)
        
        if 'sender_phone' not in conv_columns:
            print("Adding sender_phone to conversations...")
            conn.execute(text("ALTER TABLE conversations ADD COLUMN sender_phone VARCHAR(20);"))
            
        # Check if processed_events table exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'processed_events'
            );
        """))
        exists = result.scalar()
        if not exists:
            print("Creating processed_events table...")
            conn.execute(text("""
                CREATE TABLE processed_events (
                    id UUID PRIMARY KEY,
                    event_id VARCHAR(255) NOT NULL UNIQUE,
                    event_type VARCHAR(80) NOT NULL,
                    processed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                );
            """))
        else:
            print("processed_events table already exists.")
            
    print("Database schema update complete!")

if __name__ == "__main__":
    update()
