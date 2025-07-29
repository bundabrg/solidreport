import datetime
from typing import List, Dict
from uuid import UUID

from pydantic import BaseModel


class TimeEntryDataModel(BaseModel):
    start_time: datetime.datetime
    end_time: datetime.datetime
    duration: int = 0
    description: str


class ProjectDataModel(BaseModel):
    name: str
    duration: int = 0
    time_entries: List[TimeEntryDataModel] = []


class ClientDataModel(BaseModel):
    name: str
    duration: int = 0
    projects: Dict[UUID, ProjectDataModel] = {}


class DateDataModel(BaseModel):
    date: datetime.date
    duration: int = 0
    clients: Dict[UUID, ClientDataModel] = {}


class MemberDataModel(BaseModel):
    name: str = "None"
    duration: int = 0
    dates: Dict[datetime.date, DateDataModel] = {}


class DateSummaryModel(BaseModel):
    date: datetime.date
    duration: int = 0


class ProjectSummaryModel(BaseModel):
    name: str
    client_name: str
    duration: int = 0


class SummaryModel(BaseModel):
    dates: Dict[datetime.date, DateSummaryModel] = {}
    projects: Dict[UUID, ProjectSummaryModel] = {}


class DataModel(BaseModel):
    members: Dict[UUID, MemberDataModel] = {}
    summary: SummaryModel = SummaryModel()
    duration: int = 0
    start: datetime.date
    end: datetime.date
