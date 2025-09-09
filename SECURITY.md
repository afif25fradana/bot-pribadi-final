# 🔒 My Personal Security Policy

As the sole developer and maintainer of this hobby project, I've put a lot of thought into making sure your financial data stays safe and private. This document outlines the security features and best practices I've implemented for my Personal Finance Bot.

## 🔑 Key Security Features I've Built In

1.  **Private Access Control**:
    *   This bot is designed for my personal use (and yours, if you choose to deploy it for yourself!). Access is strictly limited to a single, authorized Telegram user ID, which you configure via the `ALLOWED_USER_ID` environment variable.
    *   Any messages from unauthorized users are ignored, and I've set up logging to catch and warn about such attempts.

2.  **Secure Credential Management**:
    *   All sensitive information, including the Telegram bot token, Google Sheets credentials, and your user ID, is managed through environment variables. This is a crucial practice to prevent hardcoding sensitive data directly into the source code, which is a major security risk.
    *   The `.gitignore` file is carefully configured to prevent the `.env` file (where these variables are typically stored locally) from ever being accidentally committed to a public repository.

3.  **No Data Storage on the Server**:
    *   I designed this bot to be stateless. This means it doesn't store any of your financial data on the server where it's hosted.
    *   All transaction data is securely transmitted to and stored in your private Google Sheet, giving you full control over your data.

4.  **Secure Communication**:
    *   The bot leverages the official Telegram API, which encrypts all communication between your Telegram app and the bot.
    *   The connection to Google Sheets is also encrypted, ensuring your data is protected during transit.

## 🚀 Best Practices for Your Secure Deployment

To ensure the security of your bot, please follow these best practices:

1.  **NEVER Share Your Credentials**:
    *   Seriously, never commit your `.env` file or any files containing your credentials to a public repository like GitHub.
    *   Always use your hosting provider's recommended method for managing environment variables (e.g., Heroku Config Vars, Vercel Environment Variables).

2.  **Use a Strong, Unique Bot Token**:
    *   Treat your Telegram bot token like a password. If it's ever exposed, regenerate it immediately from BotFather on Telegram.

3.  **Secure Your Google Sheet**:
    *   Ensure that your Google Sheet is not publicly accessible.
    *   Only share it with the service account email address you created for the bot.

4.  **Monitor Bot Activity**:
    *   I've included logging to help you monitor the bot's activity. Regularly check the logs for any suspicious behavior or unauthorized access attempts.

## 🚨 Reporting a Vulnerability

If you happen to discover a security vulnerability, please report it responsibly. Do not disclose it publicly. Instead, create a new issue in the GitHub repository with the label "security" to bring it to my attention.

I take security seriously, even in a hobby project, and will address any vulnerabilities as quickly as possible.

---

By following these guidelines, you can confidently use your Personal Finance Bot to manage your finances securely.
