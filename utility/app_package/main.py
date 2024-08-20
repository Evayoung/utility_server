import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .database import engine
from . import models
from .routers import (counter, auth, region, user, state, group, location, workers, register, programs, attendance,
                      tithes, fellowship, information, websocket, permissions, roles, rolescore, recovery)

description = """
This DCLM Utility server manages all the utility mobile and desktop application relating to the data management in the church

The app consists of seven(7) levels of admin privileges with a total of 11 admin types ( as of the moment of documenting).

## Admin types and privilege

**The list goes from the highest to the least**
* **General Superintendent and Super Admin** (_Top Admin_).
* **National Overseer and National Admin** (_National Admin_).
* **State Overseer and State Usher** (_State Admin_).
* **Regional Coordinator and Regional Admin** (_Region Admin_).
* **Group Coordinator and Group Admin** (_Group Admin_).
* **Associate Coordinator and General Coordinator** (_Location Admin_).
* **User and Usher** (_Users_).



"""

models.Base.metadata.create_all(bind=engine)  # create all the database tables

# app instance initialization


app = FastAPI(
    title="DCLM UTILITY APP",
    description=description,
    summary="This server is still in development stage therefore, full description not available",
    version="0.0.4",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Impath-lab Technology",
        "email": "meshelleva@gmail.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)

# Setup logging
logging.basicConfig(level=logging.INFO)

app.include_router(auth.router)  # this route controls the user authentication of the application
app.include_router(permissions.router)  # this route handles the CRUD operations for creating the permissions
app.include_router(roles.router)  # this route handles the CRUD operations for creating the permissions
app.include_router(rolescore.router)  # this route handles the CRUD operations for creating the role score or levels
app.include_router(user.router)  # this route handles the CRUD operations of the users, this includes the Ushers
app.include_router(workers.router)  # this route controls all the CRUD operations of the workers
app.include_router(attendance.router)  # this is the route that handles the CRUD operations on the workers attendance
app.include_router(recovery.router)  # this router handles reset and recovery of password
app.include_router(counter.router)  # this route handles the CRUD operations on the count data of all the applications
app.include_router(tithes.router)  # this route saves as a support route to the count to manage the tithe and offerings
app.include_router(register.router)  # this route manages the newcomer and convert CRUD operations across the app
app.include_router(state.router)  # route for the state CRUD operations
app.include_router(region.router)  # route for the region CRUD operations
app.include_router(group.router)  # route for the group CRUD operations
app.include_router(location.router)  # this route is for the CRUD operations of the locations
app.include_router(programs.router)  # this route controls the CRUD operations for the program setup, local or statewide
app.include_router(fellowship.router)  # the route that manage the fellowship CRUD operations
app.include_router(information.router)

app.include_router(websocket.router)  # this route is for the websocket to manage realtime operations like notifications


# Exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logging.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )


@app.get("/")
def root():
    return {"message": "Deeper Christian Life Ministry"}


""" Add include_in_schema=False to the route to disable it from showing in the docs """
