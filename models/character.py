from pydantic import BaseModel
from typing import List,Dict

class RecommendedArtifact(BaseModel):
    set_name: List[str]
    main_stat: Dict[List[str]]
    sub_stats: List[str]

class Build(BaseModel):
    build_type: str
    recommend_artifact: List[RecommendedArtifact]

class Character(BaseModel):
    name:str
    element:str
    weapon_type:str
    builds:List[Build]

    