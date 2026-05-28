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

Optional:

- `SMTP_EMAIL`, `SMTP_PASSWORD` (for email confirmations)
- `MIN_PRICE`, `TARGET_PRICE`, `MAX_DISCOUNT_PERCENT`
- `OPENROUTER_MODEL`

## 3) Run

```powershell
venv\Scripts\activate
python main.py
```

## 4) Admin commands in Telegram

- `/inventory` - List available products
- `/check <product>` - Check specific product
- `/add <name>|<price>|<stock>` - Add product
- `/update <name>|<stock>` - Update stock
- `/sales` - View recent sales
- `/price` - Show pricing policy
- `/help` - Show help

## 5) Database

The bot uses SQLite to store:

- Product inventory (name, price, stock)
- Sales history (customer, product, amount, status)
- Customer inquiries (tracking)

Database file: `inventory.db` (auto-created)

## 6) How it works

1. **Customer messages you** → Bot receives inquiry
2. **AI generates response** → Sharp, professional crypto seller tone
3. **Payment keywords detected** → Bot adds crypto payment methods
4. **Admin manages inventory** → `/add`, `/update` commands
5. **Sales tracked** → `/sales` command shows all transactions
6. **Email confirmations** (optional) → SMTP sends order/credential emails

## 7) Troubleshooting

### "Missing required environment variable"
Ensure all required vars are in `.env`.

### "Telethon connection failed"
- Verify `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE`
- First run may require phone verification code

### "OpenRouter API error"
- Check `OPENROUTER_API_KEY` is valid and has credits
- Verify model exists: `qwen/qwen3`

### Database not created
- Check folder permissions
- Verify `DATABASE_PATH` is writable
