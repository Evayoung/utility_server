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
    prefix="/counts",
    tags=["Counts"]
)


@router.get('/read-counts/', response_model=Union[schemas.CountResponse, List[schemas.CountResponse]])
async def get_counts(
        _id: Optional[int] = None,
        limit: Optional[int] = 100,  # Default limit set to 100
        offset: Optional[int] = 0,  # Default offset set to 0
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
        user_access: None = Depends(oauth2.has_permission("read_count")),
        program_domain: Optional[str] = None,
        program_type: Optional[str] = None,
        location_id: Optional[str] = None,
        date: Optional[str] = None,
        get_all: Optional[bool] = None,
        start_month: Optional[int] = None,  # Start month of range
        end_month: Optional[int] = None,  # End month of range
        start_year: Optional[int] = None,  # Start year of range
        end_year: Optional[int] = None,  # End year of range
        # Add other query parameters as needed
):
    user_type = await utils.create_admin_access_id(current_user)

    if user_type is None:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    query = db.query(models.Counter).filter(models.Counter.location_id.ilike(f'%{user_type}%'),
                                            models.Counter.is_deleted == False)

    if _id:
        query = query.filter(models.Counter.id == _id)

    if program_domain:
        query = query.filter(models.Counter.program_domain == program_domain)

    if program_type:
        query = query.filter(models.Counter.program_type == program_type)

    if location_id:
        query = query.filter(models.Counter.location_id == location_id)

    if date:
        query = query.filter(models.Counter.date == date)

    if start_month and end_month:
        query = query.filter(
            extract('month', models.Counter.date) >= start_month,
            extract('month', models.Counter.date) <= end_month)

    if start_year and end_year:
        query = query.filter(
            extract('year', models.Counter.date) >= start_year,
            extract('year', models.Counter.date) <= end_year)

    # Add conditions for other parameters
    # Apply limit and offset to the query
    query = query.offset(offset).limit(limit)
    counts = query.all()
    if not counts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found')

    if get_all:
        return counts

    # If a single user was requested by ID, return just that user
    if _id:
        if len(counts) == 1:
            return counts[0]
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Count with id: {_id} not found!')

    return counts


@router.post('/create-counts/', status_code=status.HTTP_201_CREATED, response_model=schemas.CountResponse)
async def create_count(counts: schemas.CreateCount, db: Session = Depends(get_db),
                       current_user: str = Depends(oauth2.get_current_user),
                       # user_access: None = Depends(oauth2.has_permission("create_count"))
                       ):
    try:
        new_count = models.Counter(**counts.dict())
        db.add(new_count)
        db.commit()
        db.refresh(new_count)

        date_time = await utils.format_date_time(str(new_count.created_at))

        await manager.broadcast(json.dumps(
            {
                "type": "notification",
                "user_id": current_user.user_id,
                "data": date_time,
                "note": "New count data submitted to the database, please check data for descriptions and more details"
            }
        ))
        return new_count
    except Exception as e:
        db.rollback()  # Rollback changes in case of exception
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error! Count could not be saved.")


# this api route update the counts already submitted to the database
@router.patch("/update-counts/", response_model=schemas.CountResponse)
async def update_count(count_id: str, counts: schemas.UpdateCount, db: Session = Depends(get_db),
                       current_user: str = Depends(oauth2.get_current_user),
                       user_access: None = Depends(oauth2.has_permission("update_count"))):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    count_query = db.query(models.Counter).filter(models.Counter.id == count_id,
                                                  models.Counter.is_deleted == False,
                                                  models.Counter.location_id.ilike(f"%{role}%"))

    record = count_query.first()

    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Count with id: {count_id} does not exist")

    if record.is_deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Record not found!")

    # Update the record with new data, and set the operation and last_modify fields
    updated_data = counts.dict(exclude_unset=True)
    updated_data["last_modify"] = datetime.utcnow()
    updated_data["operation"] = "update"

    count_query.update(updated_data)
    db.commit()
    db.refresh(record)

    await manager.broadcast(json.dumps(
        {
            "type": "notification",
            "user_id": current_user.user_id,
            "data": record.location_id
        }
    ))

    return record


@router.delete("/delete-counts/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_count(_id: str, db: Session = Depends(get_db),
                       current_user: str = Depends(oauth2.get_current_user),
                       user_access: None = Depends(oauth2.has_permission("delete_count"))
                       ):

    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    count = db.query(models.Counter).filter(models.Counter.id == _id,
                                            models.Counter.is_deleted == False,
                                            models.Counter.location_id.ilike(f'%{role}%')).first()

    if count is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Data with id: {_id} does not exist")

    update_data = schemas.UpdateCount(
        is_deleted=True,
        last_modify=datetime.now(),
        operation="delete"
    )

    # Update the user with the new data
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(count, field, value)
    db.commit()

    return {"status": "successful!",
            "message": f"Count record with ID: {_id} deleted successfully!"
            }


""" 
actually  i have my server folder structured like this

utility 
    |__requirement.txt
    |__run_server.py
    |__app_package
            |__config,py
            |__database.py
            |__main.py
            |__models.py
            |__oauth2.py
            |__schemas.py
            |__utils.py
            |__routers
                |__attendance.py
                |__auth.py
                |__counter.py
                |__websocket.py
                |__other py files
                

"""
