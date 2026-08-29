print("MAIN.PY IS RUNNING - TEST 123")
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()


# =========================
# Render Health Check
# =========================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is online!")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

    def log_message(self, format, *args):
        return


def start_web_server():
    port = int(os.getenv("PORT", 10000))

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    print(f"Health server started on port {port}")

    server.serve_forever()


threading.Thread(
    target=start_web_server,
    daemon=True
).start()


# =========================
# Discord Intents
# =========================

intents = discord.Intents.default()

intents.members = True
intents.message_content = True


# =========================
# Cogs
# =========================

COGS = [
    "cogs.activation",
    "cogs.roles",
    "cogs.violations",
    "cogs.gv_roles",
    "cogs.announcements",
    "cogs.code",
]


# =========================
# Bot
# =========================

class MyBot(commands.Bot):

    async def setup_hook(self):

        print("========== LOADING COGS ==========")

        for cog in COGS:

            try:
                await self.load_extension(cog)

                print(
                    f"LOADED: {cog}"
                )

            except Exception as e:

                print(
                    f"FAILED: {cog} | "
                    f"{type(e).__name__}: {e}"
                )

        print(
            "========== COMMANDS BEFORE SYNC =========="
        )

        commands_list = self.tree.get_commands()

        print(
            f"TOTAL COMMANDS: "
            f"{len(commands_list)}"
        )

        for command in commands_list:

            print(
                f"COMMAND FOUND: /{command.name}"
            )

        print(
            "========== GUILD SYNC =========="
        )

        guild = discord.Object(
            id=1441189523689312307
        )

        try:

            synced = await self.tree.sync(
                guild=guild
            )

            print(
                f"SYNC SUCCESS: "
                f"{len(synced)} commands"
            )

            for command in synced:

                print(
                    f"SYNCED: /{command.name}"
                )

        except Exception as e:

            print(
                f"SYNC ERROR: "
                f"{type(e).__name__}: {e}"
            )


bot = MyBot(
    command_prefix="!",
    intents=intents
)


# =========================
# Ready
# =========================

@bot.event
async def on_ready():

    print(
        "================================"
    )

    print(
        f"BOT ONLINE: "
        f"{bot.user} ({bot.user.id})"
    )

    print(
        f"CONNECTED GUILDS: "
        f"{len(bot.guilds)}"
    )

    guild = bot.get_guild(
        1441189523689312307
    )

    if guild:

        print(
            f"TARGET GUILD FOUND: "
            f"{guild.name} ({guild.id})"
        )

    else:

        print(
            "TARGET GUILD NOT FOUND"
        )

    print(
        "================================"
    )


# =========================
# Start Bot
# =========================

async def main():

    token = os.getenv("TOKEN")

    if not token:

        raise RuntimeError(
            "TOKEN environment variable is missing"
        )

    print("Starting Discord bot...")

    await bot.start(token)


if __name__ == "__main__":

    import asyncio

    asyncio.run(main())
