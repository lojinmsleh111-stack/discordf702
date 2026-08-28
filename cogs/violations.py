import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone
from utils.config import VIOLATION_CHANNEL_ID

class ViolationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="تم السداد", style=discord.ButtonStyle.success, custom_id="violation_paid")
    async def paid(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0] if interaction.message.embeds else discord.Embed()
        embed.description = "**__\\nحالة المخالفه : تم السداد\\n__**"
        await interaction.message.edit(embed=embed)
        await interaction.response.send_message("تم تحديث حالة المخالفة إلى تم السداد.", ephemeral=True)

    @discord.ui.button(label="لم يتم السداد", style=discord.ButtonStyle.danger, custom_id="violation_unpaid")
    async def unpaid(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0] if interaction.message.embeds else discord.Embed()
        embed.description = "**__\\nحالة المخالفه : لم يتم السداد\\n__**"
        await interaction.message.edit(embed=embed)
        await interaction.response.send_message("حالة المخالفة: لم يتم السداد.", ephemeral=True)

class Violations(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="اصدار_مخالفة", description="إصدار مخالفة")
    @app_commands.describe(
        العسكري="العسكري",
        المخالف="المخالف",
        سبب_المخالفة="سبب المخالفة",
        مبلغ_المخالفة="مبلغ المخالفة",
        لوحة_المركبة="لوحة المركبة",
        الدليل="الدليل",
        الدليل_الإضافي="الدليل الإضافي"
    )
    async def issue(
        self, interaction: discord.Interaction,
        العسكري: str,
        المخالف: discord.Member,
        سبب_المخالفة: str,
        مبلغ_المخالفة: str,
        لوحة_المركبة: str,
        الدليل: str,
        الدليل_الإضافي: str = "لا يوجد"
    ):
        await interaction.response.defer(ephemeral=True)

        channel = interaction.guild.get_channel(VIOLATION_CHANNEL_ID)
        if not channel:
            return await interaction.followup.send("لم أجد روم المخالفات.", ephemeral=True)

        text = (
            "**__تم اصدار مخالفه__\\n\\n"
            f"- العسكري : {العسكري}\\n\\n"
            f"- المخالف : {المخالف.mention}\\n\\n"
            f"- سبب المخالفه : {سبب_المخالفة}\\n\\n"
            f"- مبلغ المخالفه : {مبلغ_المخالفة}\\n\\n"
            f"- الوحه : {لوحة_المركبة}\\n\\n"
            f"- الدليل : {الدليل}\\n\\n"
            f"- الدليل الإضافي : {الدليل_الإضافي}\\n\\n"
            "..\\n\\n__**"
        )
        msg = await channel.send(text)

        thread = await msg.create_thread(name=f"مخالفة - {المخالف.display_name}")

        status = discord.Embed(
            title="حالة المخالفه",
            description="**__\\nحالة المخالفه : لم يتم السداد\\n__**",
        )
        status.set_footer(text=f"إصدار: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
        await thread.send(embed=status, view=ViolationView())

        dm_text = (
            f"**__تم اصدار مخالفه__\\n\\n"
            f"- العسكري : {العسكري}\\n\\n"
            f"- المخالف : {المخالف.mention}\\n\\n"
            f"- سبب المخالفه : {سبب_المخالفة}\\n\\n"
            f"- مبلغ المخالفه : {مبلغ_المخالفة}\\n\\n"
            f"- الوحه : {لوحة_المركبة}\\n\\n"
            f"- الدليل : {الدليل}\\n\\n"
            f"- الدليل الإضافي : {الدليل_الإضافي}\\n\\n"
            "..\\n\\n__**"
        )
        try:
            await المخالف.send(dm_text)
        except discord.Forbidden:
            pass

        await interaction.followup.send("تم إصدار المخالفة.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Violations(bot))
