import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()


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
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


threading.Thread(target=start_web_server, daemon=True).start()


intents = discord.Intents.default()
intents.members = True
intents.message_content = True


class MyBot(commands.Bot):
    async def setup_hook(self):
        for cog in COGS:
            try:
                await self.load_extension(cog)
                print(f"Loaded {cog}")
            except Exception as e:
                print(f"Failed to load {cog}: {e}")

        try:
            guild = discord.Object(id=1441189523689312307)

            self.tree.copy_global_to(guild=guild)

            synced = await self.tree.sync(guild=guild)

            print(
                f"Synced {len(synced)} slash commands "
                f"to guild {guild.id}."
            )

        except Exception as e:
            print(f"Slash sync error: {type(e).__name__}: {e}")


bot = MyBot(
    command_prefix="!",
    intents=intents
)


COGS = [
    "cogs.activation",
    "cogs.roles",
    "cogs.violations",
    "cogs.gv_roles",
    "cogs.announcements",
    "cogs.code",
]


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")


async def main():
    token = os.getenv("TOKEN")

    if not token or token == "PUT_BOT_TOKEN_HERE":
        raise RuntimeError("ضع TOKEN البوت داخل متغير TOKEN")

    await bot.start(token)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
