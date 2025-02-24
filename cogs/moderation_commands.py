import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import asyncio
import re

class ModerationCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.banned_words = self.load_banned_words()
        self.trusted_links = self.load_trusted_links()
        self.setup_db()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"👮 {__name__} is ready.")

    def setup_db(self):
        with sqlite3.connect("./database/moderation.db") as db:
            cursor = db.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sanctions (
                    user_id INTEGER PRIMARY KEY,
                    warn_count INTEGER
                )
            """)
            db.commit()

    def load_banned_words(self):
        with open("banned_words.txt", "r", encoding="utf-8") as file:
            return [line.strip() for line in file.readlines()]

    def load_trusted_links(self):
        with open("trusted_links.txt", "r", encoding="utf-8") as file:
            return [line.strip() for line in file.readlines()]

    def add_banned_word(self, word):
        with open("banned_words.txt", "a", encoding="utf-8") as file:
            file.write(word.lower() + "\n")

    def add_trusted_link(self, link):
        with open("trusted_links.txt", "a", encoding="utf-8") as file:
            file.write(link.lower() + "\n")

    def get_warn_count(self, user_id):
        with sqlite3.connect("./database/moderation.db") as db:
            cursor = db.cursor()
            cursor.execute("SELECT warn_count FROM sanctions WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
        return result[0] if result else 0

    def reset_warnings(self, user_id):
        with sqlite3.connect("./database/moderation.db") as db:
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
        user_id = user.id  # Get user id
        self.reset_warnings(user_id)

        await interaction.response.send_message(f"✅ Les avertissements de {user.mention} ont été réinitialisés.", ephemeral=True)

    @clear_warnings.error
    async def clear_warnings_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingRole):
            await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)

    @app_commands.command(name="addbannedword", description="Ajoute un mot à la liste des mots interdits")
    @app_commands.checks.has_role("ModoModo")
    @app_commands.describe(word="Mot à interdire")
    async def add_banned_word_command(self, interaction: discord.Interaction, word: str):
        # check existing word
        with open("banned_words.txt", "r", encoding="utf-8") as file:
            banned_words = file.readlines()
        
        if word.lower() + "\n" not in banned_words:
            self.add_banned_word(word)
            self.load_banned_words()
            await interaction.response.send_message(f"🚫 Le mot `{word}` a été ajouté à la liste des mots interdits.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Le mot `{word}` est déjà dans la liste des mots interdits.", ephemeral=True)

    @app_commands.command(name="addtrustedlink", description="Ajoute un lien à la liste des liens de confiance")
    @app_commands.checks.has_role("ModoModo")
    @app_commands.describe(link="Lien à ajouter en tant que lien de confiance")
    async def add_trusted_link_command(self, interaction: discord.Interaction, link: str):
        # Check existing link
        with open("trusted_links.txt", "r", encoding="utf-8") as file:
            trusted_links = file.readlines()
        
        if link.lower() + "\n" not in trusted_links:
            self.add_trusted_link(link)
            self.load_trusted_links()
            await interaction.response.send_message(f"🔗 Le lien `{link}` a été ajouté à la liste des liens de confiance.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Le lien `{link}` est déjà dans la liste des liens de confiance.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ModerationCommands(bot))
