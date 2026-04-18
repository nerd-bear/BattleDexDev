# BattleDex Server Operations Guide

This guide explains how to manage the full BattleDex bot on a Linux server, including:

- starting and stopping the bot
- checking logs
- updating code safely
- protecting `.env` and `cards.db`
- backing up important files
- recovering from common problems

This is written for the current setup:

- Ubuntu server
- Python virtual environment at `.venv`
- bot started with `systemd`
- project located at `/home/battledex/BattleDexDev`
- service name: `battledex`

---

## 1. Project layout

Expected layout:

```text
/home/battledex/BattleDexDev/
├── .env
├── .venv/
├── assets/
├── bot.py
├── cards.db
├── cogs/
├── config.py
├── data/
├── database.py
├── models.py
├── services/
└── views/
```

Important files:

- `.env` → secrets like the Discord bot token
- `cards.db` → the live SQLite database
- `data/card.json` → card definitions and seed data
- `bot.py` → app entry point
- `/etc/systemd/system/battledex.service` → service config

---

## 2. The golden rule for updates

Never let Git overwrite these runtime files:

- `.env`
- `cards.db`

Those files belong to the server, not to the codebase.

### Best practice
Treat these as server-local files and make sure they are ignored by Git.

---

## 3. One-time Git protection setup

Run these inside the project folder:

```bash
cd /home/battledex/BattleDexDev
```

### 3.1 Add a `.gitignore`
Create or edit `.gitignore`:

```bash
nano .gitignore
```

Put this in it:

```gitignore
.env
.venv/
cards.db
__pycache__/
*.pyc
```

Save it.

### 3.2 If `.env` or `cards.db` were already tracked by Git
You need to untrack them once:

```bash
git rm --cached .env cards.db
```

If one of them was never tracked, Git may warn about it. That is fine.

Then commit that change:

```bash
git add .gitignore
git commit -m "Stop tracking local runtime files"
```

Push it to GitHub:

```bash
git push
```

After that, future pulls should not try to replace `.env` or `cards.db`.

---

## 4. Safe update workflow

Use this every time you update the bot.

### 4.1 Go to the project
```bash
cd /home/battledex/BattleDexDev
```

### 4.2 Check for local changes
```bash
git status
```

You want `.env` and `cards.db` to be ignored, not showing as tracked changes.

### 4.3 Stop the bot before updating
```bash
sudo systemctl stop battledex
```

### 4.4 Pull the latest code
```bash
git pull origin main
```

If your branch is not `main`, use the correct branch name.

### 4.5 Activate the venv
```bash
source .venv/bin/activate
```

### 4.6 Install or update dependencies
If you have a `requirements.txt`:

```bash
pip install -r requirements.txt
```

If you do not yet have one, create it once:

```bash
pip freeze > requirements.txt
```

Then commit `requirements.txt` to Git.

### 4.7 Start the bot again
```bash
sudo systemctl start battledex
```

### 4.8 Check status
```bash
sudo systemctl status battledex
```

### 4.9 Watch logs
```bash
journalctl -u battledex -f
```

---

## 5. Daily management commands

### Start the bot
```bash
sudo systemctl start battledex
```

### Stop the bot
```bash
sudo systemctl stop battledex
```

### Restart the bot
```bash
sudo systemctl restart battledex
```

### Check if the bot is running
```bash
sudo systemctl status battledex
```

### Enable auto-start on boot
```bash
sudo systemctl enable battledex
```

### Disable auto-start on boot
```bash
sudo systemctl disable battledex
```

### View live logs
```bash
journalctl -u battledex -f
```

### View recent logs
```bash
journalctl -u battledex -n 100 --no-pager
```

---

## 6. Recommended `systemd` service file

Path:

```text
/etc/systemd/system/battledex.service
```

Contents:

```ini
[Unit]
Description=BattleDex Discord Bot
After=network.target

[Service]
User=battledex
WorkingDirectory=/home/battledex/BattleDexDev
EnvironmentFile=/home/battledex/BattleDexDev/.env
ExecStart=/home/battledex/BattleDexDev/.venv/bin/python /home/battledex/BattleDexDev/bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

After editing the service file, always run:

```bash
sudo systemctl daemon-reload
sudo systemctl restart battledex
```

---

## 7. Environment file rules

Your `.env` should look like this:

```env
BOT_TOKEN=your_real_token_here
```

Rules:

- no spaces around `=`
- no extra quotes unless truly needed
- keep `.env` out of Git
- never paste the token into public chat, screenshots, or commits

### If you ever leak the token
Immediately reset it in the Discord Developer Portal, then update `.env`.

After updating `.env`:

```bash
sudo systemctl restart battledex
```

---

## 8. Database safety rules

Your live database is:

```text
/home/battledex/BattleDexDev/cards.db
```

Rules:

- do not commit it to Git
- do not delete it during deploys
- back it up before major updates
- stop the bot before copying it for a clean backup

### Safe manual backup
```bash
cd /home/battledex/BattleDexDev
sudo systemctl stop battledex
cp cards.db cards.db.backup
sudo systemctl start battledex
```

### Timestamped backup
```bash
cp /home/battledex/BattleDexDev/cards.db /home/battledex/BattleDexDev/cards-$(date +%F-%H%M%S).db
```

### Restore from backup
Stop the bot first:

```bash
sudo systemctl stop battledex
cp cards.db.backup cards.db
sudo systemctl start battledex
```

---

## 9. Stronger update pattern for zero-risk local files

This is the neatest structure long term.

### Keep code and runtime data separate

Instead of storing everything directly in the repo folder forever, move runtime data to a separate folder later:

```text
/home/battledex/battledex-data/
├── .env
└── cards.db
```

Then update your service file to use:

```ini
EnvironmentFile=/home/battledex/battledex-data/.env
WorkingDirectory=/home/battledex/BattleDexDev
```

And update `config.py` so the database path points to:

```python
DATABASE_PATH = "/home/battledex/battledex-data/cards.db"
```

That way:
- Git updates only touch code
- secrets and database live outside the repo
- deploys become much safer

This is highly recommended once the bot is stable.

---

## 10. How to update without breaking `.env` and `cards.db`

### Best simple method
Use this exact sequence:

```bash
cd /home/battledex/BattleDexDev
git status
sudo systemctl stop battledex
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl start battledex
sudo systemctl status battledex
journalctl -u battledex -n 50 --no-pager
```

### What should NOT happen
You should not:
- delete the whole project folder before every update
- reclone the repo every time
- store secrets only in `config.py`
- commit `cards.db`
- run production only from a manually started terminal

---

## 11. First-time deploy checklist

Use this once on a fresh server.

### Install packages
```bash
sudo apt update
sudo apt install python3 python3.12-venv python3-pip git -y
```

### Clone repo
```bash
cd /home/battledex
git clone https://github.com/nerd-bear/BattleDexDev
cd BattleDexDev
```

### Create `.env`
```bash
nano .env
```

Add:
```env
BOT_TOKEN=your_token_here
```

### Create venv
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install dependencies
```bash
pip install disnake python-dotenv
```

Or, if you have `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Test manually
```bash
python bot.py
```

If the bot connects, stop it with `Ctrl+C`.

### Create service file
```bash
sudo nano /etc/systemd/system/battledex.service
```

Paste the service contents from section 6.

### Enable and start
```bash
sudo systemctl daemon-reload
sudo systemctl enable battledex
sudo systemctl start battledex
sudo systemctl status battledex
```

---

## 12. Recommended Git workflow

### On your local dev machine
Make changes, commit, push:

```bash
git add .
git commit -m "Describe the update"
git push origin main
```

### On the server
Pull and restart:

```bash
cd /home/battledex/BattleDexDev
sudo systemctl stop battledex
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl start battledex
```

---

## 13. If `git pull` complains about local changes

Check:

```bash
git status
```

If `.env` or `cards.db` are the problem, it means they are still being tracked.

Fix once:

```bash
git rm --cached .env cards.db
git add .gitignore
git commit -m "Ignore runtime files"
git push
```

If only code files are changed and you want to discard them:

```bash
git restore .
```

If files are staged and you want to unstage them:

```bash
git restore --staged .
```

---

## 14. Useful troubleshooting

### Bot service won't start
Check:
```bash
sudo systemctl status battledex --no-pager -l
sudo journalctl -xeu battledex.service --no-pager
```

### Bot works manually but not in `systemd`
Usually one of these:
- bad `EnvironmentFile`
- wrong username in service file
- wrong `ExecStart` path
- bad `.env` formatting
- missing permissions

### Token login fails
Check:
- `.env` exists
- variable name is exactly `BOT_TOKEN`
- no spaces around `=`
- token is the current bot token, not client secret

### Dependency import error
Install inside the venv:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Database seems reset
Likely cause:
- wrong working directory
- wrong database path
- repo folder got replaced
- `cards.db` was deleted or overwritten

Always confirm:
```bash
ls -l /home/battledex/BattleDexDev/cards.db
```

---

## 15. Recommended improvements for a cleaner production setup

These are worth doing next:

### Add a `requirements.txt`
From inside the venv:

```bash
pip freeze > requirements.txt
```

Commit it.

### Move runtime files outside the repo
Recommended:
```text
/home/battledex/battledex-data/.env
/home/battledex/battledex-data/cards.db
```

### Add automated backups
For example, a simple cron job that copies `cards.db` every night.

### Rotate secrets if exposed
If a token was ever committed or pasted publicly, reset it.

### Reboot after kernel updates
Your server showed a pending kernel update. Reboot when convenient:

```bash
sudo reboot
```

Then reconnect and verify:

```bash
sudo systemctl status battledex
```

---

## 16. Clean operator routine

This is the practical routine to follow.

### To update the bot
```bash
cd /home/battledex/BattleDexDev
git status
sudo systemctl stop battledex
cp cards.db cards.db.backup
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl start battledex
sudo systemctl status battledex
journalctl -u battledex -n 50 --no-pager
```

### To monitor the bot
```bash
sudo systemctl status battledex
journalctl -u battledex -f
```

### To recover from a bad update
```bash
cd /home/battledex/BattleDexDev
sudo systemctl stop battledex
cp cards.db.backup cards.db
git log --oneline -5
git checkout <older_commit_hash>
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl start battledex
```

---

## 17. Final rules to keep things neat

- keep secrets in `.env`, never in source
- keep `cards.db` out of Git
- stop the bot before updates
- back up `cards.db` before risky changes
- use `systemd` for 24/7 uptime
- use full paths in the service file
- do not delete and reclone the project for normal updates
- check logs after every deploy

If you follow those rules, updates stay clean and your live data stays safe.
