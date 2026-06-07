# 🤖 yt-dlp Telegram Bot

An asynchronous, modular, and test-driven Telegram Bot written in Python (3.12+) using `aiogram` (v3), `yt-dlp`, and `SQLAlchemy` (v2) with `SQLite`. 

The bot intercepts video URLs from **YouTube/Shorts**, **Twitter/X**, **Instagram Reels/Posts**, and **TikTok** in chat messages, downloads them in concurrent worker threads, uploads them back to the chat as playable Telegram Videos, and automatically cleans up all local temporary files. 

---

## 🌟 Key Features

- ⚡ **Asynchronous by Design**: Blocking disk and network I/O downloads via `yt-dlp` run in separate threads using `asyncio.to_thread` to maintain a highly responsive bot event loop.
- 🔐 **Access Control & Gating**: Restricts access only to authorized users. The Super Admin ID is automatically seeded at startup.
- 📨 **Access Request System**: Unauthorized users can use the `/request` command. This sends an interactive inline button request ("Allow ✅" / "Deny ❌") to the Super Admin. Clicking a button updates permissions instantly and notifies the requester.
- 🛠️ **Modular Services Factory**: Dedicated, isolated downloader modules for YouTube, Twitter/X, Instagram, and TikTok, resolved dynamically via a downloader factory.
- 🧹 **Robust File Cleaning**: UUID-based sandbox directories are generated for each download job to support parallel downloads safely, and are recursively cleaned up in a `finally` block.
- 📦 **Modern Dependency Management**: Built on `uv` for lightning-fast virtual environments and reproducible builds.
- 🧪 **High Test Coverage (TDD)**: Comprehensive suite of 37 unit and integration tests verifying database CRUD, auth middleware gating, regex URL matching, and mocked downloader pipelines.
- 🐳 **Containerized & Local Friendly**: Can be run locally or deployed instantly via `docker-compose`.

---

## 🛠️ System Prerequisites

- **Python**: version `3.12` or higher.
- **FFmpeg**: Required by `yt-dlp` to merge high-quality audio and video formats.
  - **macOS**: `brew install ffmpeg`
  - **Linux (Debian/Ubuntu)**: `sudo apt-get install -y ffmpeg`
- **uv**: recommended for virtual environments (`curl -LsSf https://astral.sh/uv/install.sh | sh`).

---

## 🚀 Local Installation & Setup

1. **Clone the Repository** and navigate to the project directory:
   ```bash
   git clone <your-repo-url>
   cd ytdlp_bot
   ```

2. **Set Up the Virtual Environment & Dependencies**:
   ```bash
   uv venv
   uv pip install -e ".[dev]"
   ```

3. **Configure Environment Variables**:
   Create a `.env` file from the provided example template:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and fill in your details:
   - `BOT_TOKEN`: Your Telegram Bot Token obtained from [@BotFather](https://t.me/BotFather).
   - `SUPER_ADMIN_ID`: Your Telegram User ID (e.g. `1150695` is set as default).
   - `DB_URL`: The SQLite connection string (default: `sqlite+aiosqlite:///data/bot.db`).
   - `TMP_DIR`: The download cache directory (default: `./tmp`).

4. **Run the Bot**:
   ```bash
   uv run python -m src.main
   ```

5. **Run the Test Suite**:
   ```bash
   uv run pytest
   ```

---

## 🐳 Docker Deployment

You can build and deploy the containerized bot in a single command. The Docker image is optimized and includes `ffmpeg` automatically.

1. Configure your `.env` file as described above.
2. Build and start the container in detached mode:
   ```bash
   docker-compose up -d --build
   ```
3. View logs:
   ```bash
   docker-compose logs -f
   ```

---

## 🔐 Production SSL & Webhooks (Optional)

If you plan to run webhooks in production, Telegram requires a secure **HTTPS** endpoint. You can easily obtain certificates and automate renewals using the included setup script.

### 1. Generate SSL Certificates via Certbot
Run the interactive `getcert.sh` script as root on your Debian 12 server. It will automatically check/install Certbot, temporarily stop any services using port 80, request the Let's Encrypt certificates, copy them into the `./certs` folder, and configure automated 90-day renewals:
```bash
sudo ./getcert.sh
```

### 2. Configure Docker Compose for Direct HTTPS
Update the `telegram-bot-api` service in your `docker-compose.yml` to mount the certificates and enable direct HTTPS:

```yaml
  telegram-bot-api:
    image: aiogram/telegram-bot-api:latest
    restart: unless-stopped
    ports:
      - "12654:12654"
    environment:
      TELEGRAM_API_ID: "${TELEGRAM_API_ID}"
      TELEGRAM_API_HASH: "${TELEGRAM_API_HASH}"
      TELEGRAM_LOCAL: 1
      TELEGRAM_HTTP_PORT: 12654
      # Enable direct HTTPS on the local API server
      TELEGRAM_SSL_CERT_FILE: "/etc/certs/fullchain.pem"
      TELEGRAM_SSL_KEY_FILE: "/etc/certs/privkey.pem"
    volumes:
      - telegram-api-data:/var/lib/telegram-bot-api
      - ./tmp:/app/tmp
      - ./certs:/etc/certs:ro  # Mount the certs directory
```

---

## 🤖 Interaction & Commands

### For Requesters (Unauthorized Users)
- `/start` or `/help` - Explains what the bot does and how to gain access.
- `/request` - Sends an access approval card (Allow/Deny) directly to the Super Admin's private chat.

### For Super Admin
- `/allow <user_id> [username]` - Manually authorize a user ID.
- `/revoke <user_id>` - Revoke access from a user ID.
- `/list` - List all currently allowed users with their dates of registration.
- **Interactive Inline Buttons**: Click `Allow ✅` or `Deny ❌` on a user's request card to instantly change permissions.

---

## 📂 Project Architecture

```
ytdlp_bot/
├── pyproject.toml         # Packaging, dependencies, and test configurations
├── README.md              # Project documentation
├── docker-compose.yml     # Compose settings for containerized service
├── Dockerfile             # Builds python environment with ffmpeg
├── getcert.sh             # Interactive SSL certificate getter and renewal hook installer
├── src/
│   ├── main.py            # Startup checking, DB initialization, and bot polling
│   ├── config.py          # Environment settings loader
│   ├── bot/
│   │   ├── dispatcher.py  # Dispatcher routing and middleware setup
│   │   ├── handlers/
│   │   │   ├── start.py   # Commands (/start, /help, /request)
│   │   │   ├── admin.py   # Admin commands (/allow, /revoke, /list) and button callbacks
│   │   │   └── downloader.py # Coordinates download jobs, limits, and video uploads
│   │   └── middlewares/
│   │       └── auth.py    # Gated user authentication middleware
│   ├── db/
│   │   ├── connection.py  # Async engine, sessionmaker, and super admin seeding
│   │   ├── models.py      # SQLAlchemy models
│   │   └── repository.py  # CRUD database repo queries
│   ├── services/
│   │   ├── base.py        # BaseDownloader interface & result schemas
│   │   ├── dependency_check.py # Startup binary check (ffmpeg, ffprobe)
│   │   ├── downloader_factory.py # Maps matched domains to downloader services
│   │   └── youtube.py, twitter.py, instagram.py, tiktok.py # Specific downloaders
│   └── utils/
│       ├── file_manager.py # UUID job directory sandboxing and cleaner
│       └── url_parser.py   # Advanced regex url extractor
└── tests/                  # Unit and integration test suites
```
