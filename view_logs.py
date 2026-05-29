import sqlite3
import os
import config

def view_logs(limit=50):
    """
    Connects to the SQLite database and prints the recent visitor logs
    in a clean, tabular format for security auditing.
    """
    db_path = config.SQLITE_DB_PATH

    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        print("The database will be automatically created when the first visitor arrives.")
        return

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Check if the table exists first
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='visitors'")
        if not cursor.fetchone():
            print("📭 The 'visitors' table does not exist yet. No logs to display.")
            return

        # Fetch logs securely
        cursor.execute('''
            SELECT id, timestamp, name, person, decision, purpose 
            FROM visitors 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()

        if not rows:
            print("📭 The database is empty. No visitors have been recorded yet.")
            return

        # ====================================================================
        # PRINT HEADER
        # ====================================================================
        print("\n" + "=" * 90)
        print(f"{'🛡️ C7 SMART ROBO — SECURITY ADMIN LOGS 🛡️':^90}")
        print("=" * 90)
        print(f"{'ID':<5} | {'Timestamp':<20} | {'Visitor Name':<15} | {'Host':<12} | {'Decision':<10} | {'Purpose'}")
        print("-" * 90)

        # ====================================================================
        # PRINT ROWS
        # ====================================================================
        for row in rows:
            v_id, ts, name, person, decision, purpose = row
            
            # Handle potential None values safely
            name     = str(name) if name else "Unknown"
            person   = str(person) if person else "N/A"
            decision = str(decision) if decision else "Pending"
            purpose  = str(purpose) if purpose else "No given reason"
            
            # Truncate long strings to keep the table clean
            name     = (name[:12] + '...') if len(name) > 15 else name
            person   = (person[:9] + '...') if len(person) > 12 else person
            decision = (decision[:7] + '...') if len(decision) > 10 else decision
            purpose  = (purpose[:25] + '...') if len(purpose) > 28 else purpose
            
            # Print formatted row
            print(f"{v_id:<5} | {ts:<20} | {name:<15} | {person:<12} | {decision:<10} | {purpose}")
        
        print("-" * 90)
        print(f"Showing last {len(rows)} records. Visitor photos are stored in: {config.VISITORS_DIR}\n")


if __name__ == "__main__":
    view_logs(limit=50)  # Change this number to see more/fewer logs
