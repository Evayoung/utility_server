from typing import List, Optional, Union
from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy import extract
from sqlalchemy.orm import Session

from .. import schemas, utils, models, oauth2
from ..database import get_db

router = APIRouter(
    prefix="/counts",
    tags=["Counts"]
)


@router.get('/', response_model=Union[schemas.CountResponse, List[schemas.CountResponse]])
async def get_counts(
        _id: Optional[int] = None,
        limit: Optional[int] = 100,  # Default limit set to 100
        offset: Optional[int] = 0,    # Default offset set to 0
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
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
    query = db.query(models.Counter)

    if user_type is None:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    if get_all:
        counts = query.filter(models.Counter.location_id.ilike(f'%{user_type}%')).all()
        return counts
    # user_type = create_admin_access_id(current_user)

    if _id:
        count = query.filter(models.Counter.id == _id, models.Counter.location_id.ilike(f'%{user_type}%')).first()
        if not count:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Count with id: {_id} not found!')

        return count

    if program_domain:
        query = query.filter(models.Counter.program_domain == program_domain,
                             models.Counter.location_id.ilike(f'%{user_type}%'))

    if program_type:
        query = query.filter(models.Counter.program_type == program_type,
                             models.Counter.location_id.ilike(f'%{user_type}%'))

    if location_id:
        query = query.filter(models.Counter.location_id == location_id,
                             models.Counter.location_id.ilike(f'%{user_type}%'))

    if date:
        query = query.filter(models.Counter.date == date,
                             models.Counter.location_id.ilike(f'%{user_type}%'))

    if start_month and end_month:
        query = query.filter(
            extract('month', models.Counter.date) >= start_month,
            extract('month', models.Counter.date) <= end_month,
            models.Counter.location_id.ilike(f'%{user_type}%')
        )

    if start_year and end_year:
        query = query.filter(
            extract('year', models.Counter.date) >= start_year,
            extract('year', models.Counter.date) <= end_year,
            models.Counter.location_id.ilike(f'%{user_type}%')
        )
    # Add conditions for other parameters
    # Apply limit and offset to the query
    query = query.offset(offset).limit(limit)
    counts = query.all()
    if not counts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found')

    return counts


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.CountResponse)
async def create_count(counts: schemas.CreateCount, db: Session = Depends(get_db),
                       current_user: str = Depends(oauth2.get_current_user)):
    try:
        new_count = models.Counter(**counts.dict())
        db.add(new_count)
        db.commit()
        db.refresh(new_count)

        return new_count
    except Exception as e:
        db.rollback()  # Rollback changes in case of exception
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error! Count could not be saved.")


# this api route update the counts already submitted to the database
@router.put("/", response_model=schemas.CountResponse)
async def update_count(count_id: str, counts: schemas.UpdateCount, db: Session = Depends(get_db),
                       current_user: str = Depends(oauth2.get_current_user)):

    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    count_query = db.query(models.Counter).filter(models.Counter.id == count_id,
                                                  models.Counter.location_id.ilike(f"%{role}%"))

    record = count_query.first()

    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {count_id} does not exist")

    count_query.update(counts.dict())
    db.commit()

    return count_query.first()


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_count(_id: str, db: Session = Depends(get_db),
                       current_user: str = Depends(oauth2.get_current_user)):

    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    count = db.query(models.Counter).filter(models.Counter.id == _id,
                                            models.Counter.location_id.ilike(f'%{role}%'))

    if count.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Data with id: {_id} does not exist")

    if current_user.role != "Super Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    count.delete(synchronize_session=False)
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
                |__other py files
                
with this structure, how or where can i put the script to suite

"""
