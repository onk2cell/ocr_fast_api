# -*- coding: utf-8 -*-

from typing import List, Union
from pydantic import BaseModel
from fastapi import status
from fastapi.responses import JSONResponse, Response

from .OCRModel import OCRModel

class RestfulModel(BaseModel):
    resultcode : int = 200 
    message: str = None 
    data: Union[List, str] = [] 

def resp_200(*, data: Union[list, dict, str]) -> Response:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
    
            'code': 200,
            'message': "Success",
            'data': data,
        }
    )
    
def resp_400(*, data: str = None, message: str="BAD REQUEST") -> Response:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
    
            'code': 400,
            'message': message,
            'data': data,
        }
    )