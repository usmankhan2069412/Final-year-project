import psycopg2

DATABASE_URL = "postgresql://postgres:Pakistan@localhost:5432/chatbot_builder"

def main():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        tables = [r[0] for r in cursor.fetchall()]
        print(f"Tables: {tables}")
        
        cursor.execute("SELECT typname FROM pg_type WHERE typcategory = 'E';")
        enums = [r[0] for r in cursor.fetchall()]
        print(f"Enums: {enums}")
    except Exception as e:
        print(f"Error: {e}")
            
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
