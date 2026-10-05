from fastapi import FastAPI
from app.modules.meetings.router import router as meetings_router

from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.chat.router import router as chat_router
from app.modules.memory.router import router as memory_router
from app.modules.ai.router import router as ai_router
from app.modules.dev.router import router as dev_router
from app.modules.notes.router import router as notes_router
from app.modules.tasks.router import router as tasks_router
from app.core.exception_handlers import (
    register_exception_handlers,
)

from app.modules.profile.router import (
    router as profile_router,
)

app = FastAPI(title="Second Brain AI")
register_exception_handlers(app)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(chat_router)
app.include_router(memory_router)
app.include_router(ai_router)
app.include_router(dev_router)
app.include_router(notes_router)
app.include_router(tasks_router)
app.include_router(profile_router)
app.include_router(meetings_router)


@app.get("/")
def home():
    return {"message": "Second Brain AI Backend Running"}
