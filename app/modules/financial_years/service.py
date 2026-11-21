"""Financial Year Service layer."""

import math
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.modules.financial_years.models import FinancialYear
from app.modules.financial_years.schemas import (
    FinancialYearCreate,
    FinancialYearUpdate,
    FinancialYearResponse,
    FinancialYearListResponse,
)


class FinancialYearService:
    @staticmethod
    def list_years(
        db: Session,
        search: str | None = None,
        is_current: bool | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> FinancialYearListResponse:
        stmt = select(FinancialYear).where(FinancialYear.is_deleted == False)

        if search:
            q = f"%{search.strip()}%"
            stmt = stmt.where(
                (FinancialYear.name.ilike(q)) | (FinancialYear.code.ilike(q))
            )
        if is_current is not None:
            stmt = stmt.where(FinancialYear.is_current == is_current)
        if is_active is not None:
            stmt = stmt.where(FinancialYear.is_active == is_active)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(count_stmt) or 0

        stmt = stmt.order_by(FinancialYear.start_date.desc()).offset((page - 1) * page_size).limit(page_size)
        rows = db.scalars(stmt).all()

        return FinancialYearListResponse(
            items=[FinancialYearResponse.model_validate(r) for r in rows],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total > 0 else 1,
        )

    @staticmethod
    def get_by_id(db: Session, year_id: int) -> FinancialYear:
        stmt = select(FinancialYear).where(
            FinancialYear.id == year_id,
            FinancialYear.is_deleted == False,
        )
        row = db.scalar(stmt)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Financial year #{year_id} not found",
            )
        return row

    @staticmethod
    def get_current(db: Session) -> FinancialYear | None:
        stmt = select(FinancialYear).where(
            FinancialYear.is_current == True,
            FinancialYear.is_active == True,
            FinancialYear.is_deleted == False,
        )
        return db.scalar(stmt)

    @staticmethod
    def create(db: Session, payload: FinancialYearCreate, user_id: int | None = None) -> FinancialYearResponse:
        # Check duplicate code
        stmt = select(FinancialYear).where(
            FinancialYear.code == payload.code.strip().upper(),
            FinancialYear.is_deleted == False,
        )
        if db.scalar(stmt):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Financial year code '{payload.code}' already exists",
            )

        if payload.is_current:
            # Unset any other current year
            db.execute(
                update(FinancialYear)
                .where(FinancialYear.is_current == True)
                .values(is_current=False)
            )

        record = FinancialYear(
            name=payload.name.strip(),
            code=payload.code.strip().upper(),
            start_date=payload.start_date,
            end_date=payload.end_date,
            is_current=payload.is_current,
            is_active=payload.is_active,
            description=payload.description.strip() if payload.description else None,
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return FinancialYearResponse.model_validate(record)

    @staticmethod
    def update(
        db: Session,
        year_id: int,
        payload: FinancialYearUpdate,
        user_id: int | None = None,
    ) -> FinancialYearResponse:
        record = FinancialYearService.get_by_id(db, year_id)

        if payload.code and payload.code.strip().upper() != record.code:
            stmt = select(FinancialYear).where(
                FinancialYear.code == payload.code.strip().upper(),
                FinancialYear.id != year_id,
                FinancialYear.is_deleted == False,
            )
            if db.scalar(stmt):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Financial year code '{payload.code}' already exists",
                )
            record.code = payload.code.strip().upper()

        if payload.is_current is True:
            # Unset all other current years
            db.execute(
                update(FinancialYear)
                .where(FinancialYear.id != year_id, FinancialYear.is_current == True)
                .values(is_current=False)
            )
            record.is_current = True
        elif payload.is_current is False:
            record.is_current = False

        if payload.name is not None:
            record.name = payload.name.strip()
        if payload.start_date is not None:
            record.start_date = payload.start_date
        if payload.end_date is not None:
            record.end_date = payload.end_date
        if payload.is_active is not None:
            record.is_active = payload.is_active
        if payload.description is not None:
            record.description = payload.description.strip() if payload.description else None

        record.updated_by = user_id
        db.commit()
        db.refresh(record)
        return FinancialYearResponse.model_validate(record)

    @staticmethod
    def set_current(db: Session, year_id: int, user_id: int | None = None) -> FinancialYearResponse:
        record = FinancialYearService.get_by_id(db, year_id)
        if not record.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot set an inactive financial year as current",
            )

        db.execute(
            update(FinancialYear)
            .where(FinancialYear.is_current == True)
            .values(is_current=False)
        )
        record.is_current = True
        record.updated_by = user_id
        db.commit()
        db.refresh(record)
        return FinancialYearResponse.model_validate(record)
