# 💰 My Personal Finance Bot 🤖

👋 Hey there! Welcome to my little corner of financial organization! This project is a super handy Telegram bot I built to keep track of my personal finances. No more messy spreadsheets or forgotten transactions – just a quick chat with my bot, and everything's neatly recorded.

It's designed to be simple, intuitive, and give me a clear picture of where my money goes (and comes from!). Think of it as my personal financial assistant, always ready to help me stay on top of my budget.

---

✨ **What can this bot do for you (or me!)?** ✨

*   **✍️ Easy Transaction Logging**: Quickly record income and expenses with simple commands. Just tell the bot the amount, category, and a short description.
    *   ` /masuk [jumlah] #[kategori] [keterangan]`
    *   ` /keluar [jumlah] #[kategori] [keterangan]`
*   **📊 Monthly Cash Flow Reports**: Get a clear summary of income, expenses, and current balance for the month. It even breaks down spending by category!
    *   ` /laporan`
*   **📈 Spending Comparison**: See how this month's spending stacks up against last month's. Great for spotting trends and keeping those budgets in check!
    *   ` /compare`
*   **🔒 Private & Secure**: Only I (or anyone with my `ALLOWED_USER_ID`) can interact with the bot, keeping my financial data safe.

---

🚀 **How I Use It (Quick Start for You!)** 🚀

1.  **Talk to the Bot**: Open Telegram and find my bot.
2.  **Start Chatting**: Send `/start` to get a friendly greeting and see the available commands.
3.  **Record Transactions**:
    *   To add income: `/masuk 1000000 #gaji Bonus dari kerja keras!`
    *   To add expense: `/keluar 50000 #makanan Makan siang enak`
4.  **Check Reports**:
    *   For monthly summary: `/laporan`
    *   To compare spending: `/compare`

---

🛠️ **Under the Hood (For the Tech-Savvy!)** 🛠️

This bot is powered by:

*   **Python**: The main language for the bot's logic.
*   **`python-telegram-bot`**: The awesome library that makes interacting with Telegram a breeze.
*   **`gspread`**: For seamless integration with Google Sheets, where all my transaction data lives.
*   **`pandas`**: My go-to for crunching numbers and generating those insightful financial reports.
*   **Flask**: To handle webhooks and keep the bot running smoothly.
*   **Logging**: Comprehensive error logging to help troubleshoot issues.
*   **Environment Variables**: Secure configuration management with `.env` support.

---

⚙️ **Setup (If You Want Your Own!)** ⚙️

Want to set up your own personal finance bot? Here's what you'll need:

1.  **Telegram Bot Token**: Get one from BotFather on Telegram.
2.  **Google Cloud Project & Service Account**:
    *   Enable Google Sheets API.
    *   Create a service account and download its JSON credentials.
    *   Share your Google Sheet (e.g., named "Catatan Keuangan") with the service account's email address.
3.  **Environment Variables**: Set these up in your deployment environment (e.g., Heroku, Vercel, or locally):
    *   `TELEGRAM_TOKEN`: Your bot's token.
    *   `GSPREAD_CREDENTIALS`: The content of your service account JSON file (as a single-line string).
    *   `SPREADSHEET_NAME`: The exact name of your Google Sheet (default: `Catatan Keuangan`).
    *   `ALLOWED_USER_ID`: Your Telegram user ID (as an integer) to restrict access to only you.

---

💖 **Why I Made This** 💖

I created this project because I wanted a simple, accessible way to manage my money without feeling overwhelmed. It's been a fantastic journey learning and building something truly useful for myself. I hope it inspires you to take control of your finances too!

Happy tracking! 💸
