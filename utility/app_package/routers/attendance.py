import json
from datetime import datetime
from typing import List, Optional, Union
from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy import extract
from sqlalchemy.orm import Session

from .. import schemas, utils, models, oauth2
from ..database import get_db
from .websocket import manager

router = APIRouter(
    prefix="/attendance",
    tags=["Worker's Attendance"]
)


@router.get('/get-worker-for-attendance/', response_model=Union[schemas.WorkerResponse, List[schemas.WorkerResponse]])
async def get_workers(
        db: Session = Depends(get_db),
        limit: Optional[int] = 100,  # Default limit set to 100
        offset: Optional[int] = 0,  # Default offset set to 0
        current_user: str = Depends(oauth2.get_current_user),
        user_access: None = Depends(oauth2.has_permission("mark_attendance")),
        location_id: Optional[str] = None,
        worker_id: Optional[str] = None,
        church_type: Optional[str] = None,
        gender: Optional[str] = None,
        occupation: Optional[str] = None,
        marital_status: Optional[str] = None,
        unit: Optional[str] = None,
):

    if not location_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Location Id is required")

    query = db.query(models.Workers).filter(models.Workers.location_id.ilike(f'%{location_id}%'),
                                            models.Workers.is_deleted == False)

    # Filter query based on provided parameters
    if worker_id:
        query = query.filter(models.Workers.user_id == worker_id)

    if location_id:
        query = query.filter(models.Workers.location_id.ilike(f'%{location_id}%'))

    if gender:
        query = query.filter(models.Workers.gender == gender)

    if church_type:
        query = query.filter(models.Workers.church_type == church_type)

    if occupation:
        query = query.filter(models.Workers.occupation.ilike(f'%{occupation}%'))

    if marital_status:
        query = query.filter(models.Workers.marital_status == marital_status)

    if unit:
        query = query.filter(models.Workers.unit.ilike(f'%{unit}%'))

    # Apply limit and offset to the query
    query = query.offset(offset).limit(limit)

    # Execute the query
    workers = query.all()

    if not workers:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Worker not found!')

    # If a single user was requested by ID, return just that user
    if worker_id:
        if len(workers) == 1:
            return workers[0]
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Worker with id: {worker_id} not found!')

    return workers


@router.get('/read-attendance/', response_model=Union[schemas.AttendanceResponse, List[schemas.AttendanceResponse]])
async def get_attendance(
        _id: Optional[int] = None,
        limit: Optional[int] = 100,  # Default limit set to 100
        offset: Optional[int] = 0,    # Default offset set to 0
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
        program_domain: Optional[str] = None,
        program_type: Optional[str] = None,
        location: Optional[str] = None,
        date: Optional[str] = None,
        get_all: Optional[bool] = None,
        start_month: Optional[int] = None,
        end_month: Optional[int] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        # Add other query parameters as needed
):
    role = await utils.create_admin_access_id(current_user)

    if role is None:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    query = db.query(models.Attendance).filter(models.Attendance.location_id.ilike(f'%{role}%'),
                                               models.Attendance.is_deleted == False)

    if _id:
        query = query.filter(models.Attendance.id == _id)

    if program_domain:
        query = query.filter(models.Attendance.program_domain == program_domain)

    if program_type:
        query = query.filter(models.Attendance.program_type == program_type)

    if location:
        query = query.filter(models.Attendance.location == location)

    if date:
        query = query.filter(models.Attendance.date == date)

    if start_month and end_month:
        query = query.filter(
            extract('month', models.Attendance.date) >= start_month,
            extract('month', models.Attendance.date) <= end_month)

    if start_year and end_year:
        query = query.filter(
            extract('year', models.Attendance.date) >= start_year,
            extract('year', models.Attendance.date) <= end_year)

    # Apply limit and offset to the query
    query = query.offset(offset).limit(limit)
    attendance = query.all()

    if not attendance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

    if get_all:
        return attendance

    # If a single attendance was requested by ID, return just that attendance
    if _id:
        if len(attendance) == 1:
            return attendance[0]
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Attendance with id: {_id} not found!')

    return attendance


@router.post('/create-attendance/', status_code=status.HTTP_201_CREATED, response_model=schemas.AttendanceResponse)
async def create_attendance(attendance_: schemas.CreateAttendance, db: Session = Depends(get_db),
                            current_user: str = Depends(oauth2.get_current_user)):
    try:
        attendance = models.Attendance(**attendance_.dict())
        db.add(attendance)
        db.commit()
        db.refresh(attendance)

        date_time = await utils.format_date_time(str(attendance.created_at))

        await manager.broadcast(json.dumps(
            {
                "type": "notification",
                "user_id": current_user.user_id,
                "data": date_time,
                "note": "New attendance submitted to the database"
            }
        ))

        return attendance
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Attendance could not be created.")


@router.delete("/delete-attendance/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attendance(_id: str, db: Session = Depends(get_db),
                            current_user: str = Depends(oauth2.get_current_user)):

    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    attendance = db.query(models.Attendance).filter(models.Attendance.id == _id,
                                                    models.Attendance.is_deleted == False,
                                                    models.Attendance.location_id.ilike(f'%{role}%')).first()

    if attendance is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Data with id: {_id} not found!")

    update_data = schemas.UpdateAttendance(
        is_deleted=True,
        last_modify=datetime.now()
    )

    # Update the user with the new data
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(attendance, field, value)

    db.commit()

    return {"status": "successful!",
            "message": f"Attendance record with ID: {_id} deleted successfully!"
            }
