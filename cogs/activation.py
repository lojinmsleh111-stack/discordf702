import re
import discord
from discord.ext import commands

from utils.config import (
    ACTIVATION_CHANNELS,
    ACTIVATION_ROLE_IDS,
    IDENTITY_START,
)


class Activation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # تجاهل البوتات والرسائل خارج السيرفر
        if message.author.bot or not message.guild:
            return

        # التأكد أن الرسالة في روم التفعيل
        if message.channel.id not in ACTIVATION_CHANNELS:
            return

        username = message.content.strip()

        # اسم Roblox فقط
        if (
            not username
            or len(username) > 32
            or not re.fullmatch(r"[A-Za-z0-9_.-]+", username)
        ):
            try:
                await message.delete()
            except discord.HTTPException:
                pass
            return

        member = message.author

        # إعطاء رتب التفعيل
        for role_id in ACTIVATION_ROLE_IDS:
            role = message.guild.get_role(role_id)

            if role:
                try:
                    await member.add_roles(
                        role,
                        reason="Activation"
                    )
                except discord.HTTPException:
                    pass

        # الحصول على الرقم التالي
        number = await self._next_identity_number(message.guild)

        # الزخرفة
        nickname = f"AN | {username} | {number}"

        try:
            await member.edit(
                nick=nickname,
                reason="Activation identity"
            )
        except discord.HTTPException:
            pass

        # حذف رسالة العضو
        try:
            await message.delete()
        except discord.HTTPException:
            pass

        # إرسال القبول في الخاص فقط
        try:
            await member.send(
                f"تم قبول تفعيلك ✅\n\n"
                f"اسم Roblox: `{username}`\n"
                f"هويتك: `{number}`"
            )
        except discord.Forbidden:
            # الخاص مقفل عند العضو
            pass
        except discord.HTTPException:
            pass

    async def _next_identity_number(self, guild: discord.Guild) -> int:
        used = set()

        pattern = re.compile(r"\|\s*(\d+)\s*$")

        for member in guild.members:
            if member.nick:
                match = pattern.search(member.nick)

                if match:
                    used.add(int(match.group(1)))

        number = IDENTITY_START

        while number in used:
            number += 1

        return number


async def setup(bot):
    await bot.add_cog(Activation(bot))
