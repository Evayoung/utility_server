
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from . import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def hash_password(password):
    return pwd_context.hash(password)


async def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


async def create_admin_access_id(user):
    loc_id = user.location_id.split('-')

    # DCL-234-KW-ILR-ILE-0002
    if user.role == "User" or user.role == "Usher":
        data = '-'.join(loc_id[:5])
        return user.user_id

    if user.role == "General Coordinator" or user.role == "Associate Coordinator":
        data = '-'.join(loc_id[:5])
        return user.location_id

    elif user.role == "Group Coordinator" or user.role == "Group Admin":
        data = '-'.join(loc_id[:5])
        return data

    elif user.role == "Regional Coordinator" or user.role == "Regional Admin":
        data = '-'.join(loc_id[:4])
        return data

    elif user.role == "State Overseer" or user.role == "State Admin":
        data = '-'.join(loc_id[:3])
        return data

    elif user.role == "National Admin" or user.role == "National Overseer":
        data = '-'.join(loc_id[:2])
        return data

    elif user.role == "General Superintendent":
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


# this function generate the user privilege by rating from a count range of 1 to 7,
# while 1 is the list and 7 is the highest
async def assess_score(user: str):
    if user.role == "User" or user.role == "Usher":
        return 1

    if user.role == "General Coordinator" or user.role == "Associate Coordinator":
        return 2

    elif user.role == "Group Coordinator" or user.role == "Group Admin":
        return 3

    elif user.role == "Regional Coordinator" or user.role == "Regional Admin":
        return 4

    elif user.role == "State Overseer" or user.role == "State Usher":
        return 5

    elif user.role == "National Admin" or user.role == "National Overseer":
        return 6

    elif user.role == "General Superintendent":
        return 7

    else:
        return 0


# this function is called to create the fellowship id using the associate location name
async def create_fellowship_id(name: str):
    pass
