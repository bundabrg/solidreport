import datetime
from typing import List, Dict
from uuid import UUID

from pydantic import BaseModel


class TimeEntryDataModel(BaseModel):
    start_time: datetime.datetime
    end_time: datetime.datetime
    duration: int = 0
    description: str


class MemberDataModel(BaseModel):
    name: str
    duration: int = 0
    time_entries: List[TimeEntryDataModel] = []


class DateDataModel(BaseModel):
    date: datetime.date
    duration: int = 0
    cost: int = 0
    members: Dict[UUID, MemberDataModel] = {}


class ProjectDataModel(BaseModel):
    name: str = "None"
    duration: int = 0
    cost: int = 0
    billable_rate: int = 0
    dates: Dict[datetime.date, DateDataModel] = {}


class ClientDataModel(BaseModel):
    id: UUID | None = None
    name: str = "None"


class DateSummaryModel(BaseModel):
    date: datetime.date
    duration: int = 0
    cost: int = 0


class SummaryModel(BaseModel):
    dates: Dict[datetime.date, DateSummaryModel] = {}


class DataModel(BaseModel):
    client: ClientDataModel
    projects: Dict[UUID, ProjectDataModel] = {}
    summary: SummaryModel = SummaryModel()
    duration: int = 0
    cost: int = 0
    start: datetime.date
    end: datetime.date
