from typing import List, Union, Optional

from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session

from .. import schemas, models, oauth2, utils
from ..database import get_db

router = APIRouter(
    prefix="/groups",
    tags=["Groups"]
)


@router.get('/', response_model=Union[schemas.GroupsResponse, List[schemas.GroupsResponse]])
async def get_groups(
        id: Optional[int] = None,
        group_id: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
        group_name: Optional[str] = None,
        get_all: Optional[bool] = None,
):
    role = await utils.create_admin_access_id(current_user)
    admin_score = await utils.assess_score(current_user)

    if admin_score < 4:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privilege")

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No privilege for user type!")

    if get_all:
        groups = db.query(models.Group).filter(models.Group.group_id.ilike(f"%{role}%")).all()
        return groups

    query = db.query(models.Group)

    if id:
        group = query.filter(models.Group.id == id,
                             models.Group.group_id.ilike(f"%{role}%")).first()
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'Group with id: {id} not found!')
        return group

    if group_id:
        group = query.filter(models.Group.group_id == group_id,
                             models.Group.group_id.ilike(f"%{role}%")).first()
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'Group with id: {group_id} not found!')
        return group

    if group_name:
        query = query.filter(models.Group.group_name.ilike(f'%{group_name}%'),
                             models.Group.group_id.ilike(f"%{role}%"))

    groups = query.all()
    if not groups:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Group with ID: {groups} not found!")

    return groups


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.GroupsResponse)
async def create_group(group: schemas.CreateGroups, db: Session = Depends(get_db),
                       current_user: str = Depends(oauth2.get_current_user)
                       ):

    admin_score = await utils.assess_score(current_user)

    if admin_score < 3:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privilege")
    try:
        new_group = models.Group(**group.dict())
        db.add(new_group)
        db.commit()
        db.refresh(new_group)

        return new_group
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Internal Error! Group could not be created.")


@router.put("/", response_model=schemas.GroupsResponse)
async def update_groups(group_id: str, groups: schemas.UpdateGroups, db: Session = Depends(get_db),
                        current_user: str = Depends(oauth2.get_current_user)):
    role = await utils.create_admin_access_id(current_user)
    admin_score = await utils.assess_score(current_user)

    if admin_score < 3:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privilege")

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No privilege for user type!")

    group_query = db.query(models.Group).filter(models.Group.group_id == group_id,
                                                models.Group.goup_id.ilike(f"%{role}%"))

    group = group_query.first()

    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Group with id: {group_id} does not exist")

    group_query.update(groups.dict())
    db.commit()

    return group_query.first()


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(group_id: str, db: Session = Depends(get_db),
                       current_user: str = Depends(oauth2.get_current_user)):

    role = await utils.create_admin_access_id(current_user)
    admin_score = await utils.assess_score(current_user)

    if admin_score < 5:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privilege!")

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No privilege for user type!")

    group = db.query(models.Group).filter(models.Group.group_id == group_id,
                                          models.Group.goup_id.ilike(f"%{role}%"))

    if group.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {group_id} does not exist")

    group.delete(synchronize_session=False)
    db.commit()
    return {"status": "successful!",
            "message": f"User with ID: {group_id} deleted successfully!"
            }
