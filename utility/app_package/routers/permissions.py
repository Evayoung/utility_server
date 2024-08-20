import json
from typing import List

from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session

from .. import schemas, utils, models, oauth2
from ..database import get_db
from .websocket import manager

router = APIRouter(
    prefix="/permissions",
    tags=["Permissions"]
)


@router.post("/create-permission/", status_code=status.HTTP_201_CREATED, response_model=schemas.PermissionResponse)
async def create_permission(permission: schemas.CreatePermission, db: Session = Depends(get_db),
                            # user_assess: dict = Depends(oauth2.has_permission("create_permission"))
                            ):
    try:
        db_permission = db.query(models.Permission).filter(
            models.Permission.permission == permission.permission).first()
        if db_permission:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Permission already exists")
        new_permission = models.Permission(**permission.dict())
        db.add(new_permission)
        db.commit()
        db.refresh(new_permission)
        return new_permission
    except Exception as e:
        db.rollback()  # Rollback changes in case of exception
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Permission could not be created.")


@router.get("/read-permission/", response_model=List[schemas.PermissionResponse])
async def get_permissions(skip: int = 0, limit: int = 10, db: Session = Depends(get_db),
                          # current_user: dict = Depends(oauth2.has_permission("read_permission"))
                          ):
    permissions = db.query(models.Permission).offset(skip).limit(limit).all()
    return permissions


@router.get("/read-permission/", response_model=schemas.PermissionResponse)
async def get_permission(permission_id: int, db: Session = Depends(get_db),
                         current_user: dict = Depends(oauth2.has_permission("read_permission"))
                         ):
    permission = db.query(models.Permission).filter(models.Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    return permission


@router.put("/update-permission/", response_model=schemas.PermissionResponse)
async def update_permission(permission_id: int, permission: schemas.UpdatePermission, db: Session = Depends(get_db),
                            current_user: dict = Depends(oauth2.has_permission("update_permission"))):
    db_permission = db.query(models.Permission).filter(models.Permission.id == permission_id).first()
    if not db_permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    for key, value in permission.dict(exclude_unset=True).items():
        setattr(db_permission, key, value)
    db.commit()
    db.refresh(db_permission)
    return db_permission


@router.delete("/delete-permission/", response_model=schemas.PermissionResponse)
async def delete_permission(permission_id: int, db: Session = Depends(get_db),
                            current_user: dict = Depends(oauth2.has_permission("delete_permission"))):
    db_permission = db.query(models.Permission).filter(models.Permission.id == permission_id).first()
    if not db_permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    db.delete(db_permission)
    db.commit()
    return db_permission
