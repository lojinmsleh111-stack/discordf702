import discord
from discord import app_commands
from discord.ext import commands

from utils.config import VIOLATION_CHANNEL_ID


# =========================================================
# نموذج المخالفة
# =========================================================

def create_violation_text(
    military: discord.Member,
    violator: discord.Member,
    reason: str,
    amount: str,
    plate: str,
    evidence: discord.Attachment,
    extra_evidence: discord.Attachment | None
):
    return (
        "**__تم اصدار مخالفه\n\n"
        f"العسكري : {military.mention}\n\n"
        f"المخالف : {violator.mention}\n\n"
        f"سبب المخالفه : {reason}\n\n"
        f"مبلغ المخالفه : {amount}\n\n"
        f"الوحه : {plate}\n\n"
        f"الدليل : {evidence.url}\n\n"
        f"الدليل الإضافي : "
        f"{extra_evidence.url if extra_evidence else 'لا يوجد'}\n\n\n"
        "..\n\n"
        "__**"
    )


# =========================================================
# أزرار السداد
# =========================================================

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
        thread = interaction.channel

        if not isinstance(thread, discord.Thread):
            return await interaction.response.send_message(
                "❌ الزر يعمل داخل Thread المخالفة فقط.",
                ephemeral=True
            )

        # الرسالة التي بدأ منها الـ Thread
        message_id = thread.message_id

        if not message_id:
            return await interaction.response.send_message(
                "❌ لم أستطع العثور على الرسالة الأساسية.",
                ephemeral=True
            )

        parent = thread.parent

        if parent is None:
            return await interaction.response.send_message(
                "❌ لم أستطع العثور على روم المخالفة.",
                ephemeral=True
            )

        try:
            original_message = await parent.fetch_message(
                message_id
            )

            # لا نغير نموذج المخالفة نفسه.
            # فقط نضيف علامة السداد في آخر الرسالة.
            new_content = (
                original_message.content
                + "\n\n✅ **تم السداد**"
            )

            await original_message.edit(
                content=new_content
            )

            await interaction.response.send_message(
                "✅ تم السداد وتحديث المخالفة الأساسية.",
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ البوت لا يملك صلاحية تعديل الرسالة.",
                ephemeral=True
            )

        except discord.NotFound:
            await interaction.response.send_message(
                "❌ لم أستطع العثور على الرسالة الأساسية.",
                ephemeral=True
            )

        except discord.HTTPException:
            await interaction.response.send_message(
                "❌ حدث خطأ أثناء تعديل المخالفة.",
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
        await interaction.response.send_message(
            "⚠️ لم يتم سداد المخالفة.",
            ephemeral=True
        )


# =========================================================
# Violations Cog
# =========================================================

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
        plate="اللوحة",
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

        # =====================================================
        # التأكد من أن الأمر داخل سيرفر
        # =====================================================

        if interaction.guild is None:
            return await interaction.followup.send(
                "❌ هذا الأمر يعمل داخل السيرفر فقط.",
                ephemeral=True
            )

        # =====================================================
        # رومات المخالفات
        # =====================================================

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
                    channel = await self.bot.fetch_channel(
                        channel_id
                    )
                except (
                    discord.NotFound,
                    discord.Forbidden,
                    discord.HTTPException
                ):
                    continue

            if isinstance(channel, discord.TextChannel):
                if channel.id not in [c.id for c in channels]:
                    channels.append(channel)

        if not channels:
            return await interaction.followup.send(
                "❌ لم أجد رومات المخالفات.",
                ephemeral=True
            )

        # =====================================================
        # التحقق من الصور
        # =====================================================

        if (
            evidence.content_type is None
            or not evidence.content_type.startswith("image/")
        ):
            return await interaction.followup.send(
                "❌ الدليل الأساسي يجب أن يكون صورة.",
                ephemeral=True
            )

        if (
            extra_evidence is not None
            and (
                extra_evidence.content_type is None
                or not extra_evidence.content_type.startswith(
                    "image/"
                )
            )
        ):
            return await interaction.followup.send(
                "❌ الدليل الإضافي يجب أن يكون صورة.",
                ephemeral=True
            )

        # =====================================================
        # إنشاء الرسالة
        # =====================================================

        violation_text = create_violation_text(
            military=military,
            violator=violator,
            reason=reason,
            amount=amount,
            plate=plate,
            evidence=evidence,
            extra_evidence=extra_evidence
        )

        sent_messages = []

        # =====================================================
        # إرسال إلى رومات المخالفات
        # =====================================================

        for channel in channels:

            try:
                # الرسالة عادية وليست Embed
                message = await channel.send(
                    content=violation_text,
                    allowed_mentions=discord.AllowedMentions(
                        users=True
                    )
                )

                sent_messages.append(message)

                # -------------------------------------------------
                # الدليل الأساسي
                # -------------------------------------------------

                try:
                    evidence_file = await evidence.to_file()

                    await channel.send(
                        file=evidence_file
                    )
                except (
                    discord.Forbidden,
                    discord.HTTPException
                ):
                    pass

                # -------------------------------------------------
                # الدليل الإضافي
                # -------------------------------------------------

                if extra_evidence:

                    try:
                        extra_file = await extra_evidence.to_file()

                        await channel.send(
                            file=extra_file
                        )
                    except (
                        discord.Forbidden,
                        discord.HTTPException
                    ):
                        pass

                # -------------------------------------------------
                # إنشاء Thread
                # -------------------------------------------------

                try:
                    thread = await message.create_thread(
                        name=f"مخالفة - {violator.display_name}"
                    )

                    await thread.send(
                        "اختر حالة السداد:",
                        view=ViolationView()
                    )

                except (
                    discord.Forbidden,
                    discord.HTTPException
                ):
                    pass

            except (
                discord.Forbidden,
                discord.HTTPException
            ):
                continue

        # =====================================================
        # لم يتم الإرسال
        # =====================================================

        if not sent_messages:
            return await interaction.followup.send(
                "❌ لم أستطع إرسال المخالفة إلى أي روم.\n\n"
                "تأكد من صلاحيات البوت:\n"
                "• View Channel\n"
                "• Send Messages\n"
                "• Attach Files\n"
                "• Create Public Threads\n"
                "• Send Messages in Threads",
                ephemeral=True
            )

        # =====================================================
        # إرسال نسخة للمخالف بالخاص
        # =====================================================

        try:
            await violator.send(
                content=violation_text
            )

            try:
                evidence_file = await evidence.to_file()

                await violator.send(
                    file=evidence_file
                )
            except (
                discord.Forbidden,
                discord.HTTPException
            ):
                pass

            if extra_evidence:
                try:
                    extra_file = await extra_evidence.to_file()

                    await violator.send(
                        file=extra_file
                    )
                except (
                    discord.Forbidden,
                    discord.HTTPException
                ):
                    pass

        except (
            discord.Forbidden,
            discord.HTTPException
        ):
            pass

        # =====================================================
        # تأكيد الأمر
        # =====================================================

        await interaction.followup.send(
            "✅ تم إصدار المخالفة وإرسالها إلى "
            f"{len(sent_messages)} روم.",
            ephemeral=True
        )


# =========================================================
# Setup
# =========================================================

async def setup(bot):
    bot.add_view(ViolationView())
    await bot.add_cog(Violations(bot))
