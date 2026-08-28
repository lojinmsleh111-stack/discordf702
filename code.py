# نظام إرسال الكود موجود داخل cogs/gv_roles.py ضمن زر "إرسال الكود".
# هذا الملف موجود للفصل والتنظيم كما طلبت.
from discord.ext import commands

class Code(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

async def setup(bot):
    await bot.add_cog(Code(bot))
