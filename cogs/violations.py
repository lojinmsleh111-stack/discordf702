import discord
from discord import app_commands
from discord.ext import commands

from utils.config import VIOLATION_CHANNEL_ID


# =========================================================
# إيموجيات حالة المخالفة
# =========================================================

UNPAID_EMOJI = "<:r_x:1540563530934390866>"
PAID_EMOJI = "<:r_tick:1538664119136161823>"


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
# إزالة حالة قديمة وإضافة الحالة الجديدة
# =========================================================

async def change_status(
    interaction: discord.Interaction,
    new_emoji: str
):
    thread = interaction.channel

    if not isinstance(thread, discord.Thread):
        return await interaction.response.send_message(
            "❌ الزر يعمل داخل Thread المخالفة فقط.",
            ephemeral=True
        )

    if thread.parent is None or thread.message_id is None:
        return await interaction.response.send_message(
            "❌ لم أستطع العثور على رسالة المخالفة.",
            ephemeral=True
        )

    try:
        message = await thread.parent.fetch_message(
            thread.message_id
        )

        # إزالة الـ reactions القديمة
        for reaction in message.reactions:
            try:
                if str(reaction.emoji) in (
                    UNPAID_EMOJI,
                    PAID_EMOJI
                ):
                    await reaction.remove(
                        self_user=True
                    )
            except (
                discord.Forbidden,
                discord.HTTPException
            ):
                pass

        # إضافة الحالة الجديدة كـ Reaction
        try:
            await message.add_reaction(new_emoji)
        except discord.HTTPException:
            pass

        await interaction.response.send_message(
            "✅ تم تحديث حالة المخالفة.",
            ephemeral=True
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ البوت لا يملك صلاحية تعديل المخالفة.",
            ephemeral=True
        )

    except discord.NotFound:
        await interaction.response.send_message(
            "❌ لم أستطع العثور على رسالة المخالفة.",
            ephemeral=True
        )

    except discord.HTTPException:
        await interaction.response.send_message(
            "❌ حدث خطأ أثناء تحديث المخالفة.",
            ephemeral=True
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
        await change_status(
            interaction,
            PAID_EMOJI
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
        await change_status(
            interaction,
            UNPAID_EMOJI
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

        await interaction.response.defer(
            ephemeral=True
        )

        # =====================================================
        # التأكد من السيرفر
        # =====================================================

        if interaction.guild is None:
            return await interaction.followup.send(
                "❌ هذا الأمر يعمل داخل السيرفر فقط.",
                ephemeral=True
            )

        # =====================================================
        # جلب رومات المخالفات
        # =====================================================

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

        if not channels:
            return await interaction.followup.send(
                "❌ لم أجد رومات المخالفات.",
                ephemeral=True
            )

        # =====================================================
        # التحقق من الدليل الأساسي
        # =====================================================

        if (
            evidence.content_type is None
            or not evidence.content_type.startswith(
                "image/"
            )
        ):
            return await interaction.followup.send(
                "❌ الدليل الأساسي يجب أن يكون صورة.",
                ephemeral=True
            )

        # =====================================================
        # التحقق من الدليل الإضافي
        # =====================================================

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
        # إنشاء نص المخالفة
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
        # إرسال المخالفة
        # =====================================================

        for channel in channels:

            try:

                # مهم:
                # لا يوجد file=
                # ولا يوجد إرسال للصورة كملف.
                # الرابط فقط موجود داخل الرسالة.
                message = await channel.send(
                    content=violation_text,
                    allowed_mentions=discord.AllowedMentions(
                        users=True
                    )
                )

                sent_messages.append(message)

                # =================================================
                # إضافة ❌ كـ Reaction
                # =================================================

                try:
                    await message.add_reaction(
                        UNPAID_EMOJI
                    )
                except (
                    discord.Forbidden,
                    discord.HTTPException
                ):
                    pass

                # =================================================
                # إنشاء Thread
                # =================================================

                try:

                    thread = await message.create_thread(
                        name=(
                            f"مخالفة - "
                            f"{violator.display_name}"
                        )
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
        # التأكد من الإرسال
        # =====================================================

        if not sent_messages:

            return await interaction.followup.send(
                "❌ لم أستطع إرسال المخالفة إلى أي روم.\n\n"
                "تأكد من صلاحيات البوت:\n"
                "• View Channel\n"
                "• Send Messages\n"
                "• Add Reactions\n"
                "• Create Public Threads\n"
                "• Send Messages in Threads",
                ephemeral=True
            )

        # =====================================================
        # لا يوجد إرسال بالخاص
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

    bot.add_view(
        ViolationView()
    )

    await bot.add_cog(
        Violations(bot)
    )
