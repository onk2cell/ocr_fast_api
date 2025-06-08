# -*- coding: utf-8 -*-
from fastapi import FastAPI, Request
import openai
import re
from fastapi import APIRouter, HTTPException, UploadFile, status, Form
from models.OCRModel import *
from models.RestfulModel import *
from paddleocr import PaddleOCR
from utils.ImageHelper import base64_to_ndarray, bytes_to_ndarray
import requests
import os
from pdf2image import convert_from_bytes
from PIL import Image
from io import BytesIO
import numpy as np
import json
from typing import Optional, List
from fastapi.responses import StreamingResponse
import uuid
from pydantic import BaseModel

OCR_LANGUAGE = os.environ.get("OCR_LANGUAGE", "en")

router = APIRouter(prefix="/ocr", tags=["OCR"])

ocr = PaddleOCR(use_angle_cls=True, lang=OCR_LANGUAGE)

# Helper: Extract text and confidence score
def extract_text_and_confidence(ocr_data):
    results = []
    for block in ocr_data:
        for line in block:
            if isinstance(line, list) and len(line) >= 2:
                box, (text, score) = line
                results.append({
                    "text": text
                })
    return results

# Helper: Generate prompt from user mappings
def generate_extraction_prompt(user_mappings: dict = None) -> str:
    if user_mappings is None:
        user_mappings = {}

    def column(col_key, default_name):
        return user_mappings.get(col_key) or default_name

    prompt = f"""
You are a powerful and reliable invoice parser. I will provide you an invoice extracted from a PDF in plain text format and/or image. Your task is to extract **all relevant structured information** from it and return a clean, well-formatted JSON.

The JSON should contain two main sections:

1. invoice_metadata:
- invoice_number, invoice_date, vendor_name, vendor_address, store_name, store_address,
  po_number, payment_terms, due_date, total_amount, subtotal, tax, freight, other_charges

2. line_items:
For each product, extract:
- product_name: (Look for columns like '{column('product_name', 'product_description/name')}')
- upc: (Look for columns like '{column('upc', 'UPC/item_code')}')
- quantity: (Look for columns like '{column('quantity', 'quantity')}')
- unit: (Look for columns like '{column('unit', 'unit_of_measure')}')
- price: (Look for columns like '{column('price', 'price')}')

Return the result in valid JSON format with these exact field names.
"""
    return prompt.strip()

# Route: OCR PDF + prompt generation
@router.post('/predict-by-pdf', response_model=RestfulModel, summary="Parse uploaded PDF file")
async def predict_by_pdf(
    file: UploadFile,
    custom_columns: Optional[str] = Form(None)  # Expecting a JSON string
):
    restfulModel: RestfulModel = RestfulModel()

    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload a .pdf file"
        )

    try:
        # Parse custom columns
        column_mapping = json.loads(custom_columns) if custom_columns else {}

        # Generate prompt
        prompt = generate_extraction_prompt(column_mapping)

        # Convert PDF to image(s)
        pdf_bytes = await file.read()
        print("PDF bytes length:", len(pdf_bytes))
        try:
            images = convert_from_bytes(pdf_bytes, poppler_path="C:\\poppler-24.08.0\\Library\\bin")
        except Exception as e:
            print("Error in convert_from_bytes:", e)
            raise

        all_results = []
        for idx, page_img in enumerate(images):
            img_array = np.array(page_img.convert("RGB"))
            result = ocr.ocr(img=img_array, cls=True)
            ocr_results = extract_text_and_confidence(result)
            filtered_results = [{"text": r["text"]} for r in ocr_results]
            page_result = {
                "page": idx + 1,
                "page_id": str(uuid.uuid4()),
                "ocr_results": filtered_results,
                "prompt": prompt
            }
            all_results.append(page_result)

        restfulModel.resultcode = 200
        restfulModel.message = f"{len(all_results)} page(s) parsed."
        restfulModel.data = all_results
        return restfulModel

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF parsing failed: {str(e)}"
        )


@router.get('/predict-by-path', response_model=RestfulModel, summary="Parse local image file")
def predict_by_path(image_path: str):
    result = ocr.ocr(image_path, cls=True)
    processed_result = extract_text_and_confidence(result)
    restfulModel = RestfulModel(
        resultcode=200, message="Success", data=processed_result, cls=OCRModel)
    return restfulModel


@router.post('/predict-by-base64', response_model=RestfulModel, summary="Parse Base64 data")
def predict_by_base64(base64model: Base64PostModel):
    img = base64_to_ndarray(base64model.base64_str)
    result = ocr.ocr(img=img, cls=True)
    processed_result = extract_text_and_confidence(result)
    restfulModel = RestfulModel(
        resultcode=200, message="Success", data=processed_result, cls=OCRModel)
    return restfulModel


@router.post('/predict-by-file', response_model=RestfulModel, summary="Parse uploaded image file")
async def predict_by_file(file: UploadFile):
    restfulModel: RestfulModel = RestfulModel()
    if file.filename.endswith((".jpg", ".png")):
        restfulModel.resultcode = 200
        restfulModel.message = file.filename
        file_data = file.file
        file_bytes = file_data.read()
        img = bytes_to_ndarray(file_bytes)
        result = ocr.ocr(img=img, cls=True)
        processed_result = extract_text_and_confidence(result)
        restfulModel.data = processed_result
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload a .jpg or .png file"
        )
    return restfulModel


@router.get('/predict-by-url', response_model=RestfulModel, summary="Parse image URL")
async def predict_by_url(imageUrl: str):
    restfulModel: RestfulModel = RestfulModel()
    response = requests.get(imageUrl)
    image_bytes = response.content
    if image_bytes.startswith(b"\xff\xd8\xff") or image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        restfulModel.resultcode = 200
        img = bytes_to_ndarray(image_bytes)
        result = ocr.ocr(img=img, cls=True)
        processed_result = extract_text_and_confidence(result)
        restfulModel.data = processed_result
        restfulModel.message = "Success"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload a .jpg or .png file"
        )
    return restfulModel

class SimpleGPT4ORequest(BaseModel):
    prompt: str
    # pages: List[List[str]]

@router.post("/gpt4o-simple-analyze")
async def gpt4o_simple_analyze(request: SimpleGPT4ORequest):
   
    openai.api_key = '""'

    # Concatenate all text from all pages
    # all_text = "\n".join(["\n".join(page) for page in request.pages])
    full_prompt = str(f"{request.prompt}")

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": full_prompt}],
            max_tokens=1024
        )
        return {"response": response.choices[0].message.content}
    except Exception as e:
        return {"error": str(e)}


openai.api_key = ""


class OCRText(BaseModel):
    text: str


class GPTPromptRequest(BaseModel):
    prompt: str
    ocr_results: List[OCRText]


@router.post("/gpt4o-structured-json")
async def gpt4o_structured_json(req: GPTPromptRequest):
    # Step 1: Format the OCR text into a string
    ocr_string = "\n".join([item.text for item in req.ocr_results])
    final_prompt = f"{req.prompt}\n\nOCR Result:\n{ocr_string}"

    try:
        # Step 2: Call GPT-4o
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": final_prompt}],
            temperature=0.2,
            max_tokens=2048
        )
        raw_output = response.choices[0].message.content

        # Step 3: Extract JSON block from markdown-style ```json ... ``` response
        match = re.search(r"```json\n(.*?)\n```", raw_output, re.DOTALL)
        extracted_json = None
        if match:
            try:
                extracted_json = json.loads(match.group(1))
            except json.JSONDecodeError as e:
                extracted_json = f"JSON parse error: {str(e)}"

        return {
            "success": True,
            "final_prompt": final_prompt,
            "gpt_response_raw": raw_output,
            "structured_json": extracted_json or "No JSON block found"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }