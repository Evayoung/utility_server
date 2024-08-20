from sqlalchemy import Column, Integer, String, TIMESTAMP, Date, func, ForeignKey, LargeBinary, Boolean, Float, Table
from sqlalchemy.orm import relationship

from .database import Base

# Association tables for many-to-many relationships
role_permissions = Table(
    'role_permissions', Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)

# this defines the user to role relationships
user_roles = Table(
    'user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)


class Permission(Base):
    """ *** THE PERMISSION DATABASE SCHEMAS *** """
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    permission = Column(String, nullable=False, index=True, unique=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    last_modify = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    operation = Column(String, nullable=False, index=True)
    is_deleted = Column(Boolean, nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


class Role(Base):
    """ *** THE ROLES DATABASE SCHEMAS *** """
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    role_name = Column(String, nullable=False, unique=True, index=True)
    last_modify = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    operation = Column(String, nullable=False, index=True)
    is_deleted = Column(Boolean, nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    score_id = Column(Integer, ForeignKey("role_scores.id"), nullable=False, index=True)

    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    users = relationship("User", secondary=user_roles, back_populates="roles")
    score = relationship("RoleScore", back_populates="roles")


class RoleScore(Base):
    """ *** THE ROLE SCORE DATABASE SCHEMAS *** """
    __tablename__ = "role_scores"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    score = Column(Integer, nullable=False, index=True, unique=True)
    score_name = Column(String, nullable=False, index=True, unique=True)
    last_modify = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    operation = Column(String, nullable=False, index=True)
    is_deleted = Column(Boolean, nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    roles = relationship("Role", back_populates="score")


class Workers(Base):
    """ *** THE WORKERS DATABASE SCHEMAS *** """
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    user_id = Column(String, nullable=False, unique=True, index=True)
    location_id = Column(String, nullable=False, index=True)
    location = Column(String, nullable=False, index=True)
    church_type = Column(String, nullable=False, index=True)
    state_ = Column(String, nullable=False)
    region = Column(String, nullable=False, index=True)
    group = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    phone = Column(String, nullable=False, unique=True, index=True)
    email = Column(String, nullable=False, unique=True)
    address = Column(String, nullable=True)
    occupation = Column(String, nullable=True)
    marital_status = Column(String, nullable=True)
    status = Column(String, nullable=True, index=True)
    unit = Column(String, nullable=False)
    last_modify = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    operation = Column(String, nullable=False, index=True)
    is_deleted = Column(Boolean, nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    users = relationship('User', back_populates='workers')


class User(Base):
    """ *** THE USER DATABASE SCHEMAS *** """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    location_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, ForeignKey("workers.phone"), nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=True, index=True)
    last_modify = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    operation = Column(String, nullable=False, index=True)
    is_deleted = Column(Boolean, nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    workers = relationship('Workers', back_populates='users')
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="users")


class PasswordResetToken(Base):
    """ *** THE PASSWORD RESET & TOKEN DATABASE SCHEMAS *** """
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, unique=True)
    token = Column(String, nullable=False, unique=True)
    expiration = Column(TIMESTAMP(timezone=True), nullable=False)
    recovery_question = Column(String, nullable=True)
    recovery_answer = Column(String, nullable=True)  # Store hashed answer
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    users = relationship("User", back_populates="password_reset_tokens")


class Counter(Base):
    """ *** THE COUNTER DATABASE SCHEMAS *** """

    __tablename__: str = "counts"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    program_domain = Column(String, nullable=False, index=True)
    program_type = Column(String, nullable=False, index=True)
    location_level = Column(String, nullable=False, index=True)
    location_id = Column(String, nullable=False, index=True)
    church_type = Column(String, nullable=False, index=True)  # Campus, Adult, Youth (DLCF, DLBC, DLSO)
    date = Column(Date, nullable=False, index=True)
    adult_male = Column(Integer, nullable=False)
    adult_female = Column(Integer, nullable=False)
    youth_male = Column(Integer, nullable=False)
    youth_female = Column(Integer, nullable=False)
    boys = Column(Integer, nullable=False)
    girls = Column(Integer, nullable=False)
    total = Column(Integer, nullable=False)
    author = Column(String, nullable=True)
    extra_note = Column(String, nullable=True, server_default="Default")
    last_modify = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    operation = Column(String, nullable=False, index=True)  # Delete, Update and create
    is_deleted = Column(Boolean, nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())


class Record(Base):
    """ *** THIS CLASS MODEL CREATE THE INVITEE / CONVERT DATABASE *** """

    __tablename__: str = "record"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    program_domain = Column(String, nullable=False, index=True)
    program_type = Column(String, nullable=False, index=True)
    location_level = Column(String, nullable=False, index=True)
    location_id = Column(String, nullable=False, index=True)
    church_type = Column(String, nullable=False, index=True)  # Campus, Adult, Youth (DLCF, DLBC, DLSO)
    date = Column(Date, nullable=False, index=True)
    reg_type = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    home_address = Column(String, nullable=False)
    marital_status = Column(String, nullable=True)
    social_group = Column(String, nullable=True)
    social_status = Column(String, nullable=True)
    status_address = Column(String, nullable=True)
    level = Column(String, nullable=True)
    salvation_type = Column(String, nullable=True)
    invited_by = Column(String, nullable=True)
    author = Column(String, nullable=False)
    last_modify = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    operation = Column(String, nullable=False, index=True)  # Delete, Update and create
    is_deleted = Column(Boolean, nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())


class Attendance(Base):
    """ *** THIS MODEL CREATE THE WORKER's AND LEADER's ATTENDANCE DATABASE *** """

    __tablename__: str = "attendance"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    program_domain = Column(String, nullable=False, index=True)
    program_type = Column(String, nullable=False, index=True)
    location_level = Column(String, nullable=False, index=True)
    location_id = Column(String, nullable=False, index=True)
    church_type = Column(String, nullable=False, index=True)  # Campus, Adult, Youth (DLCF, DLBC, DLSO)
    date = Column(Date, nullable=False, index=True)
    worker_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    contact = Column(String, nullable=False)
    email = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    church_id = Column(String, nullable=False, index=True)
    local_church = Column(String, nullable=False)
    status = Column(String, nullable=False)
    last_modify = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    operation = Column(String, nullable=False, index=True)  # Delete, Update and create
    is_deleted = Column(Boolean, nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())


class States(Base):
    """ *** THIS MODEL CREATE THE INDIVIDUAL STATES IN EACH COUNTRY DATABASE *** """

    __tablename__: str = "states"

    state_id = Column(String, primary_key=True, nullable=False, unique=True)
    country = Column(String, nullable=False, index=True)
    state = Column(String, nullable=False, index=True)
    city = Column(String, nullable=False)
    address = Column(String, nullable=False)
    state_hq = Column(String, nullable=False)
    state_pastor = Column(String, nullable=False)
    last_modify = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    operation = Column(String, nullable=False, index=True)  # Delete, Update and create
    is_deleted = Column(Boolean, nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    region = relationship("Region", back_populates="states")


class Region(Base):
    """ *** THIS MODEL CREATE THE VARIOUS REGIONS IN THE STATE DATABASE *** """

    __tablename__: str = "region"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    state_id = Column(String, ForeignKey("states.state_id"), nullable=False, index=True)
    region_id = Column(String, nullable=False, unique=True, index=True)
    region_name = Column(String, nullable=False, index=True)
    region_head = Column(String, nullable=False)
    regional_pastor = Column(String, nullable=False)
    last_modify = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    operation = Column(String, nullable=False, index=True)  # Delete, Update and create
    is_deleted = Column(Boolean, nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    information = relationship("Information", back_populates="region")
    states = relationship("States", back_populates="region")
    groups = relationship("Group", back_populates="region")


class Group(Base):
    """ *** THIS MODEL CREATE THE CHURCH GROUP DATABASE *** """

    __tablename__: str = "group"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    region_id = Column(String, ForeignKey("region.region_id"), nullable=False, index=True)
    group_id = Column(String, nullable=False, unique=True)  # Custom string primary key
    group_name = Column(String, nullable=False, index=True)
    group_head = Column(String, nullable=False)
    group_pastor = Column(String, nullable=False)
    last_modify = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    operation = Column(String, nullable=False, index=True)  # Delete, Update and create
    is_deleted = Column(Boolean, nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    region = relationship("Region", back_populates="groups")
    location = relationship("Location", back_populates="groups")


class Location(Base):
    """ *** THIS MODEL CREATE THE INDIVIDUAL CHURCH LOCATION DATABASE *** """

    __tablename__: str = "location"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    group_id = Column(String, ForeignKey("group.group_id"), nullable=False, index=True)
    location_id = Column(String, nullable=False, unique=True)  # Custom string primary key system
    location_name = Column(String, nullable=False, index=True)
    church_type = Column(String, nullable=False, index=True)  # Campus, Adult, Youth (DLCF, DLBC, DLSO)
    address = Column(String, nullable=False)
    associate_cord = Column(String, nullable=False)
    last_modify = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    operation = Column(String, nullable=False, index=True)  # Delete, Update and create
    is_deleted = Column(Boolean, nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    groups = relationship("Group", back_populates="location")
    fellowships = relationship("Fellowship", back_populates="location")
    fellowship_members = relationship("FellowshipMembers", back_populates="location")
    fellowship_attendance = relationship("FellowshipAttendance", back_populates="location")
    attendance_summaries = relationship("AttendanceSum", back_populates="location")
    testimonies = relationship("Testimony", back_populates="location")
    prayer_requests = relationship("PrayerRequest", back_populates="location")


class Fellowship(Base):
    """ ** THIS MODEL CREATES THE FELLOWSHIP TABLE THAT SAVES THE FELLOWSHIP DATA ** """
    __tablename__ = 'fellowships'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    fellowship_id = Column(String, nullable=False, unique=True, index=True)
    fellowship_name = Column(String, nullable=False, index=True)
    fellowship_address = Column(String, nullable=False)
    associate_church = Column(String, nullable=False)
    location_id = Column(String, ForeignKey('location.location_id'), nullable=False)
    church_type = Column(String, nullable=False, index=True)  # Campus, Adult, Youth (DLCF, DLBC, DLSO)
    leader_in_charge = Column(String, nullable=False)
    leader_contact = Column(String, nullable=False)
    last_modify = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    operation = Column(String, nullable=False, index=True)  # Delete, Update and create
    is_deleted = Column(Boolean, nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    location = relationship("Location", back_populates="fellowships")
    fellowship_members = relationship("FellowshipMembers", back_populates="fellowships")
    fellowship_attendance = relationship("FellowshipAttendance", back_populates="fellowships")
    attendance_summaries = relationship("AttendanceSum", back_populates="fellowships")
    testimonies = relationship("Testimony", back_populates="fellowships")
    prayer_requests = relationship("PrayerRequest", back_populates="fellowships")


class FellowshipMembers(Base):
    __tablename__ = 'fellowship_member'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    fellowship_id = Column(String, ForeignKey('fellowships.fellowship_id'), nullable=False)
    fellowship_name = Column(String, nullable=False, index=True)
    location_id = Column(String, ForeignKey('location.location_id'), nullable=False, index=True)
    associate_church = Column(String, nullable=False)
    name = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    marital_status = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=False)
    address = Column(String, nullable=False)
    occupation = Column(String, nullable=False)
    local_church = Column(String, nullable=False)
    last_modify = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    operation = Column(String, nullable=False, index=True)  # Delete, Update and create
    is_deleted = Column(Boolean, nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    fellowships = relationship("Fellowship", back_populates="fellowship_members")
    location = relationship("Location", back_populates="fellowship_members")


class FellowshipAttendance(Base):
    __tablename__ = 'fellowship_attendance'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    fellowship_id = Column(String, ForeignKey('fellowships.fellowship_id'), nullable=False)
    location_id = Column(String, ForeignKey('location.location_id'), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    member_name = Column(String, nullable=False, index=True)
    gender = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    address = Column(String, nullable=False)
    member_type = Column(String, nullable=False, index=True)  # first timer, new convert
    last_modify = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    operation = Column(String, nullable=False, index=True)  # Delete, Update and create
    is_deleted = Column(Boolean, nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    fellowships = relationship("Fellowship", back_populates="fellowship_attendance")
    location = relationship("Location", back_populates="fellowship_attendance")


class AttendanceSum(Base):
    __tablename__ = 'attendance_summaries'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    fellowship_id = Column(String, ForeignKey('fellowships.fellowship_id'), nullable=False)
    location_id = Column(String, ForeignKey('location.location_id'), nullable=False)
    date = Column(Date, nullable=False, index=True)
    male_count = Column(Integer, nullable=False)
    female_count = Column(Integer, nullable=False)
    total_count = Column(Integer, nullable=False)
    new_comers = Column(Integer, nullable=False)
    new_converts = Column(Integer, nullable=False)
    last_modify = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    operation = Column(String, nullable=False, index=True)  # Delete, Update and create
    is_deleted = Column(Boolean, nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    location = relationship("Location", back_populates="attendance_summaries")
    fellowships = relationship("Fellowship", back_populates="attendance_summaries")


class Testimony(Base):
    __tablename__ = 'testimonies'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    fellowship_id = Column(String, ForeignKey('fellowships.fellowship_id'), nullable=False)
    location_id = Column(String, ForeignKey('location.location_id'), nullable=False)
    fellowship_name = Column(String, nullable=False)
    date = Column(Date, nullable=False, index=True)
    testimony_type = Column(String, nullable=False)
    testimony = Column(String, nullable=False)
    testifier = Column(String, nullable=False)
    last_modify = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    operation = Column(String, nullable=False, index=True)  # Delete, Update and create
    is_deleted = Column(Boolean, nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    fellowships = relationship("Fellowship", back_populates="testimonies")
    location = relationship("Location", back_populates="testimonies")


class PrayerRequest(Base):
    __tablename__ = 'prayer_requests'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    fellowship_id = Column(String, ForeignKey('fellowships.fellowship_id'), nullable=False)
    location_id = Column(String, ForeignKey('location.location_id'), nullable=False)
    fellowship_name = Column(String, nullable=False)
    date = Column(Date, nullable=False, index=True)
    prayer_request = Column(String, nullable=False)
    requester = Column(String, nullable=False)
    last_modify = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    operation = Column(String, nullable=False, index=True)  # Delete, Update and create
    is_deleted = Column(Boolean, nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    fellowships = relationship("Fellowship", back_populates="prayer_requests")
    location = relationship("Location", back_populates="prayer_requests")


class ChurchPrograms(Base):
    """ *** THIS MODEL CREATE THE CHURCH PROGRAMS SETUP DATABASE *** """

    __tablename__: str = "programs_setup"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    location_id = Column(String, nullable=False, index=True)
    level = Column(String, nullable=False, index=True)
    church_type = Column(String, nullable=False, index=True)  # Campus, Adult, Youth (DLCF, DLBC, DLSO)
    program_picture = Column(String, nullable=True)
    program_type = Column(String, nullable=False)
    program_title = Column(String, nullable=False)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False)
    last_modify = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    operation = Column(String, nullable=False, index=True)  # Delete, Update and create
    is_deleted = Column(Boolean, nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())


class TitheAndOffering(Base):
    __tablename__: str = "tithe_offering"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    location_id = Column(String, nullable=False, index=True)
    church_type = Column(String, nullable=False, index=True)  # Campus, Adult, Youth (DLCF, DLBC, DLSO)
    date = Column(Date, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    last_modify = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    operation = Column(String, nullable=False, index=True)  # Delete, Update and create
    is_deleted = Column(Boolean, nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())


class Information(Base):
    """ ** This model creates the table where the weekly information for each region will be saved ** """
    __tablename__ = "information"

    information_id = Column(String, primary_key=True, nullable=False)
    region_id = Column(String, ForeignKey("region.region_id"), nullable=False)
    region_name = Column(String, nullable=False)
    meeting = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    trets_topic = Column(String, nullable=True)
    trets_date = Column(Date, nullable=True)
    sws_topic = Column(String, nullable=True)
    sts_study = Column(String, nullable=True)
    adult_hcf_lesson = Column(String, nullable=True)
    youth_hcf_lesson = Column(String, nullable=True)
    children_hcf_lesson = Column(String, nullable=True)
    adult_hcf_volume = Column(String, nullable=True)
    youth_hcf_volume = Column(String, nullable=True)
    children_hcf_volume = Column(String, nullable=True)
    sws_bible_reading = Column(String, nullable=True)
    mbs_bible_reading = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False)
    last_modify = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    operation = Column(String, nullable=False, index=True)  # Delete, Update and create
    is_deleted = Column(Boolean, nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    region = relationship("Region", back_populates="information")
    items = relationship("InformationItems", backref="information")


class InformationItems(Base):
    __tablename__ = "information_items"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    information_id = Column(String, ForeignKey('information.information_id'), nullable=False)
    title = Column(String, nullable=False)
    text = Column(String, nullable=False)
    last_modify = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    operation = Column(String, nullable=False, index=True)  # Delete, Update and create
    is_deleted = Column(Boolean, nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
