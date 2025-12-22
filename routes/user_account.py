from datetime import datetime

from fastapi import (APIRouter, BackgroundTasks, Depends, File, Form,
                     HTTPException, UploadFile, status)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import RepairRequest, User
from routes.auth import get_current_user
from schemas.user import UserOut
from settings import get_db
from tools.file_upload import generate_file_url, save_file

router = APIRouter()


@router.get("/user/me", response_model=UserOut)
async def user_me_data(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["sub"]
    stmt = select(User).where(User.id == int(user_id))
    user = await db.scalar(stmt)
    return user


@router.post("/repair/add")
async def create_repair_request(
    bgt: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    description: str = Form(...),
    image: UploadFile | None = File(None),
    required_time: datetime = Form(None),
):
    user_id = current_user["sub"]
    image_url = None
    if image:
        image_url = await generate_file_url(image.filename)
        bgt.add_task(save_file, image, image_url)

    new_req = RepairRequest(
        user_id=int(user_id),
        description=description,
        photo_url=image_url,
        required_time=required_time,
    )

    db.add(new_req)
    await db.commit()
    await db.refresh(new_req)
    return new_req


@router.get("/repairs")
async def get_all_repairs(
    current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    repairs = await db.scalars(
        select(RepairRequest).where(RepairRequest.user_id == int(current_user["sub"]))
    )
    return repairs.all()


@router.get("/repair/{repair_id}")
async def get_repair_request(
    repair_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(RepairRequest).where(RepairRequest.id == int(repair_id))
    repair_request = await db.scalar(stmt)

    if not repair_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Repair request not found"
        )

    return repair_request


@router.put("/repair/{repair_id}")
async def update_repair_request(
    repair_id: int,
    bgt: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    description: str = Form(None),
    image: UploadFile | None = File(None),
    required_time: datetime | None = Form(None),
):
    stmt = select(RepairRequest).where(
        RepairRequest.id == repair_id, RepairRequest.user_id == int(current_user["sub"])
    )
    result = await db.execute(stmt)
    repair = result.scalar_one_or_none()

    if not repair:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Repair request not found"
        )

    if description:
        repair.description = description
    if image:
        image_url = await generate_file_url(image.filename)
        bgt.add_task(save_file, image, image_url)
        repair.photo_url = image_url
    if required_time:
        repair.required_time = required_time

    await db.commit()
    await db.refresh(repair)
    return repair


@router.delete("/repair/{repair_id}")
async def delete_repair_request(
    repair_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(RepairRequest).where(
        RepairRequest.id == repair_id, RepairRequest.user_id == int(current_user["sub"])
    )
    result = await db.execute(stmt)
    repair = result.scalar_one_or_none()

    if not repair:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Repair request not found"
        )

    await db.delete(repair)
    await db.commit()
    return {"message": f"Repair request {repair_id} deleted successfully"}
