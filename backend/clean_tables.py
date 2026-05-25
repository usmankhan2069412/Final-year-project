import psycopg2

DATABASE_URL = "postgresql://postgres:Pakistan@localhost:5432/chatbot_builder"

def main():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    tables_to_drop = [
        "knowledge_jobs",
        "chatbot_knowledge_bases",
        "knowledge_bases"
    ]
    for table in tables_to_drop:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
            print(f"Dropped table {table}")
        except Exception as e:
            print(f"Error dropping {table}: {e}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
