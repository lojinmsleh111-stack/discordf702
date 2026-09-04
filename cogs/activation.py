import re
import json
import os
import asyncio

import discord
from discord.ext import commands

from utils.config import (
    ACTIVATION_CHANNELS,
    ACTIVATION_ROLE_IDS,
)

IDENTITY_LOG_CHANNEL_ID = 1542702871135523026

# أول هوية
IDENTITY_START = 1172

# ملف حفظ العداد
IDENTITY_FILE = "identity_counter.json"


class Activation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.identity_lock = asyncio.Lock()
        self.identity_number = None

    def _load_counter(self):
        if self.identity_number is not None:
            return self.identity_number

        if not os.path.exists(IDENTITY_FILE):
            self.identity_number = IDENTITY_START
            return self.identity_number

        try:
            with open(IDENTITY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            last_id = int(data.get("last_id", IDENTITY_START - 1))

            # يمنع الرجوع لأقل من 1172
            self.identity_number = max(last_id + 1, IDENTITY_START)

            return self.identity_number

        except (ValueError, TypeError, json.JSONDecodeError, OSError):
            self.identity_number = IDENTITY_START
            return self.identity_number

    def _save_counter(self, number):
        temp_file = IDENTITY_FILE + ".tmp"

        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(
                {"last_id": number},
                f,
                ensure_ascii=False,
                indent=2
            )

        os.replace(temp_file, IDENTITY_FILE)

        # الرقم التالي
        self.identity_number = number + 1

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        # تجاهل البوتات والرسائل خارج السيرفر
        if message.author.bot or not message.guild:
            return

        # التأكد أن الرسالة في روم التفعيل
        if message.channel.id not in ACTIVATION_CHANNELS:
            return

        username = message.content.strip()

        # التأكد أن اسم Roblox صحيح
        if (
            not username
            or len(username) > 32
            or not re.fullmatch(
                r"[A-Za-z0-9_.-]+",
                username
            )
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

        # الحصول على هوية جديدة
        async with self.identity_lock:
            number = self._load_counter()
            self._save_counter(number)

        # تغيير اسم العضو
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

        # إرسال رسالة القبول للعضو بالخاص
        try:
            await member.send(
                f"تم قبول تفعيلك ✅\n\n"
                f"اسم Roblox: `{username}`\n"
                f"هويتك: `{number}`"
            )

        except discord.Forbidden:
            pass

        except discord.HTTPException:
            pass

        # إرسال إشعار التفعيل في روم سجل التفعيل
        log_channel = message.guild.get_channel(
            IDENTITY_LOG_CHANNEL_ID
        )

        if log_channel:
            try:
                await log_channel.send(
                    f"لقد تم تفعيل العضو\n\n"
                    f": {member.mention}\n\n"
                    f": {number}"
                )

            except discord.HTTPException:
                pass


async def setup(bot):
    await bot.add_cog(Activation(bot))
