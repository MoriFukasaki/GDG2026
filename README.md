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
HOST=127.0.0.1
```

`GROQ_MODEL` và `ELEVENLABS_MODEL` là tùy chọn vì ứng dụng đã có giá trị mặc định. Ba voice ID ElevenLabs cần thiết khi gọi chức năng đọc giọng nói; endpoint hiện tại dùng voice mức `easy`.

> Không đưa file `.env` hoặc API key lên Git. Hãy kiểm tra `.gitignore` trước khi commit.

## Chạy PDF Quiz Builder

Khởi động API và frontend:

```powershell
python apps/api/main.py
```

Mở trình duyệt tại [http://127.0.0.1:8000](http://127.0.0.1:8000).

### GET `hello world`

```powershell
curl.exe http://127.0.0.1:8000/api/hello
```

Khi thành công, HTTP 200 trả về text thuần `hello world`. Có thể kiểm tra cả status và body bằng `python tools/smoke_api.py --url http://127.0.0.1:8000/api/hello --expected-body "hello world"`.

Nếu port 8000 đang được dùng, đặt `$env:PORT=8001` trước khi khởi động API, rồi gọi `http://127.0.0.1:8001/api/hello`.

### Frontend chạy trên máy khác

Cho backend lắng nghe trên mạng nội bộ trước khi khởi động:

```powershell
$env:HOST="0.0.0.0"
$env:PORT="8001"
python apps/api/main.py
```

Trên máy backend, chạy `ipconfig` để tìm địa chỉ IPv4 của card mạng đang dùng. Trên máy frontend cùng mạng, gọi `http://<IP-máy-backend>:8001/api/hello`; ví dụ:

```js
const response = await fetch("http://192.168.1.10:8001/api/hello");
const message = await response.text(); // "hello world"
```

`0.0.0.0` chỉ là địa chỉ để server lắng nghe; frontend phải dùng IP thực của máy backend. Nếu không kết nối được, kiểm tra hai máy có cùng mạng và Windows Firewall có cho phép kết nối TCP đến port 8001. Nếu frontend chạy trên HTTPS công khai, trình duyệt thường sẽ chặn yêu cầu HTTP tới IP nội bộ; khi đó backend cần một địa chỉ HTTPS có thể truy cập từ máy frontend.

### Frontend khác mạng qua ngrok

Endpoint demo công khai được tách riêng ở `apps/api/public_hello.py` trên port 8002. Tiến trình này chỉ phục vụ `GET /api/hello`; các API dùng Groq hoặc ElevenLabs không nằm trên tunnel này.

Ngrok đã được tải vào `.local/ngrok/ngrok.exe` (thư mục này không được commit). [Tạo tài khoản và lấy authtoken](https://dashboard.ngrok.com/get-started/your-authtoken), sau đó nhập token **trực tiếp trên máy**, không gửi qua chat:

```powershell
.\.local\ngrok\ngrok.exe config add-authtoken "<YOUR_AUTHTOKEN>"
```

Giữ `python apps/api/public_hello.py` chạy ở terminal thứ nhất. Tạo URL ở terminal thứ hai:

```powershell
.\.local\ngrok\ngrok.exe http 8002
```

Frontend khác mạng gọi `https://<URL-ngrok>/api/hello` và đọc response bằng `response.text()`:

```js
const response = await fetch("https://<URL-ngrok>/api/hello", {
  headers: { "ngrok-skip-browser-warning": "true" }
});
if (!response.ok) throw new Error(`HTTP ${response.status}`);
const message = await response.text(); // "hello world"
```

Header trên bỏ qua trang cảnh báo của gói ngrok miễn phí khi gọi bằng trình duyệt. URL ngrok chỉ hoạt động khi cả server demo và ngrok còn chạy.

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
python -m unittest discover -s apps/api -p "test_*.py" -v
```

Kiểm tra cú pháp Python:

```powershell
python -m py_compile apps/api/main.py apps/api/test_main.py tools/smoke_api.py
```

## Cấu trúc dự án

```text
.
├── ARCHITECTURE.md        # Sơ đồ và nguyên tắc kiến trúc
├── apps/
│   ├── api/
│   │   ├── main.py         # FastAPI, xử lý PDF, Groq, ElevenLabs
│   │   ├── public_hello.py # Endpoint hello riêng cho ngrok
│   │   └── test_main.py    # Test GET và trang web
│   └── web/
│       └── index.html      # Giao diện PDF Quiz Builder
├── tools/
│   └── smoke_api.py        # Gọi thử API
└── requirements.txt       # Python dependencies
```

Chi tiết kiến trúc và cách mở rộng xem tại
[`ARCHITECTURE.md`](ARCHITECTURE.md).

## Xử lý lỗi thường gặp

- **`Thiếu GROQ_API_KEY`:** kiểm tra file `.env` ở đúng thư mục gốc và khởi động lại server.
- **`Thiếu ELEVENLABS_API_KEY` hoặc voice ID:** bổ sung đầy đủ biến ElevenLabs.
- **PDF không đọc được:** dùng PDF có thể bôi đen/copy chữ hoặc chạy OCR trước.
- **Groq trả về lỗi hoặc timeout:** kiểm tra API key, hạn mức tài khoản và tên model trong `GROQ_MODEL`.
- **Không nghe được audio:** kiểm tra trình duyệt có quyền phát âm thanh và ElevenLabs đã trả về file thành công.
