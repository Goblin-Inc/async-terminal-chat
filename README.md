# Async Terminal Chat

> 🌐 **Language:** **English** | [Русский (README_Ru.md)](README_Ru.md)

A multi-user client-server terminal chat built with **Python (`asyncio`, `sqlite3`)**, featuring user registration and authentication, SQLite account storage, and automatic ANSI nickname coloring.

## ✨ Features
- ⚡ **Asynchronous Core (`asyncio`)** — handles multiple concurrent client connections without blocking (`server/core_server.py`).
- 🔐 **SQLite Authentication (`server/auth_db.py`)** — user registration and credential verification upon joining the chat.
- 🎨 **Colored Terminal UI** — automatically assigns a unique ANSI color to each participant and separates input/output streams cleanly (`client/core_client.py`).

## 🚀 Usage

### Server
```bash
cd server
python3 core_server.py
```

## 📄 License
MIT © [Goblin-Inc](https://github.com/Goblin-Inc)

### Client
```bash
cd client
python3 core_client.py
```
