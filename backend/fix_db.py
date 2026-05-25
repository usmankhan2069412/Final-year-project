import psycopg2

DATABASE_URL = "postgresql://postgres:Pakistan@localhost:5432/chatbot_builder"

def main():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    enums_to_drop = [
        "enum_knowledge_job_status",
        "enum_knowledge_document_status",
        "enum_knowledge_base_status",
        "enum_chatbot_knowledge_base_status"
    ]
    
    for enum in enums_to_drop:
        try:
            cursor.execute(f"DROP TYPE IF EXISTS {enum} CASCADE;")
            print(f"Dropped {enum}")
        except Exception as e:
            print(f"Error dropping {enum}: {e}")
            
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
