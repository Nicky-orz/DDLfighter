# DDL Fighter — AI‑Powered Deadline Reminder

**DDL Fighter** is a lightweight, AI‑assisted tool that extracts events and deadlines from Chinese group chat notifications, stores them locally, and sends you timely reminders via desktop notifications and WeChat (PushPlus). It also supports automated daily checks through GitHub Actions — so you get alerts even when your PC is off.

---

## ✨ Features

- **AI Extraction** – Paste any Chinese notification; the tool extracts event name, due date, and due time using DeepSeek API.
- **Batch Processing** – Handles multiple events from a single message (e.g. “meeting at 3pm, submit report by 6pm”).
- **Clipboard Monitor** – (Optional) watches your clipboard and asks for confirmation before extracting, saving API costs.
- **Local Database** – Stores all tasks in a SQLite file (`tasks.db`).
- **Dual Reminders**:
  - Windows toast notifications (if run locally).
  - WeChat push via PushPlus (works both locally and in the cloud).
- **Cloud‑Ready** – Automatically runs twice a day via GitHub Actions, sends WeChat alerts without needing your PC to be on.
- **Calendar Export** – Generates `.ics` files for importing into your phone’s calendar.
- **Task Management** – View pending/history/all tasks, edit or delete tasks individually or in batch.

---

## 🧰 Tech Stack

- Python 3.10+
- [DeepSeek API](https://platform.deepseek.com/) – for natural language understanding
- SQLite – local data persistence
- [PushPlus](http://www.pushplus.plus/) – WeChat push notifications
- GitHub Actions – scheduled cloud execution
- `requests`, `python-dotenv`, `win10toast` (Windows), `pyperclip`, `icalendar`, `pytz`

---

## 📁 Project Structure

```
DDLfighter/
├── .github/workflows/
│   └── main.yml                # GitHub Actions workflow (daily reminders)
├── .env.example                # Template for environment variables
├── .gitignore
├── README.md
├── requirements.txt            # Python dependencies
│
├── main.py                     # Manual entry: paste and extract
├── monitor.py                  # Clipboard monitor (copy & confirm)
├── query.py                    # List pending tasks (reminded=0)
├── history.py                  # List completed/reminded tasks (reminded=1)
├── all_tasks.py                # Dashboard: all tasks + statistics
├── edit_task.py                # Edit/delete/reset tasks (supports batch)
├── check_remind.py             # Reminder engine: desktop popup + WeChat push
├── export_calendar.py          # Export tasks to .ics (phone calendar)
│
└── tasks.db                    # SQLite database (not committed if using Supabase)
```

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/DDLfighter.git
cd DDLfighter
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
Copy `.env.example` to `.env` and fill in your keys:
```ini
DEEPSEEK_API_KEY=sk-xxxxx
PUSHPLUS_TOKEN=your_pushplus_token   # optional, only if you use WeChat push
```

### 4. Run locally
- **Manual entry**: `python main.py` – paste a notification and let AI extract.
- **Clipboard monitor**: `python monitor.py` – copy a notification, then press `y` to confirm extraction.

### 5. View tasks
- Pending: `python query.py`
- History: `python history.py`
- All: `python all_tasks.py`

### 6. Edit or delete
`python edit_task.py` – supports single and batch operations.

### 7. Export to calendar
`python export_calendar.py` – generates `tasks.ics`; send it to your phone and open with Calendar.

---

## ☁️ Automated Cloud Reminders (GitHub Actions)

1. Push your code (including `tasks.db` and `.github/workflows/main.yml`) to GitHub.
2. Go to your repository → **Settings** → **Secrets and variables** → **Actions** → add:
   - `PUSHPLUS_TOKEN` – your PushPlus token.
3. The workflow will run daily at **09:00** and **21:00** Beijing time.
4. You can also manually trigger it from the **Actions** tab.

> **Note**: If you use a local `tasks.db`, remember to push it after adding new tasks so the cloud version stays up‑to‑date.  
> For a fully automatic sync, consider migrating to Supabase (see [wiki](#) or ask).

---

## 🛠️ Configuration via `.env`

| Variable | Description |
| :--- | :--- |
| `DEEPSEEK_API_KEY` | Your DeepSeek API key (required for extraction). |
| `PUSHPLUS_TOKEN` | Your PushPlus token for WeChat push. |

---

## 🤝 Contributing

Feel free to open issues or pull requests. Suggestions for improvement are always welcome.

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.

---

## 🙋 FAQ

**Q: Do I need to keep my PC on for reminders?**  
A: No. If you enable GitHub Actions, reminders run in the cloud.

**Q: How do I avoid duplicate reminders?**  
A: The script updates `reminded=1` after sending a notification. Make sure your cloud database is synced (push `tasks.db` or use Supabase).

**Q: Can I use this without DeepSeek?**  
A: Currently yes, but you’d need to modify the extraction logic to use another compatible API.

---

## 📬 Contact

For questions, reach out via GitHub Issues.