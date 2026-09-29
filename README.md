# PDF Quiz Builder

Ứng dụng đọc tài liệu PDF, tạo câu hỏi tự luận bằng Groq, chấm câu trả lời bằng AI và đọc câu hỏi bằng ElevenLabs.

## Yêu cầu

- Python 3.10 trở lên
- Tài khoản Groq cho quiz và chấm điểm
- Tài khoản ElevenLabs cho chuyển văn bản thành giọng nói

## Cài đặt

Tạo môi trường ảo và cài dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Nếu PowerShell chặn kích hoạt môi trường ảo, chạy:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Cấu hình `.env`

Tạo file `.env` ở thư mục gốc. Chỉ cần khai báo các biến của chức năng bạn sử dụng.

### PDF Quiz Builder

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b

ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_EASY_VOICE_ID=your_easy_voice_id
ELEVENLABS_MEDIUM_VOICE_ID=your_medium_voice_id
ELEVENLABS_HARD_VOICE_ID=your_hard_voice_id
ELEVENLABS_MODEL=eleven_flash_v2_5

PORT=8000
```

`GROQ_MODEL` và `ELEVENLABS_MODEL` là tùy chọn vì ứng dụng đã có giá trị mặc định. Ba voice ID ElevenLabs cần thiết khi gọi chức năng đọc giọng nói; endpoint hiện tại dùng voice mức `easy`.

> Không đưa file `.env` hoặc API key lên Git. Hãy kiểm tra `.gitignore` trước khi commit.

## Chạy PDF Quiz Builder

Khởi động API và frontend:

```powershell
python api.py
```

Mở trình duyệt tại [http://127.0.0.1:8000](http://127.0.0.1:8000).

Quy trình sử dụng:

1. Chọn một file PDF có lớp văn bản.
2. Chọn số câu hỏi từ 1 đến 50.
3. Chọn mức độ `Dễ`, `Trung bình` hoặc `Khó`.
4. Bấm **Tạo bộ câu hỏi**.
5. Nhập câu trả lời và bấm **Chấm câu trả lời**.
6. Bấm **Đọc câu hỏi** để tạo audio tiếng Việt bằng ElevenLabs.

PDF scan không có lớp văn bản sẽ không đọc được nếu chưa chạy OCR.

## API chính

### Kiểm tra trạng thái

```powershell
curl http://127.0.0.1:8000/api/health
```

Kết quả:

```json
{"status":"ok"}
```

### Tạo câu hỏi từ PDF

```powershell
curl -X POST http://127.0.0.1:8000/api/questions `
  -F "file=@./tai-lieu.pdf" `
  -F "count=10" `
  -F "difficulty=medium"
```

Các giá trị `difficulty` hợp lệ là `easy`, `medium` và `hard`. API trả về tiêu đề, nguồn PDF và danh sách câu hỏi gồm `question`, `expected_answer`, `explanation` và `difficulty`.

### Chấm câu trả lời

```powershell
curl -X POST http://127.0.0.1:8000/api/interview/evaluate `
  -H "Content-Type: application/json" `
  -d '{"question":"HTTP là gì?","expected_answer":"Giao thức truyền siêu văn bản","answer":"HTTP là giao thức dùng để truyền dữ liệu trên web.","difficulty":"medium"}'
```

Kết quả gồm điểm trên thang 10, các ý đã nêu, ý còn thiếu, nhận xét, đáp án mẫu và hành động tiếp theo.

### Chuyển văn bản thành giọng nói

```powershell
curl -X POST http://127.0.0.1:8000/api/speech `
  -H "Content-Type: application/json" `
  -d '{"text":"Xin chào, chúng ta bắt đầu nhé.","language":"vi","difficulty":"easy"}' `
  --output voice.mp3
```

`language` nhận `vi` hoặc `en`.

## Kiểm thử

Chạy test API:

```powershell
pytest -q
```

Kiểm tra cú pháp Python:

```powershell
python -m py_compile api.py test_api.py
```

## Cấu trúc dự án

```text
.
├── api.py                 # FastAPI, xử lý PDF, Groq, ElevenLabs
├── test_api.py            # Công cụ gọi endpoint và kiểm tra HTTP status
├── requirements.txt       # Python dependencies
└── frontend/
    └── index.html         # Giao diện PDF Quiz Builder
```

## Xử lý lỗi thường gặp

- **`Thiếu GROQ_API_KEY`:** kiểm tra file `.env` ở đúng thư mục gốc và khởi động lại server.
- **`Thiếu ELEVENLABS_API_KEY` hoặc voice ID:** bổ sung đầy đủ biến ElevenLabs.
- **PDF không đọc được:** dùng PDF có thể bôi đen/copy chữ hoặc chạy OCR trước.
- **Groq trả về lỗi hoặc timeout:** kiểm tra API key, hạn mức tài khoản và tên model trong `GROQ_MODEL`.
- **Không nghe được audio:** kiểm tra trình duyệt có quyền phát âm thanh và ElevenLabs đã trả về file thành công.
