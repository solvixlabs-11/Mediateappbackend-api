"""Wave W9 Database Migration: Financial Years & App Releases (What's New)"""

import pyodbc

conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=127.0.0.1,1433;"
    "DATABASE=mediate_mr_db;"
    "UID=sa;PWD=pRanjal@7272;"
    "TrustServerCertificate=yes;"
)

def run_migration():
    conn = pyodbc.connect(conn_str, timeout=30)
    conn.autocommit = True
    cursor = conn.cursor()

    print("[W9 MIGRATION] Creating financial_years table...")
    cursor.execute("""
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'financial_years')
    BEGIN
        CREATE TABLE financial_years (
            id BIGINT IDENTITY(1,1) PRIMARY KEY,
            client_uuid NVARCHAR(36) NULL UNIQUE,
            created_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            created_by BIGINT NULL,
            updated_by BIGINT NULL,
            is_active BIT NOT NULL DEFAULT 1,
            is_deleted BIT NOT NULL DEFAULT 0,
            row_version INT NOT NULL DEFAULT 1,
            name NVARCHAR(100) NOT NULL,
            code NVARCHAR(20) NOT NULL UNIQUE,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            is_current BIT NOT NULL DEFAULT 0,
            description NVARCHAR(255) NULL
        );
        CREATE INDEX ix_financial_years_code ON financial_years (code);
        CREATE INDEX ix_financial_years_is_current ON financial_years (is_current);
        CREATE INDEX ix_financial_years_is_active ON financial_years (is_active);
        PRINT 'Created financial_years table successfully.';
    END
    ELSE
    BEGIN
        PRINT 'financial_years table already exists.';
    END
    """)

    print("[W9 MIGRATION] Creating app_releases table...")
    cursor.execute("""
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'app_releases')
    BEGIN
        CREATE TABLE app_releases (
            id BIGINT IDENTITY(1,1) PRIMARY KEY,
            client_uuid NVARCHAR(36) NULL UNIQUE,
            created_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            created_by BIGINT NULL,
            updated_by BIGINT NULL,
            is_active BIT NOT NULL DEFAULT 1,
            is_deleted BIT NOT NULL DEFAULT 0,
            row_version INT NOT NULL DEFAULT 1,
            version NVARCHAR(30) NOT NULL,
            title NVARCHAR(200) NOT NULL,
            release_date DATE NOT NULL,
            release_type NVARCHAR(30) NOT NULL DEFAULT 'WEB_UPDATE',
            summary NVARCHAR(500) NOT NULL,
            highlights_json NVARCHAR(MAX) NULL,
            target_audience NVARCHAR(30) NOT NULL DEFAULT 'ALL',
            is_published BIT NOT NULL DEFAULT 1,
            apk_download_url NVARCHAR(500) NULL
        );
        CREATE INDEX ix_app_releases_version ON app_releases (version);
        CREATE INDEX ix_app_releases_release_date ON app_releases (release_date);
        CREATE INDEX ix_app_releases_is_published ON app_releases (is_published);
        PRINT 'Created app_releases table successfully.';
    END
    ELSE
    BEGIN
        PRINT 'app_releases table already exists.';
    END
    """)

    cursor.close()
    conn.close()
    print("[W9 MIGRATION] Migration completed successfully.")

if __name__ == "__main__":
    run_migration()
