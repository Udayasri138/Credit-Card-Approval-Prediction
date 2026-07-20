import mysql.connector
from config import Config

def init_database():
    print("Connecting to MySQL host...")
    try:
        # Connect without specifying database name first
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            port=Config.DB_PORT,
            charset="utf8mb4",
            autocommit=True
        )
        cursor = conn.cursor()
        
        print("Reading schema.sql...")
        with open("schema.sql", "r", encoding="utf-8") as f:
            sql_script = f.read()
            
        # Split statements by semicolon (simple splitter, works for this schema)
        # We need to filter out comments and empty commands
        statements = []
        current_statement = []
        for line in sql_script.splitlines():
            # Strip comments
            stripped = line.strip()
            if not stripped or stripped.startswith("--") or stripped.startswith("/*"):
                continue
            current_statement.append(line)
            if stripped.endswith(";"):
                statements.append("\n".join(current_statement))
                current_statement = []
                
        print(f"Executing {len(statements)} SQL statements...")
        for i, stmt in enumerate(statements, 1):
            stmt_clean = stmt.strip()
            if stmt_clean:
                # Print first line of statement for logging
                first_line = stmt_clean.split("\n")[0][:60]
                print(f"  [{i}/{len(statements)}] Executing: {first_line}...")
                cursor.execute(stmt_clean)
                
        cursor.close()
        conn.close()
        print("Database initialized successfully!")
        
    except mysql.connector.Error as e:
        print(f"MySQL Error: {e}")
    except Exception as e:
        print(f"General Error: {e}")

if __name__ == "__main__":
    init_database()
