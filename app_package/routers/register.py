from typing import List, Optional, Union
from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy import extract
from sqlalchemy.orm import Session

from .. import schemas, utils, models, oauth2
from ..database import get_db

router = APIRouter(
    prefix="/record",
    tags=["Invitee & Converts Record"]
)


@router.get('/', response_model=Union[schemas.RecordResponse, List[schemas.RecordResponse]])
async def get_records(
        _id: Optional[str] = None,
        offset: Optional[int] = 0,  # Default offset set to 0
        limit: Optional[int] = 100,  # Default limit set to 100
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
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
    query = db.query(models.Record)
    if get_all:
        record = query.filter(models.Record.location_id.ilike(f'%{user_type}%')).all()
        if not record:
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail=f'Record is empty!')
        return record

    if _id:
        record = query.filter(models.Record.id == _id,
                              models.Record.location_id.ilike(f'%{user_type}%')).first()
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Record with id: {_id} not found!')
        return record

    if program_domain:
        query = query.filter(models.Record.program_domain == program_domain,
                             models.Record.location_id.ilike(f'%{user_type}%'))
    if program_type:
        query = query.filter(models.Record.program_type == program_type,
                             models.Record.location_id.ilike(f'%{user_type}%'))
    if location:
        query = query.filter(models.Record.location == location,
                             models.Record.location_id.ilike(f'%{user_type}%'))
    if location_id:
        query = query.filter(models.Record.location_id == location_id,
                             models.Record.location_id.ilike(f'%{user_type}%'))
    if date:
        query = query.filter(models.Record.date == date,
                             models.Record.location_id.ilike(f'%{user_type}%'))
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

    return record


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.RecordResponse)
async def create_record(record: schemas.CreateRecord, db: Session = Depends(get_db),
                        current_user: str = Depends(oauth2.get_current_user)):
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


@router.put("/{record_id}", response_model=schemas.RecordResponse)
async def update_record(record_id: str, records: schemas.UpdateRecord, db: Session = Depends(get_db),
                        current_user: str = Depends(oauth2.get_current_user)):

    role = await utils.create_admin_access_id(current_user)
    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No read privilege for user type!")

    record_query = db.query(models.User).filter(models.Record.id == record_id,
                                                models.Record.location_id.ilike(f"%{role}%"))

    record = record_query.first()

    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {record_id} does not exist")

    record_query.update(records.dict())
    db.commit()

    return record_query.first()


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_record(record_id: str, db: Session = Depends(get_db),
                        current_user: str = Depends(oauth2.get_current_user)):

    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    record = db.query(models.Record).filter(models.Record.id == record_id,
                                            models.Record.location_id.ilike(f'%{role}%'))

    if record.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Record with id: {record_id} does not exist")

    record.delete(synchronize_session=False)
    db.commit()

    return {"status": "successful!",
            "message": f"Record with ID: {record_id} deleted successfully!"
            }
