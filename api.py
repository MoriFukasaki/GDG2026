import json
import os
from io import BytesIO
from pathlib import Path
from typing import Any, Literal, cast

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from groq import Groq
from pypdf import PdfReader
from pydantic import BaseModel, Field

load_dotenv()

MODEL_CHOICE = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
Difficulty = Literal["easy", "medium", "hard"]
VoiceDifficulty = Literal["easy", "medium", "hard"]
VoiceLanguage = Literal["vi", "en"]
VOICE_ENV_KEYS: dict[str, str] = {
    "easy": "ELEVENLABS_EASY_VOICE_ID",
    "medium": "ELEVENLABS_MEDIUM_VOICE_ID",
    "hard": "ELEVENLABS_HARD_VOICE_ID",
}
app = FastAPI(title="PDF Quiz API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_client() -> Any:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Thiếu GROQ_API_KEY trong file .env.")
    return Groq(api_key=api_key)


def _parse_json_response(response: Any) -> dict[str, Any]:
    content = response.choices[0].message.content
    if not content:
        raise HTTPException(status_code=502, detail="Groq không trả về nội dung hợp lệ.")

    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```").removeprefix("json").removesuffix("```").strip()

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=502, detail="Groq trả về JSON không hợp lệ.") from error

    if not isinstance(result, dict):
        raise HTTPException(status_code=502, detail="Groq trả về dữ liệu sai định dạng.")
    return cast(dict[str, Any], result)


def _call_groq_json(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    response = _get_client().chat.completions.create(
        model=MODEL_CHOICE,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )
    return _parse_json_response(response)


def _generate_quiz(
    pdf_text: str,
    question_count: int,
    difficulty: Difficulty = "medium",
) -> dict[str, Any]:
    prompt = f"""
Bạn là giám khảo tạo câu hỏi vấn đáp 1:1 từ tài liệu tiếng Việt.
Hãy tạo đúng {question_count} câu hỏi dựa ONLY trên nội dung tài liệu dưới đây.
Mức độ yêu cầu: {difficulty}.
QUAN TRỌNG: Toàn bộ JSON phải viết bằng tiếng Việt, gồm title, question, expected_answer và explanation.
Nếu tài liệu gốc là tiếng Anh hoặc ngôn ngữ khác, hãy dịch và diễn đạt câu hỏi sang tiếng Việt.
Trả về JSON hợp lệ, không markdown, theo đúng cấu trúc:
{{
  "title": "Tiêu đề ngắn",
  "source": "PDF",
  "questions": [
    {{
    "type": "essay",
    "difficulty": "easy|medium|hard",
      "question": "Nội dung câu hỏi",
    "expected_answer": "Các ý chính cần có trong câu trả lời",
    "explanation": "Tiêu chí đánh giá ngắn"
    }}
  ]
}}
Mỗi câu phải là câu hỏi tự luận, có đúng một difficulty trong easy, medium, hard.

TÀI LIỆU:
{pdf_text}
"""
    result = _call_groq_json(
        "Chỉ trả về JSON hợp lệ theo đúng cấu trúc. Toàn bộ nội dung phải bằng tiếng Việt, không markdown.",
        prompt,
    )
    questions = result.get("questions")
    if not isinstance(questions, list) or not questions:
        raise HTTPException(status_code=502, detail="Groq không tạo được câu hỏi.")
    result["source"] = result.get("source") or "PDF"
    return result


class EvaluateAnswerRequest(BaseModel):
    question: str = Field(min_length=1, max_length=10000)
    answer: str = Field(min_length=1, max_length=20000)
    expected_answer: str = Field(default="", max_length=10000)
    difficulty: VoiceDifficulty = "medium"
    history: list[dict[str, str]] = []


class SpeechRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    difficulty: VoiceDifficulty = "medium"
    language: VoiceLanguage = "vi"


def _evaluate_answer(payload: EvaluateAnswerRequest) -> dict[str, Any]:
    history = json.dumps(payload.history[-10:], ensure_ascii=False)
    prompt = f"""
Đánh giá câu trả lời tự luận của người dùng trong một buổi vấn đáp 1:1.
Chỉ dựa trên câu hỏi và đáp án kỳ vọng được gửi dưới đây.
Mức độ câu hỏi: {payload.difficulty}.

Trả về JSON đúng cấu trúc:
{{
  "score": 0,
  "max_score": 10,
  "is_correct": false,
  "covered_points": ["ý đã nêu đúng"],
  "missing_points": ["ý còn thiếu"],
  "feedback": "Nhận xét ngắn, cụ thể bằng tiếng Việt",
  "ideal_answer": "Câu trả lời mẫu ngắn",
  "next_action": "follow_up|continue|retry"
}}

CÂU HỎI: {payload.question}
ĐÁP ÁN KỲ VỌNG: {payload.expected_answer or "Tự suy ra tiêu chí từ câu hỏi."}
CÂU TRẢ LỜI NGƯỜI DÙNG: {payload.answer}
LỊCH SỬ GẦN ĐÂY: {history}
"""
    result = _call_groq_json(
        "Bạn là giám khảo công bằng. Chấm theo nội dung, không chấm theo văn phong hay lỗi chính tả. Phản hồi phải bằng tiếng Việt.",
        prompt,
    )
    try:
        result["score"] = max(0, min(10, int(result.get("score", 0))))
    except (TypeError, ValueError):
        result["score"] = 0
    result["max_score"] = 10
    return result


async def _text_to_speech(text: str, difficulty: VoiceDifficulty, language: VoiceLanguage) -> bytes:
    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv(VOICE_ENV_KEYS[difficulty])
    if not api_key:
        raise HTTPException(status_code=500, detail="Thiếu ELEVENLABS_API_KEY trong file .env.")
    if not voice_id:
        raise HTTPException(status_code=500, detail=f"Thiếu voice ID ElevenLabs cho mức {difficulty}.")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
    }
    body: dict[str, Any] = {
        "text": text,
        "model_id": os.getenv("ELEVENLABS_MODEL", "eleven_flash_v2_5"),
        "language_code": language,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, headers=headers, json=body)
    if response.status_code >= 400:
        try:
            error_data = response.json()
            detail = error_data.get("detail", {}).get("message", "ElevenLabs không tạo được audio.")
        except (ValueError, AttributeError):
            detail = "ElevenLabs không tạo được audio."
        status_code = response.status_code if response.status_code in {400, 401, 402, 403, 404, 429} else 502
        raise HTTPException(status_code=status_code, detail=detail)
    return response.content


def extract_pdf_text(file_content: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(file_content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception as error:
        raise HTTPException(status_code=400, detail="Không thể đọc file PDF.") from error

    if not text:
        raise HTTPException(status_code=400, detail="PDF không có lớp văn bản để đọc.")
    return text


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/questions")
async def create_questions(
    file: UploadFile = File(...),
    count: int = Form(10),
    difficulty: Difficulty = Form("medium"),
) -> dict[str, Any]:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Vui lòng tải lên file PDF.")
    if not 1 <= count <= 50:
        raise HTTPException(status_code=400, detail="Số câu hỏi phải từ 1 đến 50.")

    pdf_text = extract_pdf_text(await file.read())
    try:
        return _generate_quiz(pdf_text, count, difficulty)
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Không thể tạo câu hỏi: {error}") from error


@app.post("/api/interview/evaluate")
def evaluate_answer(payload: EvaluateAnswerRequest) -> dict[str, Any]:
    try:
        return _evaluate_answer(payload)
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Không thể chấm câu trả lời: {error}") from error


@app.post("/api/speech")
async def speech(payload: SpeechRequest) -> Any:
    audio = await _text_to_speech(payload.text, "easy", payload.language)
    from fastapi.responses import Response

    return Response(content=audio, media_type="audio/mpeg")


frontend_dir = Path(__file__).with_name("frontend")
if frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("PORT", "8000")))