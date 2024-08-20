import random
from datetime import datetime
from typing import List, Union, Optional

from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy import func, Integer
from sqlalchemy.orm import Session

from .. import schemas, utils, models, oauth2
from ..database import get_db

router = APIRouter(
    prefix="/locations",
    tags=["Location"]
)


@router.get('/read-location/', response_model=Union[schemas.LocationResponse, List[schemas.LocationResponse]])
async def get_locations(
        location_id: Optional[str] = None,
        limit: Optional[int] = 100,  # Default limit set to 100
        offset: Optional[int] = 0,  # Default offset set to 0
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
        user_access: None = Depends(oauth2.has_permission("read_location")),
        group_id: Optional[str] = None,
        location_name: Optional[str] = None,
        get_all: Optional[bool] = None,
):
    """ this api route returns the lists of all locations in the state depending on certain criteria of the admin """

    user_type = await utils.create_admin_access_id(current_user)

    if user_type is None:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    query = db.query(models.Location).filter(models.Location.location_id.ilike(f'%{user_type}%'),
                                             models.Location.is_deleted == False)

    if location_id:
        query = query.filter(models.Location.id == location_id)

    if group_id:
        query = query.filter(models.Location.group_id == group_id)

    if location_name:
        query = query.filter(models.Location.location_name.ilike(f'%{location_name}%'))

    query = query.offset(offset).limit(limit)
    locations = query.all()
    if not locations:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Location with ID: {locations} not found!")

    if get_all:
        return locations

    return locations


@router.post('/create-location/', status_code=status.HTTP_201_CREATED, response_model=schemas.LocationResponse)
async def create_locations(location: schemas.CreateLocations, db: Session = Depends(get_db),
                           current_user: str = Depends(oauth2.get_current_user),
                           user_access: None = Depends(oauth2.has_permission("create_location"))
                           ):
    try:
        # generate location_id
        location_id = await generate_serial_id(location.group_id, db)

        new_location = models.Location(**location.dict(), location_id=location_id)
        db.add(new_location)
        db.commit()
        db.refresh(new_location)

        return new_location
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Internal Error! Location could not be created.")


@router.patch("/update-location/", response_model=schemas.LocationResponse)
async def update_locations(location_id: str, location_: schemas.UpdateLocations, db: Session = Depends(get_db),
                           current_user: str = Depends(oauth2.get_current_user),
                           user_access: None = Depends(oauth2.has_permission("update_location"))
                           ):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privilege!")

    location_query = db.query(models.Location).filter(models.Location.location_id == location_id,
                                                      models.Location.is_deleted == False,
                                                      models.Location.location_id.ilike(f'%{role}%'))

    location = location_query.first()

    if location is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Location with id: {location_id} does not exist")

    if location.is_deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Record not found!")

    # Update the record with new data, and set the operation and last_modify fields
    updated_data = location_.dict(exclude_unset=True)
    updated_data["last_modify"] = datetime.utcnow()
    updated_data["operation"] = "update"

    location_query.update(updated_data)
    db.commit()
    db.refresh(location)

    return location_query


@router.delete("/delete-location/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_locations(locations_id: str, db: Session = Depends(get_db),
                           current_user: str = Depends(oauth2.get_current_user),
                           user_access: None = Depends(oauth2.has_permission("delete_location"))
                           ):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privilege!")

    locations = db.query(models.Location).filter(models.Location.location_id == locations_id,
                                                 models.Location.is_deleted == False,
                                                 models.Location.location_id.ilike(f'%{role}%')).first()

    if locations is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Location with id: {locations_id} does not exist")

    update_data = schemas.UpdateLocations(
        is_deleted=True,
        last_modify=datetime.now(),
        operation="delete"
    )

    # Update the user with the new data
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(locations, field, value)

    db.commit()

    return {"status": "successful!",
            "message": f"User with ID: {locations_id} deleted successfully!"
            }


async def generate_serial_id(group_id: str, db: Session) -> str:
    def generate_next_serial():
        try:
            # Fetch the latest record based on group_id
            query = db.query(models.Location).filter(models.Location.location_id.like(f"{group_id}-%"))

            # Fetch the latest record with the highest serial number
            latest_record = query.order_by(
                func.cast(
                    func.substring(models.Location.location_id, len(group_id) + 2), Integer
                ).desc()
            ).first()

            if latest_record:
                # Extract the current highest serial number and increment it
                last_serial = int(latest_record.location_id.split('-')[-1])  # Extract serial part directly
                next_serial = last_serial + 1
            else:
                # Start with 001 if no records exist
                next_serial = 1

            # Format the serial number to be 3 digits long
            return f"{next_serial:03}"
        except Exception:
            raise

    while True:
        try:
            serial_number = generate_next_serial()
            location_id = f"{group_id}-{serial_number}"

            # Check if the location_id already exists in the database
            existing_location = db.query(models.Location).filter(models.Location.location_id == location_id).first()
            if not existing_location:
                break
        except Exception:
            raise

    return location_id

