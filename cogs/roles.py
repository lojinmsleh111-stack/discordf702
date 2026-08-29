import discord
from discord import app_commands
from discord.ext import commands

def role_option(name, description):
    return app_commands.describe(**{name: description})

class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _apply(self, interaction, member, roles, add=True):
        if not interaction.guild:
            return await interaction.response.send_message("هذا الأمر داخل السيرفر فقط.", ephemeral=True)

        roles = [r for r in roles if r is not None]
        # Remove duplicates while preserving order.
        unique = []
        seen = set()
        for r in roles:
            if r.id not in seen:
                unique.append(r)
                seen.add(r.id)

        if not unique:
            return await interaction.response.send_message("اختر رتبة واحدة على الأقل.", ephemeral=True)

        bot_member = interaction.guild.me
        if not bot_member or not bot_member.guild_permissions.manage_roles:
            return await interaction.response.send_message("البوت يحتاج صلاحية Manage Roles.", ephemeral=True)

        failed = []
        changed = 0
        for role in unique:
            if role.is_default() or role.managed or role >= bot_member.top_role:
                failed.append(role.name)
                continue
            try:
                if add:
                    await member.add_roles(role, reason=f"Slash role command by {interaction.user}")
                else:
                    await member.remove_roles(role, reason=f"Slash role command by {interaction.user}")
                changed += 1
            except discord.HTTPException:
                failed.append(role.name)

        action = "إضافة" if add else "إزالة"
        text = f"تمت {action} **{changed}** رتبة لـ {member.mention}."
        if failed:
            text += "\nلم أستطع التعامل مع: " + ", ".join(f"`{x}`" for x in failed)

        await interaction.response.send_message(text, ephemeral=True)

    @app_commands.command(name="give_roles", description="إعطاء حتى 20 رتبة لعضو")
    @app_commands.describe(
        العضو="العضو",
        الرتبة1="الرتبة 1",
        الرتبة2="الرتبة 2",
        الرتبة3="الرتبة 3",
        الرتبة4="الرتبة 4",
        الرتبة5="الرتبة 5",
        الرتبة6="الرتبة 6",
        الرتبة7="الرتبة 7",
        الرتبة8="الرتبة 8",
        الرتبة9="الرتبة 9",
        الرتبة10="الرتبة 10",
        الرتبة11="الرتبة 11",
        الرتبة12="الرتبة 12",
        الرتبة13="الرتبة 13",
        الرتبة14="الرتبة 14",
        الرتبة15="الرتبة 15",
        الرتبة16="الرتبة 16",
        الرتبة17="الرتبة 17",
        الرتبة18="الرتبة 18",
        الرتبة19="الرتبة 19",
        الرتبة20="الرتبة 20",
    )
    async def give_roles(
        self, interaction: discord.Interaction, العضو: discord.Member,
        الرتبة1: discord.Role=None, الرتبة2: discord.Role=None, الرتبة3: discord.Role=None,
        الرتبة4: discord.Role=None, الرتبة5: discord.Role=None, الرتبة6: discord.Role=None,
        الرتبة7: discord.Role=None, الرتبة8: discord.Role=None, الرتبة9: discord.Role=None,
        الرتبة10: discord.Role=None, الرتبة11: discord.Role=None, الرتبة12: discord.Role=None,
        الرتبة13: discord.Role=None, الرتبة14: discord.Role=None, الرتبة15: discord.Role=None,
        الرتبة16: discord.Role=None, الرتبة17: discord.Role=None, الرتبة18: discord.Role=None,
        الرتبة19: discord.Role=None, الرتبة20: discord.Role=None
    ):
        roles = locals().copy()
        selected = [roles[f"الرتبة{i}"] for i in range(1, 21)]
        await self._apply(interaction, العضو, selected, True)

    @app_commands.command(name="remove_roles", description="إزالة حتى 20 رتبة من عضو")
    @app_commands.describe(
        العضو="العضو",
        الرتبة1="الرتبة 1",
        الرتبة2="الرتبة 2",
        الرتبة3="الرتبة 3",
        الرتبة4="الرتبة 4",
        الرتبة5="الرتبة 5",
        الرتبة6="الرتبة 6",
        الرتبة7="الرتبة 7",
        الرتبة8="الرتبة 8",
        الرتبة9="الرتبة 9",
        الرتبة10="الرتبة 10",
        الرتبة11="الرتبة 11",
        الرتبة12="الرتبة 12",
        الرتبة13="الرتبة 13",
        الرتبة14="الرتبة 14",
        الرتبة15="الرتبة 15",
        الرتبة16="الرتبة 16",
        الرتبة17="الرتبة 17",
        الرتبة18="الرتبة 18",
        الرتبة19="الرتبة 19",
        الرتبة20="الرتبة 20",
    )
    async def remove_roles(
        self, interaction: discord.Interaction, العضو: discord.Member,
        الرتبة1: discord.Role=None, الرتبة2: discord.Role=None, الرتبة3: discord.Role=None,
        الرتبة4: discord.Role=None, الرتبة5: discord.Role=None, الرتبة6: discord.Role=None,
        الرتبة7: discord.Role=None, الرتبة8: discord.Role=None, الرتبة9: discord.Role=None,
        الرتبة10: discord.Role=None, الرتبة11: discord.Role=None, الرتبة12: discord.Role=None,
        الرتبة13: discord.Role=None, الرتبة14: discord.Role=None, الرتبة15: discord.Role=None,
        الرتبة16: discord.Role=None, الرتبة17: discord.Role=None, الرتبة18: discord.Role=None,
        الرتبة19: discord.Role=None, الرتبة20: discord.Role=None
    ):
        roles = locals().copy()
        selected = [roles[f"الرتبة{i}"] for i in range(1, 21)]
        await self._apply(interaction, العضو, selected, False)

async def setup(bot):
    await bot.add_cog(Roles(bot))
