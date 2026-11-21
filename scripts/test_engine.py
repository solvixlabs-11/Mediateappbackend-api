from sqlalchemy import create_engine, text

for url in [
    "mssql+pyodbc://sa:pRanjal%407272@127.0.0.1:1433/mediate_mr_db?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes",
    "mssql+pyodbc://sa:pRanjal%407272@localhost\\SQLEXPRESS/mediate_mr_db?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes",
    "mssql+pyodbc://sa:pRanjal%407272@localhost/mediate_mr_db?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes",
]:
    try:
        eng = create_engine(url, connect_args={"timeout": 3})
        with eng.connect() as c:
            r = c.execute(text("SELECT 1")).scalar()
            print("SUCCESS:", url.split("@")[1].split("?")[0], "->", r, flush=True)
            break
    except Exception as e:
        print("FAIL:", url.split("@")[1].split("?")[0], "->", str(e)[:120], flush=True)
