from typing import List, Union, Optional

from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy import extract
from sqlalchemy.orm import Session

from .. import schemas, models, oauth2, utils
from ..database import get_db

router = APIRouter(
    prefix="/information",
    tags=["Information"]
)


@router.get('/', response_model=Union[schemas.InformationResponse, List[schemas.InformationResponse]])
async def request_information(user_id: str, db: Session = Depends(get_db),
                              current_user: str = Depends(oauth2.get_current_user)):
    role = await utils.create_admin_access_id(current_user)
    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No privilege for user type!")

    user = db.query(models.Information).filter(models.Information.user_id == user_id,
                                        models.User.location_id.ilike(f"%{role}%")).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'User with id: {user_id} not found!')

    return user


@router.get('/', response_model=Union[schemas.InformationResponse, List[schemas.InformationResponse]])
async def get_information(
        id: Optional[int] = None,
        limit: Optional[int] = 100,  # Default limit set to 100
        offset: Optional[int] = 0,  # Default offset set to 0
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
        program_type: Optional[str] = None,
        program_title: Optional[str] = None,
        level: Optional[str] = None,
        location_id: Optional[str] = None,
        date: Optional[str] = None,
        get_all: Optional[bool] = None,
        start_month: Optional[int] = None,
        end_month: Optional[int] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
):
    role = await utils.create_admin_access_id(current_user)

    if role is None:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    query = db.query(models.Information)

    if get_all:
        information = query.filter(models.Information.location_id.ilike(f'%{role}%')).offset(offset).limit(
            limit).all()

        if not information:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

        return information

    if id:
        information = query.filter(models.Information.id == id,
                                   models.Information.location_id.ilike(f'%{role}%')).first()

        if not information:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Attendance with id: {id} not found!')

        return information

    if program_title:
        query = query.filter(models.Information.program_title == program_title,
                             models.Information.location_id.ilike(f'%{role}%'))

    if program_type:
        query = query.filter(models.Information.program_type == program_type,
                             models.Information.location_id.ilike(f'%{role}%'))

    if level:
        query = query.filter(models.Information.level == level,
                             models.Information.location_id.ilike(f'%{role}%'))

    if location_id:
        query = query.filter(models.Information.location_id == location_id,
                             models.Information.location_id.ilike(f'%{role}%'))

    if date:
        query = query.filter(models.Information.date == date,
                             models.Information.location_id.ilike(f'%{role}%'))

    if start_month and end_month:
        query = query.filter(
            extract('month', models.Information.date) >= start_month,
            extract('month', models.Information.date) <= end_month,
            models.Information.location_id.ilike(f'%{role}%')
        )
    if start_year and end_year:
        query = query.filter(
            extract('year', models.Information.date) >= start_year,
            extract('year', models.Information.date) <= end_year,
            models.Information.location_id.ilike(f'%{role}%')
        )

    # Apply limit and offset to the query
    query = query.offset(offset).limit(limit)
    information = query.all()

    if not information:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

    return information


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.InformationResponse)
async def create_information(information: schemas.CreateInformation, db: Session = Depends(get_db),
                             current_user: str = Depends(oauth2.get_current_user)
                             ):
    try:
        new_information = models.Information(**information.dict())
        db.add(new_information)
        db.commit()
        db.refresh(new_information)

        return new_information
    except Exception as e:
        db.rollback()  # Rollback changes in case of exception
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Program could not be created.")


@router.put("/", response_model=schemas.InformationResponse)
async def update_information(information_id: str, setup_: schemas.UpdateInformation, db: Session = Depends(get_db),
                             current_user: str = Depends(oauth2.get_current_user)):
    admin_score = await utils.assess_score(current_user)

    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    if admin_score < 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privilege")

    information_query = db.query(models.Information).filter(models.Information.id == information_id,
                                                            models.Information.location_id.ilike(f'%{role}%'))

    information = information_query.first()

    if information is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id: {information_id} does not exist")

    information_query.update(setup_.dict())
    db.commit()

    return information_query.first()


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_information(information_id: str, db: Session = Depends(get_db),
                             current_user: str = Depends(oauth2.get_current_user)):
    admin_score = await utils.assess_score(current_user)

    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    if admin_score < 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privilege")
    information = db.query(models.Information).filter(models.Information.id == information_id,
                                                      models.Information.location_id.ilike(f'%{role}%'))

    if information.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id: {information_id} does not exist")

    information.delete(synchronize_session=False)
    db.commit()
    return {"response": "Data deleted successfully!"}
