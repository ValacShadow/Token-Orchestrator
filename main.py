import uuid
import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta
import redis
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager

# app = FastAPI()


REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379
EXPIRATION_TIME = 300
UNBLOCK_TIME = 60

# Initialize Redis
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

# Key prefix for Redis
KEY_PREFIX = "api_key:"

class KeyInfo(BaseModel):
    key: str
    created_at: datetime
    isblocked: bool
    unblocks_at: Optional[datetime] = None


async def handle_unblock_worker():
    print("in worker")
    while True:
        keys = redis_client.keys(f"{KEY_PREFIX}*")
        for key in keys:
            key_info = KeyInfo.parse_raw(redis_client.get(key))
            if key_info.isblocked and key_info.unblocks_at and key_info.unblocks_at < datetime.now():
                key_info.isblocked = False
                key_info.unblocks_at = None
                redis_client.setex(key, redis_client.ttl(key), key_info.json())
                print(f"Key unblocked: {key}")
        await asyncio.sleep(10)



@asynccontextmanager
async def lifespan(app: FastAPI):
    # asyncio.create_task(subscribe_key_expiration())
    asyncio.create_task(handle_unblock_worker())
    yield
    # Shutdown logic here (if any)

app = FastAPI(lifespan=lifespan)


@app.post("/keys", status_code=201)
async def create_key():
    key = str(uuid.uuid4())
    key_info = KeyInfo(
        key=key,
        created_at=datetime.now(),
        isblocked=False,
    )
    redis_client.setex(f"{KEY_PREFIX}{key}", EXPIRATION_TIME, key_info.json())
    return {"key": key}

@app.get("/keys")
async def get_key():
    keys = redis_client.keys(f"{KEY_PREFIX}*")
    if not keys:
        raise HTTPException(status_code=404, detail="Key not found")

    for key in keys:
        key_info = KeyInfo.parse_raw(redis_client.get(key))
        if not key_info.isblocked:
            key_info.isblocked = True
            key_info.unblocks_at = datetime.now() + timedelta(seconds=UNBLOCK_TIME)
            redis_client.setex(key, redis_client.ttl(key), key_info.json())
            return {"key": key_info.key}
    
    raise HTTPException(status_code=404, detail="Key not found")

@app.get("/keys/{key_id}")
async def get_key_info(key_id: str):
    key = f"{KEY_PREFIX}{key_id}"
    key_info = redis_client.get(key)
    if not key_info:
        raise HTTPException(status_code=404, detail="Key not found")
    
    key_info = KeyInfo.parse_raw(key_info)
    return key_info.dict()

@app.post("/keys/{key_id}/unblock")
async def unblock_key(key_id: str):
    key = f"{KEY_PREFIX}{key_id}"
    key_info = redis_client.get(key)
    if not key_info:
        raise HTTPException(status_code=404, detail="Key not found")
    
    key_info = KeyInfo.parse_raw(key_info)
    key_info.isblocked = False
    key_info.unblocks_at = None
    redis_client.setex(key, redis_client.ttl(key), key_info.json())
    return {"message": "key unblocked"}

@app.delete("/keys/{key_id}")
async def delete_key(key_id: str):
    key = f"{KEY_PREFIX}{key_id}"
    if not redis_client.delete(key):
        raise HTTPException(status_code=404, detail="Key not found")
    
    return {"message": "key deleted"}

@app.post("/keys/{key_id}/keep-alive")
async def keep_alive(key_id: str):
    key = f"{KEY_PREFIX}{key_id}"
    key_info = redis_client.get(key)
    if not key_info:
        raise HTTPException(status_code=404, detail="Key not found")
    
    key_info = KeyInfo.parse_raw(key_info)
    NEW_EXPIRATION_TIME = redis_client.ttl(key) + EXPIRATION_TIME
    redis_client.setex(key, NEW_EXPIRATION_TIME, key_info.json())
    return {"message": "key is alive"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)