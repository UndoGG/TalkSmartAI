import ipaddress

from fastapi import FastAPI

from . import endpoints
from logging_engine import start_logger
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

logger = start_logger('DEBUG')
HOST = '147.45.68.208'
PORT = 8000


tortoise_logger = logging.getLogger('tortoise')
tortoise_logger.setLevel(logging.WARN)

sqlite3_logger = logging.getLogger('aiosqlite')
sqlite3_logger.setLevel(logging.WARN)

logger.info('[bold green]Launching Payment Backend')

app = FastAPI()

# noinspection PyTypeChecker
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.main_router)

logger.info("[bold green]All ready to launch!")
uvicorn.run(app, host=HOST, port=PORT)
