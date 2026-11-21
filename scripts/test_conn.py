import pyodbc

conn_strings = [
    "DRIVER={ODBC Driver 17 for SQL Server};SERVER=127.0.0.1,1433;DATABASE=mediate_mr_db;UID=sa;PWD=pRanjal@7272;TrustServerCertificate=yes;Connection Timeout=2",
    "DRIVER={ODBC Driver 17 for SQL Server};SERVER=.\\SQLEXPRESS;DATABASE=mediate_mr_db;UID=sa;PWD=pRanjal@7272;TrustServerCertificate=yes;Connection Timeout=2",
    "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=mediate_mr_db;UID=sa;PWD=pRanjal@7272;TrustServerCertificate=yes;Connection Timeout=2",
    "DRIVER={ODBC Driver 17 for SQL Server};SERVER=.\\SQLEXPRESS;DATABASE=mediate_mr_db;Trusted_Connection=yes;TrustServerCertificate=yes;Connection Timeout=2",
    "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=mediate_mr_db;UID=sa;PWD=pRanjal@7272;TrustServerCertificate=yes;Connection Timeout=2",
]

for cs in conn_strings:
    try:
        cn = pyodbc.connect(cs)
        print("SUCCESS:", cs.split(";")[1], flush=True)
        cn.close()
        break
    except Exception as e:
        print("FAIL:", cs.split(";")[1], "->", str(e)[:120], flush=True)
