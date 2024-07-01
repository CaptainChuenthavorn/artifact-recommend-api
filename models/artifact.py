from pydantic import BaseModel
from typing import List

class SubStat(BaseModel):
    name: str
    value: float

class Artifact(BaseModel):
    set_name: str
    main_stat:str
    sub_stats: List[SubStat]