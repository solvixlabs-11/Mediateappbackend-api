"""Migration script for Wave W6 backend schema updates."""

import sys
from pathlib import Path
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import engine


def migrate() -> None:
    print("Starting Wave W6 schema migration...")
    with engine.connect() as conn:
        # 1. Add is_provisional to master_items if not exists
        conn.execute(
            text(
                """
            IF NOT EXISTS (
                SELECT * FROM sys.columns 
                WHERE object_id = OBJECT_ID('master_items') AND name = 'is_provisional'
            )
            BEGIN
                ALTER TABLE master_items ADD is_provisional BIT NOT NULL DEFAULT 0;
            END
            """
            )
        )

        # Drop newly created empty tables to recreate with correct DATETIMEOFFSET columns
        conn.execute(
            text(
                """
            IF OBJECT_ID('expense_payouts', 'U') IS NOT NULL DROP TABLE expense_payouts;
            IF OBJECT_ID('meetings', 'U') IS NOT NULL DROP TABLE meetings;
            IF OBJECT_ID('company_profile', 'U') IS NOT NULL DROP TABLE company_profile;

            CREATE TABLE company_profile (
                id BIGINT IDENTITY(1,1) PRIMARY KEY,
                company_name VARCHAR(150) NOT NULL,
                company_code VARCHAR(50) NOT NULL,
                area VARCHAR(100) NULL,
                address NVARCHAR(MAX) NULL,
                city VARCHAR(100) NULL,
                state VARCHAR(100) NULL,
                pincode VARCHAR(20) NULL,
                phone_no VARCHAR(50) NULL,
                mobile_no VARCHAR(50) NULL,
                email VARCHAR(100) NULL,
                website VARCHAR(100) NULL,
                logo_file_id BIGINT NULL,
                signature_file_id BIGINT NULL,
                client_uuid VARCHAR(36) NULL UNIQUE,
                created_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
                updated_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
                created_by BIGINT NULL,
                updated_by BIGINT NULL,
                is_active BIT NOT NULL DEFAULT 1,
                is_deleted BIT NOT NULL DEFAULT 0,
                row_version INT NOT NULL DEFAULT 1
            );

            CREATE TABLE meetings (
                id BIGINT IDENTITY(1,1) PRIMARY KEY,
                agenda NVARCHAR(255) NOT NULL,
                meeting_type VARCHAR(50) NOT NULL DEFAULT 'CYCLE_MEETING',
                start_date DATETIME NOT NULL,
                end_date DATETIME NOT NULL,
                created_by_id BIGINT NOT NULL FOREIGN KEY REFERENCES users(id),
                organiser_id BIGINT NOT NULL FOREIGN KEY REFERENCES users(id),
                location NVARCHAR(255) NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'DRAFT',
                remarks NVARCHAR(MAX) NULL,
                client_uuid VARCHAR(36) NULL UNIQUE,
                created_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
                updated_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
                created_by BIGINT NULL,
                updated_by BIGINT NULL,
                is_active BIT NOT NULL DEFAULT 1,
                is_deleted BIT NOT NULL DEFAULT 0,
                row_version INT NOT NULL DEFAULT 1
            );

            CREATE TABLE expense_payouts (
                id BIGINT IDENTITY(1,1) PRIMARY KEY,
                expense_id INT NOT NULL UNIQUE FOREIGN KEY REFERENCES expenses(id) ON DELETE CASCADE,
                amount DECIMAL(12,2) NOT NULL,
                payment_mode VARCHAR(50) NOT NULL,
                reference_no VARCHAR(100) NOT NULL,
                payment_date DATE NOT NULL,
                processed_by_id BIGINT NOT NULL FOREIGN KEY REFERENCES users(id),
                idempotency_key VARCHAR(64) NULL UNIQUE,
                remarks VARCHAR(255) NULL,
                client_uuid VARCHAR(36) NULL UNIQUE,
                created_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
                updated_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
                created_by BIGINT NULL,
                updated_by BIGINT NULL,
                is_active BIT NOT NULL DEFAULT 1,
                is_deleted BIT NOT NULL DEFAULT 0,
                row_version INT NOT NULL DEFAULT 1
            );
            """
            )
        )
        conn.commit()
    print("Wave W6 schema recreated cleanly with DATETIMEOFFSET.")


if __name__ == "__main__":
    migrate()
