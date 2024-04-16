from typing import List, Union, Optional

from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy import extract
from sqlalchemy.orm import Session

from .. import schemas, utils, models, oauth2
from ..database import get_db

router = APIRouter(
    prefix="/fellowship",
    tags=["Fellowships"]
)


@router.get('/', response_model=Union[schemas.FellowshipResponse, List[schemas.FellowshipResponse]])
async def get_fellowship(
        id: Optional[int] = None,
        limit: Optional[int] = 100,  # Default limit set to 100
        offset: Optional[int] = 0,  # Default offset set to 0
        fellowship_id: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
        location_id: Optional[str] = None,
        fellowship_name: Optional[str] = None,
        get_all: Optional[bool] = None,
):
    """ this api route returns the lists of all locations in the state depending on certain criteria of the admin """

    role = await utils.create_admin_access_id(current_user)
    query = db.query(models.Fellowship)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No privilege for user type!")

    if id:
        fellowship = query.filter(models.Fellowship.id == id,
                                  models.Fellowship.location_id.ilike(f'%{role}%')).first()
        if not fellowship:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

        return fellowship

    if get_all:  # get all data
        fellowship = query.filter(models.Fellowship.location_id.ilike(f'%{role}%')).offset(offset).limit(limit).all()
        if not fellowship:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')
        return fellowship

    if location_id:
        query = query.filter(models.Fellowship.location_id == location_id,
                             models.Fellowship.location_id.ilike(f'%{role}%'))

    if fellowship_id:
        query = query.filter(models.Fellowship.fellowship_id == fellowship_id,
                             models.Fellowship.location_id.ilike(f'%{role}%'))

    if fellowship_name:
        query = query.filter(models.Fellowship.location_name.ilike(f'%{fellowship_name}%'),
                             models.Fellowship.location_id.ilike(f'%{role}%'))

    query = query.offset(offset).limit(limit)
    fellowships = query.all()

    if not fellowships:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Record not found!")

    return fellowships


# this endpoint handles all incoming data for the fellowship creation
@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.FellowshipResponse)
async def create_fellowship(fellowship: schemas.CreateFellowship, db: Session = Depends(get_db),
                            current_user: str = Depends(oauth2.get_current_user)
                            ):
    try:
        new_fellowship = models.Fellowship(**fellowship.dict())
        db.add(new_fellowship)
        db.commit()
        db.refresh(new_fellowship)

        return new_fellowship

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Internal Error! Fellowship could not be created.")


@router.put("/", response_model=schemas.FellowshipResponse)
async def update_fellowship(fellowship_id: str, fellowship_: schemas.UpdateFellowship,
                            db: Session = Depends(get_db),
                            current_user: str = Depends(oauth2.get_current_user)):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No privilege for user type!")

    fellowship_query = db.query(models.Fellowship).filter(models.Fellowship.fellowship_id == fellowship_id,
                                                          models.Fellowship.location_id.ilike(f'%{role}%'))

    fellowship = fellowship_query.first()

    if fellowship is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Fellowship with id: {fellowship_id} does not exist")

    fellowship_query.update(fellowship_.dict())
    db.commit()

    return fellowship_query.first()


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fellowship(fellowship_id: str, db: Session = Depends(get_db),
                            current_user: str = Depends(oauth2.get_current_user)):
    role = await utils.create_admin_access_id(current_user)
    admin_score = await utils.assess_score(current_user)

    if admin_score < 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privilege!")

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No privilege for user type!")

    fellowship = db.query(models.Fellowship).filter(models.Fellowship.fellowship_id == fellowship_id,
                                                    models.Fellowship.location_id.ilike(f'%{role}%'))

    if fellowship.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Fellowship with id: {fellowship_id} does not exist")

    fellowship.delete(synchronize_session=False)
    db.commit()
    return {"status": "successful!",
            "message": f"Fellowship with ID: {fellowship_id} deleted successfully!"
            }


# #####################################################################################################################
# ########################### the fellowship attendance routes ###############################################

@router.get('/attendance', response_model=Union[schemas.FAttendanceResponse, List[schemas.FAttendanceResponse]])
async def get_attendance(
        id: Optional[int] = None,
        fellowship_id: Optional[str] = None,
        limit: Optional[int] = 100,  # Default limit set to 100
        offset: Optional[int] = 0,  # Default offset set to 0
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
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
    query = db.query(models.FellowshipAttendance)

    if id:
        fellowship = query.filter(models.FellowshipAttendance.id == id,
                                  models.FellowshipAttendance.location_id.ilike(f'%{role}%')).first()
        if not fellowship:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

        return fellowship

    if get_all:

        attendance = query.filter(models.FellowshipAttendance.location_id.ilike(f'%{role}%')).offset(offset).limit(
            limit).all()
        if not attendance:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Attendance not found!')

        return attendance

    if location_id:
        query = query.filter(models.FellowshipAttendance.location_id == location_id,
                             models.FellowshipAttendance.location_id.ilike(f'%{role}%'))

    if date:
        query = query.filter(models.FellowshipAttendance.date == date,
                             models.FellowshipAttendance.location_id.ilike(f'%{role}%'))

    if fellowship_id:
        query = query.filter(models.FellowshipAttendance.fellowship_id == fellowship_id,
                             models.FellowshipAttendance.location_id.ilike(f'%{role}%'))

    if fellowship_name:
        query = query.filter(models.FellowshipAttendance.fellowship_name.ilike(f'%{fellowship_name}%'),
                             models.FellowshipAttendance.location_id.ilike(f'%{role}%'))

    if start_month and end_month:
        query = query.filter(
            extract('month', models.FellowshipAttendance.date) >= start_month,
            extract('month', models.FellowshipAttendance.date) <= end_month,
            models.FellowshipAttendance.location_id.ilike(f'%{role}%')
        )

    if start_year and end_year:
        query = query.filter(
            extract('year', models.FellowshipAttendance.date) >= start_year,
            extract('year', models.FellowshipAttendance.date) <= end_year,
            models.FellowshipAttendance.location_id.ilike(f'%{role}%')
        )

    # Apply limit and offset to the query
    query = query.offset(offset).limit(limit)
    attendance = query.all()
    if not attendance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

    return attendance


@router.post('/attendance', status_code=status.HTTP_201_CREATED, response_model=schemas.FAttendanceResponse)
async def create_attendance(fellowship: schemas.CreateFAttendance, db: Session = Depends(get_db),
                            current_user: str = Depends(oauth2.get_current_user)
                            ):
    try:
        new_fellowship = models.FellowshipAttendance(**fellowship.dict())
        db.add(new_fellowship)
        db.commit()
        db.refresh(new_fellowship)

        return new_fellowship
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Internal Error! Attendance could not be created.")


@router.put("/attendance", response_model=schemas.FAttendanceResponse)
async def update_attendance(fellowship_id: str, fellowship_: schemas.UpdateFAttendance, db: Session = Depends(get_db),
                            current_user: str = Depends(oauth2.get_current_user)):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    fellowship_query = db.query(models.FellowshipAttendance).filter(
        models.FellowshipAttendance.fellowship_id == fellowship_id,
        models.FellowshipAttendance.location_id.ilike(f'%{role}%'))

    fellowship = fellowship_query.first()

    if fellowship is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Fellowship with id: {fellowship_id} does not exist")

    fellowship_query.update(fellowship_.dict())
    db.commit()

    return fellowship_query.first()


@router.delete("/attendance", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attendance(fellowship_id: str, db: Session = Depends(get_db),
                            current_user: str = Depends(oauth2.get_current_user)):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    fellowship = db.query(models.FellowshipAttendance).filter(
        models.FellowshipAttendance.fellowship_id == fellowship_id,
        models.FellowshipAttendance.location_id.ilike(f'%{role}%'))

    if fellowship.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Fellowship attendance with id: {fellowship_id} does not exist")

    if current_user.role != "Super Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    fellowship.delete(synchronize_session=False)
    db.commit()
    return {"status": "successful!",
            "message": f"Count record with ID: {fellowship_id} deleted successfully!"
            }


# #####################################################################################################################
# ########################### the fellowship member routes ###############################################

@router.get('/members', response_model=Union[schemas.FMembersResponse, List[schemas.FMembersResponse]])
async def get_members(
        id: Optional[int] = None,
        fellowship_id: Optional[str] = None,
        limit: Optional[int] = 100,  # Default limit set to 100
        offset: Optional[int] = 0,  # Default offset set to 0
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
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
    query = db.query(models.FellowshipMembers)

    if id:
        members = query.filter(models.FellowshipMembers.id == id,
                               models.FellowshipMembers.location_id.ilike(f'%{role}%')).first()
        if not members:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

        return members

    if get_all:

        members = query.filter(models.FellowshipMembers.location_id.ilike(f'%{role}%')).offset(offset).limit(
            limit).all()
        if not members:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Attendance not found!')

        return members

    if location_id:
        query = query.filter(models.FellowshipMembers.location_id == location_id,
                             models.FellowshipMembers.location_id.ilike(f'%{role}%'))

    if date:
        query = query.filter(models.FellowshipMembers.date == date,
                             models.FellowshipMembers.location_id.ilike(f'%{role}%'))

    if fellowship_id:
        query = query.filter(models.FellowshipMembers.fellowship_id == fellowship_id,
                             models.FellowshipMembers.location_id.ilike(f'%{role}%'))

    if fellowship_name:
        query = query.filter(models.FellowshipMembers.fellowship_name.ilike(f'%{fellowship_name}%'),
                             models.FellowshipMembers.location_id.ilike(f'%{role}%'))

    if gender:
        query = query.filter(models.FellowshipMembers.gender == gender,
                             models.FellowshipMembers.location_id.ilike(f'%{role}%'))

    if phone:
        query = query.filter(models.FellowshipMembers.phone == phone,
                             models.FellowshipMembers.location_id.ilike(f'%{role}%'))

    if local_church:
        query = query.filter(models.FellowshipMembers.local_church == local_church,
                             models.FellowshipMembers.location_id.ilike(f'%{role}%'))

    # Apply limit and offset to the query
    query = query.offset(offset).limit(limit)
    members = query.all()
    if not members:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

    return members


@router.post('/members', status_code=status.HTTP_201_CREATED, response_model=schemas.FMembersResponse)
async def create_members(members: schemas.CreateFMembers, db: Session = Depends(get_db),
                         current_user: str = Depends(oauth2.get_current_user)
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


@router.put("/attendance", response_model=schemas.FMembersResponse)
async def update_members(member_id: str, fellowship_: schemas.UpdateFMembers, db: Session = Depends(get_db),
                         current_user: str = Depends(oauth2.get_current_user)):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    member_query = db.query(models.FellowshipMembers).filter(
        models.FellowshipMembers.fellowship_id == member_id,
        models.FellowshipMembers.location_id.ilike(f'%{role}%'))

    member = member_query.first()

    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Fellowship with id: {member_id} does not exist")

    member_query.update(fellowship_.dict())
    db.commit()

    return member_query.first()


@router.delete("/member", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(member_id: str, db: Session = Depends(get_db),
                        current_user: str = Depends(oauth2.get_current_user)):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    member = db.query(models.FellowshipMembers).filter(
        models.FellowshipMembers.fellowship_id == member_id,
        models.FellowshipMembers.location_id.ilike(f'%{role}%'))

    if member.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Fellowship attendance with id: {member_id} does not exist")

    if current_user.role != "Super Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    member.delete(synchronize_session=False)
    db.commit()
    return {"status": "successful!",
            "message": f"Member's record with ID: {member_id} deleted successfully!"
            }


# #####################################################################################################################
# ########################### the fellowship summary routes ###############################################

@router.get('/attendance_summaries',
            response_model=Union[schemas.FAttendanceSumResponse, List[schemas.FAttendanceSumResponse]])
async def get_attendance_summaries(
        id: Optional[int] = None,
        fellowship_id: Optional[str] = None,
        limit: Optional[int] = 100,  # Default limit set to 100
        offset: Optional[int] = 0,  # Default offset set to 0
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
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
    query = db.query(models.AttendanceSum)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No privilege for user type!")

    if id:
        summary = query.filter(models.AttendanceSum.id == id,
                               models.AttendanceSum.location_id.ilike(f'%{role}%')).first()

        if not summary:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

        return summary

    if get_all:
        summary = query.filter(models.AttendanceSum.location_id.ilike(f'%{role}%')).offset(offset).limit(limit).all()

        if not summary:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

        return summary

    if location_id:
        query = query.filter(models.AttendanceSum.location_id == location_id,
                             models.AttendanceSum.location_id.ilike(f'%{role}%'))

    if date:
        query = query.filter(models.AttendanceSum.date == date,
                             models.AttendanceSum.location_id.ilike(f'%{role}%'))

    if fellowship_id:
        query = query.filter(models.AttendanceSum.fellowship_id == fellowship_id,
                             models.AttendanceSum.location_id.ilike(f'%{role}%'))

    if fellowship_name:
        query = query.filter(models.AttendanceSum.fellowship_name.ilike(f'%{fellowship_name}%'),
                             models.AttendanceSum.location_id.ilike(f'%{role}%'))

    if start_month and end_month:
        query = query.filter(
            extract('month', models.AttendanceSum.date) >= start_month,
            extract('month', models.AttendanceSum.date) <= end_month,
            models.AttendanceSum.location_id.ilike(f'%{role}%')
        )

    if start_year and end_year:
        query = query.filter(
            extract('year', models.AttendanceSum.date) >= start_year,
            extract('year', models.AttendanceSum.date) <= end_year,
            models.AttendanceSum.location_id.ilike(f'%{role}%')
        )

    # Apply limit and offset to the query
    query = query.offset(offset).limit(limit)
    summary = query.all()

    if not summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Record not found!")

    return summary


@router.post('/attendance_summaries', status_code=status.HTTP_201_CREATED,
             response_model=schemas.FAttendanceSumResponse)
async def create_attendance_summaries(summary: schemas.CreateFAttendanceSum, db: Session = Depends(get_db),
                                      current_user: str = Depends(oauth2.get_current_user)
                                      ):
    try:
        new_summary = models.AttendanceSum(**summary.dict())
        db.add(new_summary)
        db.commit()
        db.refresh(new_summary)

        return new_summary
    except Exception as e:
        db.rollback()  # Rollback changes in case of exception
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error! Attendance summary could not be saved.")


@router.put("/attendance_summaries", response_model=schemas.FAttendanceSumResponse)
async def update_attendance_summaries(summary_id: str, fellowship_: schemas.UpdateFAttendanceSum,
                                      db: Session = Depends(get_db),
                                      current_user: str = Depends(oauth2.get_current_user)):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    summary_query = db.query(models.AttendanceSum).filter(
        models.AttendanceSum.id == summary_id,
        models.AttendanceSum.location_id.ilike(f'%{role}%'))

    fellowship = summary_query.first()

    if fellowship is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Data with id: {summary_id} does not exist")

    summary_query.update(fellowship_.dict())
    db.commit()

    return summary_query.first()


@router.delete("/attendance_summaries", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attendance_summaries(summary_id: str, db: Session = Depends(get_db),
                                      current_user: str = Depends(oauth2.get_current_user)):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    summary = db.query(models.AttendanceSum).filter(
        models.AttendanceSum.id == summary_id,
        models.AttendanceSum.location_id.ilike(f'%{role}%'))

    if summary.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Data with id: {summary_id} not found!")

    summary.delete(synchronize_session=False)
    db.commit()
    return {"status": "successful!",
            "message": f"Attendance record with ID: {summary_id} deleted successfully!"
            }


# #####################################################################################################################
# ########################### the fellowship plans routes ###############################################

@router.get('/fellowship_plan',
            response_model=Union[schemas.FellowshipPlanResponse, List[schemas.FellowshipPlanResponse]])
async def get_fellowship_plan(
        id: Optional[int] = None,
        fellowship_id: Optional[str] = None,
        limit: Optional[int] = 100,  # Default limit set to 100
        offset: Optional[int] = 0,  # Default offset set to 0
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
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
    query = db.query(models.FellowshipPlan)

    if role is None:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    if id:
        plans = query.filter(models.FellowshipPlan.id == id,
                             models.FellowshipPlan.location_id.ilike(f'%{role}%')).first()

        if not plans:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

        return plans

    if get_all:
        # groups = db.query(models.Group).all()
        plans = query.filter(models.FellowshipPlan.location_id.ilike(f'%{role}%')).offset(offset).limit(limit).all()

        if not plans:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

        return plans

    if location_id:
        query = query.filter(models.FellowshipPlan.location_id == location_id,
                             models.FellowshipPlan.location_id.ilike(f'%{role}%'))

    if date:
        query = query.filter(models.FellowshipPlan.date == date,
                             models.FellowshipPlan.location_id.ilike(f'%{role}%'))

    if fellowship_id:
        query = query.filter(models.FellowshipPlan.fellowship_id == fellowship_id,
                             models.FellowshipPlan.location_id.ilike(f'%{role}%'))

    if fellowship_name:
        query = query.filter(models.FellowshipPlan.fellowship_name.ilike(f'%{fellowship_name}%'),
                             models.FellowshipPlan.location_id.ilike(f'%{role}%'))

    if start_month and end_month:
        query = query.filter(
            extract('month', models.FellowshipPlan.date) >= start_month,
            extract('month', models.FellowshipPlan.date) <= end_month,
            models.FellowshipPlan.location_id.ilike(f'%{role}%')
        )

    if start_year and end_year:
        query = query.filter(
            extract('year', models.FellowshipPlan.date) >= start_year,
            extract('year', models.FellowshipPlan.date) <= end_year,
            models.FellowshipPlan.location_id.ilike(f'%{role}%')
        )

    query = query.offset(offset).limit(limit)
    plan = query.all()

    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found')

    return plan


@router.post('/fellowship_plan', status_code=status.HTTP_201_CREATED,
             response_model=schemas.FellowshipPlanResponse)
async def create_fellowship_plan(plan: schemas.CreateFellowshipPlan, db: Session = Depends(get_db),
                                 current_user: str = Depends(oauth2.get_current_user)):
    try:
        new_plan = models.FellowshipPlan(**plan.dict())
        db.add(new_plan)
        db.commit()
        db.refresh(new_plan)

        return new_plan
    except Exception as e:
        db.rollback()  # Rollback changes in case of exception
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error! Fellowship plan could not be saved.")


@router.put("/fellowship_plan", response_model=schemas.FellowshipPlanResponse)
async def update_fellowship_plan(plan_id: str, plan_: schemas.UpdateFellowshipPlan,
                                 db: Session = Depends(get_db),
                                 current_user: str = Depends(oauth2.get_current_user)):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    plan_query = db.query(models.FellowshipPlan).filter(
        models.FellowshipPlan.id == plan_id,
        models.FellowshipPlan.location_id.ilike(f'%{role}%'))

    plan = plan_query.first()

    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Data with id: {plan_id} does not exist")

    plan_query.update(plan_.dict())
    db.commit()

    return plan_query.first()


@router.delete("/fellowship_plan", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fellowship_plan(plan_id: str, db: Session = Depends(get_db),
                                 current_user: str = Depends(oauth2.get_current_user)):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    plan = db.query(models.FellowshipPlan).filter(
        models.FellowshipPlan.id == plan_id,
        models.FellowshipPlan.location_id.ilike(f'%{role}%'))

    if plan.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Data with id: {plan_id} not found!")

    plan.delete(synchronize_session=False)
    db.commit()
    return {"status": "successful!",
            "message": f"Plan record with ID: {plan_id} deleted successfully!"
            }


# #####################################################################################################################
# ########################### the fellowship testimonies routes ###############################################

@router.get('/testimonies',
            response_model=Union[schemas.TestimoniesResponse, List[schemas.TestimoniesResponse]])
async def get_testimonies(
        id: Optional[int] = None,
        fellowship_id: Optional[str] = None,
        limit: Optional[int] = 100,  # Default limit set to 100
        offset: Optional[int] = 0,  # Default offset set to 0
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
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
    query = db.query(models.Testimony)

    if role is None:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    if id:
        # groups = db.query(models.Group).all()
        plans = query.filter(models.Testimony.id == id,
                             models.Testimony.location_id.ilike(f'%{role}%')).first()

        if not plans:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

        return plans

    if get_all:
        # groups = db.query(models.Group).all()
        plans = query.filter(models.Testimony.location_id.ilike(f'%{role}%')).offset(offset).limit(limit).all()

        if not plans:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

        return plans

    if location_id:
        query = query.filter(models.Testimony.location_id == location_id,
                             models.Testimony.location_id.ilike(f'%{role}%'))

    if date:
        query = query.filter(models.Testimony.date == date,
                             models.Testimony.location_id.ilike(f'%{role}%'))

    if fellowship_id:
        query = query.filter(models.Testimony.fellowship_id == fellowship_id,
                             models.Testimony.location_id.ilike(f'%{role}%'))

    if fellowship_name:
        query = query.filter(models.Testimony.fellowship_name.ilike(f'%{fellowship_name}%'),
                             models.Testimony.location_id.ilike(f'%{role}%'))

    if start_month and end_month:
        query = query.filter(
            extract('month', models.Testimony.date) >= start_month,
            extract('month', models.Testimony.date) <= end_month,
            models.Testimony.location_id.ilike(f'%{role}%')
        )

    if start_year and end_year:
        query = query.filter(
            extract('year', models.Testimony.date) >= start_year,
            extract('year', models.Testimony.date) <= end_year,
            models.Testimony.location_id.ilike(f'%{role}%')
        )

    # Apply limit and offset to the query
    query = query.offset(offset).limit(limit)
    testimony = query.all()

    if not testimony:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

    return testimony


@router.post('/testimonies', status_code=status.HTTP_201_CREATED, response_model=schemas.TestimoniesResponse)
async def create_testimony(testimony: schemas.CreateTestimonies, db: Session = Depends(get_db),
                           current_user: str = Depends(oauth2.get_current_user)):
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


@router.put("/testimonies", response_model=schemas.TestimoniesResponse)
async def update_testimony(testimony_id: str, testimony_: schemas.UpdateTestimonies,
                           db: Session = Depends(get_db),
                           current_user: str = Depends(oauth2.get_current_user)):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    testimony_query = db.query(models.Testimony).filter(
        models.Testimony.id == testimony_id,
        models.Testimony.location_id.ilike(f'%{role}%'))

    testimony = testimony_query.first()

    if testimony is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Data with id: {testimony_id} does not exist")

    testimony_query.update(testimony_.dict())
    db.commit()

    return testimony_query.first()


@router.delete("/testimonies", status_code=status.HTTP_204_NO_CONTENT)
async def delete_testimony(testimony_id: str, db: Session = Depends(get_db),
                           current_user: str = Depends(oauth2.get_current_user)):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    testimony = db.query(models.Testimony).filter(
        models.Testimony.id == testimony_id,
        models.Testimony.location_id.ilike(f'%{role}%'))

    if testimony.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Data with id: {testimony_id} not found!")

    testimony.delete(synchronize_session=False)
    db.commit()
    return {"status": "successful!",
            "message": f"Testimony record with ID: {testimony_id} deleted successfully!"
            }


# #####################################################################################################################
# ########################### the fellowship prayer request routes ###############################################

@router.get('/prayer_request',
            response_model=Union[schemas.PrayerRequestResponse, List[schemas.PrayerRequestResponse]])
async def get_prayer(
        id: Optional[int] = None,
        fellowship_id: Optional[str] = None,
        limit: Optional[int] = 100,  # Default limit set to 100
        offset: Optional[int] = 0,  # Default offset set to 0
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
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
    query = db.query(models.PrayerRequest)

    if role is None:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    if id:
        # groups = db.query(models.Group).all()
        prayer = query.filter(models.PrayerRequest.id == id,
                              models.PrayerRequest.location_id.ilike(f'%{role}%')).first()
        if not prayer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

        return prayer

    if get_all:
        # groups = db.query(models.Group).all()
        prayer = query.filter(models.PrayerRequest.location_id.ilike(f'%{role}%')).offset(offset).limit(limit).all()
        if not prayer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found!')

        return prayer

    if location_id:
        query = query.filter(models.PrayerRequest.location_id == location_id,
                             models.PrayerRequest.location_id.ilike(f'%{role}%'))

    if date:
        query = query.filter(models.PrayerRequest.date == date,
                             models.PrayerRequest.location_id.ilike(f'%{role}%'))

    if fellowship_id:
        query = query.filter(models.PrayerRequest.fellowship_id == fellowship_id,
                             models.PrayerRequest.location_id.ilike(f'%{role}%'))

    if fellowship_name:
        query = query.filter(models.PrayerRequest.fellowship_name.ilike(f'%{fellowship_name}%'),
                             models.PrayerRequest.location_id.ilike(f'%{role}%'))

    if start_month and end_month:
        query = query.filter(
            extract('month', models.PrayerRequest.date) >= start_month,
            extract('month', models.PrayerRequest.date) <= end_month,
            models.PrayerRequest.location_id.ilike(f'%{role}%')
        )

    if start_year and end_year:
        query = query.filter(
            extract('year', models.PrayerRequest.date) >= start_year,
            extract('year', models.PrayerRequest.date) <= end_year,
            models.PrayerRequest.location_id.ilike(f'%{role}%')
        )

    # Apply limit and offset to the query
    query = query.offset(offset).limit(limit)
    prayer = query.all()

    if not prayer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No data found')

    return prayer


@router.post('/prayer_request', status_code=status.HTTP_201_CREATED, response_model=schemas.PrayerRequestResponse)
async def create_prayer(prayer: schemas.CreatePrayerRequest, db: Session = Depends(get_db),
                        current_user: str = Depends(oauth2.get_current_user)):
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


@router.put("/prayer_request", response_model=schemas.PrayerRequestResponse)
async def update_prayer(prayer_id: str, prayer_: schemas.UpdatePrayerRequest,
                        db: Session = Depends(get_db),
                        current_user: str = Depends(oauth2.get_current_user)):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    prayer_query = db.query(models.PrayerRequest).filter(
        models.PrayerRequest.id == prayer_id,
        models.PrayerRequest.location_id.ilike(f'%{role}%'))

    prayer = prayer_query.first()

    if prayer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Data with id: {prayer_id} does not exist")

    prayer_query.update(prayer_.dict())
    db.commit()

    return prayer_query.first()


@router.delete("/prayer_request", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prayer(prayer_id: str, db: Session = Depends(get_db),
                        current_user: str = Depends(oauth2.get_current_user)):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    prayer = db.query(models.PrayerRequest).filter(
        models.PrayerRequest.id == prayer_id,
        models.PrayerRequest.location_id.ilike(f'%{role}%'))

    if prayer.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Data with id: {prayer_id} not found!")

    prayer.delete(synchronize_session=False)
    db.commit()
    return {"status": "successful!",
            "message": f"Record with ID: {prayer_id} deleted successfully!"
            }
