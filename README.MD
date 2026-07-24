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

### 🔗 ArtFlowWeb Deep Links
- Supports links from ArtFlowWeb in the format `https://t.me/{BOT_USERNAME}?start=competition_{id}`
- Opens only existing published competitions
- Keeps the existing registration flow and saves the selected competition with the application

### 🔔 Application Notifications
- After a new application is saved, the bot can send the application data to an organizer in Telegram and by email.
- Notifications are sent only after the database save is successful.
- Telegram and email notifications are independent: a failure in one channel does not cancel the application or block the other channel.

Required Railway variables for Telegram notifications:

```env
APPLICATION_RECIPIENT_CHAT_ID=
```

The organizer must open the bot and press Start at least once before the bot can send a private Telegram message. To find the organizer chat id, ask the organizer to open a trusted Telegram ID bot, for example `@userinfobot`, and copy the numeric user id. For a private chat, this id is the value for `APPLICATION_RECIPIENT_CHAT_ID`.

Required Railway variables for email notifications:

```env
APPLICATION_RECIPIENT_EMAIL=
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
SMTP_USE_SSL=false
SMTP_USE_STARTTLS=true
```

Use `SMTP_USE_STARTTLS=true` for most providers on port `587`. Use `SMTP_USE_SSL=true` and `SMTP_PORT=465` only when the SMTP provider requires SSL from the start.

To check Telegram notification delivery, set `APPLICATION_RECIPIENT_CHAT_ID`, restart the Railway service, open the bot as the organizer with `/start`, and submit a test application. To check email delivery, set the SMTP variables, restart the Railway service, submit a test application, and verify that the email subject has the format `Новая заявка ArtFlow №<application_id> — <competition_name>`.

### ⚡ Public Telegram Commands
The bot supports these public commands:

```text
/start - open the main menu
/competitions - show competitions
/faq - show FAQ
/contact - contact the organizer
/help - show command help
```

Deep links such as `/start competition_<id>` continue to open published competitions from ArtFlowWeb.

Commands to add manually in BotFather:

```text
start - открыть главное меню
competitions - посмотреть конкурсы
faq - частые вопросы
contact - связаться с организатором
help - помощь по боту
```

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
