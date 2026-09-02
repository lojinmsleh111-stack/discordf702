import discord
from discord import app_commands
from discord.ext import commands

from utils.config import VIOLATION_CHANNEL_ID


# =========================================================
# دالة إنشاء رسالة المخالفة
# =========================================================

def create_violation_text(
    military: discord.Member,
    violator: discord.Member,
    reason: str,
    amount: str,
    plate: str,
    evidence: discord.Attachment,
    extra_evidence: discord.Attachment | None,
    status: str = "لم يتم السداد"
):
    return (
        "**__تم اصدار مخالفه\n\n\n"
        f"- العسكري : {military.mention}\n\n\n"
        f"- المخالف : {violator.mention}\n\n\n"
        f"- سبب المخالفه : {reason}\n\n\n"
        f"- مبلغ المخالفه : {amount}\n\n\n"
        f"- الوحه : {plate}\n\n\n"
        f"- الدليل : {evidence.url}\n\n\n"
        f"- الدليل الإضافي : "
        f"{extra_evidence.url if extra_evidence else 'لا يوجد'}\n\n\n"
        f"- حالة المخالفه : {status}\n\n\n"
        "..\n\n"
        "__**"
    )


# =========================================================
# أزرار المخالفة
# =========================================================

class ViolationView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    # =====================================================
    # تم السداد
    # =====================================================

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

        # زر الحالة موجود داخل الـ Thread
        thread = interaction.channel

        if not isinstance(thread, discord.Thread):
            return await interaction.response.send_message(
                "❌ لا يمكن العثور على الرسالة الأساسية للمخالفة.",
                ephemeral=True
            )

        # الحصول على الرسالة الأساسية
        parent_channel = thread.parent

        if parent_channel is None:
            return await interaction.response.send_message(
                "❌ لا يمكن العثور على روم المخالفة.",
                ephemeral=True
            )

        try:
            original_message = await parent_channel.fetch_message(
                thread.id
            )
        except discord.NotFound:
            return await interaction.response.send_message(
                "❌ لم أستطع العثور على الرسالة الأساسية.",
                ephemeral=True
            )
        except discord.Forbidden:
            return await interaction.response.send_message(
                "❌ البوت لا يملك صلاحية الوصول إلى الرسالة الأساسية.",
                ephemeral=True
            )
        except discord.HTTPException:
            return await interaction.response.send_message(
                "❌ حدث خطأ أثناء الوصول إلى الرسالة الأساسية.",
                ephemeral=True
            )

        # تعديل حالة المخالفة في الرسالة الأساسية
        new_content = original_message.content.replace(
            "- حالة المخالفه : لم يتم السداد",
            "- حالة المخالفه : تم السداد"
        )

        # إذا كانت بالفعل مسددة
        if new_content == original_message.content:
            await interaction.response.send_message(
                "ℹ️ المخالفة مسجلة بالفعل كـ تم السداد.",
                ephemeral=True
            )
            return

        try:
            await original_message.edit(
                content=new_content
            )
        except discord.Forbidden:
            return await interaction.response.send_message(
                "❌ البوت لا يملك صلاحية تعديل الرسالة.",
                ephemeral=True
            )
        except discord.HTTPException:
            return await interaction.response.send_message(
                "❌ حدث خطأ أثناء تعديل المخالفة.",
                ephemeral=True
            )

        # تعديل رسالة الحالة داخل الـThread
        try:
            if interaction.message:
                await interaction.message.edit(
                    content=(
                        "**__\n"
                        "حالة المخالفه : تم السداد\n"
                        "__**"
                    )
                )
        except discord.HTTPException:
            pass

        await interaction.response.send_message(
            "✅ تم السداد وتحديث المخالفة الأساسية تلقائيًا.",
            ephemeral=True
        )

    # =====================================================
    # لم يتم السداد
    # =====================================================

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

        thread = interaction.channel

        if not isinstance(thread, discord.Thread):
            return await interaction.response.send_message(
                "❌ هذا الزر يعمل داخل Thread المخالفة.",
                ephemeral=True
            )

        parent_channel = thread.parent

        if parent_channel is None:
            return await interaction.response.send_message(
                "❌ لا يمكن العثور على روم المخالفة.",
                ephemeral=True
            )

        # الحصول على الرسالة الأساسية
        try:
            original_message = await parent_channel.fetch_message(
                thread.id
            )
        except (
            discord.NotFound,
            discord.Forbidden,
            discord.HTTPException
        ):
            return await interaction.response.send_message(
                "❌ لم أستطع العثور على الرسالة الأساسية للمخالفة.",
                ephemeral=True
            )

        # التأكد أن الحالة لم تتغير إلى مسدد
        if "- حالة المخالفه : تم السداد" in original_message.content:
            return await interaction.response.send_message(
                "⚠️ هذه المخالفة تم تسجيلها بالفعل كـ تم السداد.",
                ephemeral=True
            )

        await interaction.response.send_message(
            "⚠️ المخالفة لم يتم سدادها.",
            ephemeral=True
        )


# =========================================================
# Violations Cog
# =========================================================

class Violations(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # =====================================================
    # /mokhalfa
    # =====================================================

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

        # منع بقاء الأمر Loading
        await interaction.response.defer(
            ephemeral=True
        )

        # =================================================
        # التأكد من السيرفر
        # =================================================

        if interaction.guild is None:
            return await interaction.followup.send(
                "❌ هذا الأمر يعمل داخل السيرفر فقط.",
                ephemeral=True
            )

        # =================================================
        # الحصول على الرومين
        # =================================================

        channel_ids = VIOLATION_CHANNEL_ID

        if not isinstance(
            channel_ids,
            (list, tuple, set)
        ):
            channel_ids = [channel_ids]

        channels = []

        for channel_id in channel_ids:

            try:
                channel_id = int(channel_id)
            except (
                TypeError,
                ValueError
            ):
                continue

            channel = interaction.guild.get_channel(
                channel_id
            )

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

            if isinstance(
                channel,
                discord.TextChannel
            ):
                if channel.id not in [
                    c.id for c in channels
                ]:
                    channels.append(channel)

        # =================================================
        # لا توجد رومات
        # =================================================

        if not channels:
            return await interaction.followup.send(
                "❌ لم أجد أي روم من رومات المخالفات.\n"
                "تأكد من الـ IDs وصلاحيات البوت.",
                ephemeral=True
            )

        # =================================================
        # التحقق من الدليل الأساسي
        # =================================================

        if (
            evidence.content_type is None
            or not evidence.content_type.startswith("image/")
        ):
            return await interaction.followup.send(
                "❌ الدليل الأساسي يجب أن يكون صورة.",
                ephemeral=True
            )

        # =================================================
        # التحقق من الدليل الإضافي
        # =================================================

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

        # =================================================
        # إنشاء نص المخالفة
        # =================================================

        violation_text = create_violation_text(
            military=military,
            violator=violator,
            reason=reason,
            amount=amount,
            plate=plate,
            evidence=evidence,
            extra_evidence=extra_evidence,
            status="لم يتم السداد"
        )

        # =================================================
        # إرسال المخالفة إلى الرومين
        # =================================================

        sent_messages = []

        for channel in channels:

            try:

                # الرسالة الأساسية
                message = await channel.send(
                    content=violation_text,
                    allowed_mentions=discord.AllowedMentions(
                        users=True
                    )
                )

                sent_messages.append(
                    message
                )

                # =========================================
                # إرسال الدليل الأساسي كصورة
                # =========================================

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

                # =========================================
                # إرسال الدليل الإضافي كصورة
                # =========================================

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

                # =========================================
                # إنشاء Thread من الرسالة الأساسية
                # =========================================

                try:

                    thread = await message.create_thread(
                        name=(
                            f"مخالفة - "
                            f"{violator.display_name}"
                        )
                    )

                    await thread.send(
                        content=(
                            "**__\n"
                            "حالة المخالفه : لم يتم السداد\n"
                            "__**"
                        ),
                        view=ViolationView()
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

        # =================================================
        # التأكد من الإرسال
        # =================================================

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

        # =================================================
        # إرسال نسخة للمخالف بالخاص
        # =================================================

        dm_text = create_violation_text(
            military=military,
            violator=violator,
            reason=reason,
            amount=amount,
            plate=plate,
            evidence=evidence,
            extra_evidence=extra_evidence,
            status="لم يتم السداد"
        )

        try:

            await violator.send(
                content=dm_text
            )

            # الدليل الأساسي
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

            # الدليل الإضافي
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
            # الخاص مغلق عند العضو
            pass

        # =================================================
        # رسالة التأكيد
        # =================================================

        await interaction.followup.send(
            "✅ تم إصدار المخالفة وإرسالها إلى "
            f"{len(sent_messages)} روم.",
            ephemeral=True
        )


# =========================================================
# Setup
# =========================================================

async def setup(bot):

    bot.add_view(
        ViolationView()
    )

    await bot.add_cog(
        Violations(bot)
    )
