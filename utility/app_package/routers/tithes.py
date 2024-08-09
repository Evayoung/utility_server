from datetime import datetime
from typing import List, Optional, Union
from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy import extract
from sqlalchemy.orm import Session

from .. import schemas, utils, models, oauth2
from ..database import get_db

router = APIRouter(
    prefix="/tithes",
    tags=["Tithes and Offering"]
)


@router.get('/read-tithe/', response_model=Union[schemas.TitheResponse, List[schemas.TitheResponse]])
async def get_tithes(
        _id: Optional[str] = None,
        limit: Optional[int] = 100,  # Default limit set to 100
        offset: Optional[int] = 0,  # Default offset set to 0
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
        user_access: None = Depends(oauth2.has_permission("read_tithe")),
        location_id: Optional[str] = None,
        date: Optional[str] = None,
        get_all: Optional[bool] = None,
        amount: Optional[float] = None,
        start_month: Optional[int] = None,
        end_month: Optional[int] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
):
    user_type = await utils.create_admin_access_id(current_user)

    if user_type is None:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    query = db.query(models.TitheAndOffering).filter(models.TitheAndOffering.location_id.ilike(f'%{user_type}%'),
                                                     models.TitheAndOffering.is_deleted == False)

    if _id:
        query = query.filter(models.TitheAndOffering.id == _id)

    if amount:
        query = query.filter(models.TitheAndOffering.amount == amount)

    if location_id:
        query = query.filter(models.TitheAndOffering.location_id == location_id)

    if date:
        query = query.filter(models.TitheAndOffering.date == date)

    if start_month and end_month:
        query = query.filter(
            extract('month', models.TitheAndOffering.date) >= start_month,
            extract('month', models.TitheAndOffering.date) <= end_month
        )

    if start_year and end_year:
        query = query.filter(
            extract('year', models.TitheAndOffering.date) >= start_year,
            extract('year', models.TitheAndOffering.date) <= end_year)

    # Apply limit and offset to the query
    query = query.offset(offset).limit(limit)
    tithe = query.all()

    if not tithe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found')

    if get_all:
        return tithe

    # If a single user was requested by ID, return just that user
    if _id:
        if len(tithe) == 1:
            return tithe[0]
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Tithe with id: {_id} not found!')

    return tithe


@router.post('/create-tithe/', status_code=status.HTTP_201_CREATED, response_model=schemas.TitheResponse)
async def create_tithes(tithes: schemas.CreateTithe, db: Session = Depends(get_db),
                        current_user: str = Depends(oauth2.get_current_user),
                        user_access: None = Depends(oauth2.has_permission("create_tithe"))):
    try:
        tithe = models.TitheAndOffering(**tithes.dict())
        db.add(tithe)
        db.commit()
        db.refresh(tithe)

        return tithe
    except Exception as e:
        db.rollback()  # Rollback changes in case of exception
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error! Tithe record could not be saved.")


@router.put("/update-tithe/", response_model=schemas.TitheResponse)
async def update_tithe(tithe_id: str, tithe_: schemas.UpdateTithe, db: Session = Depends(get_db),
                       current_user: str = Depends(oauth2.get_current_user),
                       user_access: None = Depends(oauth2.has_permission("update_tithe"))):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No read privilege for user type!")

    tithe_query = db.query(models.TitheAndOffering).filter(models.TitheAndOffering.id == tithe_id,
                                                           models.TitheAndOffering.is_deleted == False,
                                                           models.TitheAndOffering.location_id.ilike(f"%{role}%"))

    tithe = tithe_query.first()

    if tithe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tithe with id: {tithe_id} not found")

    if tithe.is_deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Record not found!")

    # Update the record with new data, and set the operation and last_modify fields
    updated_data = tithe_.dict(exclude_unset=True)
    updated_data["last_modify"] = datetime.utcnow()
    updated_data["operation"] = "update"

    tithe_query.update(updated_data)
    db.commit()
    db.refresh(tithe)

    return tithe


@router.delete("/delete-tithe/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tithes(tithe_id: str, db: Session = Depends(get_db),
                        current_user: str = Depends(oauth2.get_current_user),
                        user_access: None = Depends(oauth2.has_permission("delete_tithe"))):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    tithe = db.query(models.TitheAndOffering).filter(models.TitheAndOffering.id == tithe_id,
                                                     models.TitheAndOffering.is_deleted == False,
                                                     models.TitheAndOffering.location_id.ilike(f'%{role}%'))

    if tithe.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tithe with id: {tithe_id} not found")

    update_data = schemas.UpdateTithe(
        is_deleted=True,
        last_modify=datetime.now(),
        operation="delete"
    )

    # Update the user with the new data
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(tithe, field, value)
    db.commit()
    return {"status": "successful!",
            "message": f"Tithe with ID: {tithe_id} deleted successfully!"
            }
