from typing import List, Union, Optional

from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session

from .. import utils, models, schemas, oauth2
from ..database import get_db
import uuid

router = APIRouter(
    prefix="/workers",
    tags=["Workers"]
)


@router.get('/details/', response_model=schemas.WorkerResponse)
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
@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.WorkerResponse)
async def create_worker(worker: schemas.CreateWorkers, db: Session = Depends(get_db)):
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
@router.get('/', response_model=Union[schemas.WorkerResponse, List[schemas.WorkerResponse]])
async def get_workers(
        user_id: Optional[str] = None,
        limit: Optional[int] = 100,  # Default limit set to 100
        offset: Optional[int] = 0,  # Default offset set to 0
        db: Session = Depends(get_db),
        current_user: str = Depends(oauth2.get_current_user),
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access for user type!")

    query = db.query(models.Workers)
    if get_all:
        workers = query.filter(models.Workers.location_id.ilike(f'%{user_type}%')).all()

        return workers

    if user_id:
        worker = query.filter(models.Workers.id == user_id,
                              models.Workers.location_id.ilike(f'%{user_type}%')).first()

        if not worker:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'Worker with id: {user_id} not found!')
        return worker

    if location_id:
        query = query.filter(models.Workers.location_id.ilike(f'%{location_id}%'),
                             models.Workers.location_id.ilike(f'%{user_type}%'))

    if gender:
        query = query.filter(models.Workers.gender.ilike(f'%{gender}%'),
                             models.Workers.location_id.ilike(f'%{user_type}%'))

    if location:
        query = query.filter(models.Workers.location.ilike(f'%{location}%'),
                             models.Workers.location_id.ilike(f'%{user_type}%'))

    if email:
        query = query.filter(models.Workers.email == email,
                             models.Workers.location_id.ilike(f'%{user_type}%'))

    if occupation:
        query = query.filter(models.Workers.occupation.ilike(f'%{occupation}%'),
                             models.Workers.location_id.ilike(f'%{user_type}%'))

    if marital_status:
        query = query.filter(models.Workers.marital_status == marital_status,
                             models.Workers.location_id.ilike(f'%{user_type}%'))

    if unit:
        query = query.filter(models.Workers.unit.ilike(f'%{unit}%'),
                             models.Workers.location_id.ilike(f'%{user_type}%'))

    if address:
        query = query.filter(models.Workers.address == address,
                             models.Workers.location_id.ilike(f'%{user_type}%'))

    query = query.offset(offset).limit(limit)
    workers = query.all()
    if not workers:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Worker with id: {user_id} not found!')

    return workers


@router.put("/", response_model=schemas.WorkerResponse)
async def update_worker(worker_id: str, worker: schemas.UpdateWorker, db: Session = Depends(get_db),
                        current_user: str = Depends(oauth2.get_current_user)):
    role = await utils.create_admin_access_id(current_user)
    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No read privilege for user type!")

    # user_type = await utils.create_admin_access_id(current_user)  # get the admin level and use to filter data

    user_query = db.query(models.Workers).filter(models.Workers.user_id == worker_id,
                                                 models.Workers.location_id.ilike(f'%{role}%'))

    user = user_query.first()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Worker with id: {worker_id} does not exist")

    user_query.update(worker.dict())
    db.commit()

    return user_query.first()


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workers(worker_id: str, db: Session = Depends(get_db),
                         current_user: str = Depends(oauth2.get_current_user)):
    role = await utils.create_admin_access_id(current_user)

    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    user = db.query(models.Workers).filter(models.Workers.user_id == worker_id,
                                           models.Workers.location_id.ilike(f'%{role}%'))

    if user.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"worker with id: {worker_id} is not found!")

    # if current_user.role != "State Usher":
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access!")

    user.delete(synchronize_session=False)
    db.commit()

    return {"status": "successful!",
            "message": f"Worker with ID: {worker_id} deleted successfully!"
            }


"""
{
  "location_id": "AF-234-KWR-ILR-ILE-0002",
  "location": "DLCF Living Spring",
  "church_type": "DLBC"
  "state_": "Kwara State",
  "region": "Ilorin Region",
  "group": "Ilorin East",
  "name": "Olorundare Micheal",
  "gender": "Male",
  "phone": "+2349029952120",
  "email": "meshelleva@gmail.com",
  "address": "Eleshin House, Lajolo, Ilorin, Kwara State",
  "occupation": "Programmer",
  "marital_status": "Single",
  "status": "active",
  "unit": "Infomation And Communication Unit",
  "created_at": "2024-03-20T11:09:54.556Z"
}
"""
