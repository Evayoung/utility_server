from typing import List, Union, Optional

from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session

from .. import schemas, models, oauth2, utils
from ..database import get_db

router = APIRouter(
    prefix="/state",
    tags=["State"]
)


@router.get('/', response_model=Union[schemas.StateResponse, List[schemas.StateResponse]])
async def get_state(
        id: Optional[int] = None,
        limit: Optional[int] = 100,  # Default limit set to 100
        offset: Optional[int] = 0,    # Default offset set to 0
        state_id: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
        state_name: Optional[str] = None,
        get_all: Optional[bool] = None,
):
    role = await utils.create_admin_access_id(current_user)
    admin_score = await utils.assess_score(current_user)

    if admin_score < 5:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privilege")

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No privilege for user type!")

    if id:
        state = db.query(models.States).filter(models.States.id == id,
                                               models.States.state_id.ilike(f"%{role}%")).first()
        if not state:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'State with id: {id} not found!')
        return state

    if get_all:
        state = db.query(models.States).filter(models.States.state_id.ilike(f"%{role}%")).offset(offset).limit(limit).all()
        if not state:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'No data found!')
        return state

    query = db.query(models.States)

    if state_id:
        state = query.filter(models.States.state_id == state_id,
                             models.States.state_id.ilike(f"%{role}%")).first()
        if not state:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'State with id: {state_id} not found!')
        return state

    if state_name:
        query = query.filter(models.States.state_name.ilike(f'%{state_name}%'),
                             models.States.state_id.ilike(f"%{role}%"))

    query = query.offset(offset).limit(limit)
    state = query.all()

    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Record with ID: {state} not found!")

    return state


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.StateResponse)
async def create_state(state: schemas.CreateState, db: Session = Depends(get_db),
                       current_user: str = Depends(oauth2.get_current_user)
                       ):
    admin_score = await utils.assess_score(current_user)

    if admin_score < 5:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privilege")

    try:
        new_state = models.States(**state.dict())
        db.add(new_state)
        db.commit()
        db.refresh(new_state)

        return new_state
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Internal Error! State could not be created.")


@router.put("/", response_model=schemas.StateResponse)
async def update_state(state_id: str, state_: schemas.UpdateState, db: Session = Depends(get_db),
                       current_user: str = Depends(oauth2.get_current_user)):

    role = await utils.create_admin_access_id(current_user)
    admin_score = await utils.assess_score(current_user)

    if admin_score < 5:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privilege")

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No privilege for user type!")

    state_query = db.query(models.States).filter(models.States.state_id == state_id,
                                                 models.States.state_id.ilike(f"%{role}%"))

    state = state_query.first()

    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {state_id} does not exist")

    state_query.update(state_.dict())
    db.commit()

    return state_query.first()


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_state(state_id: str, db: Session = Depends(get_db),
                       current_user: str = Depends(oauth2.get_current_user)):
    role = await utils.create_admin_access_id(current_user)
    admin_score = await utils.assess_score(current_user)

    if admin_score < 5:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privilege!")

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No privilege for user type!")

    state = db.query(models.States).filter(models.States.state_id == state_id,
                                           models.States.state_id.ilike(f"%{role}%"))

    if state.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f" State ID: {state_id} does not exist")

    state.delete(synchronize_session=False)
    db.commit()
    return {"status": "successful!",
            "message": f"User with ID: {state_id} deleted successfully!"
            }
