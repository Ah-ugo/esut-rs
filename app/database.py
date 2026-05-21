from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging

logger = logging.getLogger(__name__)

client: AsyncIOMotorClient = None
database = None


async def connect_db():
    global client, database
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    database = client[settings.DATABASE_NAME]
    
    # Create indexes
    await create_indexes()
    logger.info(f"Connected to MongoDB: {settings.DATABASE_NAME}")


async def disconnect_db():
    global client
    if client:
        client.close()


async def create_indexes():
    # Users
    await database.users.create_index("email", unique=True)
    await database.users.create_index("matric_number", sparse=True)
    
    # Students
    await database.students.create_index("matric_number", unique=True)
    await database.students.create_index([("programme_id", 1), ("level", 1)])
    
    # Courses
    await database.courses.create_index("code", unique=True)
    await database.courses.create_index([("programme_id", 1), ("semester", 1), ("level", 1)])
    
    # Results
    await database.results.create_index(
        [("student_id", 1), ("course_id", 1), ("session", 1), ("semester", 1)],
        unique=True
    )
    
    # Audit logs
    await database.audit_logs.create_index([("created_at", -1)])
    await database.audit_logs.create_index("user_id")


def get_database():
    return database
