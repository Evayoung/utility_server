from datetime import datetime, date
from typing import Optional, Union, List
from pydantic import BaseModel, EmailStr


# ############################################# THE STATE SCHEMAS #############################################
class CreateWorkers(BaseModel):
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
    created_at: Optional[datetime] = None


class WorkerResponse(BaseModel):
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


class UpdateWorker(BaseModel):
    location_id: str
    location: str
    church_type: str
    state_: str
    region: str
    group: str
    name: str
    gender: str
    phone: str
    email: str
    address: str
    occupation: str
    marital_status: str
    unit: str


# ############################################# THE USER SCHEMAS ######################################################
class UserCreate(BaseModel):
    """ *** Schemas that validate the create user form *** """

    location_id: str
    user_id: str
    name: str
    phone: str
    email: EmailStr
    password: str
    is_active: Optional[bool] = False
    role: str
    created_at: Optional[datetime] = None


class UpdateUser(BaseModel):
    """ *** Schema that validates the update user form (and these are the data that can be updated) *** """
    # Not also that this update schema only servers for the users

    location_id: str
    user_id: str
    name: str
    phone: str
    email: EmailStr
    is_active: bool
    role: str


class UserResponse(BaseModel):
    """ *** This schema validates the data send back to user after the registration *** """

    location_id: str
    user_id: str
    name: str
    phone: str
    email: str
    role: str


# class UserSchema(BaseModel):
#     access_token: access_token,
#     token_type: "bearer",
#     user_id: user.user_id,
#     user_name: user.name,
#     user_email: user.email,
#     user_role: user.role


# ############################################## THE COUNT SCHEMAS ###################################################
# ####################################################################################################################
class CreateCount(BaseModel):
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
    created_at: Optional[datetime] = None


class CountResponse(BaseModel):
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


class UpdateCount(BaseModel):
    program_domain: str
    program_type: str
    location_level: str
    location_id: str
    church_type: str
    date: date
    adult_male: int
    adult_female: int
    youth_male: int
    youth_female: int
    boys: int
    girls: int
    total: int
    extra_note: Optional[str] = 'No note'


# ############################################## THE AUTH SCHEMAS ###################################################
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[str] = None
    role: Optional[str] = None


class LoginUser(BaseModel):
    email: EmailStr
    password: str


# ############################################# CONVERT/INVITEE SCHEMAS #############################################
class CreateRecord(BaseModel):
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
    created_at: Optional[datetime] = None


class RecordResponse(BaseModel):
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


class UpdateRecord(BaseModel):
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


# ############################################# THE GROUP SCHEMAS #############################################
class CreateGroups(BaseModel):
    group_id: str
    group_name: str
    group_head: str
    group_pastor: str
    created_at: Optional[datetime] = None


class GroupsResponse(BaseModel):
    group_id: str
    group_name: str
    group_head: str
    group_pastor: str


class UpdateGroups(BaseModel):
    group_name: str
    group_head: str
    group_pastor: str


# ############################################# THE LOCATION SCHEMAS #############################################
class CreateLocations(BaseModel):
    location_id: str
    location_name: str
    church_type: Optional[str] = "DLBC"
    address: str
    associate_cord: str
    created_at: Optional[datetime] = None


class LocationResponse(BaseModel):
    location_id: str
    location_name: str
    church_type: str
    address: str
    associate_cord: str


class UpdateLocations(BaseModel):
    location_name: str
    church_type: str
    address: str
    associate_cord: str


# ############################################# THE Region SCHEMAS #############################################
class CreateRegions(BaseModel):
    region_id: str
    region_name: str
    region_head: str
    regional_pastor: str
    created_at: Optional[datetime] = None


class RegionResponse(BaseModel):
    region_id: str
    region_name: str
    region_head: str
    regional_pastor: str


class UpdateRegions(BaseModel):
    region_name: str
    region_head: str
    regional_pastor: str


# ############################################# THE STATE SCHEMAS ####################################################
class CreateState(BaseModel):
    state_id: str
    country: str
    state: str
    city: str
    address: str
    state_hq: str
    state_pastor: str
    created_at: Optional[datetime] = None


class StateResponse(BaseModel):
    state_id: str
    country: str
    state: str
    city: str
    address: str
    state_hq: str
    state_pastor: str


class UpdateState(BaseModel):
    city: str
    address: str
    state_hq: str
    state_pastor: str


# ############################################# THE UNITS SCHEMAS #############################################
class CreateUnits(BaseModel):
    state_id: str
    state_name: str
    units: str
    units_head: str
    created_at: Optional[datetime] = None


class UnitResponse(BaseModel):
    state_id: str
    state_name: str
    units: str
    units_head: str


class UpdateUnits(BaseModel):
    state_id: str
    state_name: str
    units: str
    units_head: str


# ############################################# THE WORKER's ATTENDANCE SCHEMAS #######################################
class CreateAttendance(BaseModel):
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
    created_at: Optional[datetime] = None


class AttendanceResponse(BaseModel):
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


class UpdateAttendance(BaseModel):
    status: str


# ############################################# THE TITHE AND OFFERING SCHEMAS #######################################
class CreateTithe(BaseModel):
    location_id: str
    church_type: Optional[str] = "DLBC"
    date: date
    amount: float
    created_at: Optional[datetime] = None


class TitheResponse(BaseModel):
    location_id: str
    church_type: str
    date: date
    amount: float


class UpdateTithe(BaseModel):
    location_id: str
    church_type: str
    date: date
    amount: float


# ###########################################   CHURCH FELLOWSHIP SCHEMAS  ##########################################
class CreateFellowship(BaseModel):
    fellowship_id: str
    fellowship_name: str
    fellowship_address: str
    associate_church: str
    location_id: str
    church_type: Optional[str] = "DLBC"
    leader_in_charge: str
    leader_contact: str
    created_at: Optional[datetime] = None


class FellowshipResponse(BaseModel):
    fellowship_id: str
    fellowship_name: str
    fellowship_address: str
    associate_church: str
    location_id: str
    church_type: str
    leader_in_charge: str
    leader_contact: str


class UpdateFellowship(BaseModel):
    fellowship_name: str
    fellowship_address: str
    associate_church: str
    location_id: str
    church_type: str
    leader_in_charge: str
    leader_contact: str


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
    created_at: Optional[datetime] = None


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


class UpdateFMembers(BaseModel):
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
    created_at: Optional[datetime] = None


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


class UpdateFAttendance(BaseModel):
    date: date
    member_name: str
    gender: str
    phone: str
    address: str
    member_type: str


# #######################################   THE FELLOWSHIP ATTENDANCE SUMMARY SCHEMAS  ###############################
class CreateFAttendanceSum(BaseModel):
    location_id: str
    date: date
    male_count: int
    female_count: int
    total_count: int
    new_comers: int
    new_converts: int
    created_at: Optional[datetime] = None


class FAttendanceSumResponse(BaseModel):
    id: int
    location_id: str
    date: date
    male_count: int
    female_count: int
    total_count: int
    new_comers: int
    new_converts: int


class UpdateFAttendanceSum(BaseModel):
    date: date
    male_count: int
    female_count: int
    total_count: int
    new_comers: int
    new_converts: int


# ###########################################   THE FELLOWSHIP PLANS SCHEMAS  #######################################
class CreateFellowshipPlan(BaseModel):
    fellowship_id: str
    location_id: str
    fellowship_name: str
    date: date
    fellowship_plan: str
    plan_type: str
    expected_outcome: str
    created_at: Optional[datetime] = None


class FellowshipPlanResponse(BaseModel):
    id: int
    fellowship_id: str
    location_id: str
    fellowship_name: str
    date: date
    fellowship_plan: str
    plan_type: str
    expected_outcome: str


class UpdateFellowshipPlan(BaseModel):
    fellowship_name: str
    date: date
    fellowship_plan: str
    plan_type: str
    expected_outcome: str


# ########################################   THE FELLOWSHIP TESTIMONIES SCHEMAS  #####################################
class CreateTestimonies(BaseModel):
    fellowship_id: str
    location_id: str
    fellowship_name: str
    date: date
    testimony_type: str
    testimony: str
    testifier: str
    created_at: Optional[datetime] = None


class TestimoniesResponse(BaseModel):
    id: int
    fellowship_id: str
    location_id: str
    fellowship_name: str
    date: date
    testimony_type: str
    testimony: str
    testifier: str


class UpdateTestimonies(BaseModel):
    fellowship_name: str
    date: date
    testimony_type: str
    testimony: str
    testifier: str


# ######################################   THE FELLOWSHIP PRAYER REQUESTS SCHEMAS  ##################################
class CreatePrayerRequest(BaseModel):
    fellowship_id: str
    location_id: str
    fellowship_name: str
    date: date
    prayer_request: str
    requester: str
    created_at: Optional[datetime] = None


class PrayerRequestResponse(BaseModel):
    id: int
    fellowship_id: str
    location_id: str
    fellowship_name: str
    date: date
    prayer_request: str
    requester: str


class UpdatePrayerRequest(BaseModel):
    fellowship_name: str
    date: date
    prayer_request: str
    requester: str


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
    created_at: Optional[datetime] = None


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


class UpdatePrograms(BaseModel):
    level: str
    church_type: str  # Campus, Adult, Youth (DLCF, DLBC, DLSO)
    program_picture: str
    program_type: str
    program_title: str
    start_date: date
    end_date: date


# ####################################### THE CHURCH WEEKLY INFORMATION SYSTEM ###################################
class InformationItems(BaseModel):
    title: str
    text: str


class InformationItemsResponse(BaseModel):
    information_id: str
    title: str
    text: str


class UpdateInformationItems(InformationItemsResponse):
    pass


class CreateInformation(BaseModel):
    region_id: str
    region_name: str
    meeting: str
    date: date
    trets_topic: str
    trets_date: date
    sws_topic: str
    sts_study: str
    adult_hcf: str
    youth_hcf: str
    children_hcf: str
    sws_bible_reading: str
    mbs_bible_reading: str
    is_active: bool
    created_at: Optional[datetime] = None
    items: List[InformationItems]


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
    adult_hcf: str
    youth_hcf: str
    children_hcf: str
    sws_bible_reading: str
    mbs_bible_reading: str
    is_active: bool
    created_at: datetime
    items: List[InformationItemsResponse]


class UpdateInformation(BaseModel):
    region_id: str
    region_name: str
    meeting: str
    date: date
    trets_topic: str
    trets_date: date
    sws_topic: str
    sts_study: str
    adult_hcf: str
    youth_hcf: str
    children_hcf: str
    sws_bible_reading: str
    mbs_bible_reading: str
    is_active: bool
    items: List[UpdateInformationItems]
