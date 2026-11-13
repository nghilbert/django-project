# Skill Matchmaker

A skill exchange site built with Django.

## Requirements

- **Git**: downloads the code and tracks changes. [Install here](https://git-scm.com/downloads).
- **uv**: installs Python with the project dependencies and runs commands. [Install here](https://docs.astral.sh/uv/getting-started/installation/), or:
  - **Windows 11** (PowerShell): `winget install --id=astral-sh.uv -e`
  - **Linux**: your package manager (e.g. `sudo pacman -S uv`), or `curl -LsSf https://astral.sh/uv/install.sh | sh`

Reopen your terminal after installing.

## Setup

Run these once in a terminal (PowerShell on Windows):

1. **Download the code and install everything** (including Python 3.14):

   ```sh
   git clone https://github.com/nghilbert/django-project.git
   cd django-project
   uv sync
   ```

2. **Create your `.env` file:**

   ```sh
   cp .env.example .env
   ```

3. **Create the database:**

   ```sh
   uv run python manage.py migrate
   ```

4. **Create your admin account:**

   ```sh
   uv run python manage.py createsuperuser
   ```

   Any email works, even a fake one like `admin@example.com`. Accounts made through the site's sign-up page will need a real `@ilstu.edu` email.

## VS Code (recommended)

VS Code is recommended, but any editor works. [Install here](https://code.visualstudio.com/).

1. **File > Open Folder** and choose `django-project`.
2. Install the **recommended extensions** when prompted (or search `@recommended` in Extensions).
3. If asked for a Python interpreter, pick the one in `.venv`.

## Run

```sh
uv run python manage.py runserver
```

Open <http://127.0.0.1:8000/admin/>. Press **Ctrl+C** to stop.

`uv run` uses `.venv` automatically, so you don't need to activate it.

### Test account verification

Open <http://127.0.0.1:8000/accounts/register/> and sign up with an `@ilstu.edu` address.
Verification emails print in the terminal running the server; they aren't delivered to an inbox.
Copy the full verification URL from that terminal and open it in your browser, then log in.
The development email backend prints links without email encoding or inserted line breaks.
Resending verification prints another link in the same terminal.

### Send real emails with Gmail

Use a dedicated project Gmail account. Signup verification, resend verification, and email-change
confirmation all use the same sender. The recipient still needs an `@ilstu.edu` address.

1. Turn on **2-Step Verification** for the project Google account, then create an
   [app password](https://support.google.com/mail/answer/185833) named **Skill Matchmaker**.
   If Google does not offer app passwords, check the account restrictions on that help page.
2. Uncomment the email settings in your local `.env` and enter the project Gmail address and
   its 16-character app password **without spaces**. Do not use your Google login password.
   Keep `.env` private; never commit credentials or paste them into an issue or PR.
3. Restart `uv run python manage.py runserver`. The SMTP backend uses Gmail on port 587 with
   STARTTLS and a 10-second connection timeout. Missing SMTP credentials stop startup with
   a configuration error instead of silently falling back to console delivery.
4. Register with your own ISU address, check your inbox and spam folder, and open the link.
   Then log in. If the address already has an inactive account, use **Resend verification email**.

The link points to the app URL used during signup. For local testing, open it on the **same
computer running the server**, with the server still running. A link to `localhost` won't reach
your laptop from your phone or a teammate's computer. A shared deployment needs its own reachable
HTTPS URL and corresponding `DJANGO_ALLOWED_HOSTS` configuration.

If sending fails during signup, the account remains inactive and the page offers a resend.
Email-change failures leave the old address in place. Resend confirmations stay neutral so they
don't reveal which addresses have accounts; delivery errors are logged by type without addresses,
passwords, or verification links. Check the sender credentials and retry after fixing the issue.
Google also revokes app passwords when the account password changes.

To return to console delivery, remove or comment out `DJANGO_EMAIL_BACKEND` and restart the server.
Teammates can leave all email settings commented out until they need to test real delivery.

Run automated tests with `uv run python manage.py test`. They use in-memory email, an explicitly
selected console backend, or a mocked SMTP connection, so they do not send real emails even when
your `.env` enables Gmail. Only the manual inbox check proves delivery to an actual ISU mailbox.

## Contributing

Before starting a task, read [CONTRIBUTING.md](CONTRIBUTING.md). Tasks are on the [project board](https://github.com/users/nghilbert/projects/6).

## Project layout

| Path | Purpose |
| --- | --- |
| `config/` | Project setup: `settings.py` and `urls.py`. |
| `skill_matchmaker/` | Our app. Most code goes here. |
| `skill_matchmaker/models/` | Database tables as Python classes. |
| `skill_matchmaker/views/` | Code that handles requests and returns pages. |
| `skill_matchmaker/templates/` | HTML pages. |
| `skill_matchmaker/migrations/` | Auto-generated database changes. Don't edit by hand. |
| `skill_matchmaker/admin.py` | Adds models to the admin site. |
| `manage.py` | Runs Django commands. |
| `pyproject.toml`, `uv.lock` | Project dependencies and their exact versions. Managed by uv. |
| `.env.example` | Template for `.env`. |
| `.env` | Your local configuration. Not committed. |
| `.venv/` | Python and the project dependencies. Created by `uv sync`. Not committed. |
| `db.sqlite3` | Your local database. Not committed. |
| `.vscode/` | Shared VS Code configuration. |
| `CONTRIBUTING.md` | How we use branches and pull requests. |
