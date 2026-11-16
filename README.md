# Bụi Records

Vinyl shop website (Vietnamese UI). FastAPI backend + SQLite + vanilla-JS frontend.

## Data ownership

- **Discogs API:** release metadata only (cover, tracklist, genre, label) for the products in the shop. It is never used for prices.
- **SQLite (`backend/bui_records.db`):**
  - `release_prices` — the shop catalogue: which Discogs releases are for sale, VND price, stock status, stock.
  - `preorders` — preorder pressings (title, slots, price, optional `discogs_release_id` for the cover).
  - `preorder_reservations` — "giữ chỗ" with code (`GC-XXXXXX`), name, phone, status (`pending → confirmed → arrived`, or `cancelled`).
  - `orders`, `order_items` — checkout results.
- **Signed session cookie:** shopping cart only.

The **Sản phẩm** tab shows only releases that have a `release_prices` row; only those can be added to the cart.

## Set up locally

From the project root in PowerShell:

```powershell
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
```

Put the generated value in `SECRET_KEY` in your local `.env`. Set
`DISCOGS_TOKEN`, or set both `DISCOGS_CONSUMER_KEY` and
`DISCOGS_CONSUMER_SECRET`. If you use the admin API, generate a separate random
value for `ADMIN_TOKEN`. Leave `COOKIE_SECURE=0` for local HTTP and set it to
`1` when serving over HTTPS.

```powershell
cd backend
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`. The application creates a fresh SQLite database
at startup. Add products with the CLI below.

## Publish to GitHub

Create an empty GitHub repository. From the project root:

```powershell
git init -b main
git add .
git diff --cached --name-only
```

Review the staged filenames before committing. Keep `.env`, SQLite files,
logs, backups, and customer exports on your local machine or in private
storage. Commit only source files and the blank `.env.example` template.
If a credential was previously shared or committed, revoke or rotate it before
publishing. If sensitive files are already in Git history, clean that history
before pushing it.

```powershell
git commit -m "Initial Bui Records source"
git remote add origin https://github.com/OWNER/REPO.git
git push -u origin main
```

## Manage the shop (CLI)

```text
python database.py set-price <discogs_id> <price> [status]   # add/update a product
python database.py import-prices prices.csv                  # bulk import
python database.py list-prices
python database.py list-reservations
python database.py set-reservation <code> <pending|confirmed|arrived|cancelled>
```

Reservation lookup is a POST (so phone numbers stay out of URLs/logs): `POST /api/reservations/lookup` `{code, phone}`.

Admin API (same effect): `PUT /api/admin/reservations/<code>` with header `X-Admin-Token` and body `{"status": "confirmed"}`.

## Before launch

The browser can never set a price: the shop price comes from `release_prices` and is re-checked at checkout together with stock.

Set up the product catalogue and preorders. Review the Phụ kiện mock data (hard-coded in `frontend/script.js`) and the shop address, map, and hours shown on the visit page.
