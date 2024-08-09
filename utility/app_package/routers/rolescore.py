import json
from typing import List

from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session

from .. import schemas, utils, models, oauth2
from ..database import get_db
from .websocket import manager

router = APIRouter(
    prefix="/levels",
    tags=["Levels"]
)


@router.post("/create-level/", status_code=status.HTTP_201_CREATED, response_model=schemas.RoleScoreResponse)
async def create_levels(level: schemas.CreateRoleScore, db: Session = Depends(get_db),
                        # current_user: dict = Depends(oauth2.has_permission("create_level"))
                        ):
    try:
        # Extract the score_name from the level Pydantic model
        db_role = db.query(models.RoleScore).filter(
            models.RoleScore.score_name == level.score_name).first()

        if db_role:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Level already exists")

        new_level = models.RoleScore(**level.dict())
        db.add(new_level)
        db.commit()
        db.refresh(new_level)
        return new_level

    except Exception as e:
        db.rollback()  # Rollback changes in case of exception
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Level could not be created.")


@router.get("/read-level/", response_model=List[schemas.RoleScoreResponse])
async def get_levels(skip: int = 0, limit: int = 10, db: Session = Depends(get_db),
                     # current_user: dict = Depends(oauth2.has_permission("read_level"))
                     ):
    level = db.query(models.RoleScore).offset(skip).limit(limit).all()
    return level


@router.get("/read-levels/", response_model=schemas.RoleScoreResponse)
async def get_level(level_id: int, db: Session = Depends(get_db),
                    current_user: dict = Depends(oauth2.has_permission("read_level"))
                    ):
    level = db.query(models.RoleScore).filter(models.RoleScore.id == level_id).first()
    if not level:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Level not found")
    return level


@router.put("/update-level/", response_model=schemas.RoleScoreResponse)
async def update_level(level_id: int, role: schemas.UpdateRoleScore, db: Session = Depends(get_db),
                       current_user: dict = Depends(oauth2.has_permission("update_level"))):
    db_level = db.query(models.RoleScore).filter(models.RoleScore.id == level_id).first()
    if not db_level:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Level not found")
    for key, value in role.dict(exclude_unset=True).items():
        setattr(db_level, key, value)
    db.commit()
    db.refresh(db_level)
    return db_level


@router.delete("/delete-level/", response_model=schemas.RoleScoreResponse)
async def delete_level(level_id: int, db: Session = Depends(get_db),
                       current_user: dict = Depends(oauth2.has_permission("delete_level"))):
    db_level = db.query(models.RoleScore).filter(models.RoleScore.id == level_id).first()
    if not db_level:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Level not found")
    db.delete(db_level)
    db.commit()
    return db_level
