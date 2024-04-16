from typing import List, Union

from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session

from .. import schemas, utils, models, oauth2
from ..database import get_db

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.UserResponse, include_in_schema=False)
async def create_users(user: schemas.UserCreate, db: Session = Depends(get_db),
                       ):

    # admin_score = await utils.assess_score(current_user)

    # if admin_score < 2:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privilege")

    try:
        # hash the password - user.password
        hashed_password = await utils.hash_password(user.password)
        user.password = hashed_password

        new_user = models.User(**user.dict())
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user
    except Exception as e:
        db.rollback()  # Rollback changes in case of exception
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error! User record could not be saved.")


@router.get('/', response_model=schemas.UserResponse)
async def get_user(user_id: str, db: Session = Depends(get_db), current_user: str = Depends(oauth2.get_current_user)):

    role = await utils.create_admin_access_id(current_user)
    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No privilege for user type!")

    user = db.query(models.User).filter(models.User.user_id == user_id,
                                        models.User.location_id.ilike(f"%{role}%")).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'User with id: {user_id} not found!')

    return user


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, db: Session = Depends(get_db),
                      current_user: str = Depends(oauth2.get_current_user),
                      ):
    role = await utils.create_admin_access_id(current_user)
    admin_score = await utils.assess_score(current_user)

    if admin_score < 5:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privilege")

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    user = db.query(models.User).filter(models.User.user_id == user_id,
                                        models.User.location_id.ilike(f"%{role}%"))

    if user.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {user_id} not found")

    user.delete(synchronize_session=False)
    db.commit()

    return {"status": "successful!",
            "message": f"User with ID: {user_id} deleted successfully!"
            }


@router.put("/", response_model=schemas.UserResponse)
async def update_user(user_id: str, users: schemas.UpdateUser, db: Session = Depends(get_db),
                      current_user: str = Depends(oauth2.get_current_user)):

    role = await utils.create_admin_access_id(current_user)
    admin_score = await utils.assess_score(current_user)

    if admin_score < 5:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privilege")

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No privilege for user type!")

    user_query = db.query(models.User).filter(models.User.user_id == user_id,
                                              models.User.location_id.ilike(f"%{role}%"))

    user = user_query.first()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {user_id} not found")

    user_query.update(users.dict())
    db.commit()

    return user_query.first()
