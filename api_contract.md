# API Contract — Frozen

## Authentication

### POST /auth/login

Request:
{
  "username": string,
  "password": string
}

Response:
{
  "access_token": string,
  "role": "farmer" | "officer",
  "expires_in": number
}

---

## Chat (Multimodal)

### POST /api/v1/chat

Request (multipart/form-data):
- text?: string
- audio?: file
- image?: file

Response:
{
  "response_text": string,
  "confidence": "High" | "Medium" | "Low",
  "citations": string[],
  "escalate": boolean,
  "reason": string | null,
  "audio_output_url": string | null
}
