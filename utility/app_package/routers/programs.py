from datetime import datetime
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


@router.get('/read-program/', response_model=Union[schemas.ProgramsResponse, List[schemas.ProgramsResponse]])
async def get_programs(
        id: Optional[int] = None,
        limit: Optional[int] = 100,  # Default limit set to 100
        offset: Optional[int] = 0,  # Default offset set to 0
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
        user_access: None = Depends(oauth2.has_permission("read_program")),
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

    query = db.query(models.ChurchPrograms).filter(models.ChurchPrograms.location_id.ilike(f'%{role}%'),
                                                   models.ChurchPrograms.is_deleted == False)

    if id:
        programs = query.filter(models.ChurchPrograms.id == id)

    if program_title:
        query = query.filter(models.ChurchPrograms.program_title == program_title)

    if program_type:
        query = query.filter(models.ChurchPrograms.program_type == program_type)

    if level:
        query = query.filter(models.ChurchPrograms.level == level)

    if location_id:
        query = query.filter(models.ChurchPrograms.location_id == location_id)

    if date:
        query = query.filter(models.ChurchPrograms.date == date)

    if start_month and end_month:
        query = query.filter(
            extract('month', models.ChurchPrograms.date) >= start_month,
            extract('month', models.ChurchPrograms.date) <= end_month)

    if start_year and end_year:
        query = query.filter(
            extract('year', models.ChurchPrograms.date) >= start_year,
            extract('year', models.ChurchPrograms.date) <= end_year)

    # Apply limit and offset to the query
    query = query.offset(offset).limit(limit)
    programs = query.all()

    if not programs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

    if get_all:
        return programs

    # If a single user was requested by ID, return just that user
    if id:
        if len(programs) == 1:
            return programs[0]
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Program with id: {id} not found!')

    return programs


@router.post('/create-program/', status_code=status.HTTP_201_CREATED, response_model=schemas.ProgramsResponse)
async def create_programs(programs: schemas.CreatePrograms, db: Session = Depends(get_db),
                          current_user: str = Depends(oauth2.get_current_user),
                          user_access: None = Depends(oauth2.has_permission("create_program"))
                          ):  # create programs endpoint

    try:
        new_setup = models.ChurchPrograms(**programs.dict())
        db.add(new_setup)
        db.commit()
        db.refresh(new_setup)

        return new_setup
    except Exception as e:
        db.rollback()  # Rollback changes in case of exception
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Program could not be created.")


@router.patch("/update-program/", response_model=schemas.ProgramsResponse)
async def update_programs(program_id: str, setup_: schemas.UpdatePrograms, db: Session = Depends(get_db),
                          current_user: str = Depends(oauth2.get_current_user),
                          user_access: None = Depends(oauth2.has_permission("update_program"))
                          ):

    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    setup_query = db.query(models.ChurchPrograms).filter(models.ChurchPrograms.id == program_id,
                                                         models.ChurchPrograms.is_deleted == False,
                                                         models.ChurchPrograms.location_id.ilike(f'%{role}%'))

    setup = setup_query.first()

    if setup is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {program_id} does not exist")

    if setup.is_deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Record not found!")

    # Update the record with new data, and set the operation and last_modify fields
    updated_data = setup_.dict(exclude_unset=True)
    updated_data["last_modify"] = datetime.utcnow()
    updated_data["operation"] = "update"

    setup_query.update(updated_data)
    db.commit()
    db.refresh(setup)

    return setup_query


@router.delete("/delete-program/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_programs(program_id: str, db: Session = Depends(get_db),
                          current_user: str = Depends(oauth2.get_current_user),
                          user_access: None = Depends(oauth2.has_permission("delete_program"))
                          ):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    setup = db.query(models.ChurchPrograms).filter(models.ChurchPrograms.id == program_id,
                                                   models.ChurchPrograms.is_deleted == False,
                                                   models.ChurchPrograms.location_id.ilike(f'%{role}%')).first()

    if setup is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {program_id} does not exist")

    update_data = schemas.UpdatePrograms(
        is_deleted=True,
        last_modify=datetime.now(),
        operation="delete"
    )

    # Update the user with the new data
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(setup, field, value)

    db.commit()

    return {"status": "successful!",
            "message": f"Program record with ID: {program_id} deleted successfully!"
            }
