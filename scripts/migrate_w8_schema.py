"""Migration script for Wave W8 Sample Inventory & Stock Management schema."""

import sys
from pathlib import Path
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import engine


def migrate() -> None:
    print("Starting Wave W8 schema migration...")
    with engine.connect() as conn:
        # 1. Create sample_stocks table
        conn.execute(
            text(
                """
            IF OBJECT_ID('sample_stocks', 'U') IS NULL
            BEGIN
                CREATE TABLE sample_stocks (
                    id BIGINT IDENTITY(1,1) PRIMARY KEY,
                    product_id INT NOT NULL FOREIGN KEY REFERENCES products(id),
                    batch_number VARCHAR(50) NOT NULL,
                    mfg_date DATE NULL,
                    expiry_date DATE NOT NULL,
                    quantity_received INT NOT NULL DEFAULT 0,
                    quantity_allocated INT NOT NULL DEFAULT 0,
                    quantity_issued INT NOT NULL DEFAULT 0,
                    quantity_balance INT NOT NULL DEFAULT 0,
                    created_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
                    updated_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
                    created_by BIGINT NULL,
                    updated_by BIGINT NULL,
                    is_active BIT NOT NULL DEFAULT 1,
                    is_deleted BIT NOT NULL DEFAULT 0,
                    row_version INT NOT NULL DEFAULT 1,
                    client_uuid VARCHAR(36) NULL UNIQUE
                );
                CREATE INDEX idx_sample_stocks_product ON sample_stocks(product_id);
                CREATE INDEX idx_sample_stocks_batch ON sample_stocks(batch_number);
                CREATE INDEX idx_sample_stocks_expiry ON sample_stocks(expiry_date);
            END
            """
            )
        )
        print("✓ Checked/Created sample_stocks table")

        # 2. Create sample_inwards table
        conn.execute(
            text(
                """
            IF OBJECT_ID('sample_inwards', 'U') IS NULL
            BEGIN
                CREATE TABLE sample_inwards (
                    id BIGINT IDENTITY(1,1) PRIMARY KEY,
                    challan_number VARCHAR(100) NOT NULL UNIQUE,
                    inward_date DATE NOT NULL,
                    product_id INT NOT NULL FOREIGN KEY REFERENCES products(id),
                    batch_number VARCHAR(50) NOT NULL,
                    mfg_date DATE NULL,
                    expiry_date DATE NOT NULL,
                    quantity INT NOT NULL,
                    unit_cost FLOAT NOT NULL DEFAULT 0.0,
                    supplier_name NVARCHAR(150) NULL,
                    remarks NVARCHAR(MAX) NULL,
                    received_by_id BIGINT NULL FOREIGN KEY REFERENCES users(id),
                    created_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
                    updated_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
                    created_by BIGINT NULL,
                    updated_by BIGINT NULL,
                    is_active BIT NOT NULL DEFAULT 1,
                    is_deleted BIT NOT NULL DEFAULT 0,
                    row_version INT NOT NULL DEFAULT 1,
                    client_uuid VARCHAR(36) NULL UNIQUE
                );
                CREATE INDEX idx_sample_inwards_challan ON sample_inwards(challan_number);
                CREATE INDEX idx_sample_inwards_date ON sample_inwards(inward_date);
                CREATE INDEX idx_sample_inwards_prod ON sample_inwards(product_id);
            END
            """
            )
        )
        print("✓ Checked/Created sample_inwards table")

        # 3. Create sample_allocations table
        conn.execute(
            text(
                """
            IF OBJECT_ID('sample_allocations', 'U') IS NULL
            BEGIN
                CREATE TABLE sample_allocations (
                    id BIGINT IDENTITY(1,1) PRIMARY KEY,
                    user_id BIGINT NOT NULL FOREIGN KEY REFERENCES users(id),
                    product_id INT NOT NULL FOREIGN KEY REFERENCES products(id),
                    month INT NOT NULL,
                    year INT NOT NULL,
                    allocated_quantity INT NOT NULL DEFAULT 0,
                    issued_quantity INT NOT NULL DEFAULT 0,
                    distributed_quantity INT NOT NULL DEFAULT 0,
                    balance_quantity INT NOT NULL DEFAULT 0,
                    allocated_by_id BIGINT NULL FOREIGN KEY REFERENCES users(id),
                    created_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
                    updated_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
                    created_by BIGINT NULL,
                    updated_by BIGINT NULL,
                    is_active BIT NOT NULL DEFAULT 1,
                    is_deleted BIT NOT NULL DEFAULT 0,
                    row_version INT NOT NULL DEFAULT 1,
                    client_uuid VARCHAR(36) NULL UNIQUE
                );
                CREATE INDEX idx_sample_alloc_user_prod ON sample_allocations(user_id, product_id, year, month);
            END
            """
            )
        )
        print("✓ Checked/Created sample_allocations table")

        # 4. Create sample_issues table
        conn.execute(
            text(
                """
            IF OBJECT_ID('sample_issues', 'U') IS NULL
            BEGIN
                CREATE TABLE sample_issues (
                    id BIGINT IDENTITY(1,1) PRIMARY KEY,
                    issue_number VARCHAR(100) NOT NULL UNIQUE,
                    issue_date DATE NOT NULL,
                    user_id BIGINT NOT NULL FOREIGN KEY REFERENCES users(id),
                    product_id INT NOT NULL FOREIGN KEY REFERENCES products(id),
                    batch_number VARCHAR(50) NOT NULL,
                    quantity INT NOT NULL,
                    dispatch_mode VARCHAR(50) NOT NULL DEFAULT 'COURIER',
                    tracking_reference VARCHAR(100) NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'DISPATCHED',
                    received_date DATE NULL,
                    remarks NVARCHAR(MAX) NULL,
                    issued_by_id BIGINT NULL FOREIGN KEY REFERENCES users(id),
                    created_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
                    updated_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
                    created_by BIGINT NULL,
                    updated_by BIGINT NULL,
                    is_active BIT NOT NULL DEFAULT 1,
                    is_deleted BIT NOT NULL DEFAULT 0,
                    row_version INT NOT NULL DEFAULT 1,
                    client_uuid VARCHAR(36) NULL UNIQUE
                );
                CREATE INDEX idx_sample_issues_user ON sample_issues(user_id);
                CREATE INDEX idx_sample_issues_prod ON sample_issues(product_id);
                CREATE INDEX idx_sample_issues_date ON sample_issues(issue_date);
            END
            """
            )
        )
        print("✓ Checked/Created sample_issues table")

        # 5. Create sample_ledgers table
        conn.execute(
            text(
                """
            IF OBJECT_ID('sample_ledgers', 'U') IS NULL
            BEGIN
                CREATE TABLE sample_ledgers (
                    id BIGINT IDENTITY(1,1) PRIMARY KEY,
                    transaction_type VARCHAR(50) NOT NULL, -- INWARD, ALLOCATION, ISSUE, SAMPLE_DISTRIBUTED_DCR, ADJUSTMENT
                    product_id INT NOT NULL FOREIGN KEY REFERENCES products(id),
                    batch_number VARCHAR(50) NULL,
                    user_id BIGINT NULL FOREIGN KEY REFERENCES users(id),
                    quantity INT NOT NULL,
                    balance_after INT NOT NULL,
                    reference_id BIGINT NULL,
                    reference_type VARCHAR(50) NULL,
                    notes NVARCHAR(255) NULL,
                    created_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
                    updated_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
                    created_by BIGINT NULL,
                    updated_by BIGINT NULL,
                    is_active BIT NOT NULL DEFAULT 1,
                    is_deleted BIT NOT NULL DEFAULT 0,
                    row_version INT NOT NULL DEFAULT 1,
                    client_uuid VARCHAR(36) NULL UNIQUE
                );
                CREATE INDEX idx_sample_ledger_prod ON sample_ledgers(product_id);
                CREATE INDEX idx_sample_ledger_type ON sample_ledgers(transaction_type);
            END
            """
            )
        )
        print("✓ Checked/Created sample_ledgers table")

        conn.commit()
    print("Wave W8 schema migration completed successfully!")


if __name__ == "__main__":
    migrate()
