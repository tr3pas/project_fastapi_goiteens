from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User, RepairRequest, AdminMessage, RequestStatus
from routes.auth import get_current_user, require_admin
from settings import get_db

router = APIRouter()

@router.get("/repairs")
async def get_all_repairs(
    new: int = Query(0),
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    if new == 1:
        stmt = select(RepairRequest).where(RepairRequest.status == RequestStatus.NEW)
    else:
        stmt = select(RepairRequest)
    
    repairs = await db.scalars(stmt)
    return repairs.all()


@router.post("/repair/{repair_id}/self/get")
async def take_repair(
    repair_id: int,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    admin_id = int(current_user["sub"])
    
    stmt = select(RepairRequest).where(RepairRequest.id == repair_id)
    repair = await db.scalar(stmt)
    
    if not repair:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repair not found")
    
    repair.admin_id = admin_id
    repair.status = RequestStatus.IN_PROGRESS
    
    await db.commit()
    await db.refresh(repair)
    return repair


@router.get("/self/repairs")
async def get_admin_repairs(
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    admin_id = int(current_user["sub"])
    
    stmt = select(RepairRequest).where(RepairRequest.admin_id == admin_id)
    repairs = await db.scalars(stmt)
    return repairs.all()


@router.put("/repair/{repair_id}/change/status")
async def change_repair_status(
    repair_id: int,
    new_status: RequestStatus,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(RepairRequest).where(RepairRequest.id == repair_id)
    repair = await db.scalar(stmt)
    
    if not repair:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repair not found")
    
    repair.status = new_status
    
    await db.commit()
    await db.refresh(repair)
    return repair


@router.post("/repair/{repair_id}/change/comment")
async def create_comment(
    repair_id: int,
    message: str,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    admin_id = int(current_user["sub"])
    
    stmt = select(RepairRequest).where(RepairRequest.id == repair_id)
    repair = await db.scalar(stmt)
    
    if not repair:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repair not found")
    
    new_message = AdminMessage(
        message=message,
        request_id=repair_id,
        admin_id=admin_id
    )
    
    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)
    return new_message