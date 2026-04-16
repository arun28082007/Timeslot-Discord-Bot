# 🌍 Discord Timezone Scheduler Bot

A smart Discord bot that helps teams, coding communities, and global friend groups find the best meeting time across different time zones.

Built for communities where members live in different countries and scheduling becomes frustrating. Instead of manually converting time zones, this bot lets everyone set their timezone, add when they are free, and instantly finds the best overlapping time slots. 0

---

## ✨ Features

- 🌐 Set your personal timezone
- ⏰ Add your available hours in your own local time
- 🤝 Automatically detect overlapping free slots
- 📅 Suggest the best meeting times for multiple members
- 👤 View or clear your saved availability
- ⚡ Simple slash commands
- 💾 Persistent data storage using JSON

---

## 📌 Commands

| Command | Description |
|--------|-------------|
| `/settimezone` | Set your timezone |
| `/free <start> <end>` | Add when you're free (your timezone) |
| `/findtime` | Find the best meeting times |
| `/myavailability view` | Show your saved slots |
| `/myavailability clear` | Clear your slots |

---

## 🚀 Example Workflow

1. Every member runs:

```bash
/settimezone Asia/Kolkata

2. Add free time:



/free 6pm 10pm

3. Find best meeting time:



/findtime

The bot will return the best overlapping slots for everyone. 


---

🛠️ Tech Stack

Python

discord.py

pytz

aiohttp


Dependencies from your project: 


---

📂 Project Structure

.
├── bot.py
├── requirements.txt
└── bot_data.json


---

⚙️ Installation

1. Clone the Repository

git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name

2. Install Dependencies

pip install -r requirements.txt

3. Add Bot Token

Create an environment variable:

DISCORD_BOT_TOKEN=your_token_here

4. Run the Bot

python bot.py


---

🔐 Environment Variable

Variable	Description

DISCORD_BOT_TOKEN	Your Discord bot token



---

💡 Why I Built This

My Discord community has members from different time zones, and finding a time for meetings or collaboration was always painful.

So I built this bot to solve that problem.

If the project grows, it becomes startup-worthy.
If not, it's still a strong resume-worthy project.


---

📈 Future Improvements

Weekly recurring schedules

Better UI embeds

Database support (MongoDB / PostgreSQL)

Smart ranking of best time slots

Web dashboard

Google Calendar integration

Voting system for suggested slots



---

🤝 Contributing

Pull requests and ideas are welcome.


---


👨‍💻 Author
Built by Arun Anand 
