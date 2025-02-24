import discord
from discord.ext import commands
from discord import Embed

class CogTemplate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"🪪{__name__} is ready.")

    """Just an exemple command, delete it if you want"""
    @commands.command()
    async def ping(self, ctx):
        ping_embed = Embed(title="Ping", description="Latence en ms.", color=0x00ff00)
        ping_embed.add_field(name=f"{self.bot.user.name} a une latence de", value=f"{round(self.bot.latency * 1000)}ms", inline=False)
        ping_embed.set_footer(text=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        await ctx.send(embed=ping_embed)
    """Just an exemple command, delete it if you want"""

async def setup(bot):
    await bot.add_cog(CogTemplate(bot))