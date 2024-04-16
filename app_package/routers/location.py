from typing import List, Union, Optional

from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session

from .. import schemas, utils, models, oauth2
from ..database import get_db

router = APIRouter(
    prefix="/locations",
    tags=["Location"]
)


@router.get('/', response_model=Union[schemas.LocationResponse, List[schemas.LocationResponse]])
async def get_locations(
        location_id: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
        group_id: Optional[str] = None,
        location_name: Optional[str] = None,
        get_all: Optional[bool] = None,
):
    """ this api route returns the lists of all locations in the state depending on certain criteria of the admin """

    user_type = await utils.create_admin_access_id(current_user)
    query = db.query(models.Location)

    if get_all:
        # groups = db.query(models.Group).all()
        location = query.filter(models.Location.location_id.ilike(f'%{user_type}%')).all()
        return location

    if location_id:
        locations = query.filter(models.Location.id == location_id,
                                 models.Location.location_id.ilike(f'%{user_type}%')).first()
        if not locations:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'Worker with id: {location_id} not found!')
        return locations

    if group_id:
        query = query.filter(models.Location.group_id == group_id,
                             models.Location.location_id.ilike(f'%{user_type}%'))

    if location_name:
        query = query.filter(models.Location.location_name.ilike(f'%{location_name}%'),
                             models.Location.location_id.ilike(f'%{user_type}%'))

    locations = query.all()
    if not locations:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Location with ID: {locations} not found!")

    return locations


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.LocationResponse)
async def create_locations(location: schemas.CreateLocations, db: Session = Depends(get_db),
                           current_user: str = Depends(oauth2.get_current_user)
                           ):
    admin_score = await utils.assess_score(current_user)

    if admin_score < 5:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privilege")
    try:
        new_location = models.Location(**location.dict())
        db.add(new_location)
        db.commit()
        db.refresh(new_location)

        return new_location
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Internal Error! Location could not be created.")


@router.put("/{location_id}", response_model=schemas.LocationResponse)
async def update_locations(location_id: str, location_: schemas.UpdateLocations, db: Session = Depends(get_db),
                           current_user: str = Depends(oauth2.get_current_user)):
    role = await utils.create_admin_access_id(current_user)
    admin_score = await utils.assess_score(current_user)

    if admin_score < 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privilege")

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privilege!")

    location_query = db.query(models.Location).filter(models.Location.location_id == location_id,
                                                      models.Location.location_id.ilike(f'%{role}%'))

    location = location_query.first()

    if location is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Location with id: {location_id} does not exist")

    location_query.update(location_.dict())
    db.commit()

    return location_query.first()


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_locations(locations_id: str, db: Session = Depends(get_db),
                           current_user: str = Depends(oauth2.get_current_user)):

    role = await utils.create_admin_access_id(current_user)
    admin_score = await utils.assess_score(current_user)

    if admin_score < 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privilege")

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privilege!")

    locations = db.query(models.Location).filter(models.Location.location_id == locations_id,
                                                 models.Location.location_id.ilike(f'%{role}%'))

    if locations.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Location with id: {locations_id} does not exist")

    locations.delete(synchronize_session=False)
    db.commit()
    return {"status": "successful!",
            "message": f"User with ID: {locations_id} deleted successfully!"
            }
