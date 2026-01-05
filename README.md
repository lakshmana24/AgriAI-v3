# AgriAI-v3 — AI-Based Multi-Modal Agricultural Advisory System

AgriAI-v3 is the third iteration of the "AI-based multi model agricultural advisory system". It provides a pragmatic, multi-role, multi-modal platform where farmers can ask questions using text, audio, and images, and agricultural officers can review low-confidence cases and send verified guidance back to farmers.

This version generalizes beyond Kerala-specific constraints used in the previous hackathon prototype and focuses on a clean, portable FastAPI backend with a lightweight, static frontend.

## Key Features
- Role-based access for farmers and officers with JWT auth
- Multi-modal inputs: text, audio (speech-to-text), image (disease detection stub)
- Structured AI reasoning via Gemini with uncertainty handling and citations
- Automatic escalation of low-confidence/uncertain answers to officers
- Officer dashboard to list escalations and submit verified advisories
- Health checks, rate limiting, structured logging, and CORS

## Architecture
```
AgriAI-v3/
├── app/                         # FastAPI application (backend)
│   ├── core/                    # App factory, config, logging
│   │   ├── app.py
│   │   ├── config.py
│   │   └── logging.py
│   ├── api/                     # Routers and versioned API
│   │   ├── v1/
│   │   │   └── health.py
│   │   ├── auth.py
│   │   ├── chat.py
│   │   └── officer.py
│   ├── middleware/              # Rate limiting, request context
│   │   ├── rate_limit.py
│   │   └── request_context.py
│   ├── prompts/                 # Prompt builders for Gemini
│   │   └── gemini.py
│   ├── schemas/                 # Pydantic models
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── errors.py
│   │   ├── gemini.py
│   │   └── officer.py
│   ├── services/                # External clients and domain services
│   │   ├── auth_service.py
│   │   ├── bhashini_client.py
│   │   ├── escalation_store.py
│   │   ├── gemini_client.py
│   │   ├── image_detection.py
│   │   ├── multimodal_chat.py
│   │   ├── text_processing.py
│   │   └── transcription.py
│   └── utils/                   # Utilities
│       └── ttl_cache.py
├── frontend/                    # Static HTML/CSS/JS frontend
│   ├── assets/
│   │   ├── css/styles.css
│   │   └── js/app.js
│   ├── index.html
│   ├── login.html
│   ├── farmer-chat.html
│   └── officer-dashboard.html
├── api_contract.md              # High-level API reference (frozen)
├── requirements.txt             # Python dependencies
├── main.py                      # Uvicorn launcher (FastAPI app)
└── .gitignore
```

## Quickstart
- Prerequisites: Python 3.10+ recommended
- Generate or choose a strong `JWT_SECRET_KEY` (required for auth)
- Obtain a `GEMINI_API_KEY` for AI reasoning; Bhashini credentials optional for speech-to-text

1) Create and activate a virtual environment (Windows PowerShell):
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Install backend dependencies:
```
pip install -r requirements.txt
```

3) Configure environment variables (create a `.env` file in the project root):
```
# Core server
HOST=127.0.0.1
PORT=8000
DEBUG=true
ALLOWED_ORIGINS=*

# Auth (required)
JWT_SECRET_KEY=replace-with-a-strong-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRES_MINUTES=30

# Gemini (required for AI answers)
GEMINI_API_KEY=replace-with-your-key
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta
GEMINI_MODEL=gemini-1.5-flash

# Bhashini (optional — speech-to-text)
BHASHINI_BASE_URL=        # e.g. https://api.bhashini.gov.in
BHASHINI_API_KEY=
```

4) Run the backend:
```
python main.py
```
Server listens on `http://127.0.0.1:8000` by default.

5) Use the frontend:
- Open `frontend/index.html` directly in your browser
- Sign in via `frontend/login.html` and proceed to the farmer chat or officer dashboard

Default demo accounts (in-memory):
- Farmer: `farmer01` / `passfarm1`
- Officer: `agrioff01` / `agripass@gov`

## API Overview
- Auth: `POST /auth/login` (OAuth2 password form)
- Health: `GET /api/v1/health`
- Chat (multipart): `POST /api/v1/chat` — accepts any combination of `text`, `audio`, `image`
- Officer list: `GET /api/v1/officer/escalations`
- Officer respond: `POST /api/v1/officer/respond/{id}`

Example calls:
```
# Login (form-encoded)
curl -X POST \
  -d "username=farmer01&password=passfarm1" \
  http://127.0.0.1:8000/auth/login

# Chat (text-only)
curl -X POST \
  -H "Authorization: Bearer <TOKEN>" \
  -F "text=Yellowing leaves in paddy" \
  http://127.0.0.1:8000/api/v1/chat

# Chat (with image)
curl -X POST \
  -H "Authorization: Bearer <TOKEN>" \
  -F "text=Leaf spots on tomato" \
  -F "image=@/path/to/photo.jpg" \
  http://127.0.0.1:8000/api/v1/chat

# Officer: list escalations
curl -H "Authorization: Bearer <TOKEN>" \
  http://127.0.0.1:8000/api/v1/officer/escalations

# Officer: respond
curl -X POST \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"response_text":"Verified guidance…","citations":["https://example.org"]}' \
  http://127.0.0.1:8000/api/v1/officer/respond/<ESCALATION_ID>
```

## How It Works
- App assembly and routing: `app/core/app.py` (routers and middleware)
- Chat endpoint and multimodal handling: `app/api/chat.py`
- Officer workflow: `app/api/officer.py` with in-memory store `app/services/escalation_store.py`
- Auth guard and token decoding: `app/api/dependencies/auth.py`
- Gemini client for structured JSON answers: `app/services/gemini_client.py`
- Prompt discipline (no hallucinations, explicit uncertainty): `app/prompts/gemini.py`
- Audio transcription via Bhashini, fallback to local Whisper: `app/services/transcription.py`
- Image detection stub (replace with YOLO/EfficientNet later): `app/services/image_detection.py`
- Structured logging with `structlog`, request tracing: `app/core/logging.py`
- Simple in-memory TTL cache used for requests and escalations: `app/utils/ttl_cache.py`

## Notes and Limitations
- The image detection is a stub returning low-confidence placeholder predictions
- Escalations are stored in-memory and expire; no persistent database
- `audio_output_url` is currently empty; add a TTS step if needed
- CORS is permissive (`*`) by default for local development
- Do not use real secrets in code; set them via environment variables

## Prior Work
AgriAI-v3 is a generalized evolution of the earlier Kerala-focused prototype ("Krishi Mitra – Enhanced Multi-Role Digital Farming Platform"). This version keeps the multi-role, multi-modal core while removing region-specific assumptions and sharpening backend portability.

## License
This project is released under an open-source license for educational, research, and non-commercial use.
Users are free to modify and extend the system with proper attribution to the original authors.
The software is provided “as is” without warranty, and misuse for critical decision-making is discouraged.
