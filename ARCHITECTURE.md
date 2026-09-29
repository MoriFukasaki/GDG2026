# Kiến trúc monorepo PDF Quiz Builder

```text
GDG2026/
├── apps/
│   ├── api/
│   │   ├── main.py          # FastAPI: quiz, chấm điểm, speech, health, hello
│   │   ├── public_hello.py  # Chỉ /api/hello cho tunnel công khai
│   │   └── test_main.py     # Kiểm tra HTTP và phục vụ web
│   └── web/
│       └── index.html       # Giao diện HTML/JS, gọi API cùng origin
├── tools/
│   └── smoke_api.py         # Gọi thử endpoint backend
├── requirements.txt         # Dependency Python dùng cho API
└── .env                     # Cấu hình local, không commit
```

Một tiến trình FastAPI phục vụ cả `/api/*` và giao diện `/`. Endpoint `GET /api/hello` nằm hoàn toàn trong backend và có thể gọi trực tiếp qua localhost.

```text
Client / curl
        │
        ▼
FastAPI :8000 ── /api/hello → "hello world"
        ├─────── /api/health → trạng thái
        ├─────── /api/questions → PDF + Groq
        ├─────── /api/interview/evaluate → Groq
        ├─────── /api/speech → ElevenLabs
        └─────── / → apps/web/index.html
```

Khi logic tăng lên, có thể tách `main.py` thành `routes/`, `services/` và `integrations/` ngay trong `apps/api`. Chỉ tạo `packages/` khi thực sự có schema hoặc mã được nhiều app dùng chung. Hiện tại frontend là HTML tĩnh nên không cần Node workspace hoặc thêm tầng build.

Với frontend ở mạng khác, ngrok chuyển tiếp vào `public_hello.py:8002`, nơi chỉ có endpoint hello. Backend đầy đủ ở port 8001 vẫn chạy riêng. Ngrok cần authtoken trên máy backend trước khi tạo URL công khai.
