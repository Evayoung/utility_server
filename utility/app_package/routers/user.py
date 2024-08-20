import json
from datetime import datetime
from typing import Union, List, Optional

from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session, joinedload

from .. import schemas, utils, models, oauth2
from ..database import get_db
from .websocket import manager

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.get("/state_region_data")
async def get_region_state(db: Session = Depends(get_db),
                           current_user: str = Depends(oauth2.get_current_user)):
    # Extract location_id from the current user
    location_id = current_user.location_id

    # Split the location_id to extract state_id and region_id
    parts = location_id.split("-")

    state_id = "-".join(parts[:3])  # Assuming state_id is the second part
    region_id = "-".join(parts[:4])  # Assuming region_id is the third part

    # Query the database to fetch state and region data based on state_id and region_id
    state = db.query(models.States).filter(models.States.state_id == state_id).first()
    region = db.query(models.Region).filter(models.Region.region_id == region_id).first()

    if not state or not region:
        raise HTTPException(status_code=404, detail="Could not fetch user location details")

    if state.is_deleted or region.is_deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Location data not found!")

    # Create instances of StateResponse and RegionResponse
    state_response = {
        "state_id": state.state_id,
        "country": state.country,
        "state": state.state,
        "city": state.city,
        "address": state.address,
        "state_hq": state.state_hq,
        "state_pastor": state.state_pastor
    }

    region_response = {
        "region_id": region.region_id,
        "region_name": region.region_name,
        "region_head": region.region_head,
        "regional_pastor": region.regional_pastor
    }

    # Return the response with StateResponse and RegionResponse
    return {"state": state_response, "region": region_response}


@router.post('/create-user/', status_code=status.HTTP_201_CREATED, response_model=schemas.UserResponse)
async def create_users(user: schemas.UserCreate, db: Session = Depends(get_db),
                       # user_access: None = Depends(oauth2.has_permission("create_user"))
                       ):
    try:
        # hash the password - user.password
        hashed_password = await utils.hash_password(user.password)
        user.password = hashed_password

        new_user = models.User(**user.dict())
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        await manager.broadcast(json.dumps(
            {
                "type": "new_user",
                "user_id": "",
                "data": new_user.location_id
            }
        ))

        return new_user
    except Exception as e:
        db.rollback()  # Rollback changes in case of exception
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error! User record could not be saved.")


@router.get('/read-user/', response_model=Union[schemas.UserResponse, List[schemas.UserResponse]])
async def get_user(
        user_id: Optional[str] = None,
        limit: Optional[int] = 100,  # Default limit set to 100
        offset: Optional[int] = 0,  # Default offset set to 0
        db: Session = Depends(get_db),
        current_user: models.User = Depends(oauth2.get_current_user),
        # user_access: None = Depends(oauth2.has_permission("read_user")),
        location_id: Optional[str] = None,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        get_all: Optional[bool] = None,
        is_active: Optional[bool] = None,
        in_active: Optional[bool] = None
):
    # Extract user roles and level to fetch relevant data for the user
    role_id = await utils.create_admin_access_id(current_user)
    print(role_id)
    if not role_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not recognized!")

    query = db.query(models.User).filter(models.User.location_id.ilike(f'%{role_id}%'),
                                         models.User.is_deleted == False)

    # Apply filters based on query parameters
    if user_id:
        query = query.filter(models.User.user_id == user_id)

    if location_id:
        query = query.filter(models.User.location_id == location_id)

    if name:
        query = query.filter(models.User.name.ilike(f'%{name}%'))

    if phone:
        query = query.filter(models.User.phone == phone)

    if email:
        query = query.filter(models.User.email == email)

    if is_active is not None:
        query = query.filter(models.User.is_active == is_active)

    if in_active is not None:
        query = query.filter(models.User.is_active == False)

    # Apply pagination
    query = query.offset(offset).limit(limit)

    # Execute the query and get the results
    users = query.all()

    # Return results or raise an exception if no data is found
    if not users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User(s) not found!")

    if get_all:
        return users

    # If a single user was requested by ID, return just that user
    if user_id:
        if len(users) == 1:
            return users[0]
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'User with id: {user_id} not found!')

    return users


@router.delete("/delete-user/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, db: Session = Depends(get_db),
                      current_user: str = Depends(oauth2.get_current_user),
                      user_access: None = Depends(oauth2.has_permission("delete_user"))
                      ):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    user = db.query(models.User).filter(models.User.user_id == user_id,
                                        models.User.is_deleted == False,
                                        models.User.location_id.ilike(f"%{role}%")).first()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {user_id} not found")

    # Create an instance of UpdateUser with the desired fields
    update_data = schemas.UpdateUser(
        is_deleted=True,
        last_modify=datetime.now()
    )

    # Update the user with the new data
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()

    return {"status": "successful!",
            "message": f"User with ID: {user_id} has been marked as deleted."
            }


@router.patch("/update-user/", status_code=status.HTTP_200_OK)
async def update_user(user_id: str, update_data: schemas.UpdateUser, db: Session = Depends(get_db),
                      current_user: str = Depends(oauth2.get_current_user),
                      user_access: None = Depends(oauth2.has_permission("update_user"))):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    user = db.query(models.User).filter(models.User.user_id == user_id,
                                        models.User.is_deleted == False,
                                        models.User.location_id.ilike(f"%{role}%")).first()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {user_id} not found")

    # Update user fields with the data provided in the request
    update_fields = update_data.dict(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(user, field, value)

    # Update last_modify and operation only once
    user.last_modify = datetime.now()
    user.operation = "update"

    db.commit()
    db.refresh(user)

    # Update related workers table with relevant fields
    update_worker_fields = {
        'last_modify': user.last_modify,
        'operation': user.operation
    }

    if 'name' in update_fields:
        update_worker_fields['name'] = update_fields['name']
    if 'phone' in update_fields:
        update_worker_fields['phone'] = update_fields['phone']
    if 'location_id' in update_fields:
        update_worker_fields['location_id'] = update_fields['location_id']

    if update_worker_fields:
        db.query(models.Workers).filter(models.Workers.user_id == user_id).update(update_worker_fields)
        db.commit()

    return {"status": "successful!",
            "message": f"User with ID: {user_id} updated successfully."
            }


@router.post("/assign-roles/")
def assign_roles_to_user(assign_roles: schemas.AssignRolesToUser,
                         db: Session = Depends(get_db),
                         # current_user: str = Depends(oauth2.get_current_user),
                         # user_access: None = Depends(oauth2.has_permission("assign_role"))
                         ):
    user = db.query(models.User).filter_by(id=assign_roles.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    roles = db.query(models.Role).filter(models.Role.id.in_(assign_roles.role_ids)).all()
    if len(roles) != len(assign_roles.role_ids):
        raise HTTPException(status_code=404, detail="One or more roles not found")

    # Add roles to the user
    user.roles.extend(roles)
    db.commit()

    return {"status": "success", "message": "Roles assigned to user successfully"}


@router.delete("/remove-roles/")
def remove_roles_from_user(user_id: int, role_ids: List[int],
                           db: Session = Depends(get_db),
                           user_access: None = Depends(oauth2.has_permission("remove_role"))):
    # Fetch the user
    user = db.query(models.User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch the roles to remove
    roles = db.query(models.Role).filter(models.Role.id.in_(role_ids)).all()

    # Remove the roles from the user
    for role in roles:
        if role in user.roles:
            user.roles.remove(role)

    db.commit()

    return {
        "status": "success",
        "message": "Roles removed from user successfully",
        "user_id": user.id,
        "roles": [r.role_name for r in user.roles]
    }