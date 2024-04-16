from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import utils, models, oauth2, database

router = APIRouter(
    prefix="/login",
    tags=["Authentication"]
)


@router.post('/')
async def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == user_credentials.username).first()

    if not user:    # check if user exists
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User Not Found!")

    if not await utils.verify_password(user_credentials.password, user.password):   # verify the user password
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")

    if not user.is_active:  # check if user account is active or not
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Account not activated, please contact admin")

    # create user access token to be used with other api endpoints
    access_token = await oauth2.create_access_token(data={"user_id": user.user_id, "local_id": user.location_id})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.user_id,
        "user_name": user.name,
        "user_email": user.email,
        "user_role": user.role
    }



