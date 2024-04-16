from typing import List, Union, Optional

from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy import extract
from sqlalchemy.orm import Session

from .. import schemas, models, oauth2, utils
from ..database import get_db

router = APIRouter(
    prefix="/programs",
    tags=["Church Programs"]
)


@router.get('/', response_model=Union[schemas.ProgramsResponse, List[schemas.ProgramsResponse]])
async def get_programs(
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

    query = db.query(models.ChurchPrograms)

    if get_all:
        programs = query.filter(models.ChurchPrograms.location_id.ilike(f'%{role}%')).offset(offset).limit(limit).all()

        if not programs:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

        return programs

    if id:
        programs = query.filter(models.ChurchPrograms.id == id,
                                models.ChurchPrograms.location_id.ilike(f'%{role}%')).first()

        if not programs:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Attendance with id: {id} not found!')

        return programs

    if program_title:
        query = query.filter(models.ChurchPrograms.program_title == program_title,
                             models.ChurchPrograms.location_id.ilike(f'%{role}%'))

    if program_type:
        query = query.filter(models.ChurchPrograms.program_type == program_type,
                             models.ChurchPrograms.location_id.ilike(f'%{role}%'))

    if level:
        query = query.filter(models.ChurchPrograms.level == level,
                             models.ChurchPrograms.location_id.ilike(f'%{role}%'))

    if location_id:
        query = query.filter(models.ChurchPrograms.location_id == location_id,
                             models.ChurchPrograms.location_id.ilike(f'%{role}%'))

    if date:
        query = query.filter(models.ChurchPrograms.date == date,
                             models.ChurchPrograms.location_id.ilike(f'%{role}%'))

    if start_month and end_month:
        query = query.filter(
            extract('month', models.ChurchPrograms.date) >= start_month,
            extract('month', models.ChurchPrograms.date) <= end_month,
            models.ChurchPrograms.location_id.ilike(f'%{role}%')
        )
    if start_year and end_year:
        query = query.filter(
            extract('year', models.ChurchPrograms.date) >= start_year,
            extract('year', models.ChurchPrograms.date) <= end_year,
            models.ChurchPrograms.location_id.ilike(f'%{role}%')
        )

    # Apply limit and offset to the query
    query = query.offset(offset).limit(limit)
    programs = query.all()

    if not programs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

    return programs


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.ProgramsResponse)
async def create_programs(programs: schemas.CreatePrograms, db: Session = Depends(get_db),
                          current_user: str = Depends(oauth2.get_current_user)
                          ):    # create programs endpoint
    try:
        new_setup = models.ChurchPrograms(**programs.dict())
        db.add(new_setup)
        db.commit()
        db.refresh(new_setup)

        return new_setup
    except Exception as e:
        db.rollback()  # Rollback changes in case of exception
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Program could not be created.")


@router.put("/", response_model=schemas.ProgramsResponse)
async def update_programs(program_id: str, setup_: schemas.UpdatePrograms, db: Session = Depends(get_db),
                          current_user: str = Depends(oauth2.get_current_user)):
    admin_score = await utils.assess_score(current_user)

    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    if admin_score < 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privilege")

    setup_query = db.query(models.ChurchPrograms).filter(models.ChurchPrograms.id == program_id,
                                                         models.ChurchPrograms.location_id.ilike(f'%{role}%'))

    setup = setup_query.first()

    if setup is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {program_id} does not exist")

    setup_query.update(setup_.dict())
    db.commit()

    return setup_query.first()


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_programs(program_id: str, db: Session = Depends(get_db),
                          current_user: str = Depends(oauth2.get_current_user)):
    admin_score = await utils.assess_score(current_user)

    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    if admin_score < 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privilege")
    setup = db.query(models.ChurchPrograms).filter(models.ChurchPrograms.id == program_id,
                                                   models.ChurchPrograms.location_id.ilike(f'%{role}%'))

    if setup.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {program_id} does not exist")

    setup.delete(synchronize_session=False)
    db.commit()
    return {"response": "Data deleted successfully!"}
