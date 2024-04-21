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


@router.get('/', response_model=Union[schemas.InformationResponse, List[schemas.InformationResponse]])
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
    role = await utils.create_admin_access_id(current_user)

    if role is None:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    _id = current_user.location_id
    parts = _id.split("-")
    region_id = "-".join(parts[:4])

    if get_info:
        # Query the database to get the last 100 fellowship records for the specified region_id
        data = db.query(models.Information).filter(
            models.Information.region_id.ilike(f"%{region_id}%")).order_by(
                models.Information.created_at.desc()).offset(offset).limit(limit).all()

        if not data:
            raise HTTPException(status_code=404, detail="No records found for this region")

        return data

    query = db.query(models.Information)
    if get_all:
        information = query.filter(models.Information.region_id.ilike(f'%{region_id}%')).offset(offset).limit(limit).all()

        if not information:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

        return information

    if id:
        information = query.filter(models.Information.information_id == id).first()

        if not information:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Attendance with id: {id} not found!')

        return information

    if program_title:
        query = query.filter(models.Information.program_title == program_title,
                             models.Information.region_id.ilike(f'%{region_id}%'))

    if program_type:
        query = query.filter(models.Information.program_type == program_type,
                             models.Information.region_id.ilike(f'%{region_id}%'))

    if level:
        query = query.filter(models.Information.level == level,
                             models.Information.region_idd.ilike(f'%{region_id}%'))

    if location_id:
        query = query.filter(models.Information.location_id == location_id,
                             models.Information.region_id.ilike(f'%{region_id}%'))

    if date:
        query = query.filter(models.Information.date == date,
                             models.Information.region_id.ilike(f'%{region_id}%'))

    if start_month and end_month:
        query = query.filter(
            extract('month', models.Information.date) >= start_month,
            extract('month', models.Information.date) <= end_month,
            models.Information.region_id.ilike(f'%{region_id}%')
        )
    if start_year and end_year:
        query = query.filter(
            extract('year', models.Information.date) >= start_year,
            extract('year', models.Information.date) <= end_year,
            models.Information.region_id.ilike(f'%{region_id}%')
        )

    # Apply limit and offset to the query
    query = query.offset(offset).limit(limit)
    information = query.all()

    if not information:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

    return information


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.InformationResponse)
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
