import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import asyncio
import re

class ModerationCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"👮 {__name__} is ready.")

    def get_warn_count(self, user_id):
        with sqlite3.connect("./database/moderation.db") as db: # Get the number of warnings
            cursor = db.cursor()
            cursor.execute("SELECT warn_count FROM sanctions WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
        return result[0] if result else 0

    def reset_warnings(self, user_id):
        with sqlite3.connect("./database/moderation.db") as db: # reset the warnings
            cursor = db.cursor()
            cursor.execute("DELETE FROM sanctions WHERE user_id = ?", (user_id,))
            db.commit()

    @app_commands.command(name="warnings", description="Affiche les sanctions d'un utilisateur")
    @app_commands.describe(user="Utilisateur dont vous voulez voir les avertissements")
    async def warnings(self, interaction: discord.Interaction, user: discord.Member):
        warn_count = self.get_warn_count(user.id)
        
        embed = discord.Embed(title="📜 Sanctions", color=discord.Color.red())
        embed.add_field(name="Utilisateur", value=user.mention, inline=True)
        embed.add_field(name="Nombre d'avertissements", value=warn_count, inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @warnings.error
    async def warnings_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingRole):
            await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)

    @app_commands.command(name="clearwarnings", description="Réinitialise les avertissements d'un utilisateur")
    @app_commands.checks.has_role("ModoModo")
    @app_commands.describe(user="ID de l'utilisateur à réinitialiser")
    async def clear_warnings(self, interaction: discord.Interaction, user: discord.Member):
        user_id = user.id  #Get user id
        self.reset_warnings(user_id)

        await interaction.response.send_message(f"✅ Les avertissements de {user.mention} ont été réinitialisés.", ephemeral=True)

    @clear_warnings.error
    async def clear_warnings_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingRole):
            await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ModerationCommands(bot))
