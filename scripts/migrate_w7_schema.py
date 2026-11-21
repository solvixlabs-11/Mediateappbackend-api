"""Migration script for Wave W7 backend schema updates."""

import sys
from pathlib import Path
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import engine


def migrate() -> None:
    print("Starting Wave W7 schema migration...")
    with engine.connect() as conn:
        # 1. Create mobile_registrations table if not exists
        conn.execute(
            text(
                """
            IF OBJECT_ID('mobile_registrations', 'U') IS NULL
            BEGIN
                CREATE TABLE mobile_registrations (
                    id BIGINT IDENTITY(1,1) PRIMARY KEY,
                    registration_code VARCHAR(100) NOT NULL,
                    employee_id BIGINT NOT NULL FOREIGN KEY REFERENCES users(id),
                    designation VARCHAR(100) NULL,
                    territory VARCHAR(100) NULL,
                    device_id_hash VARCHAR(255) NULL,
                    device_model VARCHAR(100) NULL,
                    app_version VARCHAR(50) NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
                    requested_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
                    decided_by_id BIGINT NULL FOREIGN KEY REFERENCES users(id),
                    decided_at DATETIMEOFFSET NULL,
                    comment NVARCHAR(MAX) NULL,
                    created_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
                    updated_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
                    created_by BIGINT NULL,
                    updated_by BIGINT NULL,
                    is_active BIT NOT NULL DEFAULT 1,
                    is_deleted BIT NOT NULL DEFAULT 0,
                    row_version INT NOT NULL DEFAULT 1,
                    client_uuid VARCHAR(36) NULL UNIQUE
                );
                CREATE INDEX idx_mobile_reg_status ON mobile_registrations(status);
                CREATE INDEX idx_mobile_reg_emp ON mobile_registrations(employee_id);
            END
            """
            )
        )
        print("✓ Checked/Created mobile_registrations table")

        # 2. Add soft-delete columns to dcr_visits, planned_visits, and follow_ups
        for table_name in ["dcr_visits", "planned_visits", "follow_ups"]:
            for col, col_type in [
                ("deleted_at", "DATETIMEOFFSET NULL"),
                ("deleted_by_id", "BIGINT NULL"),
                ("deletion_reason", "NVARCHAR(MAX) NULL"),
                ("deletion_token", "VARCHAR(100) NULL"),
            ]:
                conn.execute(
                    text(
                        f"""
                    IF NOT EXISTS (
                        SELECT * FROM sys.columns 
                        WHERE object_id = OBJECT_ID('{table_name}') AND name = '{col}'
                    )
                    BEGIN
                        ALTER TABLE {table_name} ADD {col} {col_type};
                    END
                    """
                    )
                )
            print(f"✓ Checked/Added soft-delete columns to {table_name}")

        # 3. Create tour_plan_locks table if not exists
        conn.execute(
            text(
                """
            IF OBJECT_ID('tour_plan_locks', 'U') IS NULL
            BEGIN
                CREATE TABLE tour_plan_locks (
                    id BIGINT IDENTITY(1,1) PRIMARY KEY,
                    scope VARCHAR(50) NOT NULL, -- ALL, TERRITORY, EMPLOYEE
                    scope_id BIGINT NULL,
                    month INT NOT NULL,
                    year INT NOT NULL,
                    financial_year VARCHAR(20) NOT NULL,
                    cutoff_date DATE NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'LOCKED', -- LOCKED, UNLOCKED
                    reason NVARCHAR(MAX) NULL,
                    created_by_id BIGINT NOT NULL FOREIGN KEY REFERENCES users(id),
                    unlocked_by_id BIGINT NULL FOREIGN KEY REFERENCES users(id),
                    unlocked_at DATETIMEOFFSET NULL,
                    created_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
                    updated_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
                    created_by BIGINT NULL,
                    updated_by BIGINT NULL,
                    is_active BIT NOT NULL DEFAULT 1,
                    is_deleted BIT NOT NULL DEFAULT 0,
                    row_version INT NOT NULL DEFAULT 1,
                    client_uuid VARCHAR(36) NULL UNIQUE
                );
                CREATE INDEX idx_tp_locks_scope ON tour_plan_locks(scope, scope_id, year, month);
                CREATE INDEX idx_tp_locks_status ON tour_plan_locks(status);
            END
            """
            )
        )
        print("✓ Checked/Created tour_plan_locks table")

        conn.commit()
    print("Wave W7 schema migration completed successfully!")


if __name__ == "__main__":
    migrate()
