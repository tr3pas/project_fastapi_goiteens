from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, UploadFile, HTTPException, status
from sqlalchemy import select

from models import User, RepairRequest
from models.models import Users_in_Telegram
from routes.auth import get_current_user
from schemas.user import UserOut
from settings import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from tools.file_upload import generate_file_url, save_file
from schemas.request import ListMessagesRepairRequestOut_schemas, ListRepairRequestOut_schemas, MessagesRepairRequestOut_schemas, RepairRequestOut_schemas

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
    required_time: datetime = Form(None)
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
        required_time=required_time
    )

    db.add(new_req)
    await db.commit()
    await db.refresh(new_req)
    return new_req


@router.get("/repairs")
async def get_all_repairs(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repairs = await db.scalars(
        select(RepairRequest).where(RepairRequest.user_id == int(current_user["sub"]))
    )
    return repairs.all()


@router.get("/repair/{repair_id}")
async def get_repair_request(
    repair_id: int, 
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(RepairRequest).where(RepairRequest.id == int(repair_id) and RepairRequest.user_id == current_user['sub'])
    repair_request = await db.scalar(stmt)
    
    if not repair_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repair request not found")
    
    return repair_request


@router.put("/repair/{repair_id}")
async def update_repair_request(
    repair_id: int, 
    bgt: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    description: str = Form(None),
    image: UploadFile | None = File(None),
    required_time: datetime | None = Form(None)
):
    stmt = select(RepairRequest).where(
        RepairRequest.id == repair_id,
        RepairRequest.user_id == int(current_user["sub"])
    )
    result = await db.execute(stmt)
    repair = result.scalar_one_or_none()
    
    if not repair:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repair request not found")
    
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
    db: AsyncSession = Depends(get_db)
):
    stmt = select(RepairRequest).where(
        RepairRequest.id == repair_id,
        RepairRequest.user_id == int(current_user["sub"])
    )
    result = await db.execute(stmt)
    repair = result.scalar_one_or_none()
    
    if not repair:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repair request not found")
    
    await db.delete(repair)
    await db.commit()
    return {"message": f"Repair request {repair_id} deleted successfully"}

@router.get("/tg/repairs", response_model=ListRepairRequestOut_schemas)
async def get_repairs_by_tg_id(
    tg_id: int = Query(),  db: AsyncSession = Depends(get_db)
):
    stmt = select(Users_in_Telegram).where(Users_in_Telegram.user_tg_id == str(tg_id))
    user_tg = await db.scalar(stmt)
    repairs = await db.scalars(select(RepairRequest).where(RepairRequest.user_id == int(user_tg.user_in_site)))
    repairs_list = repairs.all()


    repairs_data = []
    for repair in repairs_list:
        repairs_data.append(RepairRequestOut_schemas(
            id=repair.id,
            description=repair.description,
            photo_url=repair.photo_url,
            status=repair.status))
    return {"repairs": repairs_data}

@router.get("/messages", response_model=ListMessagesRepairRequestOut_schemas)
async def get_repairs_by_tg_id(
    tg_id: int = Query(),repair_id:int = Query(),  db: AsyncSession = Depends(get_db),
):
    stmt = select(Users_in_Telegram).where(Users_in_Telegram.user_tg_id == str(tg_id))
    user_tg = await db.scalar(stmt)
    repairs = await db.scalars(select(RepairRequest).where(RepairRequest.user_id == int(user_tg.user_in_site) and RepairRequest.id == repair_id))
    repairs_list = repairs.all()

    messages_data = []
    for repair in repairs_list:
        messages_data.append(MessagesRepairRequestOut_schemas(
        id=repair.id,
        message=repair.messages
    ))
    return {"messages": messages_data}