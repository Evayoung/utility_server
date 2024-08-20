import random
import string
from datetime import datetime
from typing import List, Union, Optional

from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session

from .. import schemas, models, oauth2, utils
from ..database import get_db

router = APIRouter(
    prefix="/regions",
    tags=["Region"]
)


@router.get('/read-region/', response_model=Union[schemas.RegionResponse, List[schemas.RegionResponse]])
async def get_regions(
        id: Optional[int] = None,
        limit: Optional[int] = 100,  # Default limit set to 100
        offset: Optional[int] = 0,  # Default offset set to 0
        region_id: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
        # user_access: None = Depends(oauth2.has_permission("read_region")),
        region_name: Optional[str] = None,
        get_all: Optional[bool] = None,
):
    role = current_user.roles[0].score.score

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    user_type = await utils.create_admin_access_id(current_user)

    query = db.query(models.Region).filter(models.Region.region_id.ilike(f'%{user_type}%'),
                                           models.Region.is_deleted == False)

    if id:
        query = query.filter(models.Region.id == id)

    if region_id:
        query = query.filter(models.Region.region_id == region_id)

    if region_name:
        query = query.filter(models.Region.region_name.ilike(f'%{region_name}%'))

    # Apply limit and offset to the query
    query = query.offset(offset).limit(limit)
    region = query.all()
    if not region:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Record with ID: {region} not found!")

    if get_all:
        return region

    # If a single user was requested by ID, return just that user
    if id:
        if len(region) == 1:
            return region[0]
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Region with id: {id} not found!')

    return region


@router.post('/create-region/', status_code=status.HTTP_201_CREATED, response_model=schemas.RegionResponse)
async def create_region(region: schemas.CreateRegions, db: Session = Depends(get_db),
                        # user_access: None = Depends(oauth2.has_permission("create_region")),
                        # current_user: str = Depends(oauth2.get_current_user)
                        ):
    try:
        # generate region_id
        region_id = await generate_region_id(region.region_name, region.state_id, db)

        new_region = models.Region(**region.dict(), region_id=region_id)
        db.add(new_region)
        db.commit()
        db.refresh(new_region)

        return new_region
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Internal Error! Region could not be created.")


@router.patch("/update-region/", response_model=schemas.RegionResponse)
async def update_regions(region_id: str, region_: schemas.UpdateRegions, db: Session = Depends(get_db),
                         current_user: str = Depends(oauth2.get_current_user),
                         user_access: None = Depends(oauth2.has_permission("update_region"))
                         ):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    region_query = db.query(models.Region).filter(models.Region.region_id == region_id,
                                                  models.Region.is_deleted == False,
                                                  models.Region.region_id.ilike(f"%{role}%"))

    region = region_query.first()

    if region is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Region with id: {region_id} does not exist")

    if region.is_deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Record not found!")

    # Update the record with new data, and set the operation and last_modify fields
    updated_data = region_.dict(exclude_unset=True)
    updated_data["last_modify"] = datetime.utcnow()
    updated_data["operation"] = "update"

    region_query.update(updated_data)
    db.commit()
    db.refresh(region)

    return region


@router.delete("/delete-region/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_region(region_id: str, db: Session = Depends(get_db),
                        current_user: str = Depends(oauth2.get_current_user),
                        user_access: None = Depends(oauth2.has_permission("read_region"))
                        ):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    region = db.query(models.Region).filter(models.Region.region_id == region_id,
                                            models.Region.is_deleted == False,
                                            models.Region.region_id.ilike(f"%{role}%")).first()

    if region is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Region with id: {region_id} does not exist")

    update_data = schemas.UpdateRegions(
        is_deleted=True,
        last_modify=datetime.now(),
        operation="delete"
    )

    # Update the user with the new data
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(region, field, value)
    db.commit()

    return {"status": "successful!",
            "message": f"Region record with ID: {region_id} deleted successfully!"
            }


async def generate_region_id(region_name: str, state_id: str, db: Session) -> str:
    def generate_id():
        # Clean the region_name by removing any non-alphanumeric characters and spaces
        cleaned_name = ''.join(c for c in region_name if c.isalnum())

        # Select 3 random letters from the cleaned name or from the alphabet
        if len(cleaned_name) >= 3:
            unique_id = ''.join(random.choices(cleaned_name, k=3)).upper()
        else:
            unique_id = ''.join(random.choices(string.ascii_uppercase, k=3))

        return unique_id

    # Ensure uniqueness of the generated region_id
    while True:
        region_id = f"{state_id}-{generate_id()}"

        # Check if the region_id already exists in the database
        existing_region = db.query(models.Region).filter(models.Region.region_id == region_id).first()
        if not existing_region:
            break

    return region_id
