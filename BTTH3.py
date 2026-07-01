from typing import List

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

app = FastAPI(title="API Quản lý lịch sử dụng phòng học")

rooms = [
    {"id": 1, "code": "R101", "name": "Room 101", "capacity": 30, "status": "AVAILABLE"},
    {"id": 2, "code": "R102", "name": "Room 102", "capacity": 20, "status": "AVAILABLE"},
    {"id": 3, "code": "R103", "name": "Room 103", "capacity": 40, "status": "MAINTENANCE"},
]

room_bookings = [
    {
        "id": 1,
        "room_id": 1,
        "class_name": "Python Basic",
        "student_count": 25,
        "date": "2026-07-01",
        "slot": "MORNING",
    }
]

class RoomBase(BaseModel):
    code: str
    name: str
    capacity: int = Field(gt=0)
    status: str

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        if value is None or not value.strip():
            raise ValueError("Mã phòng không được để trống")
        return value.strip().upper()

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if value is None or not value.strip():
            raise ValueError("Tên phòng không được để trống")
        return value.strip()

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        allowed = {"AVAILABLE", "IN_USE", "MAINTENANCE"}
        if value.upper() not in allowed:
            raise ValueError("Status phải là AVAILABLE, IN_USE hoặc MAINTENANCE")
        return value.upper()

class RoomCreate(RoomBase):
    pass

class RoomUpdate(RoomBase):
    pass

class RoomOut(RoomBase):
    id: int

class RoomBookingBase(BaseModel):
    room_id: int
    class_name: str
    student_count: int = Field(gt=0)
    date: str
    slot: str

    @field_validator("class_name")
    @classmethod
    def validate_class_name(cls, value: str) -> str:
        if value is None or not value.strip():
            raise ValueError("Tên lớp không được để trống")
        return value.strip()

    @field_validator("slot")
    @classmethod
    def validate_slot(cls, value: str) -> str:
        allowed = {"MORNING", "AFTERNOON", "EVENING"}
        if value.upper() not in allowed:
            raise ValueError("Slot phải là MORNING, AFTERNOON hoặc EVENING")
        return value.upper()


class RoomBookingCreate(RoomBookingBase):
    pass

class RoomBookingOut(RoomBookingBase):
    id: int

def find_room_by_id(room_id: int):
    for room in rooms:
        if room["id"] == room_id:
            return room
    return None

def is_room_code_exists(code: str, exclude_id: int | None = None) -> bool:
    normalized_code = code.strip().upper()
    for room in rooms:
        if room["code"] == normalized_code and room["id"] != exclude_id:
            return True
    return False

def is_booking_conflict(room_id: int, date: str, slot: str, exclude_id: int | None = None) -> bool:
    normalized_slot = slot.upper()
    for booking in room_bookings:
        if (
            booking["room_id"] == room_id
            and booking["date"] == date
            and booking["slot"] == normalized_slot
            and booking["id"] != exclude_id
        ):
            return True
    return False

@app.get("/rooms", response_model=List[RoomOut])
def get_rooms(
    keyword: str | None = Query(default=None, description="Tìm theo mã hoặc tên phòng"),
    status: str | None = Query(default=None, description="Lọc theo trạng thái phòng"),
    min_capacity: int | None = Query(default=None, ge=0, description="Sức chứa tối thiểu"),
):
    result = rooms

    if keyword:
        keyword = keyword.strip().lower()
        result = [
            room
            for room in result
            if keyword in room["code"].lower() or keyword in room["name"].lower()
        ]

    if status is not None:
        status_value = status.strip().upper()
        result = [room for room in result if room["status"] == status_value]

    if min_capacity is not None:
        result = [room for room in result if room["capacity"] >= min_capacity]

    return result

@app.get("/rooms/{room_id}", response_model=RoomOut)
def get_room_detail(room_id: int):
    room = find_room_by_id(room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

@app.post("/rooms", response_model=RoomOut, status_code=201)
def create_room(room: RoomCreate):
    if is_room_code_exists(room.code):
        raise HTTPException(status_code=400, detail="Mã phòng đã tồn tại")

    new_room = {
        "id": max((item["id"] for item in rooms), default=0) + 1,
        "code": room.code,
        "name": room.name,
        "capacity": room.capacity,
        "status": room.status,
    }
    rooms.append(new_room)
    return new_room

@app.put("/rooms/{room_id}", response_model=RoomOut)
def update_room(room_id: int, room: RoomUpdate):
    existing_room = find_room_by_id(room_id)
    if existing_room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    if is_room_code_exists(room.code, exclude_id=room_id):
        raise HTTPException(status_code=400, detail="Mã phòng đã tồn tại")

    existing_room.update(
        {
            "code": room.code,
            "name": room.name,
            "capacity": room.capacity,
            "status": room.status,
        }
    )
    return existing_room

@app.delete("/rooms/{room_id}")
def delete_room(room_id: int):
    for index, room in enumerate(rooms):
        if room["id"] == room_id:
            del rooms[index]
            return {"message": "Phòng học đã được xóa thành công"}

    raise HTTPException(status_code=404, detail="Room not found")

@app.get("/room-bookings", response_model=List[RoomBookingOut])
def get_room_bookings():
    return room_bookings

@app.post("/room-bookings", response_model=RoomBookingOut, status_code=201)
def create_room_booking(booking: RoomBookingCreate):
    room = find_room_by_id(booking.room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    if room["status"] != "AVAILABLE":
        raise HTTPException(status_code=400, detail="Phòng hiện không khả dụng")

    if booking.student_count > room["capacity"]:
        raise HTTPException(status_code=400, detail="Số học viên vượt quá sức chứa phòng")

    if is_booking_conflict(booking.room_id, booking.date, booking.slot):
        raise HTTPException(status_code=400, detail="Phòng đã được đặt vào ngày và ca này")

    new_booking = {
        "id": max((item["id"] for item in room_bookings), default=0) + 1,
        "room_id": booking.room_id,
        "class_name": booking.class_name,
        "student_count": booking.student_count,
        "date": booking.date,
        "slot": booking.slot.upper(),
    }
    room_bookings.append(new_booking)
    return new_booking
