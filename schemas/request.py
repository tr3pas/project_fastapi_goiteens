from pydantic import BaseModel, ConfigDict, EmailStr
from models import RequestStatus
from typing import List
import datetime as dt

class RepairRequestOut_schemas(BaseModel):
    id: int
    description: str
    photo_url: str
    status: RequestStatus
    # required_time: dt.datetime
    class Config:
        from_attributes = True

class ListRepairRequestOut_schemas(BaseModel):
    repairs: List[RepairRequestOut_schemas]

class MessagesRepairRequestOut_schemas(BaseModel):
    id: int
    message: List

    class Config:
        from_attributes = True

class ListMessagesRepairRequestOut_schemas(BaseModel):
    messages: List[MessagesRepairRequestOut_schemas]

# class ListRepairRequests_schemas(BaseModel):
#     requests: List[RepairRequest_schemas]
