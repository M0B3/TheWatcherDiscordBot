import discord
from discord import app_commands
from discord.ext import commands, tasks
import mysql.connector
import os
import datetime
from dotenv import load_dotenv

load_dotenv('config.env')

def get_connection(): # Function to get a database connection
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # maybe change ID's in a secured way later #
        self.leaderboard_channel_id = 1245676190434328658  # ID of your leaderboard channel

        self.role_ids = {
            "🥇 1er": 1336645452514328687,  # Role ID for 1st place
            "🥈 2ème": 1336645782438154271,  # Role ID for 2nd place
            "🥉 3ème": 1336646105881907201   # Role ID for 3rd place
        }

        self.update_leaderboard.start()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"🥇{__name__} is ready.")

    def cog_unload(self):
        self.update_leaderboard.cancel()  # cancel the task when the cog is unloaded

    @tasks.loop(minutes=1)  # verify every minute
    async def update_leaderboard(self):
        now = datetime.datetime.now()
        if now.hour == 12 and now.minute == 00:  # Check for 12:00 PM
            guilds = self.bot.guilds

            for guild in guilds:
                leaderboard_channel = self.bot.get_channel(self.leaderboard_channel_id)
                if leaderboard_channel:
                    await self.send_leaderboard(leaderboard_channel, guild) # Send the leaderboard to the channel

    async def send_leaderboard(self, channel, guild): # Function to send the leaderboard
        db = get_connection()
        cursor = db.cursor()
        cursor.execute(
            "SELECT user_id, level, xp FROM Users WHERE guild_id = %s ORDER BY level DESC, xp DESC LIMIT 10",
            (guild.id,)
        ) # Get top 10 users by level and xp
        top_users = cursor.fetchall()
        cursor.close()
        db.close() # Close the database connection

        if not top_users:
            await channel.send("Aucun joueur n'est encore classé.") # If no users found, prevent error
            return

        LB_embed = discord.Embed( # Create the embed for the leaderboard
            title="🏆 Classement des joueurs 🏆",
            description="Top 10 des joueurs avec le plus d'XP",
            color=discord.Color.blue()
        )

        medals = ["🥇", "🥈", "🥉"] + ["🔹"] * 7 # Medals for top 3 and others
        new_top_users = []

        for index, (user_id, level, xp) in enumerate(top_users): # Add each user to the embed
            user = guild.get_member(user_id) or await guild.fetch_member(user_id)
            mention = user.display_name if user else "Utilisateur introuvable"
            LB_embed.add_field(name=f"{medals[index]} {mention}", value=f"Niveau **{level}** | XP: `{xp}`", inline=False) # Add user info to embed

            if index < 3 and user:
                new_top_users.append(user) # Collect top 3 users for role assignment

        # Customize the embed image and footer
        LB_embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/1330848782312538123/1330851613404958752/White_and_Grey_Square_Curvy_Photography_Brand_Logo.png?ex=6792c766&is=679175e6&hm=9b4201b675a5acf264d1ef013a7924667bc356b175150fbc26b425ff26d1973a&')
        LB_embed.set_footer(text="Continuez à chatter pour monter dans le classement ! 🚀") # Small italic text at the bottom

        await channel.send(embed=LB_embed) # Send the embed to the channel
        await self.assign_roles(guild, new_top_users) # Assign roles to top 3 users

    async def assign_roles(self, guild, new_top_users): # Function to assign roles to top 3 users
        roles = {name: guild.get_role(role_id) for name, role_id in self.role_ids.items()}

        # Verify that all roles exist
        for name, role in roles.items():
            if not role:
                print(f"⚠️ Erreur : Le rôle {name} n'existe pas dans le serveur {guild.name}.")
                return

        # Delete all roles from last winners
        for member in guild.members:
            for role in roles.values():
                if role in member.roles:
                    await member.remove_roles(role)

        # Add the new roles to the winners
        for index, user in enumerate(new_top_users):
            if user and index < 3:
                role_name = list(self.role_ids.keys())[index]
                role = roles[role_name]
                await user.add_roles(role)
                print(f"✅ {user.display_name} a reçu le rôle {role_name}.")

    @app_commands.command(name="simulate12h", description="Simule 12h pour envoyer le leaderboard.")
    @commands.has_permissions(administrator=True)
    async def simulate_noon(self, interaction: discord.Interaction):
        leaderboard_channel = self.bot.get_channel(self.leaderboard_channel_id)
        if not leaderboard_channel:
            await interaction.response.send_message("Le salon de leaderboard n'a pas été trouvé.", ephemeral=True)
            return
    
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("Cette commande doit être utilisée dans un serveur.", ephemeral=True)
            return
    
        await self.send_leaderboard(leaderboard_channel, guild)
        await interaction.response.send_message("💡 Simulation d'envoi du leaderboard effectuée !", ephemeral=True)

    @update_leaderboard.before_loop
    async def before_update_leaderboard(self): # Wait until the bot is ready
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))