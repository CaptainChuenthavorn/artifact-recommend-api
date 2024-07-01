from pydantic import BaseModel, EmailStr
from typing import List


class UserArtifact(BaseModel):
    set_name: str
    main_stat: str
    sub_stats: List[str]


class User(BaseModel):
    email: EmailStr
    password: str
    artifacts: List[UserArtifact] = []

