"""
Create conflict table on PostgreSQL database
"""
import psycopg2
from psycopg2 import sql

# PostgreSQL connection parameters
DB_URL = 'postgresql://neondb_owner:npg_lXSIMtk05eHv@ep-bold-wave-adctsiey-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require'

def create_conflict_table():
    """Create conflict table on PostgreSQL"""
    try:
        # Parse the connection string
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        print("🔍 Creating conflict table on PostgreSQL...")
        
        # Create the table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS conflict (
            id SERIAL PRIMARY KEY,
            slot TIME NOT NULL,
            "Date" DATE NOT NULL,
            "Court" VARCHAR(100) NOT NULL,
            playo_user VARCHAR(255),
            khelomore_user VARCHAR(255),
            "Resolved" BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        cursor.execute(create_table_query)
        conn.commit()
        
        print("✅ Conflict table created successfully!")
        
        # Create index on created_at for faster queries
        create_index_query = """
        CREATE INDEX IF NOT EXISTS idx_conflict_created_at 
        ON conflict(created_at DESC);
        """
        cursor.execute(create_index_query)
        conn.commit()
        
        print("✅ Index created successfully!")
        
        # Verify table exists
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'conflict'
            );
        """)
        exists = cursor.fetchone()[0]
        
        if exists:
            # Get table info
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'conflict'
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            print("\n📋 Conflict table schema:")
            for col_name, col_type in columns:
                print(f"   {col_name}: {col_type}")
        
        cursor.close()
        conn.close()
        
        return {"status": "success", "message": "Conflict table created"}
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    result = create_conflict_table()
    print(f"\nResult: {result}")
