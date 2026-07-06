import os
import sqlite3
import json

DB_DIR = os.path.join(os.path.dirname(__file__), "database")
DB_PATH = os.path.join(DB_DIR, "scan_history.db")


class ScanDatabase:
    """Handles SQLite persistence for scan history."""

    def __init__(self):
        os.makedirs(DB_DIR, exist_ok=True)
        self.connection = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        query = """
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target TEXT NOT NULL,
            resolved_ip TEXT NOT NULL,
            scan_results TEXT NOT NULL,
            duration TEXT NOT NULL,
            timestamp INTEGER NOT NULL
        )
        """
        self.connection.execute(query)
        self.connection.commit()

    def save_scan(self, target, resolved_ip, results, duration, timestamp):
        scan_json = json.dumps(results)
        query = "INSERT INTO scans (target, resolved_ip, scan_results, duration, timestamp) VALUES (?, ?, ?, ?, ?)"
        self.connection.execute(query, (target, resolved_ip, scan_json, duration, timestamp))
        self.connection.commit()

    def close(self):
        self.connection.close()
