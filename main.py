from fastapi import FastAPI, HTTPException, Body, Query
from pydantic import BaseModel
from bson import ObjectId
from bson.errors import InvalidId
from pymongo import MongoClient
from typing import List, Optional

app = FastAPI()

# MongoDB connection settings
MONGO_DETAILS = "mongodb+srv://admin:admin@cluster0.e1hu4of.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_DETAILS)
database = client["GenshinArtifactDB"]
user_artifacts_collection = database["userArtifacts"]
artifacts_collection = database["artifacts"]
recommended_artifacts_collection = database["recommendedArtifacts"]


# Pydantic models
class Artifact(BaseModel):
    name: str
    type: str
    main_stat: str
    sub_stats: List[str]


class UserArtifact(BaseModel):
    user_id: str
    artifact_id: str
    main_stat: str
    sub_stats: List[str]


# Utility function to convert ObjectId to str
def artifact_helper(artifact) -> dict:
    return {
        "id": str(artifact["_id"]),
        "user_id": artifact["user_id"],
        "artifact_id": str(artifact["artifact_id"]),
        "main_stat": artifact["main_stat"],
        "sub_stats": artifact["sub_stats"],
    }


# Create
@app.post(
    "/artifacts/", response_description="Add new artifact", response_model=UserArtifact
)
async def add_user_artifact(user_artifact: UserArtifact = Body(...)):
    user_artifact = user_artifact.dict()
    new_artifact = user_artifacts_collection.insert_one(user_artifact)
    created_artifact = user_artifacts_collection.find_one(
        {"_id": new_artifact.inserted_id}
    )
    return artifact_helper(created_artifact)


# Read
@app.get(
    "/artifacts/{user_id}",
    response_description="List user's artifacts",
    response_model=List[UserArtifact],
)
async def get_user_artifacts(user_id: str):
    artifacts = list(user_artifacts_collection.find({"user_id": user_id}))
    return [artifact_helper(artifact) for artifact in artifacts]


# Update
@app.put(
    "/artifacts/{user_id}/{artifact_id}",
    response_description="Update an artifact",
    response_model=UserArtifact,
)
async def update_user_artifact_route(
    user_id: str, artifact_id: str, artifact: UserArtifact = Body(...)
):
    try:
        artifact_id_obj = ObjectId(artifact_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid artifact ID")

    artifact = {k: v for k, v in artifact.dict().items() if v is not None}
    update_result = user_artifacts_collection.update_one(
        {"user_id": user_id, "_id": artifact_id_obj}, {"$set": artifact}
    )
    if update_result.modified_count == 1:
        updated_artifact = user_artifacts_collection.find_one({"_id": artifact_id_obj})
        if updated_artifact:
            return artifact_helper(updated_artifact)
    raise HTTPException(status_code=404, detail="Artifact not found")


# Delete
@app.delete(
    "/artifacts/{user_id}/{artifact_id}", response_description="Delete an artifact"
)
async def delete_user_artifact_route(user_id: str, artifact_id: str):
    try:
        artifact_id_obj = ObjectId(artifact_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid artifact ID")

    delete_result = user_artifacts_collection.delete_one(
        {"user_id": user_id, "_id": artifact_id_obj}
    )
    if delete_result.deleted_count == 1:
        return {"message": "Artifact deleted successfully"}
    raise HTTPException(status_code=404, detail="Artifact not found")


# Find suitable characters
@app.get("/artifact/{artifact_id}/suitable_characters")
async def get_suitable_characters(artifact_id: str):
    try:
        artifact_id_obj = ObjectId(artifact_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid artifact ID")

    artifact = user_artifacts_collection.find_one({"_id": artifact_id_obj})
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    artifact_details = artifacts_collection.find_one(
        {"_id": ObjectId(artifact["artifact_id"])}
    )
    if not artifact_details:
        raise HTTPException(status_code=404, detail="Artifact details not found")

    suitable_characters = recommended_artifacts_collection.aggregate(
        [
            {"$unwind": "$artifact_sets"},
            {
                "$match": {
                    "$or": [
                        {"artifact_sets.set_name": artifact_details["name"]},
                        {"artifact_sets.order": {"$lte": 3}},
                    ],
                    "main_stats": artifact["main_stat"],
                    "sub_stats": {"$in": artifact["sub_stats"]},
                }
            },
            {
                "$addFields": {
                    "sub_stat_matches": {
                        "$size": {
                            "$filter": {
                                "input": artifact["sub_stats"],
                                "as": "sub_stat",
                                "cond": {"$in": ["$$sub_stat", "$sub_stats"]},
                            }
                        }
                    }
                }
            },
            {"$match": {"sub_stat_matches": {"$gte": 2}}},
            {"$sort": {"artifact_sets.order": 1, "sub_stat_matches": -1}},
        ]
    )

    result = []
    async for character in suitable_characters:
        result.append(character)
    return result


@app.get("/artifact/suitable_characters")
async def get_suitable_characters(
    artifact_set: Optional[str] = Query(None, description="Artifact set name"),
    main_stat_type: Optional[str] = Query(
        None, description="Main stat type, e.g., Sands, Goblet, Circlet"
    ),
    main_stat: Optional[str] = Query(None, description="Main stat value"),
    sub_stats: Optional[List[str]] = Query(None, description="List of sub stats"),
):
    query = {}

    if artifact_set:
        query["artifact_sets.set_name"] = artifact_set
    if main_stat:
        query["main_stats"] = main_stat
    if sub_stats:
        query["sub_stats"] = {"$in": sub_stats}

    if not query:
        raise HTTPException(
            status_code=400, detail="At least one query parameter must be provided"
        )

    suitable_characters = recommended_artifacts_collection.aggregate(
        [
            {"$unwind": "$artifact_sets"},
            {"$match": query},
            {
                "$addFields": {
                    "sub_stat_matches": {
                        "$size": {
                            "$filter": {
                                "input": sub_stats,
                                "as": "sub_stat",
                                "cond": {"$in": ["$$sub_stat", "$sub_stats"]},
                            }
                        }
                    }
                }
            },
            {"$match": {"sub_stat_matches": {"$gte": 2}}},
            {"$sort": {"artifact_sets.order": 1, "sub_stat_matches": -1}},
        ]
    )

    result = []
    for character in suitable_characters:
        result.append(character)
        print(character)
    print(result)
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
