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
        evidence="الدليل",
        extra_evidence="الدليل الإضافي"
    )
    async def issue(
        self,
        interaction: discord.Interaction,
        military: str,
        violator: discord.Member,
        reason: str,
        amount: str,
        plate: str,
        evidence: str,
        extra_evidence: str = "لا يوجد"
    ):
        await interaction.response.defer(ephemeral=True)

        channel = interaction.guild.get_channel(
            VIOLATION_CHANNEL_ID
        )

        if channel is None:
            return await interaction.followup.send(
                "لم أجد روم المخالفات.",
                ephemeral=True
            )

        text = (
            "**__تم اصدار مخالفه__\n\n"
            f"- العسكري : {military}\n\n"
            f"- المخالف : {violator.mention}\n\n"
            f"- سبب المخالفه : {reason}\n\n"
            f"- مبلغ المخالفه : {amount}\n\n"
            f"- الوحه : {plate}\n\n"
            f"- الدليل : {evidence}\n\n"
            f"- الدليل الإضافي : {extra_evidence}\n\n"
            "..\n\n"
            "__**"
        )

        msg = await channel.send(text)

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

        dm_text = (
            "**__تم اصدار مخالفه__\n\n"
            f"- العسكري : {military}\n\n"
            f"- المخالف : {violator.mention}\n\n"
            f"- سبب المخالفه : {reason}\n\n"
            f"- مبلغ المخالفه : {amount}\n\n"
            f"- الوحه : {plate}\n\n"
            f"- الدليل : {evidence}\n\n"
            f"- الدليل الإضافي : {extra_evidence}\n\n"
            "..\n\n"
            "__**"
        )

        try:
            await violator.send(dm_text)
        except discord.Forbidden:
            pass

        await interaction.followup.send(
            "تم إصدار المخالفة.",
            ephemeral=True
        )


async def setup(bot):
    bot.add_view(ViolationView())
    await bot.add_cog(Violations(bot))
