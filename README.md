# Personal Finance Telegram Bot

This is a Telegram bot designed to help you track your personal finances by recording income and expenses, generating monthly reports, and comparing spending between months. It integrates with Google Sheets to store your financial data.

## Features

*   **Record Transactions**: Easily log your income and expenses directly from Telegram.
    *   `/masuk [amount] #[category] [description]` (e.g., `/masuk 100000 #gaji bonus bulan ini`)
    *   `/keluar [amount] #[category] [description]` (e.g., `/keluar 50000 #makanan makan siang`)
*   **Monthly Cash Flow Report**: Get a summary of your income, expenses, and current balance for the current month.
    *   `/laporan`
*   **Spending Comparison**: Compare your expenses between the current and previous month, broken down by category.
    *   `/compare`
*   **Restricted Access**: The bot can be configured to only respond to a specific Telegram user ID for privacy and security.

## Setup and Configuration

To run this bot, you need to set up several environment variables and configure Google Sheets API access.

### 1. Google Sheets Setup

1.  **Create a Google Sheet**: Create a new Google Sheet (e.g., named "Catatan Keuangan") in your Google Drive.
2.  **Create a "Transaksi" Worksheet**: Inside your spreadsheet, ensure you have a worksheet named `Transaksi`. This sheet should have the following header columns in the first row: `Tanggal`, `Tipe`, `Jumlah`, `Kategori`, `Deskripsi`.
3.  **Enable Google Sheets API**:
    *   Go to the [Google Cloud Console](https://console.cloud.google.com/).
    *   Create a new project or select an existing one.
    *   Navigate to "APIs & Services" > "Enabled APIs & Services".
    *   Search for "Google Sheets API" and enable it.
4.  **Create Service Account Credentials**:
    *   In the Google Cloud Console, go to "APIs & Services" > "Credentials".
    *   Click "Create Credentials" > "Service Account".
    *   Give it a name (e.g., `telegram-bot-service`).
    *   Grant it the "Editor" role (or a more specific role if you prefer, like "Sheets Editor") for your project.
    *   After creation, click on the service account email, then go to the "Keys" tab.
    *   Click "Add Key" > "Create new key" > "JSON".
    *   A JSON file will be downloaded. This file contains your service account credentials.
5.  **Share the Spreadsheet with Service Account**:
    *   Open your Google Sheet ("Catatan Keuangan").
    *   Click the "Share" button.
    *   Copy the `client_email` from the downloaded JSON credentials file (it looks like an email address).
    *   Paste this email into the "Share with people and groups" field and grant it "Editor" access to your spreadsheet.

### 2. Environment Variables

Set the following environment variables in your deployment environment (e.g., Heroku, Docker, `.env` file for local development):

*   `TELEGRAM_TOKEN`: Your Telegram Bot API Token, obtained from BotFather.
*   `GSPREAD_CREDENTIALS`: The entire content of the JSON file you downloaded for your Google Service Account credentials. **Ensure this is a single-line string without newlines or escaped newlines if your deployment method requires it.** For example, you might need to use `cat your-credentials.json | tr -d '\n'` to remove newlines.
*   `SPREADSHEET_NAME`: The exact name of your Google Spreadsheet (default: `Catatan Keuangan`).
*   `ALLOWED_USER_ID`: (Optional) Your Telegram user ID (a number) if you want the bot to only respond to you. If not set or invalid, the bot will be restricted to no one. You can get your user ID by forwarding a message to the `@userinfobot` on Telegram.

Example `.env` file for local development:

```
TELEGRAM_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
GSPREAD_CREDENTIALS='{"type": "service_account", "project_id": "...", "private_key_id": "...", "private_key": "...", "client_email": "...", "client_id": "...", "auth_uri": "...", "token_uri": "...", "auth_provider_x509_cert_url": "...", "client_x509_cert_url": "...", "universe_domain": "..."}'
SPREADSHEET_NAME=Catatan Keuangan
ALLOWED_USER_ID=YOUR_TELEGRAM_USER_ID
```

## Running the Bot

### Local Development

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Set Environment Variables**: Create a `.env` file as described above, or set them directly in your shell.
3.  **Run the Flask App**:
    ```bash
    python main.py
    ```
    *Note: For local testing with webhooks, you'll need a tool like `ngrok` to expose your local server to the internet.*

### Deployment (e.g., Heroku)

This project is configured for deployment using a `Procfile` and `requirements.txt`.

1.  **Ensure `requirements.txt` is up-to-date**:
    ```bash
    pip freeze > requirements.txt
    ```
2.  **Configure Environment Variables**: Set the `TELEGRAM_TOKEN`, `GSPREAD_CREDENTIALS`, `SPREADSHEET_NAME`, and `ALLOWED_USER_ID` (optional) as config vars in your Heroku app settings.
3.  **Set up Webhook**: After deployment, you need to tell Telegram where to send updates. Replace `YOUR_APP_URL` with your deployed application's URL.
    ```bash
    https://api.telegram.org/bot<YOUR_TELEGRAM_TOKEN>/setWebhook?url=YOUR_APP_URL/webhook
    ```
    You can open this URL in your browser or use `curl`.

The `Procfile` specifies `web: gunicorn main:app`, which will run the Flask application using Gunicorn. Ensure your deployment environment supports asynchronous workers for Gunicorn (e.g., `gunicorn --worker-class uvicorn.workers.UvicornWorker main:app` if you were to run it manually, though Heroku often handles this).

## Project Structure

*   `main.py`: The main Python script containing the bot's logic, Flask application, and Telegram handlers.
*   `Procfile`: Defines the process types for deployment platforms like Heroku.
*   `requirements.txt`: Lists Python dependencies.
