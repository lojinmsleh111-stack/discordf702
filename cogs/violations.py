import discord
from discord import app_commands
from discord.ext import commands

from utils.config import VIOLATION_CHANNEL_ID


# =========================================================
# IDs الإيموجيات
# =========================================================

UNPAID_EMOJI_ID = 1540563530934390866
PAID_EMOJI_ID = 1538664119136161823


# =========================================================
# إنشاء نص المخالفة
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
# جلب الإيموجي المخصص
# =========================================================

async def get_custom_emoji(
    guild: discord.Guild,
    emoji_id: int
):
    emoji = guild.get_emoji(emoji_id)

    if emoji is not None:
        return emoji

    try:
        return await guild.fetch_emoji(emoji_id)
    except (
        discord.NotFound,
        discord.Forbidden,
        discord.HTTPException
    ):
        return None


# =========================================================
# تحديث حالة السداد
# الرسالة المستهدفة = الرسالة الأساسية للمخالفة
# =========================================================

async def change_status(
    interaction: discord.Interaction,
    emoji_id: int
):

    if interaction.guild is None:
        return await interaction.response.send_message(
            "❌ تعذر تحديد السيرفر.",
            ephemeral=True
        )

    if not isinstance(interaction.channel, discord.Thread):
        return await interaction.response.send_message(
            "❌ يجب الضغط على الزر من داخل Thread المخالفة.",
            ephemeral=True
        )

    thread = interaction.channel

    # Thread الخاص برسالة المخالفة الأساسية
    if thread.parent is None or thread.message_id is None:
        return await interaction.response.send_message(
            "❌ لم أستطع العثور على الرسالة الأساسية للمخالفة.",
            ephemeral=True
        )

    try:
        # =====================================================
        # جلب الرسالة الأساسية للمخالفة
        # =====================================================

        original_message = await thread.parent.fetch_message(
            thread.message_id
        )

        # =====================================================
        # جلب الإيموجي المطلوب
        # =====================================================

        new_emoji = await get_custom_emoji(
            interaction.guild,
            emoji_id
        )

        if new_emoji is None:
            return await interaction.response.send_message(
                "❌ الإيموجي غير موجود أو البوت لا يستطيع استخدامه.",
                ephemeral=True
            )

        # =====================================================
        # إزالة إيموجيات السداد القديمة من الرسالة الأساسية
        # =====================================================

        for reaction in original_message.reactions:

            if not isinstance(reaction.emoji, discord.Emoji):
                continue

            if reaction.emoji.id in (
                UNPAID_EMOJI_ID,
                PAID_EMOJI_ID
            ):
                try:
                    await original_message.clear_reaction(
                        reaction.emoji
                    )
                except (
                    discord.Forbidden,
                    discord.NotFound,
                    discord.HTTPException
                ):
                    pass

        # =====================================================
        # إضافة الإيموجي الجديد إلى الرسالة الأساسية
        # =====================================================

        await original_message.add_reaction(
            new_emoji
        )

        # =====================================================
        # الرد على الزر
        # =====================================================

        status_text = (
            "تم السداد 💰"
            if emoji_id == PAID_EMOJI_ID
            else "لم يتم السداد"
        )

        await interaction.response.send_message(
            f"✅ تم تحديث حالة المخالفة إلى: **{status_text}**",
            ephemeral=True
        )

    except discord.Forbidden:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "❌ البوت لا يملك الصلاحيات اللازمة لتعديل الإيموجيات.",
                ephemeral=True
            )

    except discord.NotFound:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "❌ الرسالة الأساسية للمخالفة غير موجودة.",
                ephemeral=True
            )

    except discord.HTTPException as e:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                f"❌ حدث خطأ أثناء تحديث السداد: {e}",
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
            PAID_EMOJI_ID
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
            UNPAID_EMOJI_ID
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

        if interaction.guild is None:
            return await interaction.followup.send(
                "❌ هذا الأمر يعمل داخل السيرفر فقط.",
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
                or not extra_evidence.content_type.startswith("image/")
            )
        ):
            return await interaction.followup.send(
                "❌ الدليل الإضافي يجب أن يكون صورة.",
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
        # إنشاء النص
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

                # الرسالة الأساسية
                message = await channel.send(
                    content=violation_text,
                    allowed_mentions=discord.AllowedMentions(
                        users=True
                    )
                )

                sent_messages.append(message)

                # =================================================
                # إضافة "لم يتم السداد" على الرسالة الأساسية
                # =================================================

                unpaid_emoji = await get_custom_emoji(
                    interaction.guild,
                    UNPAID_EMOJI_ID
                )

                if unpaid_emoji is not None:
                    try:
                        await message.add_reaction(
                            unpaid_emoji
                        )
                    except (
                        discord.Forbidden,
                        discord.HTTPException
                    ):
                        pass

                # =================================================
                # إنشاء Thread مربوط بالرسالة الأساسية
                # =================================================

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
        # التأكد من الإرسال
        # =====================================================

        if not sent_messages:
            return await interaction.followup.send(
                "❌ لم أستطع إرسال المخالفة إلى أي روم.\n\n"
                "تأكد من صلاحيات البوت:\n"
                "• View Channel\n"
                "• Send Messages\n"
                "• Read Message History\n"
                "• Add Reactions\n"
                "• Create Public Threads\n"
                "• Send Messages in Threads",
                ephemeral=True
            )

        # =====================================================
        # إرسال الخاص
        # =====================================================

        try:

            await violator.send(
                content=violation_text,
                allowed_mentions=discord.AllowedMentions(
                    users=False
                )
            )

            dm_status = "وتم إرسالها للخاص."

        except (
            discord.Forbidden,
            discord.HTTPException
        ):

            dm_status = (
                "لكن تعذر إرسالها للخاص "
                "(قد تكون الرسائل الخاصة مقفلة)."
            )

        # =====================================================
        # التأكيد
        # =====================================================

        await interaction.followup.send(
            f"✅ تم إصدار المخالفة وإرسالها إلى "
            f"{len(sent_messages)} روم، "
            f"{dm_status}",
            ephemeral=True
        )


# =========================================================
# Setup
# =========================================================

async def setup(bot):

    # تسجيل الأزرار حتى تعمل بعد إعادة تشغيل البوت
    bot.add_view(
        ViolationView()
    )

    await bot.add_cog(
        Violations(bot)
        )
