import discord
from discord.ext import commands
from discord import app_commands
import mysql.connector
import os
import asyncio
import re
from dotenv import load_dotenv

load_dotenv('config.env')

def get_connection(): # Function to get a database connection
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

class AutoModeration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.link_regex = re.compile(r"(https?://|www\.)\S+") # Regex to detect links
        self.warn_cache = {}
        self.banned_words = set()
        self.trusted_links = set()
        self.preload_data() # Load data on startup

    def preload_data(self):
        self.load_banned_words()
        self.load_trusted_links()
        self.preload_warnings()

    def load_banned_words(self): # Load banned words from the database
        db = get_connection()
        cursor = db.cursor()
        cursor.execute("SELECT word FROM banned_words")
        result = cursor.fetchall()
        self.banned_words = set(word[0] for word in result)
        cursor.close()
        db.close()

    def load_trusted_links(self): # Load trusted links from the database
        db = get_connection()
        cursor = db.cursor()
        cursor.execute("SELECT link FROM trusted_links")
        result = cursor.fetchall()
        self.trusted_links = set(link for link in result)
        cursor.close()
        db.close()

    def preload_warnings(self): # Load existing warnings from the database
        db = get_connection()
        cursor = db.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS sanctions (user_id BIGINT PRIMARY KEY, username VARCHAR(255), warn_count INT)")
        db.commit()
        cursor.execute("SELECT user_id, warn_count FROM sanctions")
        self.warn_cache = {user_id: warn_count for user_id, warn_count in cursor.fetchall()}
        cursor.close()
        db.close()

    def get_warn_count(self, user_id): # Get the current warn count for a user
        return self.warn_cache.get(user_id, 0)

    def update_warn_count(self, user_id, username): # Update the warn count for a user
        current_count = self.warn_cache.get(user_id, 0) + 1
        self.warn_cache[user_id] = current_count

        db = get_connection()
        cursor = db.cursor()
        cursor.execute("""
                       INSERT INTO sanctions (user_id, username, warn_count)
                       VALUES (%s, %s, 1)
                           ON DUPLICATE KEY UPDATE warn_count = warn_count + 1, username = VALUES(username)
                       """, (user_id, username)) # Update username in case it changed
        db.commit()
        cursor.close()
        db.close()
        return current_count

    def reset_warns(self, user_id): # Reset the warn count for a user
        self.warn_cache.pop(user_id, None)

        db = get_connection()
        cursor = db.cursor()
        cursor.execute("DELETE FROM sanctions WHERE user_id = %s", (user_id,)) # Remove user from warn database
        db.commit()
        cursor.close()
        db.close()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"👮 {__name__} is ready.")

    @commands.Cog.listener()
    async def on_message(self, message):
        intents = discord.Intents.default() # Ensure message content intent is enabled
        intents.message_content = True # Enable message content intent

        if message.author.bot: # Ignore messages from bots
            return

        print(f"Message reçu: {message.content}")  # Debug check the receipt message 

        lower_msg = message.content.lower() # Convert message to lowercase for comparison

        # Debug prints for banned words and trusted links
        print(f"Mots bannis: {self.banned_words}")
        print(f"Liens de confiance: {self.trusted_links}")

        contains_bad_word = any(word in lower_msg for word in self.banned_words) # Check for banned words
        print(f"Contient mot interdit ?: {contains_bad_word}") # Debug check for bad words true or false

        contains_bad_link = (
                self.link_regex.search(message.content)
                and not any(link in message.content for link in self.trusted_links)
                and not message.content.startswith("https://tenor.com")
        ) # Check for bad links
        print(f"Contient lien non autorisé ?: {contains_bad_link}") # Debug check for bad words true or false

        if contains_bad_word or contains_bad_link: # If message contains bad word or bad link
            print(f"Message supprimé de {message.author}: {message.content}") # Debug print before deleting
            await message.delete()
            await self.warn_user(message)

            await self.bot.process_commands(message) # Ensure commands still work

    async def warn_user(self, message): # Warn function for users
        member = message.author
        guild = message.guild
        warn_count = self.update_warn_count(member.id, str(member))

        embed = discord.Embed(title="⚠️ Avertissement", color=discord.Color.orange())
        embed.add_field(name="Utilisateur", value=member.mention, inline=True)
        embed.add_field(name="Infraction", value=f"Utilisation d'un mot interdit ({warn_count}/4)", inline=True)
        await message.channel.send(embed=embed)

        print(f"{member} a reçu un avertissement ({warn_count}/4).") # Debug print for warning

        if warn_count == 3:
            mute_role = discord.utils.get(guild.roles, name="Muted") # Ensure a Muted role exists by name (test need to change asap)
            if mute_role:
                await member.add_roles(mute_role)
                await message.channel.send(f"{member.mention} a été muté pendant 10 minutes.")
                await asyncio.sleep(600) # Mute duration
                await member.remove_roles(mute_role)
            else:
                print("⚠️ Le rôle 'Muted' n'existe pas ! Pense à le créer.") # Debug print if Muted role doesn't exist
        elif warn_count >= 4: # Ban user on 4th warning
            await message.channel.send(f"{member.mention} a été banni pour récidive.")
            await guild.ban(member, reason="Trop d'infractions au filtre anti-insultes")
            self.reset_warns(member.id)

    @app_commands.command(name="refreshlists", description="Recharge les mots bannis et liens de confiance") # Command to refresh lists after adding new ones
    @app_commands.checks.has_permissions(administrator=True)
    async def refresh_lists(self, interaction: discord.Interaction):
        self.load_banned_words()
        self.load_trusted_links()
        await interaction.response.send_message(
            "🔄 Listes de mots bannis et liens de confiance rechargées avec succès !", ephemeral=True
        )

    @refresh_lists.error # Error handling for refresh_lists command
    async def refresh_lists_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True
            )

    async def close_connection(self):
        print("🔌 Connexion à la base de données fermée.")

async def setup(bot):
    await bot.add_cog(AutoModeration(bot))
