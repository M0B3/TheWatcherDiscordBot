import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import asyncio
import re

class AutoModeration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.banned_words = self.load_banned_words()
        self.trusted_links = self.load_trusted_links()
        self.warn_cache = {}  # Cache pour éviter trop de requêtes SQL
        self.link_regex = re.compile(r"(https?://|www\.)\S+")
        self.preload_warnings()

    def load_banned_words(self):
        try:
            with open("banned_words.txt", "r", encoding="utf-8") as file:
                return set(word.strip().lower() for word in file.readlines())
        except FileNotFoundError:
            print("⚠️ Fichier banned_words.txt introuvable !")
            return set()
        
    def load_trusted_links(self):
        try:
            with open("trusted_links.txt", "r", encoding="utf-8") as file:
                return set(line.strip().lower() for line in file.readlines())
        except FileNotFoundError:
            print("⚠️ Fichier trusted_links.txt introuvable !")
            return set()

    def preload_warnings(self):
        """Charge les avertissements en cache pour éviter trop d'accès à la base."""
        with sqlite3.connect("./database/moderation.db") as db:
            cursor = db.cursor()
            cursor.execute("SELECT user_id, warn_count FROM sanctions")
            self.warn_cache = {user_id: warn_count for user_id, warn_count in cursor.fetchall()}

    def get_warn_count(self, user_id):
        return self.warn_cache.get(user_id, 0)

    def update_warn_count(self, user_id):
        """Met à jour l'avertissement en mémoire et en base."""
        self.warn_cache[user_id] = self.warn_cache.get(user_id, 0) + 1
        
        with sqlite3.connect("./database/moderation.db") as db:
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO sanctions (user_id, warn_count)
                VALUES (?, 1)
                ON CONFLICT(user_id)
                DO UPDATE SET warn_count = warn_count + 1
            """, (user_id,))
            db.commit()
        return self.warn_cache[user_id]

    def reset_warns(self, user_id):
        """Réinitialise les avertissements d'un utilisateur."""
        self.warn_cache.pop(user_id, None)
        with sqlite3.connect("./database/moderation.db") as db:
            cursor = db.cursor()
            cursor.execute("DELETE FROM sanctions WHERE user_id = ?", (user_id,))
            db.commit()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"👮 {__name__} is ready.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        lower_msg = message.content.lower()
        contains_bad_word = any(word in lower_msg for word in self.banned_words)
        contains_bad_link = self.link_regex.search(message.content) and not any(link in message.content for link in self.trusted_links)

        if contains_bad_word or contains_bad_link:
            await message.delete()
            await self.warn_user(message)

    async def warn_user(self, message):
        member = message.author
        guild = message.guild
        warn_count = self.update_warn_count(member.id)

        embed = discord.Embed(title="⚠️ Avertissement", color=discord.Color.orange())
        embed.add_field(name="Utilisateur", value=member.mention, inline=True)
        embed.add_field(name="Infraction", value=f"Utilisation d'un mot interdit ({warn_count}/4)", inline=True)

        await message.channel.send(embed=embed)
        print(f"{member} a reçu un avertissement ({warn_count}/4).")

        if warn_count == 3:
            mute_role = discord.utils.get(guild.roles, name="Muted")
            if mute_role:
                await member.add_roles(mute_role)
                await message.channel.send(f"{member.mention} a été muté pendant 10 minutes.")
                await asyncio.sleep(600)
                await member.remove_roles(mute_role)
            else:
                print("⚠️ Le rôle 'Muted' n'existe pas ! Pense à le créer.")

        elif warn_count >= 4:
            await message.channel.send(f"{member.mention} a été banni pour récidive.")
            await guild.ban(member, reason="Trop d'infractions au filtre anti-insultes")
            self.reset_warns(member.id)

    @app_commands.command(name="links", description="Recharge la liste des liens de confiance")
    @app_commands.checks.has_role("ModoModo")  # check modo role
    async def links(self, interaction: discord.Interaction):
        self.trusted_links = self.load_trusted_links()
        await interaction.response.send_message("✅ Liste des liens de confiance mise à jour !", ephemeral=True)

    @links.error
    async def reload_trusted_links_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingRole):
            await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)

    async def close_connection(self):
        """Fermeture propre de la connexion à la base de données."""
        print("🔌 Connexion à la base de données fermée.")

async def setup(bot):
    await bot.add_cog(AutoModeration(bot))
