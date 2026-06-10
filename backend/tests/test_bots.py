import sys
import os
import uuid

# Add current directory to path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.user import User
from app.models.organization import Organization, OrgMember, OrgRole
from app.models.persona import Persona
from app.models.chatbot import Chatbot, ChatbotStatus
from app.models.ai_model import RoutingRule
from app.services.bot import bot_service, model_config_service
from app.schemas.bot import PersonaCreate, ChatbotCreate, AIModelConfigCreate, RoutingRuleCreate

def run_tests():
    db = SessionLocal()
    # Redirect db.commit to db.flush to prevent closing the transaction in tests
    db.commit = db.flush
    
    # Start a transaction
    transaction = db.begin_nested() if db.in_transaction() else db.begin()
    try:
        print("--- RUNNING INTEGRATION TESTS FOR BOT ENGINE AND TENANT ISOLATION ---")
        
        # 1. Create test users
        user_a = User(
            email=f"user-a-{uuid.uuid4().hex[:6]}@test.com",
            full_name="User A",
            password_hash="fakehash"
        )
        user_b = User(
            email=f"user-b-{uuid.uuid4().hex[:6]}@test.com",
            full_name="User B",
            password_hash="fakehash"
        )
        db.add_all([user_a, user_b])
        db.flush()
        print(f"Created Test Users: User A ({user_a.id}), User B ({user_b.id})")

        # 2. Create test organizations
        org_a = Organization(owner_id=user_a.id, slug=f"org-a-{uuid.uuid4().hex[:6]}")
        org_b = Organization(owner_id=user_b.id, slug=f"org-b-{uuid.uuid4().hex[:6]}")
        db.add_all([org_a, org_b])
        db.flush()
        print(f"Created Test Organizations: Org A ({org_a.id}), Org B ({org_b.id})")

        # 3. Create organization memberships
        member_a = OrgMember(org_id=org_a.id, user_id=user_a.id, role=OrgRole.OWNER)
        member_b = OrgMember(org_id=org_b.id, user_id=user_b.id, role=OrgRole.OWNER)
        db.add_all([member_a, member_b])
        db.flush()
        print("Created organization memberships.")

        # Seed providers if empty
        model_config_service.seed_providers(db)
        providers = model_config_service.get_providers(db)
        provider = providers[0]
        print(f"Using AI Provider: {provider.name} ({provider.id})")

        # 4. Test Personas and Traits
        # Create a system (built-in) persona
        system_persona = Persona(
            name="System Assistant",
            language="en"
        )
        db.add(system_persona)
        db.flush()
        print(f"Created System Persona: {system_persona.name} ({system_persona.id})")

        # Create Org A Persona
        persona_a_in = PersonaCreate(name="Org A Persona", language="en", traits=["Friendly", "Helpful"])
        persona_a = bot_service.create_persona(db=db, org_id=org_a.id, persona_in=persona_a_in)
        print(f"Created Org A Persona: {persona_a.name} ({persona_a.id})")

        # Retrieve personas for Org A
        personas_for_a = bot_service.get_personas(db=db, org_id=org_a.id)
        persona_ids_for_a = [p.id for p in personas_for_a]
        assert system_persona.id in persona_ids_for_a, "System persona should be accessible to Org A"
        assert persona_a.id in persona_ids_for_a, "Org A persona should be accessible to Org A"
        print("Success: Org A fetched both custom and system personas.")

        # Retrieve personas for Org B
        personas_for_b = bot_service.get_personas(db=db, org_id=org_b.id)
        persona_ids_for_b = [p.id for p in personas_for_b]
        assert system_persona.id in persona_ids_for_b, "System persona should be accessible to Org B"
        assert persona_a.id not in persona_ids_for_b, "Org A persona should NOT be accessible to Org B"
        print("Success: Tenant isolation verified for listing personas (Org B cannot see Org A's persona).")

        # Test single persona retrieval and security scoping
        fetched_persona_a = bot_service.get_persona(db=db, org_id=org_a.id, persona_id=persona_a.id)
        assert fetched_persona_a is not None, "Org A should be able to fetch its own persona"
        
        fetched_persona_b = bot_service.get_persona(db=db, org_id=org_b.id, persona_id=persona_a.id)
        assert fetched_persona_b is None, "Org B should NOT be able to fetch Org A's persona"
        print("Success: Tenant isolation verified for single persona retrieval.")

        # Try to update Org A's persona as Org B
        from app.schemas.bot import PersonaUpdate
        update_res = bot_service.update_persona(
            db=db, org_id=org_b.id, persona_id=persona_a.id, persona_in=PersonaUpdate(name="Hacked")
        )
        assert update_res is None, "Org B should not be able to update Org A's persona"
        print("Success: Tenant isolation verified for persona updates.")

        # 5. Test Chatbots
        # Create Chatbot for Org A
        chatbot_a_in = ChatbotCreate(persona_id=persona_a.id, status=ChatbotStatus.DRAFT)
        chatbot_a = bot_service.create_chatbot(db=db, org_id=org_a.id, chatbot_in=chatbot_a_in)
        print(f"Created Chatbot for Org A: {chatbot_a.id}")

        # Verify Org B cannot access Org A's chatbot
        fetched_chatbot_b = bot_service.get_chatbot(db=db, org_id=org_b.id, chatbot_id=chatbot_a.id)
        assert fetched_chatbot_b is None, "Org B should NOT be able to fetch Org A's chatbot"
        
        # Verify Org B cannot update Org A's chatbot
        from app.schemas.bot import ChatbotUpdate
        update_bot_res = bot_service.update_chatbot(
            db=db, org_id=org_b.id, chatbot_id=chatbot_a.id, chatbot_in=ChatbotUpdate(status=ChatbotStatus.ACTIVE)
        )
        assert update_bot_res is None, "Org B should NOT be able to update Org A's chatbot"
        print("Success: Tenant isolation verified for chatbots.")

        # 6. Test Model Configurations and API Key Encryption
        # Create Model Config for Org A
        raw_key = "secret_key_12345"
        config_a_in = AIModelConfigCreate(
            provider_id=provider.id,
            api_key=raw_key,
            secret_ref="org-a-openai-ref",
            routing_rules=[
                RoutingRuleCreate(intent="customer_support"),
                RoutingRuleCreate(intent="coding")
            ]
        )
        config_a = model_config_service.create_model_config(db=db, org_id=org_a.id, config_in=config_a_in)
        print(f"Created AI Model Config for Org A: {config_a.id}")

        # Check key encryption
        assert config_a.encrypted_api_key != raw_key, "API key should be encrypted in database"
        decrypted_key = model_config_service.decrypt_key(config_a.encrypted_api_key)
        assert decrypted_key == raw_key, "Decrypted API key should match original"
        print("Success: API Key encryption and decryption verified.")

        # Verify Org B cannot access Org A's Model Config
        fetched_config_b = model_config_service.get_model_config(db=db, org_id=org_b.id, config_id=config_a.id)
        assert fetched_config_b is None, "Org B should NOT be able to fetch Org A's model config"
        print("Success: Tenant isolation verified for AI model configurations.")

        # Verify routing rules cascade delete
        rules_count = db.query(RoutingRule).filter(RoutingRule.config_id == config_a.id).count()
        assert rules_count == 2, f"Expected 2 routing rules, got {rules_count}"
        
        # Delete config
        delete_success = model_config_service.delete_model_config(db=db, org_id=org_a.id, config_id=config_a.id)
        assert delete_success is True, "Org A should be able to delete its own config"
        
        rules_count_after = db.query(RoutingRule).filter(RoutingRule.config_id == config_a.id).count()
        assert rules_count_after == 0, "Routing rules should be deleted when AI model config is deleted (cascade)"
        print("Success: Routing rules cascade deletion verified.")

        print("\nAll integration tests passed successfully!")
    finally:
        # Rollback the transaction to keep database clean
        transaction.rollback()
        db.close()
        print("Database transaction rolled back. Database is clean.")

if __name__ == "__main__":
    run_tests()
