import pyodbc

conn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER=127.0.0.1,1433;DATABASE=mediate_mr_db;UID=sa;PWD=pRanjal@7272;TrustServerCertificate=yes")
cur = conn.cursor()
cur.execute("SELECT version_num FROM alembic_version")
print("Alembic current version:", cur.fetchall())
conn.close()
