from datetime import datetime, timedelta

from passlib.context import CryptContext
from sqlalchemy.orm import Session
from . import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def hash_password(password):
    return pwd_context.hash(password)


async def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


async def hash_answer(answer: str) -> str:
    return pwd_context.hash(answer)


async def verify_answer(stored_hash: str, answer: str) -> bool:
    return pwd_context.verify(answer, stored_hash)


async def create_admin_access_id(user):
    # Check if the user has roles
    print(user)
    if not user.roles:
        raise ValueError("User has no roles assigned.")

    # Get the first role for simplicity
    role_score = user.roles[0].score.score
    print(role_score)
    loc_id = user.location_id.split('-')

    # Determine access based on role_score
    if role_score <= 3:
        data = '-'.join(loc_id[:5])
        return data

    if role_score == 4:
        data = '-'.join(loc_id[:4])
        return data

    elif role_score == 5:
        data = '-'.join(loc_id[:3])
        return data

    elif role_score == 7:
        data = '-'.join(loc_id[:2])
        return data

    elif 8 <= role_score <= 9:
        data = '_'.join(loc_id[:1])
        return data

    else:
        return False


async def generate_id(location_id: str, phone: str, db: Session):
    if location_id and phone:
        if "+" in phone:
            phone = phone.lstrip("+")

        while True:
            location = location_id.split("-")
            user_id = f"{location[2].upper()}/{str(phone)}"
            if not db.query(models.Workers).filter(models.Workers.user_id == user_id).first():
                return user_id  # Return the user_id if it's unique


# this function is called to create the fellowship id using the associate location name
async def create_fellowship_id(name: str):
    pass


async def format_date_time(data: str):
    # convert to datetime object
    dt = datetime.fromisoformat(data)

    # get current date and time
    now = datetime.now(dt.tzinfo)
    today = now.date()
    yesterday = today - timedelta(days=1)

    # determine the date part
    if dt.date() == today:
        date_part = "Today"
    elif dt.date() == yesterday:
        date_part = "Yesterday"
    else:
        date_part = dt.strftime("%Y/%m/%d")

    # determine the time part
    time_part = dt.strftime("%I:%M %p")

    # combine date and time parts
    final_datetime = f"{date_part}    {time_part}"

    return final_datetime


async def return_region_filter(user: str) -> str:
    id_parts = user.location_id.split("-")
    score = user.roles[0].score.score
    if score <= 4:
        region_id = "-".join(id_parts[:4])
        return region_id

    elif score == 5:
        data = '-'.join(id_parts[:3])
        return data

    elif score == 7:
        data = '-'.join(id_parts[:2])
        return data

    elif 8 <= score <= 9:
        data = '_'.join(id_parts[:1])
        return data

    else:
        return None
