from datetime import datetime
from typing import List, Union, Optional

from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session

from .. import schemas, models, oauth2, utils
from ..database import get_db

router = APIRouter(
    prefix="/state",
    tags=["State"]
)


@router.get('/read-state/', response_model=Union[schemas.StateResponse, List[schemas.StateResponse]])
async def get_state(
        id: Optional[int] = None,
        limit: Optional[int] = 100,  # Default limit set to 100
        offset: Optional[int] = 0,  # Default offset set to 0
        state_id: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
        # user_access: None = Depends(oauth2.has_permission("read_state")),
        state_name: Optional[str] = None,
        get_all: Optional[bool] = None,
):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No privilege for user type!")

    query = db.query(models.States).filter(models.States.id == id,
                                           models.States.is_deleted == False,
                                           models.States.location_id.ilike(f'%{role}%')).first()

    if id:
        query = db.query(models.States).filter(models.States.id == id)

    if state_id:
        query = query.filter(models.States.state_id == state_id)

    if state_name:
        query = query.filter(models.States.state_name.ilike(f'%{state_name}%'))

    query = query.offset(offset).limit(limit)
    state = query.all()

    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Record with ID: {state} not found!")

    if get_all:
        return state

    # If a single user was requested by ID, return just that user
    if id:
        if len(state) == 1:
            return state[0]
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'State with id: {id} not found!')

    return state


@router.post('/create-state/', status_code=status.HTTP_201_CREATED, response_model=schemas.StateResponse)
async def create_state(state: schemas.CreateState, db: Session = Depends(get_db),
                       current_user: str = Depends(oauth2.get_current_user),
                       # user_access: None = Depends(oauth2.has_permission("create_state"))
                       ):
    try:
        new_state = models.States(**state.dict())
        db.add(new_state)
        db.commit()
        db.refresh(new_state)

        return new_state
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error! State could not be created.")


@router.put("/update-state/", response_model=schemas.StateResponse)
async def update_state(state_id: str, state_: schemas.UpdateState, db: Session = Depends(get_db),
                       current_user: str = Depends(oauth2.get_current_user),
                       user_access: None = Depends(oauth2.has_permission("update_state"))):

    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No privilege for user type!")

    state_query = db.query(models.States).filter(models.States.state_id == state_id,
                                                 models.States.is_deleted == False,
                                                 models.States.state_id.ilike(f"%{role}%"))

    state = state_query.first()

    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {state_id} does not exist")

    if state.is_deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Record not found!")

    # Update the record with new data, and set the operation and last_modify fields
    updated_data = state.dict(exclude_unset=True)
    updated_data["last_modify"] = datetime.utcnow()
    updated_data["operation"] = "update"

    state_query.update(updated_data)
    db.commit()
    db.refresh(state)

    return state


@router.delete("/delete-state/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_state(state_id: str, db: Session = Depends(get_db),
                       current_user: str = Depends(oauth2.get_current_user),
                       user_access: None = Depends(oauth2.has_permission("delete_state"))):

    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No privilege for user type!")

    state = db.query(models.States).filter(models.States.state_id == state_id,
                                           models.States.is_deleted == False,
                                           models.States.state_id.ilike(f"%{role}%")).first()

    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f" State ID: {state_id} does not exist")

    update_data = schemas.UpdateState(
        is_deleted=True,
        last_modify=datetime.now(),
        operation="delete"
    )

    # Update the user with the new data
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(state, field, value)

    db.commit()

    return {"status": "successful!",
            "message": f"User with ID: {state_id} deleted successfully!"
            }
