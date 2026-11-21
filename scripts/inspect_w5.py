import os
import sys
sys.path.insert(0, os.path.abspath("."))
import pyodbc

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=127.0.0.1,1433;DATABASE=mediate_mr_db;UID=sa;PWD=pRanjal@7272;TrustServerCertificate=yes"
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME")
tables = [row[0] for row in cursor.fetchall()]
print("=== EXISTING DB TABLES ===", flush=True)
for t in tables:
    print(f" - {t}", flush=True)

check_tables = [
    "audit_logs",
    "app_settings",
    "geofence_settings",
    "expense_limits",
    "expenses",
    "expense_items",
    "user_territory_assignments",
    "customer_coverages",
    "customer_assignments",
    "master_items",
    "users",
    "designations",
    "mapping_batches",
    "mapping_batch_items"
]

import os
import sys
sys.path.insert(0, os.path.abspath("."))
import pyodbc

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=127.0.0.1,1433;DATABASE=mediate_mr_db;UID=sa;PWD=pRanjal@7272;TrustServerCertificate=yes"
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

print("=== CUSTOMER & TERRITORY COLUMNS ===", flush=True)
for table in ["doctors", "chemists", "stockists", "hospitals", "territories", "territory_areas"]:
    cursor.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}'")
    cols = [f"{r[0]} ({r[1]})" for r in cursor.fetchall()]
    print(f"\n[{table}]:", flush=True)
    print("  " + ", ".join(cols), flush=True)

conn.close()

