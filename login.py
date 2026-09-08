"""
One-time interactive login for the Premium account (see main.py/scheduler.py).

main.py's own process has no attached tty (systemd/podman, Restart=always),
so it can never complete Telegram's interactive phone-code/2FA prompt
itself. Run this once, interactively, e.g. from nyx:

    podman run --rm -it --network pgnet \\
      -v ~/projects/tg-mn:/app:Z -w /app \\
      --env-file ~/projects/tg-mn/.env \\
      docker.io/library/python:3.12-slim \\
      sh -c "pip install --no-cache-dir -r requirements.txt && python3 login.py"

It saves the session file into the current directory, which is the same
workdir main.py/scheduler.py use - so the regular service can then just
reuse it on every subsequent start without any further interaction.
"""

import asyncio

from pyrogram import Client

import config


async def main():
    app = Client(
        name="Premium",
        api_id=config.API,
        api_hash=config.HASH,
        phone_number=config.NUMBER,
    )
    async with app:
        me = await app.get_me()
        print(f"Logged in as {me.first_name} ({me.id}) - session saved, tg-mn can now start normally.")


if __name__ == "__main__":
    asyncio.run(main())
