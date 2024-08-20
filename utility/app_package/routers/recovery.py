from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

import json
from datetime import datetime
from typing import List, Optional, Union
from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy import extract
from sqlalchemy.orm import Session

from .. import schemas, utils, models, oauth2
from ..database import get_db
from .websocket import manager

router = APIRouter(
    prefix="/recovery",
    tags=["Password Reset"]
)


def validate_token(db: Session, token: str):
    reset_token = db.query(models.PasswordResetToken).filter_by(token=token, is_used=False).first()
    if reset_token and reset_token.expiration > datetime.utcnow():
        return reset_token
    return None


@router.post("/set-recovery-question/")
async def set_recovery_question(data: schemas.RecoveryQuestionSetup, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(user_id=data.user_id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    hashed_answer = await utils.hash_answer(data.answer)
    # Store the recovery question and answer
    reset_token = models.PasswordResetToken(
        user_id=user.user_id,
        token=str(uuid.uuid4()),  # Generate a token
        expiration=datetime.utcnow() + timedelta(minutes=30),
        recovery_question=data.question,
        recovery_answer=hashed_answer,
        is_used=False
    )
    db.add(reset_token)
    db.commit()

    return {"message": "Recovery Question saved successfully!!"}


@router.post("/request-reset/", response_model=schemas.PasswordResetResponse)
async def request_password_reset(data: schemas.PasswordResetRequest, db: Session = Depends(get_db)):
    reset_token = db.query(models.PasswordResetToken).filter_by(user_id=data.user_id, is_used=False).first()

    # hashed_answer = (await utils.hash_password(data.answer))
    verified = await utils.verify_answer(reset_token.recovery_answer, data.answer)
    if not reset_token or verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect answer or token not found")

    # Generate a new token for password reset
    new_token = str(uuid.uuid4())
    reset_token.token = new_token
    reset_token.expiration = datetime.utcnow() + timedelta(minutes=30)
    db.commit()

    return schemas.PasswordResetResponse(token=new_token)


@router.post("/reset-password/")
async def reset_password(data: schemas.PasswordResetComplete, db: Session = Depends(get_db)):
    reset_token = db.query(models.PasswordResetToken).filter_by(
        token=data.token,
        is_used=False
    ).first()
    if not reset_token or reset_token.expiration < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    user = db.query(models.User).filter_by(user_id=reset_token.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Update the user's password
    user.password = await utils.hash_password(data.new_password)
    reset_token.is_used = True
    db.commit()

    return {"message": "Password successfully reset"}
