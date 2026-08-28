import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

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
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Slash sync error: {e}")

async def main():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"Loaded {cog}")
        except Exception as e:
            print(f"Failed to load {cog}: {e}")

    token = os.getenv("TOKEN")
    if not token or token == "PUT_BOT_TOKEN_HERE":
        raise RuntimeError("ضع TOKEN البوت داخل ملف .env")
    await bot.start(token)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
