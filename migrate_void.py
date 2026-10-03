import sqlite3

def run_migration():
    conn = sqlite3.connect("trustvote.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = OFF")
    
    cursor.execute("PRAGMA table_info(ballot_items)")
    cols = [r[1] for r in cursor.fetchall()]
    if "is_void" not in cols:
        cursor.execute("DROP TABLE IF EXISTS ballot_items_new")
        cursor.execute("""
        CREATE TABLE ballot_items_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ballot_id INTEGER NOT NULL,
            position_id INTEGER NOT NULL,
            candidate_id INTEGER,
            is_void INTEGER DEFAULT 0,
            FOREIGN KEY (ballot_id) REFERENCES ballots(id) ON DELETE CASCADE,
            FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE CASCADE,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
        )
        """)
        cursor.execute("INSERT INTO ballot_items_new (id, ballot_id, position_id, candidate_id, is_void) SELECT id, ballot_id, position_id, candidate_id, 0 FROM ballot_items")
        cursor.execute("DROP TABLE ballot_items")
        cursor.execute("ALTER TABLE ballot_items_new RENAME TO ballot_items")
        conn.commit()
        print("MIGRATION_SUCCESS")
    else:
        print("ALREADY_MIGRATED")
        
    cursor.execute("PRAGMA foreign_keys = ON")
    conn.close()

if __name__ == "__main__":
    run_migration()
