from typing import List, Optional, Union
from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy import extract
from sqlalchemy.orm import Session

from .. import schemas, utils, models, oauth2
from ..database import get_db

router = APIRouter(
    prefix="/attendance",
    tags=["Worker's Attendance"]
)


@router.get('/worker/', response_model=Union[schemas.WorkerResponse, List[schemas.WorkerResponse]])
async def get_workers(
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
        location_id: Optional[str] = None,
        church_type: Optional[str] = None,
        gender: Optional[str] = None,
        occupation: Optional[str] = None,
        marital_status: Optional[str] = None,
        unit: Optional[str] = None,
):
    query = db.query(models.Workers)

    # Filter query based on provided parameters
    # user = current_user.location_id
    if not location_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Location Id is required")

    if location_id:
        query = query.filter(models.Workers.location_id.ilike(f'%{location_id}%'))

    if gender:
        query = query.filter(models.Workers.gender == gender,
                             models.Workers.location_id.ilike(f'%{location_id}%'))

    if church_type:
        query = query.filter(models.Workers.church_type == church_type,
                             models.Workers.location_id.ilike(f'%{location_id}%'))

    if occupation:
        query = query.filter(models.Workers.occupation.ilike(f'%{occupation}%'),
                             models.Workers.location_id.ilike(f'%{location_id}%'))

    if marital_status:
        query = query.filter(models.Workers.marital_status == marital_status,
                             models.Workers.location_id.ilike(f'%{location_id}%'))

    if unit:
        query = query.filter(models.Workers.unit.ilike(f'%{unit}%'),
                             models.Workers.location_id.ilike(f'%{location_id}%'))

    # Apply limit and offset to the query
    # query = query.offset(offset).limit(limit)

    # Execute the query
    workers = query.all()

    if not workers:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

    return workers


@router.get('/', response_model=Union[schemas.AttendanceResponse, List[schemas.AttendanceResponse]])
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
    query = db.query(models.Attendance)

    if role is None:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    if get_all:
        attendance = query.filter(models.Attendance.location_id.ilike(f'%{role}%')).offset(offset).limit(limit).all()

        if not attendance:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

        return attendance

    if _id:
        attendance = query.filter(models.Attendance.id == _id,
                                  models.Attendance.location_id.ilike(f'%{role}%')).first()

        if not attendance:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Attendance with id: {_id} not found!')

        return attendance

    if program_domain:
        query = query.filter(models.Attendance.program_domain == program_domain,
                             models.Attendance.location_id.ilike(f'%{role}%'))

    if program_type:
        query = query.filter(models.Attendance.program_type == program_type,
                             models.Attendance.location_id.ilike(f'%{role}%'))

    if location:
        query = query.filter(models.Attendance.location == location,
                             models.Attendance.location_id.ilike(f'%{role}%'))

    if date:
        query = query.filter(models.Attendance.date == date,
                             models.Attendance.location_id.ilike(f'%{role}%'))

    if start_month and end_month:
        query = query.filter(
            extract('month', models.Attendance.date) >= start_month,
            extract('month', models.Attendance.date) <= end_month,
            models.Attendance.location_id.ilike(f'%{role}%')
        )
    if start_year and end_year:
        query = query.filter(
            extract('year', models.Attendance.date) >= start_year,
            extract('year', models.Attendance.date) <= end_year,
            models.Attendance.location_id.ilike(f'%{role}%')
        )

    # Apply limit and offset to the query
    query = query.offset(offset).limit(limit)
    attendance = query.all()

    if not attendance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

    return attendance


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.AttendanceResponse)
async def create_attendance(attendance_: schemas.CreateAttendance, db: Session = Depends(get_db),
                            current_user: str = Depends(oauth2.get_current_user)):
    try:
        attendance = models.Attendance(**attendance_.dict())
        db.add(attendance)
        db.commit()
        db.refresh(attendance)

        return attendance
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Attendance could not be created.")


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attendance(_id: str, db: Session = Depends(get_db),
                            current_user: str = Depends(oauth2.get_current_user)):

    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    attendance = db.query(models.Attendance).filter(models.Attendance.id == _id,
                                                    models.Attendance.location_id.ilike(f'%{role}%'))

    if attendance.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Data with id: {_id} not found!")

    attendance.delete(synchronize_session=False)
    db.commit()

    return {"status": "successful!",
            "message": f"Attendance record with ID: {_id} deleted successfully!"
            }
