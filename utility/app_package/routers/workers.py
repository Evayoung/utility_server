from datetime import datetime
from typing import List, Union, Optional

from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session

from .. import utils, models, schemas, oauth2
from ..database import get_db

router = APIRouter(
    prefix="/workers",
    tags=["Workers"]
)


@router.get('/get-workers-details/', response_model=schemas.WorkerResponse)
async def get_workers_details(email: str = None,
                              db: Session = Depends(get_db),
                              workers_id: str = None):
    if not workers_id and workers_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'No worker Id entered')

    worker = db.query(models.Workers).filter(models.Workers.email == email).first()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'User with id: {email} not found!')

    return worker


# this endpoint creates the workers account on the server and is opened to all
@router.post('/create-worker/', status_code=status.HTTP_201_CREATED, response_model=schemas.WorkerResponse)
async def create_worker(worker: schemas.CreateWorkers,
                        db: Session = Depends(get_db),
                        # user_access: None = Depends(oauth2.has_permission("create_worker"))
                        ):
    try:
        user_id = await utils.generate_id(worker.location_id, worker.phone, db)

        # Create a new dictionary with all data from hospital_data and add hospital_id
        worker_dict = worker.dict()
        worker_dict['user_id'] = user_id

        new_worker = models.Workers(**worker_dict)
        db.add(new_worker)
        db.commit()
        db.refresh(new_worker)

        return new_worker
    except Exception as e:
        db.rollback()  # Rollback changes in case of exception
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Worker could not be created.")


# this endpoint get workers details base on search parameters and data are filtered based on user access
@router.get('/read-worker/', response_model=Union[schemas.WorkerResponse, List[schemas.WorkerResponse]])
async def get_workers(
        user_id: Optional[str] = None,
        limit: Optional[int] = 100,  # Default limit set to 100
        offset: Optional[int] = 0,  # Default offset set to 0
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
        user_access: None = Depends(oauth2.has_permission("read_worker")),
        location_id: Optional[str] = None,
        gender: Optional[str] = None,
        location: Optional[str] = None,
        email: Optional[str] = None,
        get_all: Optional[bool] = None,
        occupation: Optional[str] = None,
        marital_status: Optional[str] = None,
        unit: Optional[str] = None,
        address: Optional[str] = None,
        # search_term: Optional[str] = None,  # New parameter for regex search term
):
    user_type = await utils.create_admin_access_id(current_user)

    if not user_type:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not recognized")

    query = db.query(models.Workers).filter(models.Workers.location_id.ilike(f'%{user_type}%'),
                                            models.Workers.is_deleted == False)

    if user_id:
        query = query.filter(models.Workers.id == user_id)

    if location_id:
        query = query.filter(models.Workers.location_id == location_id)

    if gender:
        query = query.filter(models.Workers.gender == gender)

    if location:
        query = query.filter(models.Workers.location.ilike(f'%{location}%'))

    if email:
        query = query.filter(models.Workers.email == email)

    if occupation:
        query = query.filter(models.Workers.occupation.ilike(f'%{occupation}%'))

    if marital_status:
        query = query.filter(models.Workers.marital_status == marital_status)

    if unit:
        query = query.filter(models.Workers.unit.ilike(f'%{unit}%'))

    if address:
        query = query.filter(models.Workers.address == address)

    # Apply pagination
    query = query.offset(offset).limit(limit)

    # Execute the query and get the results
    worker = query.all()

    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Worker(s) not found!")

    if get_all:
        return worker

    # If a single user was requested by ID, return just that user
    if user_id:
        if len(worker) == 1:
            return worker[0]
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Worker with id: {user_id} not found!')

    return worker


@router.patch("/update-worker/", status_code=status.HTTP_200_OK)
async def update_worker(worker_id: str, worker: schemas.UpdateWorker, db: Session = Depends(get_db),
                        current_user: str = Depends(oauth2.get_current_user),
                        # user_access: None = Depends(oauth2.has_permission("update_worker"))
                        ):

    role = await utils.create_admin_access_id(current_user)
    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No read privilege for user type!")

    user_query = db.query(models.Workers).filter(models.Workers.user_id == worker_id,
                                                 models.Workers.location_id.ilike(f'%{role}%'))

    user = user_query.first()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Worker with id: {worker_id} does not exist")

    # Update user fields with the data provided in the request
    update_fields = worker.dict(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(user, field, value)

    user.last_modify = datetime.now()
    user.operation = "update"

    db.commit()

    # Update related workers table with relevant fields
    update_user_fields = {
        'last_modify': user.last_modify,
        'operation': user.operation
    }

    if 'name' in update_fields:
        update_user_fields['name'] = update_fields['name']
    if 'phone' in update_fields:
        update_user_fields['phone'] = update_fields['phone']
    if 'location_id' in update_fields:
        update_user_fields['location_id'] = update_fields['location_id']

    if update_user_fields:
        db.query(models.User).filter(models.User.user_id == worker_id).update(update_user_fields)
        db.commit()

    return {"status": "successful!",
            "message": f"User with ID: {worker_id} updated successfully."
            }


@router.delete("/delete-worker/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workers(worker_id: str, db: Session = Depends(get_db),
                         current_user: str = Depends(oauth2.get_current_user),
                         user_access: None = Depends(oauth2.has_permission("delete_worker")),
                         ):

    """ this is the workers delete endpoint. this deletes system uses a soft delete mechanism, meaning data deleted
    are not actually deleted but marked as deleted thereby making it unavailable to anyone requesting it """

    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    worker = db.query(models.Workers).filter(models.Workers.user_id == worker_id,
                                             models.Workers.location_id.ilike(f'%{role}%')).first()

    if worker is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"worker with id: {worker_id} is not found!")

    update_data = schemas.UpdateWorker(
        is_deleted=True,
        last_modify=datetime.now(),
        operation='delete'
    )

    # Update the worker with the new data
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(worker, field, value)

    db.commit()

    # Update related user table to set is_deleted = True
    delete_user = {
        'last_modify': update_data.last_modify,
        'operation': update_data.operation,
        'is_deleted': update_data.is_deleted
    }

    if delete_user:
        db.query(models.User).filter(models.User.user_id == worker_id).update(delete_user)
        db.commit()

    return {"status": "successful!",
            "message": f"Worker with ID: {worker_id} deleted successfully!"
            }