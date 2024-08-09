import json
from datetime import datetime
from typing import List, Union, Optional

from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy import extract
from sqlalchemy.orm import Session

from .websocket import manager
from .. import schemas, utils, models, oauth2
from ..database import get_db

router = APIRouter(
    prefix="/fellowship",
    tags=["Fellowships"]
)


@router.get('/read-fellowship/', response_model=Union[schemas.FellowshipResponse, List[schemas.FellowshipResponse]])
async def get_fellowship(
        id: Optional[int] = None,
        limit: Optional[int] = 100,  # Default limit set to 100
        offset: Optional[int] = 0,  # Default offset set to 0
        fellowship_id: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
        user_access: None = Depends(oauth2.has_permission("read_fellowship")),
        location_id: Optional[str] = None,
        fellowship_name: Optional[str] = None,
        get_all: Optional[bool] = None,
):
    """ this api route returns the lists of all locations in the state depending on certain criteria of the admin """

    role = await utils.create_admin_access_id(current_user)

    query = db.query(models.Fellowship).filter(models.Fellowship.Fellowship.id.ilike(f'%{role}%'),
                                               models.Fellowship.is_deleted == False)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No privilege for user type!")

    if id:
        query = query.filter(models.Fellowship.id == id)

    if location_id:
        query = query.filter(models.Fellowship.location_id == location_id)

    if fellowship_id:
        query = query.filter(models.Fellowship.fellowship_id == fellowship_id)

    if fellowship_name:
        query = query.filter(models.Fellowship.location_name.ilike(f'%{fellowship_name}%'))

    query = query.offset(offset).limit(limit)
    fellowships = query.all()

    if not fellowships:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Record not found!")

    if get_all:
        return fellowships

    # If a single user was requested by ID, return just that user
    if id:
        if len(fellowships) == 1:
            return fellowships[0]
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Count with id: {id} not found!')

    return fellowships


# this endpoint handles all incoming data for the fellowship creation
@router.post('/create-fellowship/', status_code=status.HTTP_201_CREATED, response_model=schemas.FellowshipResponse)
async def create_fellowship(fellowship: schemas.CreateFellowship, db: Session = Depends(get_db),
                            current_user: str = Depends(oauth2.get_current_user),
                            user_access: None = Depends(oauth2.has_permission("create_fellowships"))
                            ):
    try:
        new_fellowship = models.Fellowship(**fellowship.dict())
        db.add(new_fellowship)
        db.commit()
        db.refresh(new_fellowship)

        date_time = await utils.format_date_time(str(new_fellowship.created_at))

        return new_fellowship

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Internal Error! Fellowship could not be created.")


@router.patch("/update-fellowship/", response_model=schemas.FellowshipResponse)
async def update_fellowship(fellowship_id: str, fellowship_: schemas.UpdateFellowship,
                            db: Session = Depends(get_db),
                            user_access: None = Depends(oauth2.has_permission("update_fellowship")),
                            current_user: str = Depends(oauth2.get_current_user)):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No privilege for user type!")

    fellowship_query = db.query(models.Fellowship).filter(models.Fellowship.fellowship_id == fellowship_id,
                                                          models.Fellowship.is_deleted == False,
                                                          models.Fellowship.location_id.ilike(f'%{role}%'))

    fellowship = fellowship_query.first()

    if fellowship is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Fellowship with id: {fellowship_id} does not exist")

    if fellowship.is_deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Requested record not found or have been deleted")

    # Update the record with new data, and set the operation and last_modify fields
    updated_data = fellowship_.dict(exclude_unset=True)
    updated_data["last_modify"] = datetime.utcnow()
    updated_data["operation"] = "update"

    fellowship_query.update(updated_data)
    db.commit()
    db.refresh(fellowship)

    return fellowship_query.first()


@router.delete("/delete-fellowship/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fellowship(fellowship_id: str, db: Session = Depends(get_db),
                            user_access: None = Depends(oauth2.has_permission("delete_fellowship")),
                            current_user: str = Depends(oauth2.get_current_user)):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No privilege for user type!")

    fellowship = db.query(models.Fellowship).filter(models.Fellowship.fellowship_id == fellowship_id,
                                                    models.Fellowship.is_deleted == False,
                                                    models.Fellowship.location_id.ilike(f'%{role}%')).first()

    if fellowship is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Fellowship with id: {fellowship_id} does not exist")

    update_data = schemas.UpdateFellowship(
        is_deleted=True,
        last_modify=datetime.now(),
        operation="delete"
    )

    # Update the user with the new data
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(fellowship, field, value)
    db.commit()

    return {"status": "successful!",
            "message": f"Fellowship with ID: {fellowship_id} deleted successfully!"
            }


# #####################################################################################################################
# ########################### the fellowship attendance routes ###############################################

@router.get('/read-attendance/', response_model=Union[schemas.FAttendanceResponse, List[schemas.FAttendanceResponse]])
async def get_attendance(
        id: Optional[int] = None,
        fellowship_id: Optional[str] = None,
        limit: Optional[int] = 100,  # Default limit set to 100
        offset: Optional[int] = 0,  # Default offset set to 0
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
        user_access: None = Depends(oauth2.has_permission("read_fellowship_attendance")),
        location_id: Optional[str] = None,
        date: Optional[str] = None,
        fellowship_name: Optional[str] = None,
        get_all: Optional[bool] = None,
        start_month: Optional[int] = None,  # Start month of range
        end_month: Optional[int] = None,  # End month of range
        start_year: Optional[int] = None,  # Start year of range
        end_year: Optional[int] = None,  # End year of range
):
    """ this api route returns the lists of all locations in the state depending on certain criteria of the admin """

    role = await utils.create_admin_access_id(current_user)

    if role is None:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    query = db.query(models.FellowshipAttendance).filter(models.FellowshipAttendance.location_id.ilike(f'%{role}%'),
                                                         models.FellowshipAttendance.is_deleted == False)

    if id:
        query = query.filter(models.FellowshipAttendance.id == id)

    if location_id:
        query = query.filter(models.FellowshipAttendance.location_id == location_id)

    if date:
        query = query.filter(models.FellowshipAttendance.date == date)

    if fellowship_id:
        query = query.filter(models.FellowshipAttendance.fellowship_id == fellowship_id)

    if fellowship_name:
        query = query.filter(models.FellowshipAttendance.fellowship_name.ilike(f'%{fellowship_name}%'))

    if start_month and end_month:
        query = query.filter(
            extract('month', models.FellowshipAttendance.date) >= start_month,
            extract('month', models.FellowshipAttendance.date) <= end_month)

    if start_year and end_year:
        query = query.filter(
            extract('year', models.FellowshipAttendance.date) >= start_year,
            extract('year', models.FellowshipAttendance.date) <= end_year)

    # Apply limit and offset to the query
    query = query.offset(offset).limit(limit)
    attendance = query.all()
    if not attendance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

    if get_all:
        return attendance

    # If a single user was requested by ID, return just that user
    if id:
        if len(attendance) == 1:
            return attendance[0]
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Attendance with id: {id} not found!')

    return attendance


@router.post('/create-attendance/', status_code=status.HTTP_201_CREATED, response_model=schemas.FAttendanceResponse)
async def create_attendance(fellowship: schemas.CreateFAttendance, db: Session = Depends(get_db),
                            current_user: str = Depends(oauth2.get_current_user),
                            user_access: None = Depends(oauth2.has_permission("create_fellowship_attendance")),
                            ):
    try:
        new_fellowship = models.FellowshipAttendance(**fellowship.dict())
        db.add(new_fellowship)
        db.commit()
        db.refresh(new_fellowship)

        date_time = await utils.format_date_time(str(new_fellowship.created_at))

        await manager.broadcast(json.dumps(
            {
                "type": "notification",
                "user_id": current_user.user_id,
                "data": date_time,
                "note": "New count data submitted to the database, please check data for descriptions and more details"
            }
        ))

        return new_fellowship
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Internal Error! Attendance could not be created.")


@router.patch("/update-attendance/", response_model=schemas.FAttendanceResponse)
async def update_attendance(fellowship_id: str, fellowship_: schemas.UpdateFAttendance, db: Session = Depends(get_db),
                            current_user: str = Depends(oauth2.get_current_user),
                            user_access: None = Depends(oauth2.has_permission("update_fellowship_attendance")), ):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    fellowship_query = db.query(models.FellowshipAttendance).filter(
        models.FellowshipAttendance.fellowship_id == fellowship_id,
        models.FellowshipAttendance.is_deleted == False,
        models.FellowshipAttendance.location_id.ilike(f'%{role}%'))

    fellowship = fellowship_query.first()

    if fellowship is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Fellowship with id: {fellowship_id} does not exist")

    if fellowship.is_deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Record not found!")

    # Update the record with new data, and set the operation and last_modify fields
    updated_data = fellowship_.dict(exclude_unset=True)
    updated_data["last_modify"] = datetime.utcnow()
    updated_data["operation"] = "update"

    fellowship_query.update(updated_data)
    db.commit()
    db.refresh(fellowship)

    return fellowship_query.first()


@router.delete("/delete-attendance/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attendance(fellowship_id: str, db: Session = Depends(get_db),
                            current_user: str = Depends(oauth2.get_current_user),
                            user_access: None = Depends(oauth2.has_permission("delete_fellowship_attendance"))
                            ):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    fellowship = db.query(models.FellowshipAttendance).filter(
        models.FellowshipAttendance.fellowship_id == fellowship_id,
        models.FellowshipAttendance.is_deleted == False,
        models.FellowshipAttendance.location_id.ilike(f'%{role}%')).first()

    if fellowship is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Fellowship attendance with id: {fellowship_id} does not exist")

    update_data = schemas.UpdateFAttendance(
        is_deleted=True,
        last_modify=datetime.now(),
        operation="delete"
    )

    # Update the user with the new data
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(fellowship, field, value)
    db.commit()

    return {"status": "successful!",
            "message": f"Count record with ID: {fellowship_id} deleted successfully!"
            }


# #####################################################################################################################
# ########################### the fellowship member routes ###############################################

@router.get('/read-member/', response_model=Union[schemas.FMembersResponse, List[schemas.FMembersResponse]])
async def get_members(
        id: Optional[int] = None,
        fellowship_id: Optional[str] = None,
        limit: Optional[int] = 100,  # Default limit set to 100
        offset: Optional[int] = 0,  # Default offset set to 0
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
        user_access: None = Depends(oauth2.has_permission("read_fellowship_member")),
        location_id: Optional[str] = None,
        date: Optional[str] = None,
        fellowship_name: Optional[str] = None,
        get_all: Optional[bool] = None,
        gender: Optional[int] = None,  # Start month of range
        phone: Optional[int] = None,  # End month of range
        local_church: Optional[int] = None,  # Start year of range
):
    """ this api route returns the lists of all locations in the state depending on certain criteria of the admin """

    role = await utils.create_admin_access_id(current_user)

    if role is None:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    query = db.query(models.FellowshipMembers).filter(models.FellowshipMembers.location_id.ilike(f'%{role}%'),
                                                      models.FellowshipMembers.is_deleted == False)

    if id:
        query = query.filter(models.FellowshipMembers.id == id)

    if location_id:
        query = query.filter(models.FellowshipMembers.location_id == location_id)

    if date:
        query = query.filter(models.FellowshipMembers.date == date)

    if fellowship_id:
        query = query.filter(models.FellowshipMembers.fellowship_id == fellowship_id)

    if fellowship_name:
        query = query.filter(models.FellowshipMembers.fellowship_name.ilike(f'%{fellowship_name}%'))

    if gender:
        query = query.filter(models.FellowshipMembers.gender == gender)

    if phone:
        query = query.filter(models.FellowshipMembers.phone == phone)

    if local_church:
        query = query.filter(models.FellowshipMembers.local_church == local_church)

    # Apply limit and offset to the query
    query = query.offset(offset).limit(limit)
    members = query.all()
    if not members:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

    if get_all:
        return members

    # If a single user was requested by ID, return just that user
    if id:
        if len(members) == 1:
            return members[0]
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Members with id: {id} not found!')

    return members


@router.post('/create-member/', status_code=status.HTTP_201_CREATED, response_model=schemas.FMembersResponse)
async def create_members(members: schemas.CreateFMembers, db: Session = Depends(get_db),
                         current_user: str = Depends(oauth2.get_current_user),
                         user_access: None = Depends(oauth2.has_permission("create_fellowship_member"))
                         ):
    try:
        new_members = models.FellowshipMembers(**members.dict())
        db.add(new_members)
        db.commit()
        db.refresh(new_members)

        return new_members
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Internal Error! Attendance could not be created.")


@router.patch("/update-member/", response_model=schemas.FMembersResponse)
async def update_members(member_id: str, fellowship_: schemas.UpdateFMembers, db: Session = Depends(get_db),
                         current_user: str = Depends(oauth2.get_current_user),
                         user_access: None = Depends(oauth2.has_permission("update_fellowship_memeber"))):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    member_query = db.query(models.FellowshipMembers).filter(
        models.FellowshipMembers.fellowship_id == member_id,
        models.FellowshipMembers.is_deleted == False,
        models.FellowshipMembers.location_id.ilike(f'%{role}%'))

    member = member_query.first()

    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Fellowship with id: {member_id} does not exist")

    if member.is_deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Record not found!")

    # Update the record with new data, and set the operation and last_modify fields
    updated_data = fellowship_.dict(exclude_unset=True)
    updated_data["last_modify"] = datetime.utcnow()
    updated_data["operation"] = "update"

    member_query.update(updated_data)
    db.commit()
    db.refresh(member)

    return member_query.first()


@router.delete("/member-delete/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(member_id: str, db: Session = Depends(get_db),
                        current_user: str = Depends(oauth2.get_current_user),
                        user_access: None = Depends(oauth2.has_permission("delete_fellowship_member"))
                        ):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    member = db.query(models.FellowshipMembers).filter(
        models.FellowshipMembers.fellowship_id == member_id,
        models.FellowshipMembers.is_deleted == False,
        models.FellowshipMembers.location_id.ilike(f'%{role}%')).first()

    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Fellowship member with id: {member_id} does not exist")

    update_data = schemas.UpdateFMembers(
        is_deleted=True,
        last_modify=datetime.now(),
        operation="delete"
    )

    # Update the user with the new data
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(member, field, value)
    db.commit()

    return {"status": "successful!",
            "message": f"Member's record with ID: {member_id} deleted successfully!"
            }


# #####################################################################################################################
# ########################### the fellowship summary routes ###############################################

@router.get('/read-attendance_summaries/',
            response_model=Union[schemas.FAttendanceSumResponse, List[schemas.FAttendanceSumResponse]])
async def get_attendance_summaries(
        id: Optional[int] = None,
        fellowship_id: Optional[str] = None,
        limit: Optional[int] = 100,  # Default limit set to 100
        offset: Optional[int] = 0,  # Default offset set to 0
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
        user_access: None = Depends(oauth2.has_permission("read_fellowship_attendance_summary")),
        location_id: Optional[str] = None,
        date: Optional[str] = None,
        fellowship_name: Optional[str] = None,
        get_all: Optional[bool] = None,
        start_month: Optional[int] = None,  # Start month of range
        end_month: Optional[int] = None,  # End month of range
        start_year: Optional[int] = None,  # Start year of range
        end_year: Optional[int] = None,  # End year of range
):
    """ this api route returns the lists of all locations in the state depending on certain criteria of the admin """

    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No privilege for user type!")

    query = db.query(models.AttendanceSum).filter(models.AttendanceSum.location_id.ilike(f'%{role}%'),
                                                  models.AttendanceSum.is_deleted == False)

    if id:
        query = query.filter(models.AttendanceSum.id == id)

    if location_id:
        query = query.filter(models.AttendanceSum.location_id == location_id)

    if date:
        query = query.filter(models.AttendanceSum.date == date)

    if fellowship_id:
        query = query.filter(models.AttendanceSum.fellowship_id == fellowship_id)

    if fellowship_name:
        query = query.filter(models.AttendanceSum.fellowship_name.ilike(f'%{fellowship_name}%'))

    if start_month and end_month:
        query = query.filter(
            extract('month', models.AttendanceSum.date) >= start_month,
            extract('month', models.AttendanceSum.date) <= end_month)

    if start_year and end_year:
        query = query.filter(
            extract('year', models.AttendanceSum.date) >= start_year,
            extract('year', models.AttendanceSum.date) <= end_year)

    # Apply limit and offset to the query
    query = query.offset(offset).limit(limit)
    summary = query.all()

    if not summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Record not found!")

    if get_all:
        return summary

    # If a single user was requested by ID, return just that user
    if id:
        if len(summary) == 1:
            return summary[0]
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Summary with id: {id} not found!')

    return summary


@router.post('/create-attendance_summaries/', status_code=status.HTTP_201_CREATED,
             response_model=schemas.FAttendanceSumResponse)
async def create_attendance_summaries(summary: schemas.CreateFAttendanceSum, db: Session = Depends(get_db),
                                      user_access: None = Depends(
                                          oauth2.has_permission("create_fellowship_attendance_summary")),
                                      current_user: str = Depends(oauth2.get_current_user)
                                      ):
    try:
        new_summary = models.AttendanceSum(**summary.dict())
        db.add(new_summary)
        db.commit()
        db.refresh(new_summary)

        date_time = await utils.format_date_time(str(new_summary.created_at))

        return new_summary
    except Exception as e:
        db.rollback()  # Rollback changes in case of exception
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error! Attendance summary could not be saved.")


@router.patch("/update-attendance_summaries/", response_model=schemas.FAttendanceSumResponse)
async def update_attendance_summaries(summary_id: str, fellowship_: schemas.UpdateFAttendanceSum,
                                      db: Session = Depends(get_db),
                                      current_user: str = Depends(oauth2.get_current_user),
                                      user_access: None = Depends(
                                          oauth2.has_permission("update_fellowship_attendance_summary"))
                                      ):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    summary_query = db.query(models.AttendanceSum).filter(
        models.AttendanceSum.id == summary_id,
        models.AttendanceSum.is_deleted == False,
        models.AttendanceSum.location_id.ilike(f'%{role}%'))

    fellowship = summary_query.first()

    if fellowship is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Data with id: {summary_id} does not exist")

    if fellowship.is_deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Record not found!")

    # Update the record with new data, and set the operation and last_modify fields
    updated_data = fellowship_.dict(exclude_unset=True)
    updated_data["last_modify"] = datetime.utcnow()
    updated_data["operation"] = "update"

    summary_query.update(updated_data)
    db.commit()
    db.refresh(fellowship)

    return summary_query.first()


@router.delete("/delete-attendance_summaries/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attendance_summaries(summary_id: str, db: Session = Depends(get_db),
                                      current_user: str = Depends(oauth2.get_current_user),
                                      user_access: None = Depends(oauth2.has_permission("delete_count"))):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    summary = db.query(models.AttendanceSum).filter(
        models.AttendanceSum.id == summary_id,
        models.AttendanceSum.is_deleted == False,
        models.AttendanceSum.location_id.ilike(f'%{role}%')).first()

    if summary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Data with id: {summary_id} not found!")

    update_data = schemas.UpdateFAttendanceSum(
        is_deleted=True,
        last_modify=datetime.now(),
        operation="delete"
    )

    # Update the user with the new data
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(summary, field, value)
    db.commit()
    return {"status": "successful!",
            "message": f"Attendance record with ID: {summary_id} deleted successfully!"
            }


# #####################################################################################################################
# ########################### the fellowship testimonies routes ###############################################

@router.get('/read-testimonies/',
            response_model=Union[schemas.TestimoniesResponse, List[schemas.TestimoniesResponse]])
async def get_testimonies(
        id: Optional[int] = None,
        fellowship_id: Optional[str] = None,
        limit: Optional[int] = 100,  # Default limit set to 100
        offset: Optional[int] = 0,  # Default offset set to 0
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
        user_access: None = Depends(oauth2.has_permission("read_fellowship_testimony")),
        location_id: Optional[str] = None,
        date: Optional[str] = None,
        fellowship_name: Optional[str] = None,
        get_all: Optional[bool] = None,
        start_month: Optional[int] = None,  # Start month of range
        end_month: Optional[int] = None,  # End month of range
        start_year: Optional[int] = None,  # Start year of range
        end_year: Optional[int] = None,  # End year of range
):
    """ this api route returns the lists of all locations in the state depending on certain criteria of the admin """

    role = await utils.create_admin_access_id(current_user)

    if role is None:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    query = db.query(models.Testimony).filter(models.Testimony.location_id.ilike(f'%{role}%'),
                                              models.Testimony.is_deleted == False)

    if id:
        query = query.filter(models.Testimony.id == id)

    if location_id:
        query = query.filter(models.Testimony.location_id == location_id)

    if date:
        query = query.filter(models.Testimony.date == date)

    if fellowship_id:
        query = query.filter(models.Testimony.fellowship_id == fellowship_id)

    if fellowship_name:
        query = query.filter(models.Testimony.fellowship_name.ilike(f'%{fellowship_name}%'))

    if start_month and end_month:
        query = query.filter(
            extract('month', models.Testimony.date) >= start_month,
            extract('month', models.Testimony.date) <= end_month)

    if start_year and end_year:
        query = query.filter(
            extract('year', models.Testimony.date) >= start_year,
            extract('year', models.Testimony.date) <= end_year)

    # Apply limit and offset to the query
    query = query.offset(offset).limit(limit)
    testimony = query.all()

    if not testimony:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

    if get_all:
        return testimony

    # If a single user was requested by ID, return just that user
    if id:
        if len(testimony) == 1:
            return testimony[0]
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Count with id: {_id} not found!')

    return testimony


@router.post('/create-testimonies/', status_code=status.HTTP_201_CREATED, response_model=schemas.TestimoniesResponse)
async def create_testimony(testimony: schemas.CreateTestimonies, db: Session = Depends(get_db),
                           current_user: str = Depends(oauth2.get_current_user),
                           user_access: None = Depends(oauth2.has_permission("create_fellowship_testimony"))):
    try:
        new_testimony = models.Testimony(**testimony.dict())
        db.add(new_testimony)
        db.commit()
        db.refresh(new_testimony)

        return new_testimony
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Attendance could not be created.")


@router.patch("/update-testimonies/", response_model=schemas.TestimoniesResponse)
async def update_testimony(testimony_id: str, testimony_: schemas.UpdateTestimonies,
                           db: Session = Depends(get_db),
                           current_user: str = Depends(oauth2.get_current_user),
                           user_access: None = Depends(oauth2.has_permission("update_fellowship_testimony"))):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    testimony_query = db.query(models.Testimony).filter(
        models.Testimony.id == testimony_id,
        models.Testimony.is_deleted == False,
        models.Testimony.location_id.ilike(f'%{role}%')).first()

    testimony = testimony_query.first()

    if testimony is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Data with id: {testimony_id} does not exist")

    if testimony.is_deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Record not found!")

    # Update the record with new data, and set the operation and last_modify fields
    updated_data = testimony_.dict(exclude_unset=True)
    updated_data["last_modify"] = datetime.utcnow()
    updated_data["operation"] = "update"

    testimony_query.update(updated_data)
    db.commit()
    db.refresh(testimony)

    return testimony_query


@router.delete("/delete-testimonies/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_testimony(testimony_id: str, db: Session = Depends(get_db),
                           current_user: str = Depends(oauth2.get_current_user),
                           user_access: None = Depends(oauth2.has_permission("delete_fellowship_testimony"))):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    testimony = db.query(models.Testimony).filter(
        models.Testimony.id == testimony_id,
        models.Testimony.is_deleted == False,
        models.Testimony.location_id.ilike(f'%{role}%')).first()

    if testimony is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Data with id: {testimony_id} not found!")

    update_data = schemas.UpdateTestimonies(
        is_deleted=True,
        last_modify=datetime.now(),
        operation="delete"
    )

    # Update the user with the new data
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(testimony, field, value)
    db.commit()

    return {"status": "successful!",
            "message": f"Testimony record with ID: {testimony_id} deleted successfully!"
            }


# #####################################################################################################################
# ########################### the fellowship prayer request routes ###############################################

@router.get('/read-prayer_request/',
            response_model=Union[schemas.PrayerRequestResponse, List[schemas.PrayerRequestResponse]])
async def get_prayer(
        id: Optional[int] = None,
        fellowship_id: Optional[str] = None,
        limit: Optional[int] = 100,  # Default limit set to 100
        offset: Optional[int] = 0,  # Default offset set to 0
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
        user_access: None = Depends(oauth2.has_permission("read_fellowship_prayer")),
        location_id: Optional[str] = None,
        date: Optional[str] = None,
        fellowship_name: Optional[str] = None,
        get_all: Optional[bool] = None,
        start_month: Optional[int] = None,  # Start month of range
        end_month: Optional[int] = None,  # End month of range
        start_year: Optional[int] = None,  # Start year of range
        end_year: Optional[int] = None,  # End year of range
):
    """ this api route returns the lists of all locations in the state depending on certain criteria of the admin """

    role = await utils.create_admin_access_id(current_user)

    if role is None:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    query = db.query(models.PrayerRequest).filter(models.PrayerRequest.location_id.ilike(f'%{user_type}%'),
                                                  models.PrayerRequest.is_deleted == False)

    if id:
        query = query.filter(models.PrayerRequest.id == id)

    if location_id:
        query = query.filter(models.PrayerRequest.location_id == location_id)

    if date:
        query = query.filter(models.PrayerRequest.date == date)

    if fellowship_id:
        query = query.filter(models.PrayerRequest.fellowship_id == fellowship_id)

    if fellowship_name:
        query = query.filter(models.PrayerRequest.fellowship_name.ilike(f'%{fellowship_name}%'))

    if start_month and end_month:
        query = query.filter(
            extract('month', models.PrayerRequest.date) >= start_month,
            extract('month', models.PrayerRequest.date) <= end_month)

    if start_year and end_year:
        query = query.filter(
            extract('year', models.PrayerRequest.date) >= start_year,
            extract('year', models.PrayerRequest.date) <= end_year)

    # Apply limit and offset to the query
    query = query.offset(offset).limit(limit)
    prayer = query.all()

    if not prayer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Record not found')

    if get_all:
        return prayer

    # If a single user was requested by ID, return just that user
    if id:
        if len(prayer) == 1:
            return prayer[0]
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Record with id: {id} not found!')

    return prayer


@router.post('/create-prayer_request/', status_code=status.HTTP_201_CREATED, response_model=schemas.PrayerRequestResponse)
async def create_prayer(prayer: schemas.CreatePrayerRequest, db: Session = Depends(get_db),
                        current_user: str = Depends(oauth2.get_current_user),
                        user_access: None = Depends(oauth2.has_permission("create_fellowship_prayer"))
                        ):
    try:
        new_prayer = models.PrayerRequest(**prayer.dict())
        db.add(new_prayer)
        db.commit()
        db.refresh(new_prayer)

        return new_prayer
    except Exception as e:
        db.rollback()  # Rollback changes in case of exception
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error! Data could not be saved.")


@router.patch("/update-prayer_request/", response_model=schemas.PrayerRequestResponse)
async def update_prayer(prayer_id: str, prayer_: schemas.UpdatePrayerRequest,
                        db: Session = Depends(get_db),
                        current_user: str = Depends(oauth2.get_current_user),
                        user_access: None = Depends(oauth2.has_permission("update_fellowship_prayer"))):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    prayer_query = db.query(models.PrayerRequest).filter(
        models.PrayerRequest.id == prayer_id,
        models.PrayerRequest.is_deleted == False,
        models.PrayerRequest.location_id.ilike(f'%{role}%'))

    prayer = prayer_query.first()

    if prayer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Data with id: {prayer_id} does not exist")

    if prayer.is_deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Record not found!.")

    updated_data = prayer_.dict(exclude_unset=True)
    updated_data["last_modify"] = datetime.utcnow()
    updated_data["operation"] = "update"

    prayer_query.update(updated_data)
    db.commit()
    db.refresh(prayer)

    return prayer


@router.delete("/delete-prayer_request/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prayer(prayer_id: str, db: Session = Depends(get_db),
                        current_user: str = Depends(oauth2.get_current_user)):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    prayer = db.query(models.PrayerRequest).filter(
        models.PrayerRequest.id == prayer_id,
        models.PrayerRequest.is_deleted == False,
        models.Counter.location_id.ilike(f'%{role}%')).first()

    if prayer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Data with id: {prayer_id} not found!")

    if prayer.is_deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Record not found!.")

    update_data = schemas.UpdatePrayerRequest(
        is_deleted=True,
        last_modify=datetime.now(),
        operation="delete"
    )

    # Update the user with the new data
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(prayer, field, value)

    db.commit()
    return {"status": "successful!",
            "message": f"Record with ID: {prayer_id} deleted successfully!"
            }
