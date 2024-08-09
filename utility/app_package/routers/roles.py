import json
from typing import List

from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session

from .. import schemas, utils, models, oauth2
from ..database import get_db
from .websocket import manager

router = APIRouter(
    prefix="/roles",
    tags=["Roles"]
)


@router.post("/create-roles/", status_code=status.HTTP_201_CREATED, response_model=schemas.RolesResponse)
async def create_roles(role: schemas.CreateRoles, db: Session = Depends(get_db),
                       # current_user: dict = Depends(oauth2.has_permission("create_permission"))
                       ):
    try:
        db_role = db.query(models.Role).filter(
            models.Role.role_name == role.role_name).first()
        if db_role:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role already exists")
        new_role = models.Role(**role.dict())
        db.add(new_role)
        db.commit()
        db.refresh(new_role)
        return new_role
    except Exception as e:
        db.rollback()  # Rollback changes in case of exception
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Role could not be created.")


@router.get("/read-roles/", response_model=List[schemas.RolesResponse])
async def get_roles(skip: int = 0, limit: int = 10, db: Session = Depends(get_db),
                    # current_user: dict = Depends(oauth2.has_permission("read_permission"))
                    ):
    roles = db.query(models.Role).offset(skip).limit(limit).all()
    return roles


@router.get("/read-role/", response_model=schemas.RolesResponse)
async def get_role(role_id: int, db: Session = Depends(get_db),
                   # current_user: dict = Depends(oauth2.has_permission("read_roles"))
                   ):
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role


@router.put("/update-role/", response_model=schemas.PermissionResponse)
async def update_role(role_id: int, role: schemas.UpdateRoles, db: Session = Depends(get_db),
                      current_user: dict = Depends(oauth2.has_permission("update_role"))):
    db_role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not db_role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    for key, value in role.dict(exclude_unset=True).items():
        setattr(db_role, key, value)
    db.commit()
    db.refresh(db_role)
    return db_role


@router.post("/permissions-to-role/")
def assign_permissions_to_role(assign_permissions: schemas.AssignPermissionsToRole, db: Session = Depends(get_db)):
    role = db.query(models.Role).filter_by(id=assign_permissions.role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    permissions = db.query(models.Permission).filter(models.Permission.id.in_(assign_permissions.permission_ids)).all()
    if len(permissions) != len(assign_permissions.permission_ids):
        raise HTTPException(status_code=404, detail="One or more permissions not found")

    # Clear existing permissions (if needed) and add new ones
    role.permissions = permissions
    db.commit()

    return {"status": "success", "message": "Permissions assigned to role successfully"}


@router.delete("/remove-permissions/")
def remove_permissions_from_role(role_id: int, permission_ids: List[int], db: Session = Depends(get_db)):
    # Fetch the role
    role = db.query(models.Role).filter_by(id=role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Fetch the permissions to remove
    permissions = db.query(models.Permission).filter(models.Permission.id.in_(permission_ids)).all()

    # Remove the permissions from the role
    for permission in permissions:
        if permission in role.permissions:
            role.permissions.remove(permission)

    db.commit()

    return {
        "status": "success",
        "message": "Permissions removed from role successfully",
        "role_id": role.id,
        "permissions": [p.permission for p in role.permissions]
    }


@router.delete("/delete-role/", response_model=schemas.RolesResponse)
async def delete_role(role_id: int, db: Session = Depends(get_db),
                      current_user: dict = Depends(oauth2.has_permission("delete_role"))):
    db_role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not db_role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    db.delete(db_role)
    db.commit()
    return db_role
