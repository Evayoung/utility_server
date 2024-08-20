from datetime import datetime, date
from typing import Optional, Union, List
from pydantic import BaseModel, EmailStr, RootModel


# ############################################# THE ROLE SCHEMAS ###############################################
class CreateRoles(BaseModel):
    """ *** these schemas is used to create new Roles *** """

    role_name: str
    score_id: int
    last_modify: Optional[datetime] = None
    operation: Optional[str] = "create"
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UpdateRoles(BaseModel):
    """ *** these schemas is used to update the roles *** """

    role_name: Optional[str] = None
    score_id: Optional[int] = None
    last_modify: Optional[datetime] = None
    operation: Optional[str] = "create"
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RolesResponse(BaseModel):
    """ *** these schemas is used to return roles *** """

    id: int
    role_name: str
    permissions: List[str]  # List of permission names
    score_id: int
    last_modify: datetime
    operation: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AssignPermissionsToRole(BaseModel):
    role_id: int
    permission_ids: List[int]


# ############################################# THE ROLE SCHEMAS ###############################################
class CreatePermission(BaseModel):
    """ *** these schemas is used to create new permission *** """

    permission: str
    name: str
    description: str
    last_modify: Optional[datetime] = None
    operation: Optional[str] = "create"
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UpdatePermission(BaseModel):
    """ *** these schemas is used to update permission *** """

    permission: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    last_modify: Optional[datetime] = None
    operation: Optional[str] = "create"
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PermissionResponse(BaseModel):
    """ *** these schemas is used to return permission *** """

    id: int
    permission: str
    name: str
    description: str
    last_modify: datetime
    operation: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ############################################# THE ROLE SCHEMAS ###############################################
class CreateRoleScore(BaseModel):
    """ *** these schemas is used to create new score count for levels *** """

    score: int
    score_name: str
    last_modify: Optional[datetime] = None
    operation: Optional[str] = "create"
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UpdateRoleScore(BaseModel):
    """ *** these schemas is used to update level score counts *** """

    score: Optional[int] = None
    score_name: Optional[str] = None
    last_modify: Optional[datetime] = None
    operation: Optional[str] = "create"
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RoleScoreResponse(BaseModel):
    """ *** these schemas is used to return score counts *** """

    id: int
    score: int
    score_name: str
    last_modify: datetime
    operation: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ############################################# THE STATE SCHEMAS #############################################
class CreateWorkers(BaseModel):
    """ *** these schemas is used to create new worker *** """

    location_id: str
    location: str
    church_type: str
    state_: str
    region: str
    group: str
    name: str
    gender: str
    phone: str
    email: EmailStr
    address: str
    occupation: str
    marital_status: str
    status: Optional[str] = "active"
    unit: str
    last_modify: Optional[datetime] = None
    operation: Optional[str] = "create"
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UpdateWorker(BaseModel):
    """ *** Schema that returns the workers data after registration *** """

    location_id: Optional[str] = None
    location: Optional[str] = None
    church_type: Optional[str] = None
    state_: Optional[str] = None
    region: Optional[str] = None
    group: Optional[str] = None
    name: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    occupation: Optional[str] = None
    marital_status: Optional[str] = None
    unit: Optional[str] = None
    last_modify: Optional[datetime] = datetime.now()
    operation: Optional[str] = "update"
    is_deleted: Optional[bool] = None

    class Config:
        from_attributes = True


class WorkerResponse(BaseModel):
    """ *** Schema that returns the workers data after registration *** """

    user_id: str
    location_id: str
    location: str
    church_type: str
    state_: str
    region: str
    group: str
    name: str
    gender: str
    phone: str
    email: EmailStr
    address: str
    occupation: str
    marital_status: str
    unit: str
    last_modify: datetime
    operation: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ############################################# THE USER SCHEMAS ######################################################
class RecoveryQuestionSetup(BaseModel):
    user_id: str
    question: str
    answer: str


class PasswordResetRequest(BaseModel):
    user_id: str
    answer: str


class PasswordResetResponse(BaseModel):
    token: str


class PasswordResetComplete(BaseModel):
    token: str
    new_password: str


class UserCreate(BaseModel):
    """ *** Schemas that validate the create user form *** """

    location_id: str
    user_id: str
    name: str
    phone: str
    email: EmailStr
    password: str
    is_active: Optional[bool] = False
    last_modify: Optional[datetime] = None
    operation: Optional[str] = "create"
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UpdateUser(BaseModel):
    """ *** Schema that validates the update user form (and these are the data that can be updated) *** """
    # Not also that this update schema only servers for the users

    location_id: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    last_modify: Optional[datetime] = datetime.now()
    operation: Optional[str] = "update"
    is_deleted: Optional[bool] = None

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """ *** This schema validates the data send back to user after the registration *** """

    id: int
    location_id: str
    user_id: str
    name: str
    phone: str
    email: EmailStr
    is_active: bool
    last_modify: datetime
    operation: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AssignRolesToUser(BaseModel):
    """ To assign role """
    user_id: int
    role_ids: List[int]


# ############################################## THE COUNT SCHEMAS ###################################################
# ####################################################################################################################
class CreateCount(BaseModel):
    """ *** Schemas to create new counts *** """

    program_domain: str
    program_type: str
    location_level: str
    location_id: str
    church_type: Optional[str] = "DLBC"
    date: date
    adult_male: int
    adult_female: int
    youth_male: int
    youth_female: int
    boys: int
    girls: int
    total: int
    author: str
    extra_note: Optional[str] = 'No note'
    last_modify: Optional[datetime] = None
    operation: Optional[str] = "create"
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CountResponse(BaseModel):
    """ *** Schemas that returns the count data *** """

    id: int
    program_domain: str
    program_type: str
    location_id: str
    location_level: str
    church_type: str
    date: date
    adult_male: int
    adult_female: int
    youth_male: int
    youth_female: int
    boys: int
    girls: int
    total: int
    author: str
    extra_note: str
    last_modify: datetime
    operation: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateCount(BaseModel):
    """ *** Schemas that is used to update the count data *** """

    program_domain: Optional[str] = None
    program_type: Optional[str] = None
    location_level: Optional[str] = None
    location_id: Optional[str] = None
    church_type: Optional[str] = None
    date: date
    adult_male: Optional[int] = None
    adult_female: Optional[int] = None
    youth_male: Optional[int] = None
    youth_female: Optional[int] = None
    boys: Optional[int] = None
    girls: Optional[int] = None
    total: Optional[int] = None
    extra_note: Optional[str] = 'No note'
    last_modify: Optional[datetime] = datetime.now()
    operation: Optional[str] = "update"
    is_deleted: Optional[bool] = None

    class Config:
        from_attributes = True


# ############################################## THE AUTH SCHEMAS ###################################################
class Token(BaseModel):
    """ *** Schemas to validate the user login credentials *** """

    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[str] = None
    role: Optional[str] = None


class LoginUser(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    location_id: str
    user_name: str
    user_email: str
    role_name: str

    class Config:
        from_attributes = True


class RoleScore(BaseModel):
    score: int
    score_name: str


class Role(BaseModel):
    role_name: str
    score: RoleScore


class UsersResponse(BaseModel):
    user_id: str
    location_id: str
    name: str
    email: str
    roles: List[Role]


# ############################################# CONVERT/INVITEE SCHEMAS #############################################
class CreateRecord(BaseModel):
    """ *** Schemas to process the convert and newcomer data *** """

    program_domain: str
    program_type: str
    location_level: str
    location_id: str
    church_type: Optional[str] = "DLBC"
    date: date
    reg_type: str
    name: str
    gender: str
    phone: str
    home_address: str
    marital_status: str
    social_group: str
    social_status: str
    status_address: str
    level: str
    salvation_type: str
    invited_by: str
    author: Optional[str] = None
    last_modify: Optional[datetime] = None
    operation: Optional[str] = "create"
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RecordResponse(BaseModel):
    """ *** Schemas used to return convert/newcomer record  *** """

    id: int
    program_domain: str
    program_type: str
    location_level: str
    location_id: str
    church_type: str
    date: date
    reg_type: str
    name: str
    gender: str
    phone: str
    home_address: str
    marital_status: str
    social_group: str
    social_status: str
    status_address: str
    level: str
    salvation_type: str
    invited_by: str
    last_modify: datetime
    operation: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateRecord(BaseModel):
    """ *** this model updates the record models *** """

    program_domain: Optional[str] = None
    program_type: Optional[str] = None
    location_level: Optional[str] = None
    location_id: Optional[str] = None
    church_type: Optional[str] = None
    date: date
    reg_type: Optional[str] = None
    name: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    home_address: Optional[str] = None
    marital_status: Optional[str] = None
    social_group: Optional[str] = None
    social_status: Optional[str] = None
    status_address: Optional[str] = None
    level: Optional[str] = None
    salvation_type: Optional[str] = None
    invited_by: Optional[str] = None
    last_modify: Optional[datetime] = datetime.now()
    operation: Optional[str] = "update"
    is_deleted: Optional[bool] = None

    class Config:
        from_attributes = True


# ############################################# THE GROUP SCHEMAS #############################################
class CreateGroups(BaseModel):
    """ *** Schemas to create new group *** """

    region_id: str
    group_name: str
    group_head: str
    group_pastor: str
    last_modify: Optional[datetime] = None
    operation: Optional[str] = "create"
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GroupsResponse(BaseModel):
    """ *** Schemas that used to return the group data *** """

    region_id: str
    group_id: str
    group_name: str
    group_head: str
    group_pastor: str
    last_modify: datetime
    operation: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateGroups(BaseModel):
    """ *** Schemas to update the group data *** """

    group_name: Optional[str] = None
    group_head: Optional[str] = None
    group_pastor: Optional[str] = None
    last_modify: Optional[datetime] = datetime.now()
    operation: Optional[str] = "update"
    is_deleted: Optional[bool] = None

    class Config:
        from_attributes = True


# ############################################# THE LOCATION SCHEMAS #############################################
class CreateLocations(BaseModel):
    """ *** Schemas to create new location *** """

    group_id: str
    location_name: str
    church_type: Optional[str] = "DLBC"
    address: str
    associate_cord: str
    last_modify: Optional[datetime] = None
    operation: Optional[str] = "create"
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LocationResponse(BaseModel):
    """ *** Schemas to return the location data *** """

    group_id: str
    location_id: str
    location_name: str
    church_type: str
    address: str
    associate_cord: str
    last_modify: datetime
    operation: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateLocations(BaseModel):
    """ *** Schemas to update the location data *** """

    location_name: Optional[str] = None
    church_type: Optional[str] = None
    address: Optional[str] = None
    associate_cord: Optional[str] = None
    last_modify: Optional[datetime] = datetime.now()
    operation: Optional[str] = "update"
    is_deleted: Optional[bool] = None

    class Config:
        from_attributes = True


# ############################################# THE Region SCHEMAS #############################################
class CreateRegions(BaseModel):
    """ *** Schemas to create new region *** """

    state_id: str
    region_name: str
    region_head: str
    regional_pastor: str
    last_modify: Optional[datetime] = None
    operation: Optional[str] = "create"
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RegionResponse(BaseModel):
    """ *** Schemas to return the region data *** """

    state_id: str
    region_id: str
    region_name: str
    region_head: str
    regional_pastor: str
    operation: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateRegions(BaseModel):
    """ *** Schemas to update the region data *** """

    region_name: Optional[str] = None
    region_head: Optional[str] = None
    regional_pastor: Optional[str] = None
    last_modify: Optional[datetime] = datetime.now()
    operation: Optional[str] = "update"
    is_deleted: Optional[bool] = None

    class Config:
        from_attributes = True


# ############################################# THE STATE SCHEMAS ####################################################
class CreateState(BaseModel):
    """ *** Schemas to create new state *** """

    state_id: str
    country: str
    state: str
    city: str
    address: str
    state_hq: str
    state_pastor: str
    last_modify: Optional[datetime] = None
    operation: Optional[str] = "create"
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StateResponse(BaseModel):
    """ *** Schemas used to return the state data *** """

    state_id: str
    country: str
    state: str
    city: str
    address: str
    state_hq: str
    state_pastor: str
    last_modify: datetime
    operation: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateState(BaseModel):
    """ *** Schemas to update the state data *** """

    city: Optional[str] = None
    address: Optional[str] = None
    state_hq: Optional[str] = None
    state_pastor: Optional[str] = None
    last_modify: Optional[datetime] = datetime.now()
    operation: Optional[str] = "update"
    is_deleted: Optional[bool] = None

    class Config:
        from_attributes = True


# ############################################# THE UNITS SCHEMAS #############################################
class CreateUnits(BaseModel):
    """ *** Schemas to create new church units *** """

    state_id: str
    state_name: str
    units: str
    units_head: str
    last_modify: Optional[datetime] = None
    operation: Optional[str] = "create"
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UnitResponse(BaseModel):
    """ *** Schemas that to return the units data *** """

    state_id: str
    state_name: str
    units: str
    units_head: str
    last_modify: datetime
    operation: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateUnits(BaseModel):
    """ *** Schemas to update the units data *** """

    state_id: str
    state_name: str
    units: str
    units_head: str
    last_modify: Optional[datetime] = datetime.now()
    operation: Optional[str] = 'update'
    is_deleted: Optional[bool] = None

    class Config:
        from_attributes = True


# ############################################# THE WORKER's ATTENDANCE SCHEMAS #######################################
class CreateAttendance(BaseModel):
    """ *** Schemas to create the attendance data *** """

    program_domain: str
    program_type: str
    location_level: str
    location_id: str
    church_type: Optional[str] = "DLBC"
    date: date
    worker_id: str
    name: str
    gender: str
    contact: str
    email: EmailStr
    unit: str
    church_id: str
    local_church: str
    status: str
    last_modify: Optional[datetime] = None
    operation: Optional[str] = "create"
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AttendanceResponse(BaseModel):
    """ *** Schemas to return the attendance data *** """

    program_domain: str
    program_type: str
    location_level: str
    location_id: str
    church_type: str
    date: date
    worker_id: str
    name: str
    gender: str
    contact: str
    email: EmailStr
    unit: str
    church_id: str
    local_church: str
    status: str
    last_modify: datetime
    operation: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateAttendance(BaseModel):
    """ *** Schemas to update the attendance data *** """

    status: Optional[str] = None
    last_modify: Optional[datetime] = datetime.now()
    operation: Optional[str] = "update"
    is_deleted: Optional[bool] = None

    class Config:
        from_attributes = True


class BatchCreateAttendance(RootModel[List[CreateAttendance]]):
    """ *** Schema to handle batch creation of attendance records *** """
    pass


# ############################################# THE TITHE AND OFFERING SCHEMAS #######################################
class CreateTithe(BaseModel):
    """ *** Schemas to create the tithe and offering data *** """

    location_id: str
    church_type: Optional[str] = "DLBC"
    date: date
    amount: float
    last_modify: Optional[datetime] = None
    operation: Optional[str] = 'create'
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TitheResponse(BaseModel):
    """ *** Schemas to return the tithe and offering data *** """

    location_id: str
    church_type: str
    date: date
    amount: float
    last_modify: datetime
    operation: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateTithe(BaseModel):
    """ *** Schemas to update the tithe and offering data *** """
    location_id: Optional[str] = None
    church_type: Optional[str] = None
    date: Optional[date] = None
    amount: Optional[float] = None
    last_modify: Optional[datetime] = datetime.now()
    operation: Optional[str] = "update"
    is_deleted: Optional[bool] = None

    class Config:
        from_attributes = True


# ###########################################   CHURCH FELLOWSHIP SCHEMAS  ##########################################
class CreateFellowship(BaseModel):
    """ *** Schemas to create new fellowship data *** """

    fellowship_id: str
    fellowship_name: str
    fellowship_address: str
    associate_church: str
    location_id: str
    church_type: Optional[str] = "DLBC"
    leader_in_charge: str
    leader_contact: str
    last_modify: Optional[datetime] = None
    operation: Optional[str] = 'create'
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FellowshipResponse(BaseModel):
    """ *** Schemas to return the fellowship data *** """

    fellowship_id: str
    fellowship_name: str
    fellowship_address: str
    associate_church: str
    location_id: str
    church_type: str
    leader_in_charge: str
    leader_contact: str
    last_modify: datetime
    operation: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateFellowship(BaseModel):
    """ *** Schemas to update the fellowship data *** """

    fellowship_name: Optional[str] = None
    fellowship_address: Optional[str] = None
    associate_church: Optional[str] = None
    location_id: Optional[str] = None
    church_type: Optional[str] = None
    leader_in_charge: Optional[str] = None
    leader_contact: Optional[str] = None
    last_modify: Optional[datetime] = datetime.now()
    operation: Optional[str] = "update"
    is_deleted: Optional[bool] = None

    class Config:
        from_attributes = True


# ###########################################   THE FELLOWSHIP ATTENDANCE SCHEMAS ####################################
class CreateFMembers(BaseModel):
    fellowship_name: str
    location_id: str
    associate_church: str
    name: str
    gender: str
    marital_status: str
    phone: str
    email: EmailStr
    address: str
    occupation: str
    local_church: str
    last_modify: Optional[datetime] = None
    operation: Optional[str] = "create"
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FMembersResponse(BaseModel):
    fellowship_id: str
    fellowship_name: str
    location_id: str
    associate_church: str
    name: str
    gender: str
    marital_status: str
    phone: str
    email: EmailStr
    address: str
    occupation: str
    local_church: str
    last_modify: datetime
    operation: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateFMembers(BaseModel):
    fellowship_name: Optional[str] = None
    location_id: Optional[str] = None
    associate_church: Optional[str] = None
    name: Optional[str] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    occupation: Optional[str] = None
    local_church: Optional[str] = None
    last_modify: Optional[datetime] = datetime.now()
    operation: Optional[str] = "update"
    is_deleted: Optional[bool] = None

    class Config:
        from_attributes = True


# ###########################################   THE FELLOWSHIP ATTENDANCE SCHEMAS ####################################
class CreateFAttendance(BaseModel):
    fellowship_id: str
    location_id: str
    date: date
    member_name: str
    gender: str
    phone: str
    address: str
    member_type: str
    last_modify: Optional[datetime] = None
    operation: Optional[str] = "create"
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FAttendanceResponse(BaseModel):
    id: int
    fellowship_id: str
    location_id: str
    date: date
    member_name: str
    gender: str
    phone: str
    address: str
    member_type: str
    last_modify: datetime
    operation: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateFAttendance(BaseModel):
    date: Optional[date] = None
    member_name: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    member_type: Optional[str] = None
    last_modify: Optional[datetime] = datetime.now()
    operation: Optional[str] = "update"
    is_deleted: Optional[bool] = None

    class Config:
        from_attributes = True


# #######################################   THE FELLOWSHIP ATTENDANCE SUMMARY SCHEMAS  ###############################
class CreateFAttendanceSum(BaseModel):
    location_id: str
    date: date
    male_count: int
    female_count: int
    total_count: int
    new_comers: int
    new_converts: int
    last_modify: Optional[datetime] = None
    operation: Optional[str] = "create"
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FAttendanceSumResponse(BaseModel):
    id: int
    location_id: str
    date: date
    male_count: int
    female_count: int
    total_count: int
    new_comers: int
    new_converts: int
    last_modify: datetime
    operation: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateFAttendanceSum(BaseModel):
    date: Optional[date] = None
    male_count: Optional[int] = None
    female_count: Optional[int] = None
    total_count: Optional[int] = None
    new_comers: Optional[int] = None
    new_converts: Optional[int] = None
    last_modify: Optional[datetime] = datetime.now()
    operation: Optional[str] = "update"
    is_deleted: Optional[bool] = None

    class Config:
        from_attributes = True


# ###########################################   THE FELLOWSHIP PLANS SCHEMAS  #######################################
class CreateFellowshipPlan(BaseModel):
    fellowship_id: str
    location_id: str
    fellowship_name: str
    date: date
    fellowship_plan: str
    plan_type: str
    expected_outcome: str
    last_modify: Optional[datetime] = None
    operation: Optional[str] = "create"
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FellowshipPlanResponse(BaseModel):
    id: int
    fellowship_id: str
    location_id: str
    fellowship_name: str
    date: date
    fellowship_plan: str
    plan_type: str
    expected_outcome: str
    last_modify: datetime
    operation: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateFellowshipPlan(BaseModel):
    fellowship_name: Optional[str] = None
    date: Optional[date] = None
    fellowship_plan: Optional[str] = None
    plan_type: Optional[str] = None
    expected_outcome: Optional[str] = None
    last_modify: Optional[datetime] = datetime.now()
    operation: Optional[str] = "update"
    is_deleted: Optional[bool] = None

    class Config:
        from_attributes = True


# ########################################   THE FELLOWSHIP TESTIMONIES SCHEMAS  #####################################
class CreateTestimonies(BaseModel):
    fellowship_id: str
    location_id: str
    fellowship_name: str
    date: date
    testimony_type: str
    testimony: str
    testifier: str
    last_modify: Optional[datetime] = None
    operation: Optional[str] = "create"
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TestimoniesResponse(BaseModel):
    id: int
    fellowship_id: str
    location_id: str
    fellowship_name: str
    date: date
    testimony_type: str
    testimony: str
    testifier: str
    last_modify: datetime
    operation: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateTestimonies(BaseModel):
    fellowship_name: Optional[str] = None
    date: Optional[date] = None
    testimony_type: Optional[str] = None
    testimony: Optional[str] = None
    testifier: Optional[str] = None
    last_modify: Optional[datetime] = datetime.now()
    operation: Optional[str] = "update"
    is_deleted: Optional[bool] = None

    class Config:
        from_attributes = True


# ######################################   THE FELLOWSHIP PRAYER REQUESTS SCHEMAS  ##################################
class CreatePrayerRequest(BaseModel):
    fellowship_id: str
    location_id: str
    fellowship_name: str
    date: date
    prayer_request: str
    requester: str
    last_modify: Optional[datetime] = None
    operation: Optional[str] = "create"
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PrayerRequestResponse(BaseModel):
    id: int
    fellowship_id: str
    location_id: str
    fellowship_name: str
    date: date
    prayer_request: str
    requester: str
    last_modify: datetime
    operation: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UpdatePrayerRequest(BaseModel):
    fellowship_name: Optional[str] = None
    date: Optional[date] = None
    prayer_request: Optional[str] = None
    requester: Optional[str] = None
    last_modify: Optional[datetime] = datetime.now()
    operation: Optional[str] = "update"
    is_deleted: Optional[bool] = None

    class Config:
        from_attributes = True


# #################################### THE CHURCH LOCAL AND STATEWIDE PROGRAM TABLE ################################
class CreatePrograms(BaseModel):
    location_id: str
    level: str
    church_type: str  # Campus, Adult, Youth (DLCF, DLBC, DLSO)
    program_picture: str
    program_type: str
    program_title: str
    start_date: date
    end_date: date
    last_modify: Optional[datetime] = None
    operation: Optional[str] = "create"
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProgramsResponse(BaseModel):
    id: int
    location_id: str
    level: str
    church_type: str  # Campus, Adult, Youth (DLCF, DLBC, DLSO)
    program_picture: str
    program_type: str
    program_title: str
    start_date: date
    end_date: date
    last_modify: datetime
    operation: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UpdatePrograms(BaseModel):
    level: Optional[str] = None
    church_type: Optional[str] = None  # Campus, Adult, Youth (DLCF, DLBC, DLSO)
    program_picture: Optional[str] = None
    program_type: Optional[str] = None
    program_title: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    last_modify: Optional[datetime] = datetime.now()
    operation: Optional[str] = "update"
    is_deleted: Optional[bool] = None

    class Config:
        from_attributes = True


# ####################################### THE CHURCH WEEKLY INFORMATION SYSTEM ###################################
class InformationItems(BaseModel):
    title: str
    text: str
    last_modify: Optional[datetime] = None
    operation: Optional[str] = "create"
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InformationItemsResponse(BaseModel):
    information_id: str
    title: str
    text: str
    last_modify: datetime
    operation: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateInformationItems(InformationItemsResponse):
    last_modify: Optional[datetime] = datetime.now()
    operation: Optional[str] = "update"
    is_deleted: Optional[bool] = None

    class Config:
        from_attributes = True


class CreateInformation(BaseModel):
    region_id: str
    region_name: str
    meeting: str
    date: date
    trets_topic: str
    trets_date: date
    sws_topic: str
    sts_study: str
    adult_hcf_lesson: str
    youth_hcf_lesson: str
    children_hcf_lesson: str
    adult_hcf_volume: str
    youth_hcf_volume: str
    children_hcf_volume: str
    sws_bible_reading: str
    mbs_bible_reading: str
    is_active: bool
    last_modify: Optional[datetime] = None
    operation: Optional[str] = "create"
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime] = None
    items: List[InformationItems]

    class Config:
        from_attributes = True


class InformationResponse(BaseModel):
    information_id: str
    region_id: str
    region_name: str
    meeting: str
    date: date
    trets_topic: str
    trets_date: date
    sws_topic: str
    sts_study: str
    adult_hcf_lesson: str
    youth_hcf_lesson: str
    children_hcf_lesson: str
    adult_hcf_volume: str
    youth_hcf_volume: str
    children_hcf_volume: str
    sws_bible_reading: str
    mbs_bible_reading: str
    is_active: bool
    last_modify: datetime
    operation: str
    is_deleted: bool
    created_at: datetime
    items: List[InformationItemsResponse]

    class Config:
        from_attributes = True


class UpdateInformation(BaseModel):
    region_id: Optional[str] = None
    region_name: Optional[str] = None
    meeting: Optional[str] = None
    date: Optional[date] = None
    trets_topic: Optional[str] = None
    trets_date: Optional[date] = None
    sws_topic: Optional[str] = None
    sts_study: Optional[str] = None
    adult_hcf_lesson: Optional[str] = None
    youth_hcf_lesson: Optional[str] = None
    children_hcf_lesson: Optional[str] = None
    adult_hcf_volume: Optional[str] = None
    youth_hcf_volume: Optional[str] = None
    children_hcf_volume: Optional[str] = None
    sws_bible_reading: Optional[str] = None
    mbs_bible_reading: Optional[str] = None
    is_active: Optional[bool] = None
    last_modify: Optional[datetime] = datetime.now()
    operation: Optional[str] = "update"
    is_deleted: Optional[bool] = None
    items: List[UpdateInformationItems]

    class Config:
        from_attributes = True
