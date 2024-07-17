from motor import motor_asyncio
import os

URI = f"mongodb+srv://{{user}}:{{password}}@{{address}}?retryWrites=true&w=majority&appName=Cluster0&tlsAllowInvalidCertificates=true"


class MongoDB():
    def __init__(self, address: str, username: str, password: str) -> None:
        self.client = motor_asyncio.AsyncIOMotorClient(URI.format(address=address, user=username, password=password))

    async def read(self, db: str, collection: str, query: dict) -> dict:
        db = self.client[db]
        collection = db[collection]
        found = await collection.find_one(query)

        return found

    async def read_multi(self, db: str, collection: str, query: dict) -> motor_asyncio.AsyncIOMotorCursor:
        db = self.client[db]
        collection = db[collection]
        found = collection.find(query)

        return found

    async def read_all(self, db: str, collection: str) -> motor_asyncio.AsyncIOMotorCursor:
        db = self.client[db]
        collection = db[collection]
        found = collection.find({})

        return found

    async def write(self, db: str, collection: str, *args) -> None:
        db = self.client[db]
        collection = db[collection]

        await collection.insert_many(args)

        return

    async def erase(self, db: str, collection: str, target: dict) -> None:
        db = self.client[db]
        collection = db[collection]
        await collection.delete_one(target)

        return

    async def update(self, db: str, collection: str, target: dict = {}, value: dict = {}, unset: dict = {}, pull: dict = {}, inc: dict = {}) -> None:
        db = self.client[db]
        collection = db[collection]
        upsert = True
        # if not "$unset" in value:
        #     upsert = False
        return await collection.update_one(target, {'$set': value, '$unset': unset, '$pull': pull, '$inc': inc}, upsert=upsert) #, upsert=True)
    
    async def update_many(self, db: str, collection: str, target: dict = {}, value: dict = {}, unset: dict = {}, pull: dict = {}, inc: dict = {}) -> None:
        db = self.client[db]
        collection = db[collection]
        upsert = True
        # if not "$unset" in value:
        #     upsert = False

        return await collection.update_many(target, {'$set': value, '$unset': unset, '$pull': pull, '$inc': inc}, upsert=upsert) #, upsert=True)
    
    async def count(self, db: str, collection: str, target: dict = {}) -> int:
        db = self.client[db]
        collection = db[collection]

        results_count = await collection.count_documents(target)

        return results_count
