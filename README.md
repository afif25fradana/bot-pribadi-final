# 🤖 My Personal Finance Bot 🤖

👋 Welcome to my personal finance bot! This is a hobby project I've poured my passion into, creating a simple yet powerful Telegram bot to help me (and hopefully you!) manage finances with ease. It's designed to be intuitive, visually appealing, and packed with features to give a clear picture of financial health.

Think of this bot as my personal financial assistant, always ready to help me stay on top of my budget and make informed financial decisions.

---

✨ **What's New in v2.0.0?** ✨

*   **🚀 Enhanced User Interface**: A completely redesigned, visually appealing interface with interactive buttons for a seamless user experience.
*   **📊 Advanced Reporting**: More detailed and insightful reports, including category breakdowns, financial health status, and performance comparisons.
*   **⚡ Improved Performance**: Optimized code for faster response times and more efficient data processing.
*   **🛡️ Robust Error Handling**: Better error handling and auto-reconnection to ensure the bot is always available when you need it.
*   **⚙️ Comprehensive Health Checks**: A new health check script to easily diagnose and troubleshoot any issues.

---

✨ **Key Features** ✨

*   **✍️ Easy Transaction Logging**: Quickly record income and expenses with simple commands.
    *   `/masuk [jumlah] #[kategori] [keterangan]`
    *   `/keluar [jumlah] #[kategori] [keterangan]`
*   **📊 Monthly Cash Flow Reports**: Get a clear summary of your income, expenses, and current balance for the month.
    *   `/laporan`
*   **📈 Spending Comparison**: Compare this month's spending against last month's to identify trends and stay on budget.
    *   `/compare`
*   **🔒 Private & Secure**: Restricted access to ensure your financial data remains confidential.
*   **💡 Interactive & User-Friendly**: A rich interface with buttons, tips, and helpful guides to make financial tracking easy and enjoyable.

---

🚀 **Quick Start Guide** 🚀

1.  **Talk to the Bot**: Open Telegram and start a chat with the bot.
2.  **Start Chatting**: Send `/start` to get a welcome message and see the available commands.
3.  **Record Transactions**:
    *   To add income: `/masuk 1000000 #gaji Bonus`
    *   To add an expense: `/keluar 50000 #makanan Makan siang`
4.  **Check Reports**:
    *   For a monthly summary: `/laporan`
    *   To compare spending: `/compare`

---

🛠️ **Tech Stack** 🛠️

*   **Python**: The core language for the bot's logic.
*   **`python-telegram-bot`**: For seamless integration with the Telegram API.
*   **`gspread`**: To connect to Google Sheets for data storage.
*   **`pandas`**: For powerful data analysis and report generation.
*   **Flask**: To handle webhooks and keep the bot running smoothly.
*   **Logging**: Comprehensive error logging for easy troubleshooting.
*   **Environment Variables**: Secure configuration management with `.env` support.

---

⚙️ **Setup Instructions** ⚙️

To set up your own personal finance bot, you'll need:

1.  **Telegram Bot Token**: Get one from BotFather on Telegram.
2.  **Google Cloud Project & Service Account**:
    *   Enable the Google Sheets API.
    *   Create a service account and download its JSON credentials.
    *   Share your Google Sheet with the service account's email address.
3.  **Environment Variables**: Set these up in your deployment environment:
    *   `TELEGRAM_TOKEN`: Your bot's token.
    *   `GSPREAD_CREDENTIALS`: The content of your service account JSON file.
    *   `SPREADSHEET_NAME`: The name of your Google Sheet.
    *   `ALLOWED_USER_ID`: Your Telegram user ID to restrict access.

---

💖 **Why I Built This** 💖

I created this project to provide a simple, accessible, and powerful tool for managing personal finances. It's been a rewarding journey, and I hope it inspires you to take control of your financial future.

Happy tracking! 💸

---

## 🔒 Security

This bot is designed with security in mind. For a detailed overview of the security features and best practices, please see the [Security Policy](SECURITY.md).
