import sys
import os
from sqlalchemy import create_engine, text

# Add current directory to path
sys.path.append(os.getcwd())

from app.core.config import settings
from app.db.base import Base

def update():
    engine = create_engine(settings.DATABASE_URL)
    
    print("Verifying and creating new tables...")
    Base.metadata.create_all(bind=engine)
    print("New tables verified/created.")
    
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
            
        print("Checking personas table columns...")
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'personas';
        """))
        persona_columns = [row[0] for row in result.fetchall()]
        print("Existing columns in personas:", persona_columns)
        
        if 'greeting' not in persona_columns:
            print("Adding greeting to personas...")
            conn.execute(text("ALTER TABLE personas ADD COLUMN greeting VARCHAR(500);"))
        if 'fallback' not in persona_columns:
            print("Adding fallback to personas...")
            conn.execute(text("ALTER TABLE personas ADD COLUMN fallback VARCHAR(500);"))
        if 'description' not in persona_columns:
            print("Adding description to personas...")
            conn.execute(text("ALTER TABLE personas ADD COLUMN description VARCHAR(1000);"))
            
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
            
        # Check and create index on subscriptions
        print("Checking subscriptions index...")
        conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_subscriptions_org_active 
            ON subscriptions(org_id) 
            WHERE status = 'active';
        """))
        
        # Check and enable RLS + create policies
        print("Enabling RLS on subscriptions and api_keys...")
        conn.execute(text("ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;"))
        conn.execute(text("ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;"))
        
        # Create policies
        conn.execute(text("""
            DROP POLICY IF EXISTS tenant_isolation_subscriptions ON subscriptions;
            CREATE POLICY tenant_isolation_subscriptions ON subscriptions
            USING (org_id = NULLIF(current_setting('app.current_org_id', true), '')::uuid);
        """))
        conn.execute(text("""
            DROP POLICY IF EXISTS tenant_isolation_api_keys ON api_keys;
            CREATE POLICY tenant_isolation_api_keys ON api_keys
            USING (org_id = NULLIF(current_setting('app.current_org_id', true), '')::uuid);
        """))
        
        # Check and seed subscription_plans
        print("Checking subscription plans seeding...")
        result = conn.execute(text("SELECT COUNT(*) FROM subscription_plans;"))
        count = result.scalar()
        if count == 0:
            print("Seeding subscription plans...")
            import uuid
            import json
            
            plans = [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Starter",
                    "price_pkr": 0.00,
                    "max_bots": 1,
                    "max_messages_per_month": 100,
                    "max_members": 1,
                    "features": json.dumps(["1 Chatbot", "100 Messages/month", "1 Team Member", "Standard Support"]),
                    "is_popular": False
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Professional",
                    "price_pkr": 4999.00,
                    "max_bots": 5,
                    "max_messages_per_month": 5000,
                    "max_members": 5,
                    "features": json.dumps(["Up to 5 Chatbots", "5,000 Messages/month", "Up to 5 Team Members", "Priority Support", "API Access"]),
                    "is_popular": True
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Enterprise",
                    "price_pkr": 14999.00,
                    "max_bots": None,
                    "max_messages_per_month": None,
                    "max_members": None,
                    "features": json.dumps(["Unlimited Chatbots", "Unlimited Messages", "Unlimited Team Members", "24/7 Dedicated Support", "Custom AI Models", "Full API Access"]),
                    "is_popular": False
                }
            ]
            
            for p in plans:
                conn.execute(text("""
                    INSERT INTO subscription_plans (id, name, price_pkr, max_bots, max_messages_per_month, max_members, features, is_popular, created_at)
                    VALUES (:id, :name, :price_pkr, :max_bots, :max_messages_per_month, :max_members, :features, :is_popular, NOW());
                """), p)
            print("Subscription plans seeded successfully!")
        else:
            print("Subscription plans already seeded.")
            
    print("Database schema update complete!")

if __name__ == "__main__":
    update()
