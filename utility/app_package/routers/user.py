from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session, joinedload

from .. import schemas, utils, models, oauth2
from ..database import get_db

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.get("/state_region_data/")
async def get_region_state(user_id: str, db: Session = Depends(get_db),
                           current_user: str = Depends(oauth2.get_current_user)):
    # Extract location_id from the current user
    location_id = current_user.location_id

    # Split the location_id to extract state_id and region_id
    parts = location_id.split("-")
    if len(parts) < 3:
        raise HTTPException(status_code=400, detail="Invalid location ID format")

    state_id = parts[1]  # Assuming state_id is the second part
    region_id = parts[2]  # Assuming region_id is the third part

    # Query the database to fetch state and region data based on state_id and region_id
    # state = db.query(models.States).filter(models.States.state_id == state_id).first()
    state = db.query(models.States).filter(models.States.state_id == state_id).first()
    region = db.query(models.Region).filter(models.Region.region_id == region_id).first()

    if not state or not region:
        raise HTTPException(status_code=404, detail="State or region not found")

    # Create instances of StateResponse and RegionResponse
    state_response = {
        "state_id": state.state_id,
        "country": state.country,
        "state": state.state,
        "head_church": state.head_church,
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


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.UserResponse)
async def create_users(user: schemas.UserCreate, db: Session = Depends(get_db),
                       ):
    # admin_score = await utils.assess_score(current_user)
    #
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
