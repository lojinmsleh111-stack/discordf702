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
        embed = (
            interaction.message.embeds[0]
            if interaction.message.embeds
            else discord.Embed()
        )

        embed.description = (
            "**__\n"
            "حالة المخالفه : تم السداد\n"
            "__**"
        )

        await interaction.message.edit(embed=embed)

        await interaction.response.send_message(
            "تم تحديث حالة المخالفة إلى تم السداد.",
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
        embed = (
            interaction.message.embeds[0]
            if interaction.message.embeds
            else discord.Embed()
        )

        embed.description = (
            "**__\n"
            "حالة المخالفه : لم يتم السداد\n"
            "__**"
        )

        await interaction.message.edit(embed=embed)

        await interaction.response.send_message(
            "حالة المخالفة: لم يتم السداد.",
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
        evidence="الدليل - يجب أن يكون صورة",
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

        # الحصول على روم المخالفات
        channel = interaction.guild.get_channel(
            VIOLATION_CHANNEL_ID
        )

        if not isinstance(channel, discord.TextChannel):
            return await interaction.followup.send(
                "❌ لم أجد روم المخالفات. تأكد من VIOLATION_CHANNEL_ID.",
                ephemeral=True
            )

        # أنواع الصور المسموحة
        allowed_image_types = {
            "image/png",
            "image/jpeg",
            "image/jpg",
            "image/webp",
            "image/gif"
        }

        # التحقق من الدليل الأساسي
        if evidence.content_type not in allowed_image_types:
            return await interaction.followup.send(
                "❌ الدليل الأساسي يجب أن يكون صورة.",
                ephemeral=True
            )

        # التحقق من الدليل الإضافي
        if (
            extra_evidence is not None
            and extra_evidence.content_type not in allowed_image_types
        ):
            return await interaction.followup.send(
                "❌ الدليل الإضافي يجب أن يكون صورة.",
                ephemeral=True
            )

        # الدليل الإضافي
        extra_text = (
            extra_evidence.url
            if extra_evidence
            else "لا يوجد"
        )

        # نص المخالفة
        text = (
            "**__تم اصدار مخالفه__\n\n"
            f"- العسكري : {military.mention}\n\n"
            f"- المخالف : {violator.mention}\n\n"
            f"- سبب المخالفه : {reason}\n\n"
            f"- مبلغ المخالفه : {amount}\n\n"
            f"- الوحه : {plate}\n\n"
            f"- الدليل : {evidence.url}\n\n"
            f"- الدليل الإضافي : {extra_text}\n\n"
            "..\n\n"
            "__**"
        )

        # تجهيز ملفات الصور
        files = []

        try:
            evidence_file = await evidence.to_file()
            files.append(evidence_file)

            if extra_evidence:
                extra_evidence_file = await extra_evidence.to_file()
                files.append(extra_evidence_file)

        except discord.HTTPException:
            return await interaction.followup.send(
                "❌ فشل تحميل صور الأدلة.",
                ephemeral=True
            )

        # ==================================================
        # إرسال المخالفة إلى روم المخالفات
        # ==================================================
        try:
            msg = await channel.send(
                content=text,
                files=files
            )

        except discord.Forbidden:
            return await interaction.followup.send(
                "❌ البوت لا يملك صلاحية إرسال المخالفة في روم المخالفات.\n"
                "تأكد من صلاحيات: View Channel / Send Messages / Attach Files.",
                ephemeral=True
            )

        except discord.HTTPException as e:
            return await interaction.followup.send(
                f"❌ فشل إرسال المخالفة للروم.\n`{e}`",
                ephemeral=True
            )

        # ==================================================
        # إنشاء Thread للمخالفة
        # ==================================================
        try:
            thread = await msg.create_thread(
                name=f"مخالفة - {violator.display_name}"
            )

            status = discord.Embed(
                title="حالة المخالفه",
                description=(
                    "**__\n"
                    "حالة المخالفه : لم يتم السداد\n"
                    "__**"
                )
            )

            status.set_footer(
                text=(
                    "إصدار: "
                    f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
                )
            )

            await thread.send(
                embed=status,
                view=ViolationView()
            )

        except discord.HTTPException:
            pass

        # ==================================================
        # إرسال نسخة من المخالفة للعضو بالخاص
        # ==================================================
        dm_text = (
            "**__تم اصدار مخالفه__\n\n"
            f"- العسكري : {military.mention}\n\n"
            f"- المخالف : {violator.mention}\n\n"
            f"- سبب المخالفه : {reason}\n\n"
            f"- مبلغ المخالفه : {amount}\n\n"
            f"- الوحه : {plate}\n\n"
            f"- الدليل : {evidence.url}\n\n"
            f"- الدليل الإضافي : {extra_text}\n\n"
            "..\n\n"
            "__**"
        )

        try:
            dm_files = []

            dm_evidence_file = await evidence.to_file()
            dm_files.append(dm_evidence_file)

            if extra_evidence:
                dm_extra_file = await extra_evidence.to_file()
                dm_files.append(dm_extra_file)

            await violator.send(
                content=dm_text,
                files=dm_files
            )

        except discord.Forbidden:
            # الخاص مغلق، لكن المخالفة بالروم تبقى ناجحة
            pass

        except discord.HTTPException:
            pass

        # تأكيد للمُصدر
        await interaction.followup.send(
            "✅ تم إصدار المخالفة وإرسالها إلى روم المخالفات.",
            ephemeral=True
        )


async def setup(bot):
    bot.add_view(ViolationView())
    await bot.add_cog(Violations(bot))
