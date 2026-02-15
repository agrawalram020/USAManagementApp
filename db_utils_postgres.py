import psycopg2
from psycopg2 import sql
import os
from datetime import datetime


def insert_conflict_to_postgres(slot_time_only, booking_date, selected_court, po_customer_name, km_customer_name, db_url=None):
    """
    Insert conflict data into PostgreSQL database.
    
    Args:
        slot_time_only: Time slot (e.g., "14:00:00")
        booking_date: Booking date (e.g., "2026-02-14")
        selected_court: Court name (e.g., "Court_1")
        po_customer_name: Playo customer name
        km_customer_name: Khelomore customer name
        db_url: PostgreSQL connection URL (uses env var if not provided)
    
    Returns:
        dict: {"status": "success"/"error", "message": "...", "id": id_or_none}
    """
    try:
        db_url = db_url or os.getenv('DATABASE_URL')
        
        if not db_url:
            raise ValueError("Database URL not provided and DATABASE_URL environment variable not set")
        
        print(f"🔍 Connecting to PostgreSQL...")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Insert the conflict record
        insert_query = """
        INSERT INTO conflict (slot, "Date", "Court", playo_user, khelomore_user, "Resolved", created_at)
        VALUES (%s, %s, %s, %s, %s, FALSE, CURRENT_TIMESTAMP)
        RETURNING id;
        """
        
        cursor.execute(insert_query, (
            slot_time_only,
            booking_date,
            selected_court,
            po_customer_name,
            km_customer_name
        ))
        
        inserted_id = cursor.fetchone()[0]
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print(f"✓ Conflict inserted successfully (ID: {inserted_id})")
        return {
            "status": "success",
            "message": f"Conflict recorded in database",
            "id": inserted_id
        }
        
    except Exception as e:
        print(f"✗ Error inserting conflict to database: {e}")
        return {
            "status": "error",
            "message": str(e),
            "id": None
        }


def get_conflicts_from_postgres(db_url=None, resolved_filter=None):
    """
    Retrieve conflicts from PostgreSQL database.
    
    Args:
        db_url: PostgreSQL connection URL (uses env var if not provided)
        resolved_filter: Filter by resolution status ('resolved', 'unresolved', or None for all)
    
    Returns:
        dict: {
            "status": "success"/"error",
            "count": number of conflicts,
            "conflicts": [list of conflict records],
            "message": "..." (error message if status is error)
        }
    """
    try:
        db_url = db_url or os.getenv('DATABASE_URL')
        
        if not db_url:
            raise ValueError("Database URL not provided and DATABASE_URL environment variable not set")
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Build query with optional filter
        if resolved_filter == 'resolved':
            query = 'SELECT * FROM conflict WHERE "Resolved" = TRUE ORDER BY created_at DESC'
        elif resolved_filter == 'unresolved':
            query = 'SELECT * FROM conflict WHERE "Resolved" = FALSE ORDER BY created_at DESC'
        else:
            query = 'SELECT * FROM conflict ORDER BY created_at DESC'
        
        cursor.execute(query)
        
        # Get column names
        columns = [description[0] for description in cursor.description]
        
        # Fetch all rows
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        conflicts = [dict(zip(columns, row)) for row in rows]
        
        cursor.close()
        conn.close()
        
        print(f"✓ Retrieved {len(conflicts)} conflicts from database")
        return {
            "status": "success",
            "count": len(conflicts),
            "conflicts": conflicts
        }
        
    except Exception as e:
        print(f"✗ Error retrieving conflicts from database: {e}")
        return {
            "status": "error",
            "count": 0,
            "conflicts": [],
            "message": str(e)
        }


def get_conflicts_summary(db_url=None):
    """
    Get a summary of conflicts (counts by status).
    
    Args:
        db_url: PostgreSQL connection URL (uses env var if not provided)
    
    Returns:
        dict: {
            "status": "success"/"error",
            "total": total count,
            "resolved": resolved count,
            "unresolved": unresolved count,
            "message": "..." (error message if status is error)
        }
    """
    try:
        db_url = db_url or os.getenv('DATABASE_URL')
        
        if not db_url:
            raise ValueError("Database URL not provided and DATABASE_URL environment variable not set")
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM conflict")
        total = cursor.fetchone()[0]
        
        # Get resolved count
        cursor.execute('SELECT COUNT(*) FROM conflict WHERE "Resolved" = TRUE')
        resolved = cursor.fetchone()[0]
        
        unresolved = total - resolved
        
        cursor.close()
        conn.close()
        
        print(f"✓ Summary: Total={total}, Resolved={resolved}, Unresolved={unresolved}")
        return {
            "status": "success",
            "total": total,
            "resolved": resolved,
            "unresolved": unresolved
        }
        
    except Exception as e:
        print(f"✗ Error getting conflicts summary: {e}")
        return {
            "status": "error",
            "total": 0,
            "resolved": 0,
            "unresolved": 0,
            "message": str(e)
        }


def update_conflict_resolved(conflict_id, db_url=None):
    """
    Mark a conflict as resolved.
    
    Args:
        conflict_id: ID of the conflict to resolve
        db_url: PostgreSQL connection URL (uses env var if not provided)
    
    Returns:
        dict: {"status": "success"/"error", "message": "..."}
    """
    try:
        db_url = db_url or os.getenv('DATABASE_URL')
        
        if not db_url:
            raise ValueError("Database URL not provided and DATABASE_URL environment variable not set")
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        update_query = 'UPDATE conflict SET "Resolved" = TRUE, updated_at = CURRENT_TIMESTAMP WHERE id = %s'
        cursor.execute(update_query, (conflict_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print(f"✓ Conflict {conflict_id} marked as resolved")
        return {
            "status": "success",
            "message": f"Conflict {conflict_id} marked as resolved"
        }
        
    except Exception as e:
        print(f"✗ Error updating conflict: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


def test_postgres_connection(db_url=None):
    """
    Test PostgreSQL connection and provide diagnostic information.
    
    Args:
        db_url: PostgreSQL connection URL (uses env var if not provided)
    
    Returns:
        dict with connection test results
    """
    try:
        db_url = db_url or os.getenv('DATABASE_URL')
        
        if not db_url:
            raise ValueError("Database URL not provided and DATABASE_URL environment variable not set")
        
        print("\n" + "="*60)
        print("🔍 PostgreSQL CONNECTION TEST")
        print("="*60)
        
        print(f"\n⏳ Attempting connection...")
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Test simple query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        print(f"\n✅ CONNECTION SUCCESSFUL!")
        print(f"\nPostgreSQL Version:")
        print(f"   {version[:80]}...")
        
        # Check if conflict table exists
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'conflict'
            );
        """)
        if cursor.fetchone()[0]:
            print(f"\n✅ 'conflict' table exists")
            
            # Get row count
            cursor.execute("SELECT COUNT(*) FROM conflict")
            count = cursor.fetchone()[0]
            print(f"   Current row count: {count}")
        else:
            print(f"\n⚠️  'conflict' table NOT found")
        
        cursor.close()
        conn.close()
        
        return {"status": "success", "message": "Connection successful"}
        
    except Exception as e:
        print(f"\n❌ CONNECTION FAILED!")
        print(f"\nError: {str(e)}")
        print(f"\n💡 Troubleshooting tips:")
        print(f"   1. Verify connection string is correct")
        print(f"   2. Check if DATABASE_URL environment variable is set")
        print(f"   3. Verify network connectivity to PostgreSQL server")
        print(f"   4. Check firewall settings")
        
        return {"status": "error", "message": str(e)}


# Example usage:
if __name__ == "__main__":
    print("\n1️⃣ Testing connection...")
    test_result = test_postgres_connection()
    
    if test_result["status"] == "success":
        print("\n\n2️⃣ Testing insert...")
        result = insert_conflict_to_postgres(
            slot_time_only="14:00:00",
            booking_date="2026-02-14",
            selected_court="Court_1",
            po_customer_name="John Doe",
            km_customer_name="Jane Smith"
        )
        print(f"\nInsert Result: {result}")
        
        if result["status"] == "success":
            print("\n\n3️⃣ Testing retrieve...")
            conflicts = get_conflicts_from_postgres()
            print(f"\nConflicts: {conflicts['count']} found")
            
            print("\n\n4️⃣ Testing summary...")
            summary = get_conflicts_summary()
            print(f"\nSummary: {summary}")
    else:
        print("\n⚠️ Skipping tests due to connection failure")
