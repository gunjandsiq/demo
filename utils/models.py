from flask import Blueprint
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

models = Blueprint('models', __name__)

db = SQLAlchemy()

class TimeStamp(object):
    created_date = db.Column(db.Date, default=datetime.now)
    created_time = db.Column(db.TIME, default=datetime.now)
    updated_date = db.Column(db.Date, default=datetime.now, onupdate=datetime.now)
    updated_time = db.Column(db.TIME, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(db.String, default='app')
    updated_by = db.Column(db.String, default='app')

class DimDate(db.Model, TimeStamp):
    __tablename__ = 'dim_date'
    date_id = db.Column(db.BigInteger, primary_key=True)
    date_actual = db.Column(db.Date)
    epoch = db.Column(db.BigInteger)
    day_suffix = db.Column(db.String)
    day_name = db.Column(db.String)
    day_of_week = db.Column(db.BigInteger)
    day_of_month = db.Column(db.BigInteger)
    day_of_quarter = db.Column(db.BigInteger)
    day_of_year = db.Column(db.BigInteger)
    week_of_month = db.Column(db.BigInteger)
    week_of_year = db.Column(db.BigInteger)
    week_of_year_iso = db.Column(db.String)
    month_actual = db.Column(db.BigInteger)
    month_name = db.Column(db.String)
    month_name_abbreviated = db.Column(db.String)
    quarter_actual = db.Column(db.BigInteger)
    quarter_name = db.Column(db.String)
    year_actual = db.Column(db.BigInteger)
    first_day_of_week = db.Column(db.Date)
    last_day_of_week = db.Column(db.Date)
    first_day_of_month = db.Column(db.Date)
    last_day_of_month = db.Column(db.Date)
    first_day_of_quarter = db.Column(db.Date)
    last_day_of_quarter = db.Column(db.Date)
    first_day_of_year = db.Column(db.Date)
    last_day_of_year = db.Column(db.Date)
    mmyyyy = db.Column(db.Integer)
    mmddyyyy = db.Column(db.Integer)
    weekend_indr = db.Column(db.Boolean)

class Company(db.Model, TimeStamp):
    __tablename__ = 'company'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    users = db.relationship('User', backref='company', cascade="all, delete-orphan", passive_deletes=True)
    clients = db.relationship('Client', backref='company', cascade="all, delete-orphan", passive_deletes=True)

class User(db.Model, TimeStamp):
    __tablename__ = 'user'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String)
    company_id = db.Column(UUID(as_uuid=True), db.ForeignKey('company.id', ondelete="CASCADE"), nullable=False)
    metas = db.relationship('TaskHours', backref='user', cascade="all, delete-orphan", passive_deletes=True)

class Client(db.Model, TimeStamp):
    __tablename__ = 'client'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    company_id = db.Column(UUID(as_uuid=True), db.ForeignKey('company.id', ondelete="CASCADE"), nullable=False)
    projects = db.relationship('Project', backref='client', cascade="all, delete-orphan", passive_deletes=True)

class Project(db.Model, TimeStamp):            
    __tablename__ = 'project'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    client_id = db.Column(UUID(as_uuid=True), db.ForeignKey('client.id', ondelete="CASCADE"), nullable=False)
    tasks = db.relationship('Task', backref='project', cascade="all, delete-orphan", passive_deletes=True)

class Task(db.Model, TimeStamp):
    __tablename__ = 'task'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('project.id', ondelete="CASCADE"), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    metas = db.relationship('TaskHours', backref='task', cascade="all, delete-orphan", passive_deletes=True)

class TaskHours(db.Model, TimeStamp):
    __tablename__ = 'taskhours'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    values = db.Column(db.ARRAY(db.Integer), nullable=False, default=lambda: [0] * 7)
    start_date = db.Column(db.Date, nullable=False)
    task_id = db.Column(UUID(as_uuid=True), db.ForeignKey('task.id', ondelete="CASCADE"), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)