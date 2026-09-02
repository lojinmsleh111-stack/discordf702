import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone

from utils.config import VIOLATION_CHANNEL_ID


class ViolationView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="تم السداد",
        style=discord.ButtonStyle.success,
        custom_id="violation_paid"
    )
    async def paid(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not interaction.message.embeds:
            return await interaction.response.send_message(
                "❌ لا يوجد Embed لتحديثه.",
                ephemeral=True
            )

        embed = interaction.message.embeds[0]

        embed.description = (
            "**__\n"
            "حالة المخالفه : تم السداد\n"
            "__**"
        )

        await interaction.message.edit(embed=embed)

        await interaction.response.send_message(
            "✅ تم تحديث حالة المخالفة إلى: تم السداد.",
            ephemeral=True
        )

    @discord.ui.button(
        label="لم يتم السداد",
        style=discord.ButtonStyle.danger,
        custom_id="violation_unpaid"
    )
    async def unpaid(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not interaction.message.embeds:
            return await interaction.response.send_message(
                "❌ لا يوجد Embed لتحديثه.",
                ephemeral=True
            )

        embed = interaction.message.embeds[0]

        embed.description = (
            "**__\n"
            "حالة المخالفه : لم يتم السداد\n"
            "__**"
        )

        await interaction.message.edit(embed=embed)

        await interaction.response.send_message(
            "⚠️ حالة المخالفة: لم يتم السداد.",
            ephemeral=True
        )


class Violations(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="mokhalfa",
        description="إصدار مخالفة"
    )
    @app_commands.describe(
        military="العسكري",
        violator="المخالف",
        reason="سبب المخالفة",
        amount="مبلغ المخالفة",
        plate="لوحة المركبة",
        evidence="الدليل - صورة",
        extra_evidence="الدليل الإضافي - صورة اختيارية"
    )
    async def issue(
        self,
        interaction: discord.Interaction,
        military: discord.Member,
        violator: discord.Member,
        reason: str,
        amount: str,
        plate: str,
        evidence: discord.Attachment,
        extra_evidence: discord.Attachment | None = None
    ):

        await interaction.response.defer(ephemeral=True)

        if interaction.guild is None:
            return await interaction.followup.send(
                "❌ هذا الأمر يعمل داخل السيرفر فقط.",
                ephemeral=True
            )

        # ================================================
        # الحصول على رومين المخالفات
        # ================================================

        channel_ids = VIOLATION_CHANNEL_ID

        if not isinstance(channel_ids, (list, tuple, set)):
            channel_ids = [channel_ids]

        channels = []

        for channel_id in channel_ids:
            try:
                channel_id = int(channel_id)
            except (TypeError, ValueError):
                continue

            channel = interaction.guild.get_channel(channel_id)

            if channel is None:
                try:
                    channel = await self.bot.fetch_channel(channel_id)
                except (
                    discord.NotFound,
                    discord.Forbidden,
                    discord.HTTPException
                ):
                    continue

            if isinstance(channel, discord.TextChannel):
                channels.append(channel)

        if not channels:
            return await interaction.followup.send(
                "❌ لم أجد أي روم من رومات المخالفات.\n"
                "تأكد من الـ IDs وصلاحيات البوت.",
                ephemeral=True
            )

        # ================================================
        # التحقق من الصور
        # ================================================

        allowed_types = {
            "image/png",
            "image/jpeg",
            "image/jpg",
            "image/webp",
            "image/gif"
        }

        if evidence.content_type not in allowed_types:
            return await interaction.followup.send(
                "❌ الدليل الأساسي يجب أن يكون صورة.",
                ephemeral=True
            )

        if (
            extra_evidence is not None
            and extra_evidence.content_type not in allowed_types
        ):
            return await interaction.followup.send(
                "❌ الدليل الإضافي يجب أن يكون صورة.",
                ephemeral=True
            )

        # ================================================
        # Embed المخالفة
        # ================================================

        embed = discord.Embed(
            title="🚨 مخالفة جديدة",
            description=(
                f"**العسكري:** {military.mention}\n\n"
                f"**المخالف:** {violator.mention}\n\n"
                f"**سبب المخالفة:** {reason}\n\n"
                f"**مبلغ المخالفة:** {amount}\n\n"
                f"**اللوحة:** {plate}\n\n"
                f"**الدليل:** [اضغط لعرض الدليل]({evidence.url})\n\n"
                f"**الدليل الإضافي:** "
                f"{f'[اضغط لعرض الدليل]({extra_evidence.url})' if extra_evidence else 'لا يوجد'}\n\n"
                "**حالة المخالفة:** لم يتم السداد"
            ),
            timestamp=datetime.now(timezone.utc)
        )

        embed.set_image(url=evidence.url)

        embed.set_footer(
            text=f"أصدرها: {interaction.user}"
        )

        # ================================================
        # إرسال إلى الرومين
        # ================================================

        sent_messages = []

        for channel in channels:

            try:
                message = await channel.send(
                    content=(
                        f"🚨 **مخالفة جديدة**\n"
                        f"المخالف: {violator.mention}"
                    ),
                    embed=embed.copy(),
                    allowed_mentions=discord.AllowedMentions(
                        users=True
                    )
                )

                sent_messages.append(message)

                # ========================================
                # إنشاء Thread لكل روم
                # ========================================

                try:
                    thread = await message.create_thread(
                        name=f"مخالفة - {violator.display_name}"
                    )

                    status_embed = discord.Embed(
                        title="حالة المخالفة",
                        description=(
                            "**__\n"
                            "حالة المخالفه : لم يتم السداد\n"
                            "__**"
                        )
                    )

                    status_embed.set_footer(
                        text=(
                            "إصدار: "
                            f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
                        )
                    )

                    await thread.send(
                        embed=status_embed,
                        view=ViolationView()
                    )

                except (
                    discord.Forbidden,
                    discord.HTTPException
                ):
                    pass

                # ========================================
                # الدليل الإضافي
                # ========================================

                if extra_evidence:

                    try:
                        extra_embed = discord.Embed(
                            title="📎 الدليل الإضافي",
                            description=(
                                f"للمخالفة: {message.jump_url}"
                            )
                        )

                        extra_embed.set_image(
                            url=extra_evidence.url
                        )

                        await channel.send(
                            embed=extra_embed
                        )

                    except (
                        discord.Forbidden,
                        discord.HTTPException
                    ):
                        pass

            except discord.Forbidden:
                continue

            except discord.HTTPException:
                continue

        # ================================================
        # التأكد من نجاح الإرسال
        # ================================================

        if not sent_messages:
            return await interaction.followup.send(
                "❌ لم أستطع إرسال المخالفة إلى أي روم.\n"
                "تأكد أن البوت يملك:\n"
                "• View Channel\n"
                "• Send Messages\n"
                "• Embed Links\n"
                "• Create Public Threads",
                ephemeral=True
            )

        # ================================================
        # إرسال نسخة للعضو بالخاص
        # ================================================

        dm_embed = discord.Embed(
            title="🚨 تم إصدار مخالفة بحقك",
            description=(
                f"**العسكري:** {military.mention}\n\n"
                f"**المخالف:** {violator.mention}\n\n"
                f"**سبب المخالفة:** {reason}\n\n"
                f"**مبلغ المخالفة:** {amount}\n\n"
                f"**اللوحة:** {plate}\n\n"
                f"**الدليل:** [عرض الدليل]({evidence.url})\n\n"
                f"**الدليل الإضافي:** "
                f"{f'[عرض الدليل]({extra_evidence.url})' if extra_evidence else 'لا يوجد'}\n\n"
                "**حالة المخالفة:** لم يتم السداد"
            ),
            timestamp=datetime.now(timezone.utc)
        )

        dm_embed.set_image(url=evidence.url)

        try:
            await violator.send(
                embed=dm_embed
            )
        except (
            discord.Forbidden,
            discord.HTTPException
        ):
            pass

        # ================================================
        # التأكيد
        # ================================================

        await interaction.followup.send(
            f"✅ تم إصدار المخالفة وإرسالها إلى "
            f"{len(sent_messages)} روم.",
            ephemeral=True
        )


async def setup(bot):

    bot.add_view(
        ViolationView()
    )

    await bot.add_cog(
        Violations(bot)
        )
