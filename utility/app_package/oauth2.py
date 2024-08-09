from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, status, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload
from starlette.responses import JSONResponse

from . import models, schemas, database
from .config import settings
from .schemas import UserResponse

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


async def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        user_id: str = payload.get("user_id")
        local_id: str = payload.get("location_id")
        if user_id is None:
            raise credentials_exception
        token_data = schemas.TokenData(user_id=user_id, local_id=local_id)
    except JWTError:
        raise credentials_exception
    return token_data


def get_current_user(token: str = Depends(oauth2_scheme),
                     db: Session = Depends(database.get_db)) -> schemas.UsersResponse:
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    # Verify the token and get the token data
    token_data = verify_access_token(token, credential_exception)

    # Fetch the user from the database with eagerly loaded roles and role scores
    user = db.query(models.User).options(
        joinedload(models.User.roles).joinedload(models.Role.score)
    ).filter(models.User.user_id == token_data.user_id).first()

    if user is None:
        raise credential_exception

    # Convert the user object to a Pydantic model
    user_response = schemas.UsersResponse(
        user_id=user.user_id,
        location_id=user.location_id,
        name=user.name,
        email=user.email,
        roles=[schemas.Role(
            role_name=role.role_name,
            score=schemas.RoleScore(
                score=role.score.score,
                score_name=role.score.score_name
            )
        ) for role in user.roles]
    )

    return user_response


def has_permission(permission: str):
    def permission_checker(current_user: str = Depends(get_current_user), db: Session = Depends(database.get_db)):

        user_role = current_user.roles[0].role_name
        # Fetch the role of the current user
        role = db.query(models.Role).filter(models.Role.role_name == user_role).first()

        if role is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role not found")

        # Check if the role has the required permission
        role_permissions = db.query(models.Permission).join(models.Role.permissions).filter(
            models.Role.id == role.id).all()

        if not any(p.permission == permission for p in role_permissions):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough Privilege")

        return current_user

    return permission_checker
