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


@router.get('/', response_model=Union[schemas.TitheResponse, List[schemas.TitheResponse]])
async def get_tithes(
        _id: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
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
    query = db.query(models.TitheAndOffering)
    if get_all:
        tithes = query.filter(models.TitheAndOffering.location_id.ilike(f'%{user_type}%')).all()

        return tithes

    if _id:
        tithes = query.filter(models.TitheAndOffering.id == _id,
                              models.TitheAndOffering.location_id.ilike(f'%{user_type}%')).first()
        if not tithes:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Tithe with id: {_id} not found!')

        return tithes

    if amount:
        query = query.filter(models.TitheAndOffering.amount == amount,
                             models.TitheAndOffering.location_id.ilike(f'%{user_type}%'))

    if location_id:
        query = query.filter(models.TitheAndOffering.location_id == location_id,
                             models.TitheAndOffering.location_id.ilike(f'%{user_type}%'))

    if date:
        query = query.filter(models.TitheAndOffering.date == date,
                             models.TitheAndOffering.location_id.ilike(f'%{user_type}%'))

    if start_month and end_month:
        query = query.filter(
            extract('month', models.TitheAndOffering.date) >= start_month,
            extract('month', models.TitheAndOffering.date) <= end_month
        )
    if start_year and end_year:
        query = query.filter(
            extract('year', models.TitheAndOffering.date) >= start_year,
            extract('year', models.TitheAndOffering.date) <= end_year,
            models.TitheAndOffering.location_id.ilike(f'%{user_type}%')
        )
    # Add conditions for other parameters

    tithe = query.all()

    if not tithe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found')

    return tithe


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.TitheResponse)
async def create_tithes(tithes: schemas.CreateTithe, db: Session = Depends(get_db),
                        current_user: str = Depends(oauth2.get_current_user)):
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


@router.put("/{tithe_id}", response_model=schemas.TitheResponse)
async def update_tithe(tithe_id: str, tithe_: schemas.UpdateTithe, db: Session = Depends(get_db),
                       current_user: str = Depends(oauth2.get_current_user)):

    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No read privilege for user type!")

    tithe_query = db.query(models.TitheAndOffering).filter(models.TitheAndOffering.id == tithe_id,
                                                           models.TitheAndOffering.location_id.ilike(f"%{role}%"))

    tithe = tithe_query.first()

    if tithe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tithe with id: {tithe_id} not found")

    tithe_query.update(tithe_.dict())
    db.commit()

    return tithe_query.first()


@router.delete("/{tithe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tithes(tithe_id: str, db: Session = Depends(get_db),
                        current_user: str = Depends(oauth2.get_current_user)):

    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    tithe = db.query(models.TitheAndOffering).filter(models.TitheAndOffering.id == tithe_id,
                                                     models.TitheAndOffering.location_id.ilike(f'%{role}%'))

    if tithe.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tithe with id: {tithe_id} not found")

    tithe.delete(synchronize_session=False)
    db.commit()
    return {"status": "successful!",
            "message": f"Tithe with ID: {tithe_id} deleted successfully!"
            }
