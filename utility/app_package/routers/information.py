import uuid
from datetime import datetime, timedelta
from typing import List, Union, Optional
from apscheduler.schedulers.background import BackgroundScheduler

from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy import extract
from sqlalchemy.orm import Session

from .. import schemas, models, oauth2, utils
from ..database import get_db

# Initialize the scheduler
scheduler = BackgroundScheduler()
scheduler.start()

router = APIRouter(
    prefix="/information",
    tags=["Information"]
)


@router.get('/read-information/', response_model=Union[schemas.InformationResponse, List[schemas.InformationResponse]])
async def get_information(
        id: Optional[str] = None,
        limit: Optional[int] = 100,
        offset: Optional[int] = 0,
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
        program_type: Optional[str] = None,
        program_title: Optional[str] = None,
        level: Optional[str] = None,
        get_info: Optional[bool] = None,
        location_id: Optional[str] = None,
        date: Optional[str] = None,
        get_all: Optional[bool] = None,
        start_month: Optional[int] = None,
        end_month: Optional[int] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
        ):

    # role = await utils.create_admin_access_id(current_user)

    _id = current_user.location_id
    parts = _id.split("-")
    region_id = "-".join(parts[:4])

    # if role is None:
    #     raise HTTPException(status_code=403, detail="Unauthorized access")

    # query = db.query(models.Information).filter(models.Information.location_id.ilike(f'%{role}%'),
    #                                             models.Information.is_deleted == False)

    if get_info:
        # Query the database to get the last 100 fellowship records for the specified region_id
        data = db.query(models.Information).filter(
            models.Information.region_id.ilike(f"%{region_id}%")).order_by(
            models.Information.created_at.desc())

        if not data:
            raise HTTPException(status_code=404, detail="No records found for this region")

        return data

    query = db.query(models.Information)
    if get_all:
        information = query.filter(models.Information.region_id.ilike(f'%{region_id}%')).offset(offset).limit(
            limit).all()

        if not information:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

        return information

    if id:
        query = query.filter(models.Information.information_id == id)

    if program_title:
        query = query.filter(models.Information.program_title == program_title)

    if program_type:
        query = query.filter(models.Information.program_type == program_type)

    if level:
        query = query.filter(models.Information.level == level)

    if location_id:
        query = query.filter(models.Information.location_id == location_id)

    if date:
        query = query.filter(models.Information.date == date)

    if start_month and end_month:
        query = query.filter(
            extract('month', models.Information.date) >= start_month,
            extract('month', models.Information.date) <= end_month)

    if start_year and end_year:
        query = query.filter(
            extract('year', models.Information.date) >= start_year,
            extract('year', models.Information.date) <= end_year)

    # Apply limit and offset to the query
    query = query.offset(offset).limit(limit)
    information = query.all()

    if not information:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

    return information


@router.post('/create-information/', status_code=status.HTTP_201_CREATED, response_model=schemas.InformationResponse)
async def create_information(information: schemas.CreateInformation, db: Session = Depends(get_db),
                             current_user: str = Depends(oauth2.get_current_user)):
    try:
        # Generate a unique information_id
        information_id = await generate_information_id()

        schedule_deactivation(information_id)

        # Create the Information instance from the Pydantic model
        new_information_data = information.dict(exclude={"items"})
        new_information_data['information_id'] = information_id  # Add the generated information_id
        new_information = models.Information(**new_information_data)
        db.add(new_information)
        db.commit()
        db.refresh(new_information)

        # Handle the nested items
        for item_data in information.items:
            item = models.InformationItems(**item_data.dict(), information_id=information_id)
            db.add(item)
        db.commit()

        return new_information
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/update-information/", response_model=schemas.InformationResponse)
async def update_information(information_id: str, setup_: schemas.UpdateInformation, db: Session = Depends(get_db),
                             current_user: str = Depends(oauth2.get_current_user),
                             user_access: None = Depends(oauth2.has_permission("update_information"))
                             ):

    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    information_query = db.query(models.Information).filter(models.Information.id == information_id,
                                                            models.Information.location_id.ilike(f'%{role}%'))

    information = information_query.first()

    if information is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Information with id: {information_id} does not exist")

    if information.is_deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Record not found!")

    # Update the record with new data, and set the operation and last_modify fields
    updated_data = setup_.dict(exclude_unset=True)
    updated_data["last_modify"] = datetime.utcnow()
    updated_data["operation"] = "update"

    information_query.update(updated_data)
    db.commit()
    db.refresh(information)

    return information_query


@router.delete("/delete-information/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_information(information_id: str, db: Session = Depends(get_db),
                             current_user: str = Depends(oauth2.get_current_user)):

    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    information = db.query(models.Information).filter(models.Information.id == information_id,
                                                      models.Information.is_deleted == False,
                                                      models.Information.location_id.ilike(f'%{role}%')).first()

    if information is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id: {information_id} does not exist")

    update_data = schemas.UpdateInformation(
        is_deleted=True,
        last_modify=datetime.now(),
        operation="delete"
    )

    # Update the user with the new data
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(information, field, value)

    db.commit()
    return {"response": "Data deleted successfully!"}


async def generate_information_id():
    return str(uuid.uuid4())


def deactivate_information(db: Session, information_id: str):
    """
    This function will be scheduled to run after 10 days to deactivate an information entry.
    """
    information = db.query(models.Information).filter(models.Information.information_id == information_id).first()
    if information:
        information.is_active = False
        db.commit()


def schedule_deactivation(information_id: str):
    """
    Schedule the 'deactivate_information' to run after 10 days.
    """
    run_date = datetime.now() + timedelta(days=10)
    scheduler.add_job(deactivate_information, 'date', run_date=run_date, args=[get_db(), information_id])


"""
{
  "region_id": "DCL-234-KW-ILR",
  "region_name": "Ilorin Region",
  "meeting": "Leaders meeting",
  "date": "2024-04-19",
  "trets_topic": "God Blessing upon man",
  "trets_date": "2024-04-19",
  "sws_topic": "Aboundance of God through Grace",
  "sts_study": "vol. 3, lesson 4",
  "adult_hcf": "lesson  25, volume 2",
  "youth_hcf": "lesson  25, volume 2",
  "children_hcf": "lesson  25, volume 2",
  "sws_bible_reading": "1 peter 4 & 5",
  "mbs_bible_reading": "Numbers 7",
  "is_active": true,
  "created_at": "2024-04-19T23:10:23.661Z",
  "items": [
    {
      "information_id": "string",
      "title": "string",
      "text": "string"
    }
  ]
}
"""
