from datetime import datetime
from typing import List, Optional, Union
from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy import extract
from sqlalchemy.orm import Session

from .. import schemas, utils, models, oauth2
from ..database import get_db

router = APIRouter(
    prefix="/records",
    tags=["Invitee & Converts Record"]
)


@router.get('/read-record/', response_model=Union[schemas.RecordResponse, List[schemas.RecordResponse]])
async def get_records(
        _id: Optional[str] = None,
        offset: Optional[int] = 0,  # Default offset set to 0
        limit: Optional[int] = 100,  # Default limit set to 100
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
        user_access: None = Depends(oauth2.has_permission("read_record")),
        program_domain: Optional[str] = None,
        program_type: Optional[str] = None,
        location: Optional[str] = None,
        location_id: Optional[str] = None,
        date: Optional[str] = None,
        get_all: Optional[bool] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
):
    user_type = await utils.create_admin_access_id(current_user)

    if user_type is None:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    query = db.query(models.Record).filter(models.Record.location_id.ilike(f'%{user_type}%'),
                                           models.Record.is_deleted == False)

    if _id:
        query = query.filter(models.Record.id == _id)

    if program_domain:
        query = query.filter(models.Record.program_domain == program_domain)

    if program_type:
        query = query.filter(models.Record.program_type == program_type)

    if location:
        query = query.filter(models.Record.location == location)

    if location_id:
        query = query.filter(models.Record.location_id == location_id)

    if date:
        query = query.filter(models.Record.date == date)

    if month:
        query = query.filter(extract('month', models.Record.date) == month,
                             models.Record.location_id.ilike(f'%{user_type}%'))
    if year:
        query = query.filter(extract('year', models.Record.date) == year,
                             models.Record.location_id.ilike(f'%{user_type}%'))

    query = query.offset(offset).limit(limit)
    record = query.all()

    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No data found!")

    if get_all:
        return record

    # If a single user was requested by ID, return just that user
    if _id:
        if len(record) == 1:
            return record[0]

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Record with id: {_id} not found!')

    return record


@router.post('/create-record/', status_code=status.HTTP_201_CREATED, response_model=schemas.RecordResponse)
async def create_record(record: schemas.CreateRecord, db: Session = Depends(get_db),
                        current_user: str = Depends(oauth2.get_current_user),
                        # user_access: None = Depends(oauth2.has_permission("create_record"))
                        ):
    try:
        new_record = models.Record(**record.dict())
        db.add(new_record)
        db.commit()
        db.refresh(new_record)

        return new_record
    except Exception as e:
        db.rollback()  # Rollback changes in case of exception
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error! Record could not be saved.")


@router.patch("/update-record/", response_model=schemas.RecordResponse)
async def update_record(record_id: str, records: schemas.UpdateRecord, db: Session = Depends(get_db),
                        current_user: str = Depends(oauth2.get_current_user),
                        user_access: None = Depends(oauth2.has_permission("update_record"))
                        ):
    role = await utils.create_admin_access_id(current_user)
    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No read privilege for user type!")

    record_query = db.query(models.Record).filter(models.Record.id == record_id,
                                                  models.Record.is_deleted == False,
                                                  models.Record.location_id.ilike(f"%{role}%"))

    record = record_query.first()

    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {record_id} does not exist")

    if record.is_deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Record not found!")

    # Update the record with new data, and set the operation and last_modify fields
    updated_data = records.dict(exclude_unset=True)
    updated_data["last_modify"] = datetime.utcnow()
    updated_data["operation"] = "update"

    record_query.update(updated_data)
    db.commit()
    db.refresh(record)

    return record


@router.delete("/delete-record/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_record(record_id: str, db: Session = Depends(get_db),
                        current_user: str = Depends(oauth2.get_current_user),
                        user_access: None = Depends(oauth2.has_permission("delete_record"))
                        ):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    record = db.query(models.Record).filter(models.Record.id == record_id,
                                            models.Record.is_deleted == False,
                                            models.Record.location_id.ilike(f'%{role}%')).first()

    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Record with id: {record_id} does not exist")

    update_data = schemas.UpdateRecord(
        is_deleted=True,
        last_modify=datetime.now(),
        operation="delete"
    )

    # Update the user with the new data
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(record, field, value)

    db.commit()

    return {"status": "successful!",
            "message": f"Record with ID: {record_id} deleted successfully!"
            }
