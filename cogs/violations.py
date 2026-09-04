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
# جلب الإيموجي
# =========================================================

async def get_custom_emoji(
    guild: discord.Guild,
    emoji_id: int
):
    emoji = guild.get_emoji(emoji_id)

    if emoji:
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
# =========================================================

async def change_status(
    interaction: discord.Interaction,
    message_id: int,
    emoji_id: int
):

    if interaction.guild is None:
        return await interaction.response.send_message(
            "❌ تعذر تحديد السيرفر.",
            ephemeral=True
        )

    try:
        # =====================================================
        # الحصول على الرسالة الأساسية مباشرة
        # =====================================================

        message = None

        # إذا كانت القناة الحالية Thread
        if isinstance(interaction.channel, discord.Thread):

            parent = interaction.channel.parent

            if parent is not None:
                try:
                    message = await parent.fetch_message(
                        message_id
                    )
                except (
                    discord.NotFound,
                    discord.Forbidden,
                    discord.HTTPException
                ):
                    message = None

        # =====================================================
        # إذا لم نجدها، نحاول جلب القناة من الرسالة
        # =====================================================

        if message is None:

            for channel_id in (
                VIOLATION_CHANNEL_ID
                if isinstance(
                    VIOLATION_CHANNEL_ID,
                    (list, tuple, set)
                )
                else [VIOLATION_CHANNEL_ID]
            ):

                try:
                    channel = interaction.guild.get_channel(
                        int(channel_id)
                    )

                    if channel is None:
                        channel = await interaction.client.fetch_channel(
                            int(channel_id)
                        )

                    if isinstance(
                        channel,
                        discord.TextChannel
                    ):
                        try:
                            message = await channel.fetch_message(
                                message_id
                            )
                            break
                        except (
                            discord.NotFound,
                            discord.Forbidden,
                            discord.HTTPException
                        ):
                            continue

                except (
                    ValueError,
                    TypeError,
                    discord.HTTPException
                ):
                    continue

        # =====================================================
        # التأكد من وجود الرسالة
        # =====================================================

        if message is None:
            return await interaction.response.send_message(
                "❌ لم أستطع العثور على الرسالة الأساسية للمخالفة.",
                ephemeral=True
            )

        # =====================================================
        # جلب الإيموجي
        # =====================================================

        emoji = await get_custom_emoji(
            interaction.guild,
            emoji_id
        )

        if emoji is None:
            return await interaction.response.send_message(
                "❌ الإيموجي غير موجود في السيرفر أو البوت لا يستطيع الوصول إليه.",
                ephemeral=True
            )

        # =====================================================
        # إزالة ريأكشن السداد القديم
        # =====================================================

        for reaction in list(message.reactions):

            if not isinstance(
                reaction.emoji,
                discord.Emoji
            ):
                continue

            if reaction.emoji.id not in (
                UNPAID_EMOJI_ID,
                PAID_EMOJI_ID
            ):
                continue

            try:
                # إزالة ريأكشن البوت فقط
                await message.remove_reaction(
                    reaction.emoji,
                    interaction.client.user
                )

            except (
                discord.NotFound,
                discord.Forbidden,
                discord.HTTPException
            ):
                pass

        # =====================================================
        # إضافة الإيموجي الجديد على الرسالة الأساسية
        # =====================================================

        await message.add_reaction(
            emoji
        )

        # =====================================================
        # الرد
        # =====================================================

        if emoji_id == PAID_EMOJI_ID:
            text = "تم السداد 💰"
        else:
            text = "لم يتم السداد"

        await interaction.response.send_message(
            f"✅ تم تحديث حالة المخالفة: **{text}**",
            ephemeral=True
        )

    except discord.Forbidden:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "❌ البوت لا يملك صلاحية إضافة/إزالة الإيموجيات.",
                ephemeral=True
            )

    except discord.NotFound:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "❌ الرسالة الأساسية غير موجودة.",
                ephemeral=True
            )

    except discord.HTTPException as e:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                f"❌ حدث خطأ من Discord: {e}",
                ephemeral=True
            )

    except Exception as e:
        print(
            f"[VIOLATION BUTTON ERROR] "
            f"{type(e).__name__}: {e}"
        )

        if not interaction.response.is_done():
            await interaction.response.send_message(
                "❌ حدث خطأ غير متوقع أثناء تحديث السداد.",
                ephemeral=True
            )


# =========================================================
# View خاصة بكل مخالفة
# =========================================================

class ViolationView(discord.ui.View):

    def __init__(self, message_id: int):
        super().__init__(
            timeout=None
        )

        self.message_id = message_id

        # زر تم السداد
        paid_button = discord.ui.Button(
            label="تم السداد",
            style=discord.ButtonStyle.success,
            custom_id=f"violation_paid:{message_id}"
        )

        # زر لم يتم السداد
        unpaid_button = discord.ui.Button(
            label="لم يتم السداد",
            style=discord.ButtonStyle.danger,
            custom_id=f"violation_unpaid:{message_id}"
        )

        async def paid_callback(
            interaction: discord.Interaction
        ):
            await change_status(
                interaction,
                message_id,
                PAID_EMOJI_ID
            )

        async def unpaid_callback(
            interaction: discord.Interaction
        ):
            await change_status(
                interaction,
                message_id,
                UNPAID_EMOJI_ID
            )

        paid_button.callback = paid_callback
        unpaid_button.callback = unpaid_callback

        self.add_item(paid_button)
        self.add_item(unpaid_button)


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
        # السيرفر
        # =====================================================

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
            or not evidence.content_type.startswith(
                "image/"
            )
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
        # رومات المخالفات
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
        # نص المخالفة
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

                sent_messages.append(
                    message
                )

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
                # إنشاء Thread
                # =================================================

                try:

                    thread = await message.create_thread(
                        name=f"مخالفة - {violator.display_name}"
                    )

                    # =================================================
                    # الأزرار مرتبطة بـ ID الرسالة الأساسية
                    # =================================================

                    await thread.send(
                        "اختر حالة السداد:",
                        view=ViolationView(
                            message.id
                        )
                    )

                except (
                    discord.Forbidden,
                    discord.HTTPException
                ) as e:

                    print(
                        f"[THREAD ERROR] "
                        f"{type(e).__name__}: {e}"
                    )

            except (
                discord.Forbidden,
                discord.HTTPException
            ) as e:

                print(
                    f"[VIOLATION SEND ERROR] "
                    f"{type(e).__name__}: {e}"
                )

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
        # الخاص
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

    await bot.add_cog(
        Violations(bot)
            )
