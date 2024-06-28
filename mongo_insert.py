from pymongo import MongoClient
from json_char_db import recommend_data

# MongoDB connection settings
MONGO_DETAILS = "mongodb+srv://admin:admin@cluster0.e1hu4of.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_DETAILS)
database = client["GenshinArtifactDB"]
recommended_artifacts_collection = database["recommended_artifacts_collection"]
print(recommend_data)
# Data to insert

# Insert data into the collection
recommended_artifacts_collection.insert_many(recommend_data)

print("Data inserted successfully.")
