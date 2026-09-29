import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        os.environ.setdefault(key, value)


def build_url(endpoint: str | None) -> str:
    url = endpoint or os.getenv("API_ENDPOINT")
    if not url:
        return "http://127.0.0.1:8000/api/hello"

    if url.startswith("wss://"):
        url = "https://" + url.removeprefix("wss://")
    elif url.startswith("ws://"):
        url = "http://" + url.removeprefix("ws://")

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Endpoint không hợp lệ: {url}")
    return url


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Gọi API và kiểm tra HTTP status")
    parser.add_argument("--url", help="Endpoint API; mặc định dùng API_ENDPOINT")
    parser.add_argument("--method", default="GET", choices=("GET", "POST", "PUT", "PATCH", "DELETE"))
    parser.add_argument("--data", help="Body JSON, ví dụ: '{\"name\": \"test\"}'")
    parser.add_argument("--expected-status", type=int, default=200)
    parser.add_argument("--expected-body", help="Kiểm tra nội dung response chính xác")
    args = parser.parse_args()

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

    try:
        url = build_url(args.url)
        body = None
        headers = {"Accept": "application/json"}
        if args.data:
            body = json.dumps(json.loads(args.data)).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = Request(url, data=body, headers=headers, method=args.method)
        with urlopen(request, timeout=15) as response:
            status = response.status
            response_body = response.read().decode("utf-8", errors="replace")
    except HTTPError as error:
        status = error.code
        response_body = error.read().decode("utf-8", errors="replace")
    except (URLError, ValueError, OSError) as error:
        print(f"Lỗi gọi API: {error}", file=sys.stderr)
        return 1

    print(f"URL: {url}")
    print(f"HTTP status: {status}")
    print(f"Response: {response_body[:1000]}")

    if status != args.expected_status:
        print(f"Không đạt: cần HTTP {args.expected_status}, nhận được {status}.", file=sys.stderr)
        return 1

    if args.expected_body is not None and response_body != args.expected_body:
        print(f"Không đạt: body cần {args.expected_body!r}, nhận {response_body!r}.", file=sys.stderr)
        return 1

    print(f"Đạt: API trả về HTTP {args.expected_status}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
