import discord
from discord.ext import commands
from discord import app_commands
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv('config.env')


def get_connection(): # Establish a connection to the database
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )


class ModerationCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.banned_words = set()
        self.trusted_links = set()
        self.setup_db()
        self.load_banned_words()
        self.load_trusted_links()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"👮 {__name__} is ready.")

    def setup_db(self): # Create the necessary tables if they don't exist
        db = get_connection()
        cursor = db.cursor()
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS sanctions
                       (
                           user_id BIGINT PRIMARY KEY,
                           username VARCHAR(255),
                           warn_count INT
                           )
                       """)
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS banned_words
                       (
                           word VARCHAR(255) PRIMARY KEY
                           )
                       """)
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS trusted_links
                       (
                           link VARCHAR(255) PRIMARY KEY
                           )
                       """)
        db.commit()
        cursor.close()
        db.close()

    def load_banned_words(self): # Load banned words from the database
        db = get_connection()
        cursor = db.cursor()
        cursor.execute("SELECT word FROM banned_words")
        words = cursor.fetchall()
        cursor.close()
        db.close()
        self.banned_words = set(word[0] for word in words)

    def load_trusted_links(self): # Load trusted links from the database
        db = get_connection()
        cursor = db.cursor()
        cursor.execute("SELECT link FROM trusted_links")
        links = cursor.fetchall()
        cursor.close()
        db.close()
        self.trusted_links = set(link[0] for link in links)

    def add_banned_word(self, word): # Add a banned word to the database and the set
        db = get_connection()
        cursor = db.cursor()
        cursor.execute("INSERT IGNORE INTO banned_words (word) VALUES (%s)", (word.lower(),))
        db.commit()
        cursor.close()
        db.close()
        self.banned_words.add(word.lower())

    def add_trusted_link(self, link): # Add a trusted link to the database and the set
        db = get_connection()
        cursor = db.cursor()
        cursor.execute("INSERT IGNORE INTO trusted_links (link) VALUES (%s)", (link.lower(),))
        db.commit()
        cursor.close()
        db.close()
        self.trusted_links.add(link.lower())

    def get_warn_count(self, user_id): # Get the number of warnings for a user
        db = get_connection()
        cursor = db.cursor()
        cursor.execute("SELECT warn_count FROM sanctions WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        cursor.close()
        db.close()
        return result[0] if result else 0

    def reset_warns(self, user_id): # Reset the warnings function for a user
        db = get_connection()
        cursor = db.cursor()
        cursor.execute("DELETE FROM sanctions WHERE user_id = %s", (user_id,))
        db.commit()
        cursor.close()
        db.close()

    @app_commands.command(name="addbannedword", description="Ajoute un mot à la liste des mots interdits")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(word="Mot à interdire")
    async def add_banned_word_command(self, interaction: discord.Interaction, word: str):
        if word.lower() not in self.banned_words:
            self.add_banned_word(word)
            await interaction.response.send_message(f"🚫 Le mot `{word}` a été ajouté à la liste des mots interdits.",
                                                    ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Le mot `{word}` est déjà dans la liste des mots interdits.",
                                                    ephemeral=True)

    @app_commands.command(name="addtrustedlink", description="Ajoute un lien à la liste des liens de confiance")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(link="Lien à ajouter en tant que lien de confiance")
    async def add_trusted_link_command(self, interaction: discord.Interaction, link: str):
        if link.lower() not in self.trusted_links:
            self.add_trusted_link(link)
            await interaction.response.send_message(
                f"🔗 Le lien `{link}` a été ajouté à la liste des liens de confiance.", ephemeral=True)
        else:
            await interaction.response.send_message(
                f"❌ Le lien `{link}` est déjà dans la liste des liens de confiance.", ephemeral=True)

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
    @commands.has_permissions(administrator=True)
    @app_commands.describe(user="ID de l'utilisateur à réinitialiser")
    async def clear_warnings(self, interaction: discord.Interaction, user: discord.Member):
        self.reset_warns(user.id)
        await interaction.response.send_message(f"✅ Les avertissements de {user.mention} ont été réinitialisés.", ephemeral=True)

    @clear_warnings.error
    async def clear_warnings_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingRole):
            await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ModerationCommands(bot))
