import re
import discord
from discord.ext import commands
from utils.config import ACTIVATION_CHANNELS, ACTIVATION_ROLE_IDS, IDENTITY_CHANNEL_ID, IDENTITY_START

class Activation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        if message.channel.id not in ACTIVATION_CHANNELS:
            return

        username = message.content.strip()

        # User sends username only.
        if not username or len(username) > 32 or not re.fullmatch(r"[A-Za-z0-9_.-]+", username):
            try:
                await message.delete()
            except discord.HTTPException:
                pass
            return

        member = message.author
        assigned = []
        for role_id in ACTIVATION_ROLE_IDS:
            role = message.guild.get_role(role_id)
            if role:
                try:
                    await member.add_roles(role, reason="Activation")
                    assigned.append(role)

        number = await self._next_identity_number(message.guild)
        nickname = f"AN | {username} | {number}"

        try:
            await member.edit(nick=nickname, reason="Activation identity")
        except discord.HTTPException:
            pass

        try:
            await message.delete()
        except discord.HTTPException:
            pass

        try:
            reply = await message.channel.send(
                f"تم قبول تفعيلك {member.mention} | الهوية: `{number}`"
            )
            await reply.delete(delay=5)
        except discord.HTTPException:
            pass

    async def _next_identity_number(self, guild: discord.Guild) -> int:
        # Persistent identity numbers are stored in guild attributes through a simple local file.
        # This implementation scans member nicknames to avoid duplicates after restarts.
        used = set()
        pattern = re.compile(r"\|\s*(\d+)\s*$")
        for member in guild.members:
            if member.nick:
                match = pattern.search(member.nick)
                if match:
                    used.add(int(match.group(1)))

        n = IDENTITY_START
        while n in used:
            n += 1
        return n

async def setup(bot):
    await bot.add_cog(Activation(bot))
