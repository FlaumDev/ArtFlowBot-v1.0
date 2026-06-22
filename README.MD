# 🎨 ArtFlow Telegram Bot

A Telegram bot designed for automating registration processes for creative competitions and festivals.

The bot allows participants to submit applications, manage their requests, and interact with the competition system through a convenient Telegram interface.

## 🚀 Features

### 📝 Registration System
- Step-by-step participant registration
- Collects all required information:
  - City
  - Team / organization name
  - Performance name
  - Performance genre
  - Number of participants
  - Age category
  - Performance duration
  - Supervisor information
  - Contact details
  - Email address

### 📋 Application Management
- Saving applications to a database
- Viewing submitted applications
- Tracking application status
- Support for multiple applications per user

### 🗄 Database
- SQLite database integration
- Separate tables for:
  - Applications
  - Participants
- Relationship between applications and participants using foreign keys

### 🎛 User Interface
- Interactive Telegram inline keyboards
- Navigation between sections
- User-friendly registration flow

---

## 🛠 Technologies

- Python 3
- pyTelegramBotAPI (TeleBot)
- SQLite
- Git
- PyCharm

---

## 📂 Project Structure
ArtFlowBot/
│
├── main.py              # Bot initialization and polling
├── loader.py            # Telegram bot configuration
├── config.py            # Environment variables and token
│
├── database.py          # Database connection and SQL queries
├── storage.py           # Temporary user data storage
│
├── commands.py          # Telegram commands (/start, /info)
├── callbacks.py         # Inline button handlers
├── registration.py      # Registration process logic
├── keyboards.py         # Telegram inline keyboards
│
└── ArtFlow.db           # SQLite database

---

## ⚙️ Installation

Clone the repository:
git clone https://github.com/your-username/ArtFlowBot.git

Install dependencies:
pip install pyTelegramBotAPI

Create a config.py file:
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

Run the bot:
python main.py

_---

## 🔐_ Security

The Telegram bot token is stored separately from the main code.

For production use, it is recommended to store sensitive data using environment variables.

---

## 📈 Future Improvements

Planned features:

- Admin panel for organizers
- Application approval system
- Notifications about application status changes
- File upload system for music tracks
- Pagination for multiple user applications
- MySQL/PostgreSQL migration
- Web dashboard for competition management

---

## 👨‍💻 Author

Created by Nikita Flyaum

A personal project focused on backend development, database design, and Telegram bot development.