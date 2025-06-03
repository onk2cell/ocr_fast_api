# 🧠 PaddleOCRFastAPI Enhanced

> A FastAPI-powered prompt-driven OCR engine using PaddleOCR with support for future LLM-based workflows and intelligent form handling.

![GitHub License](https://img.shields.io/github/license/cgcel/PaddleOCRFastAPI)

---

## 📄 Overview

**PaddleOCRFastAPI** is a flexible, prompt-driven OCR engine built with **FastAPI**, currently designed to:
- Take user-defined **prompts** describing what fields to extract
- Use **PaddleOCR** to parse images or PDFs
- Optionally send extracted text to **LLMs** (e.g. OpenAI) to generate structured JSON output

> ⚠️ Currently, this works as a **prompt-enhanced OCR engine**, not as a fully automated form-filler.

This system will soon support:
- **Interactive PDF field mapping**
- **LLM-driven JSON-to-PDF filling**
- **Multi-model LLM support (OpenAI, local models, etc.)**

---

## ✅ Current Features

- [x] PaddleOCR for image and PDF OCR
- [x] Input format: image upload, base64, or file path
- [x] Output: plain text or structured JSON (via LLM prompt)
- [x] Customizable prompts to guide information extraction
- [x] Integrated OpenAI GPT support for structured JSON from text

---

## 🔮 Planned (Future Use Cases)

> These features are on the roadmap and will be released incrementally.

- [ ] PDF form field detection and dynamic mapping
- [ ] JSON → PDF auto-fill with coordinates
- [ ] Interactive UI to tag fields on uploaded PDFs
- [ ] Support for local LLMs (e.g., LLaMA, Mistral, Gemini)
- [ ] Store/reuse field templates for common forms (e.g., Aadhar, PAN, loan, invoice)
- [ ] Chain multiple LLMs for document classification + extraction + filling

---

## 🧠 How It Works (Currently)

### Step 1: Upload file
- Accepts PDF or image formats

### Step 2: Provide prompt
```txt
Extract Product Name , Price , Unit .
```

### Step 3: Get OCR + LLM output
```json
{
  "Product Name": "P1",
  "SKU": "1234-5678-9012",
  "Price": "2.00",
  "Unit": "ML"
}
```

> Prompting defines what the engine looks for – the LLM maps the OCR'd text to structured fields.

---

## 📦 Installation

### 🔧 Local

```bash
git clone https://github.com/your-org/PaddleOCRFastAPI.git
cd PaddleOCRFastAPI
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 🐳 Docker

```bash
cd PaddleOCRFastAPI
cd pp-ocrv4 && sh download_det_cls_rec.sh
cd ..
docker build -t paddleocrfastapi:latest --network host .
docker compose up -d
```

---

## 📑 API Endpoints Summary

| Method | Endpoint                      | Description                                      |
|--------|-------------------------------|--------------------------------------------------|
| `POST` | `/ocr/predict-by-pdf`         | Upload and OCR a PDF file                        |
| `GET`  | `/ocr/predict-by-path`        | OCR from a local file path                       |
| `POST` | `/ocr/predict-by-base64`      | OCR on a base64-encoded image                    |
| `POST` | `/ocr/predict-by-file`        | Upload and OCR an image file                     |
| `GET`  | `/ocr/predict-by-url`         | OCR from an image URL                            |
| `POST` | `/ocr/gpt4o-simple-analyze`   | Use GPT-4o to process OCR text into JSON         |
| `POST` | `/ocr/process` (custom route) | OCR + Prompt-driven LLM analysis (custom flow)   |

---

### POST `/ocr/process`

**Request:**
```json
{
  "file": "<base64 or image>",
  "prompt": "Extract invoice number and vendor name in JSON."
}
```

**Response:**
```json
{
  "invoice_number": "INV-8234",
  "vendor_name": "RNDC"
}
```

---

## 🛠 Language Setup

In `routers/ocr.py`:

```python
ocr = PaddleOCR(use_angle_cls=True, lang="en")
```

Full list: [Supported Languages →](https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.7/doc/doc_en/multi_languages_en.md)

---

## 📸 Swagger UI

Available at: `http://localhost:8000/docs`

![Swagger Screenshot](https://raw.githubusercontent.com/onk2cell/ocr_fast_api/refs/heads/main/AAA_OCR.png)

---

## 🧾 License

MIT License 

[LICENSE](./LICENSE)

---

## 🤝 Contribution

We welcome:
- Prompt format suggestions
- Open-source form templates
- Integrations with LangChain, LlamaIndex, or Streamlit

---

## 🌍 Vision

This repo aims to become a **complete document intelligence engine** that:

- Understands documents by prompt
- Extracts + fills forms via OCR & LLMs
- Works offline and online
- Supports multiple language models and plugins

Stay tuned for weekly updates!

---

## 📦 Inventory Document Example (Prompt-based Extraction)

This is an example of how you can use this OCR engine to extract inventory data from scanned forms:

### Sample Prompt:
```text
Extract product name, quantity, unit price, and total for each line item in the inventory sheet.
```

### OCR + LLM Response:
```json
[
  {
    "product_name": "Coca Cola 500ml",
    "quantity": 24,
    "unit_price": 1.25,
    "total": 30.0
  },
  {
    "product_name": "Pepsi 1L",
    "quantity": 12,
    "unit_price": 2.00,
    "total": 24.0
  }
]
```

This structure can be directly sent to your POS, ERP, or inventory system.
