import discord
from discord import app_commands
from discord.ext import commands

class Announcements(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ارسال_اعلان", description="إرسال إعلان إلى روم محدد")
    @app_commands.describe(
        الروم="الروم الذي سيتم إرسال الإعلان فيه",
        الكلام="نص الإعلان"
    )
    async def announcement(self, interaction: discord.Interaction, الروم: discord.TextChannel, الكلام: str):
        await الروم.send(الكلام)
        await interaction.response.send_message(f"تم إرسال الإعلان في {الروم.mention}.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Announcements(bot))
