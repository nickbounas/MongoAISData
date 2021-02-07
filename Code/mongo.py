from motor.motor_asyncio import AsyncIOMotorClient
from settings import get_settings, Settings
from databases import DatabaseURL
from sshtunnel import SSHTunnelForwarder

class DataBase:
    client: AsyncIOMotorClient = None

settings = get_settings() 

if settings.SSH_CONNECTION:
    # define ssh tunnel
    server = SSHTunnelForwarder(
        settings.SSH_HOST,
        ssh_username=settings.SSH_USER,
        ssh_password=settings.SSH_PASS,
        remote_bind_address=('127.0.0.1', 27017)
    )

   

db = DataBase()


async def get_database() -> AsyncIOMotorClient:
    return db.client

async def connect_to_mongo():
    if settings.SSH_CONNECTION:
        server.start()
        db.client = AsyncIOMotorClient('localhost', server.local_bind_port)
    else:
        
        db.client = AsyncIOMotorClient(str(DatabaseURL(settings.MONGODB_URL)),
                                    maxPoolSize=settings.MAX_CONNECTIONS_COUNT,
                                    minPoolSize=settings.MIN_CONNECTIONS_COUNT,
                                    uuidRepresentation="standard")


async def close_mongo_connection():
    db.client.close()
    
    if settings.SSH_CONNECTION:
        server.stop()