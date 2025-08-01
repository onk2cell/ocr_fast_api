# -*- coding: utf-8 -*-

# import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# import uvicorn
import yaml

from models.RestfulModel import *
from routers import ocr
from utils.ImageHelper import *

app = FastAPI(title="Paddle OCR API",
              description="Paddle OCR API for invoice parsing")


# 跨域设置
origins = [
    "*"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(ocr.router)

# uvicorn.run(app=app, host="0.0.0.0", port=8000)
