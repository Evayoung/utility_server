import random
import string
from datetime import datetime
from typing import List, Union, Optional

from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session

from .. import schemas, models, oauth2, utils
from ..database import get_db

router = APIRouter(
    prefix="/groups",
    tags=["Groups"]
)


@router.get('/read-group/', response_model=Union[schemas.GroupsResponse, List[schemas.GroupsResponse]])
async def get_groups(
        id: Optional[int] = None,
        group_id: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
        user_access: None = Depends(oauth2.has_permission("read_group")),
        group_name: Optional[str] = None,
        get_all: Optional[bool] = None,
):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No privilege for user type!")

    if get_all:
        groups = db.query(models.Group).filter(models.Group.group_id.ilike(f"%{role}%"),
                                               models.Group.is_deleted == False).all()
        return groups

    query = db.query(models.Group)

    if id:
        group = query.filter(models.Group.id == id,
                             models.Group.is_deleted == False,
                             models.Group.group_id.ilike(f"%{role}%")).first()
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'Group with id: {id} not found!')
        return group

    if group_id:
        group = query.filter(models.Group.group_id == group_id,
                             models.Group.is_deleted == False,
                             models.Group.group_id.ilike(f"%{role}%")).first()
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'Group with id: {group_id} not found!')
        return group

    if group_name:
        query = query.filter(models.Group.group_name.ilike(f'%{group_name}%'),
                             models.Group.is_deleted == False,
                             models.Group.group_id.ilike(f"%{role}%"))

    groups = query.all()
    if not groups:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Group with ID: {groups} not found!")

    return groups


@router.post('/create-group/', status_code=status.HTTP_201_CREATED, response_model=schemas.GroupsResponse)
async def create_group(group: schemas.CreateGroups, db: Session = Depends(get_db),
                       # user_access: None = Depends(oauth2.has_permission("create_group")),
                       # current_user: str = Depends(oauth2.get_current_user)
                       ):
    try:
        # generate region_id
        group_id = await generate_group_id(group.group_name, group.region_id, db)

        new_group = models.Group(**group.dict(), group_id=group_id)
        db.add(new_group)
        db.commit()
        db.refresh(new_group)

        return new_group
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Internal Error! Group could not be created.")


@router.patch("/update-group/", response_model=schemas.GroupsResponse)
async def update_groups(group_id: str, groups: schemas.UpdateGroups, db: Session = Depends(get_db),
                        current_user: str = Depends(oauth2.get_current_user),
                        user_access: None = Depends(oauth2.has_permission("update_group"))
                        ):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No privilege for user type!")

    group_query = db.query(models.Group).filter(models.Group.group_id == group_id,
                                                models.Group.goup_id.ilike(f"%{role}%"))

    group = group_query.first()

    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Group with id: {group_id} does not exist")

    if group.is_deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Record not found!")

    # Update the record with new data, and set the operation and last_modify fields
    updated_data = groups.dict(exclude_unset=True)
    updated_data["last_modify"] = datetime.utcnow()
    updated_data["operation"] = "update"

    group_query.update(updated_data)
    db.commit()
    db.refresh(group)

    return group_query.first()


@router.delete("/delete-group/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(group_id: str, db: Session = Depends(get_db),
                       current_user: str = Depends(oauth2.get_current_user),
                       user_access: None = Depends(oauth2.has_permission("delete_group"))
                       ):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No privilege for user type!")

    group = db.query(models.Group).filter(models.Group.group_id == group_id,
                                          models.Group.is_deleted == False,
                                          models.Group.goup_id.ilike(f"%{role}%")).first()

    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Group with id: {group_id} does not exist")

    update_data = schemas.UpdateGroups(
        is_deleted=True,
        last_modify=datetime.now(),
        operation="delete"
    )

    # Update the user with the new data
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(group, field, value)
    db.commit()

    return {"status": "successful!",
            "message": f"User with ID: {group_id} deleted successfully!"
            }


async def generate_group_id(group_name: str, region_id: str, db: Session) -> str:
    def generate_id():
        # Clean the region_name by removing any non-alphanumeric characters and spaces
        cleaned_name = ''.join(c for c in group_name if c.isalnum())

        # Select 3 random letters from the cleaned name or from the alphabet
        if len(cleaned_name) >= 3:
            unique_id = ''.join(random.choices(cleaned_name, k=3)).upper()
        else:
            unique_id = ''.join(random.choices(string.ascii_uppercase, k=3))

        return unique_id

    # Ensure uniqueness of the generated region_id
    while True:
        group_id = f"{region_id}-{generate_id()}"

        # Check if the region_id already exists in the database
        existing_group = db.query(models.Group).filter(models.Group.group_id == group_id).first()
        if not existing_group:
            break

    return group_id
