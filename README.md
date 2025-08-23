# 🤖 Personal Finance Telegram Bot

Welcome to your personal finance assistant! This Telegram bot helps you effortlessly track your income and expenses, generate insightful reports, and compare your spending habits over time, all powered by Google Sheets.

## ✨ Features

Here are the powerful commands your bot understands:

*   `✍️ /masuk [jumlah] #[kategori] [keterangan]` : Easily record your income.
    *   Example: `/masuk 1000000 #gaji Bonus bulanan`
*   `✍️ /keluar [jumlah] #[kategori] [keterangan]` : Log your expenses with details.
    *   Example: `/keluar 50000 #makanan Makan siang di kafe`
*   `📊 /laporan` : Get a comprehensive financial report for the current month, including your starting balance, total income, total expenses, and final balance.
*   `📈 /compare` : Analyze your spending! Compare expenses between the current month and the previous month, broken down by category, to spot trends.

## 🚀 Setup Guide

To get your bot up and running, follow these steps to configure environment variables and set up your Google Sheet.

### 1. 📄 Google Sheet Configuration

1.  Create a new Google Sheet (e.g., name it "Catatan Keuangan").
2.  Inside this spreadsheet, create a worksheet specifically named "Transaksi".
3.  Ensure the "Transaksi" worksheet has the following exact column headers: `Tanggal`, `Tipe`, `Jumlah`, `Kategori`, `Deskripsi`.

### 2. ☁️ Google Cloud Project & Service Account

1.  Head over to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a brand new project or select an existing one.
3.  Enable the "Google Sheets API" and "Google Drive API" for your chosen project.
4.  Create a Service Account for secure access:
    *   Navigate to "IAM & Admin" > "Service Accounts".
    *   Click "Create Service Account".
    *   Give it a meaningful name and grant it the "Editor" role (or a more restrictive role if you prefer, ensuring it has full access to Google Sheets).
    *   After creation, click on the service account's email address.
    *   Go to the "Keys" tab and click "Add Key" > "Create new key".
    *   Select "JSON" and click "Create". This action will download a JSON file containing your service account credentials. Keep this file secure!
5.  Share your Google Sheet with the service account's email address (you'll find this email in the downloaded JSON file, typically under `client_email`).

### 3. 🔑 Environment Variables (e.g., for Render.com Deployment)

You'll need to set these crucial environment variables in your hosting platform's (e.g., Render.com) service settings:

*   `TELEGRAM_TOKEN`: Your unique Telegram Bot API token, which you can obtain from BotFather.
*   `GSPREAD_CREDENTIALS`: The *entire content* of the JSON key file you downloaded in step 2. **Important: This must be a single-line string without any line breaks.** You might need to escape double quotes depending on your hosting platform, but usually, pasting the raw JSON works.
*   `SPREADSHEET_NAME`: The *exact* name of your Google Sheet (e.g., `Catatan Keuangan`).
*   `ALLOWED_USER_ID`: Your personal Telegram user ID (a numerical ID) to ensure only you can interact with the bot. You can easily find this by forwarding any message to the `@userinfobot` on Telegram.

### 4. 📦 Dependencies

The bot relies on the following Python packages, listed in `requirements.txt`:

```
python-telegram-bot
gspread
oauth2client
pandas
Flask
gunicorn
```

### 5. 🚀 Deployment (e.g., on Render.com)

*   **Procfile**: The `Procfile` is essential for specifying how your web application should run:
    ```
    web: gunicorn main:app
    ```
    This command instructs platforms like Render.com to launch your Flask application using Gunicorn.
*   Ensure your Python version on your deployment platform (e.g., Render.com) matches your local development environment (Python 3.9+ is recommended).

## 💬 Usage

Once successfully deployed and configured, simply send commands to your bot on Telegram! Remember, only the `ALLOWED_USER_ID` will be authorized to interact with it.

## 💡 Future Enhancements

Based on a thorough audit, here are some exciting potential improvements for future development:

1.  **Centralized Configuration Management**: Implement a more structured configuration system (e.g., `config.ini`, `YAML`) for non-sensitive settings, while keeping sensitive data in environment variables.
2.  **Robust Logging**: Integrate Python's `logging` module for better error tracking, debugging, and configurable log outputs.
3.  **Asynchronous Gspread Operations**: Use `asyncio.to_thread()` or `loop.run_in_executor()` to run synchronous `gspread` calls in a separate thread pool, preventing blocking of the Telegram bot's asynchronous operations.
4.  **Enhanced Data Validation**: Improve input validation in `parse_message` and other functions to handle more diverse user inputs and edge cases.
5.  **Modularize Bot Logic**: Refactor command handlers into smaller, more focused modules or classes to improve code organization, readability, and maintainability as the bot grows.
6.  **User-Friendly Error Feedback**: Provide more specific and helpful error messages to the user instead of generic "Waduh, ada error saat mencatat."
7.  **Timezone Awareness**: Implement explicit UTC or user-configurable timezone handling for `datetime.datetime.now()` to ensure consistent time recording across different server locations and user preferences.
8.  **Dependency Version Pinning**: Pin exact versions of dependencies in `requirements.txt` (e.g., `python-telegram-bot==20.0.0`) to ensure consistent deployments and prevent unexpected breaking changes.
9.  **Refactor `parse_message`**: Consider using regular expressions or a more structured parsing library to make the message parsing logic more robust.
10. **Specific Spreadsheet Error Handling**: Add more granular error handling for `gspread` operations (e.g., `SpreadsheetNotFound`, `WorksheetNotFound`) to provide more informative messages or recovery mechanisms.
