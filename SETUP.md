# Setup (Windows, weak-laptop friendly)

Use cloud APIs only. Do not use WSL, Docker, CUDA, Ollama, or local models.

## 1) Create virtual environment

```powershell
py -3 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 2) Configure environment variables

```powershell
copy .env.example .env
```

Edit `.env` and set:

- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `TELEGRAM_PHONE`
- `OPENROUTER_API_KEY`
- `ADMIN_USERNAME`

Optional tuning:

- `MIN_PRICE`
- `TARGET_PRICE`
- `MAX_DISCOUNT_PERCENT`
- `OPENROUTER_MODEL`

## 3) Run

```powershell
venv\Scripts\activate
py -3 main.py
```

## 4) Admin commands in Telegram

- `/pause`
- `/resume`
- `/memory <username> <text>`
- `/clear <username>`
- `/style <new style>`
- `/price`
- `/stats`
- `/approve <draft_id|chat_id>`
- `/ignore [draft_id]`

## 5) Database

The bot uses SQLite to store:

- Message history per user
- Buyer information and notes
- Settings and preferences
- Draft messages pending approval

Database file is created automatically at `database.db` (or custom `DATABASE_PATH`).

## 6) Troubleshooting

### "Missing required environment variable"
Ensure all required variables are set in `.env` and the file is in the project root.

### "Telethon connection failed"
- Verify `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, and `TELEGRAM_PHONE` are correct.
- First run may require phone verification code input.

### "OpenRouter API error"
- Check that `OPENROUTER_API_KEY` is valid and has available credits.
- Verify the model specified in `OPENROUTER_MODEL` exists and is accessible.

### Draft not appearing in Saved Messages
- Check bot has permission to send to your account.
- Verify `/stats` shows drafts are being created.
