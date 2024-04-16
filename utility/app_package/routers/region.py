from typing import List, Union, Optional

from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session

from .. import schemas, models, oauth2, utils
from ..database import get_db

router = APIRouter(
    prefix="/regions",
    tags=["Region"]
)


@router.get('/', response_model=Union[schemas.RegionResponse, List[schemas.RegionResponse]])
async def get_regions(
        id: Optional[int] = None,
        region_id: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
        region_name: Optional[str] = None,
        get_all: Optional[bool] = None,
):
    role = await utils.create_admin_access_id(current_user)
    admin_score = await utils.assess_score(current_user)

    if admin_score < 4:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privilege")

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No privilege for user type!")

    if get_all:
        groups = db.query(models.Group.region_id.ilike(f"%{role}%")).all()
        return groups

    query = db.query(models.Region)

    if id:
        region = query.filter(models.Region.id == id,
                              models.Group.region_id.ilike(f"%{role}%")).first()
        if not region:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'Region with id: {id} not found!')
        return region

    if region_id:
        region = query.filter(models.Region.region_id == region_id,
                              models.Group.region_id.ilike(f"%{role}%")).first()
        if not region:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'Region with id: {region_id} not found!')
        return region

    if region_name:
        query = query.filter(models.Region.region_name.ilike(f'%{region_name}%'),
                             models.Group.region_id.ilike(f"%{role}%"))

    region = query.all()
    if not region:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Record with ID: {region} not found!")

    return region


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.RegionResponse)
async def create_region(region: schemas.CreateRegions, db: Session = Depends(get_db),
                        current_user: str = Depends(oauth2.get_current_user)
                        ):
    admin_score = await utils.assess_score(current_user)

    if admin_score < 4:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privilege")
    try:
        new_region = models.Region(**region.dict())
        db.add(new_region)
        db.commit()
        db.refresh(new_region)

        return new_region
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Internal Error! Region could not be created.")


@router.put("/", response_model=schemas.RegionResponse)
async def update_regions(region_id: str, region_: schemas.UpdateRegions, db: Session = Depends(get_db),
                         current_user: str = Depends(oauth2.get_current_user)):
    role = await utils.create_admin_access_id(current_user)
    admin_score = await utils.assess_score(current_user)

    if admin_score < 5:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privilege")

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No privilege for user type!")

    region_query = db.query(models.Region).filter(models.Region.region_id == region_id,
                                                  models.Group.region_id.ilike(f"%{role}%"))

    region = region_query.first()

    if region is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Region with id: {region_id} does not exist")

    region_query.update(region_.dict())
    db.commit()

    return region_query.first()


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_region(region_id: str, db: Session = Depends(get_db),
                        current_user: str = Depends(oauth2.get_current_user)):
    role = await utils.create_admin_access_id(current_user)
    admin_score = await utils.assess_score(current_user)

    if admin_score < 5:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privilege")

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No privilege for user type!")

    region = db.query(models.Region).filter(models.Region.region_id == region_id,
                                            models.Group.region_id.ilike(f"%{role}%"))

    if region.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {region_id} does not exist")

    region.delete(synchronize_session=False)
    db.commit()
    return {"response": "Data deleted successfully!"}
