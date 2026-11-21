import pyodbc

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};SERVER=127.0.0.1,1433;DATABASE=mediate_mr_db;UID=sa;PWD=pRanjal@7272;TrustServerCertificate=yes',
    timeout=10
)
cur = conn.cursor()
cur.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME IN ('financial_years', 'app_releases', 'whats_new', 'releases')")
tables = [row[0] for row in cur.fetchall()]
print("Existing matching tables:", tables)

for t in tables:
    cur.execute(f"SELECT column_name, data_type FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '{t}'")
    cols = [(row[0], row[1]) for row in cur.fetchall()]
    print(f"{t} columns:", cols)

cur.close()
conn.close()
