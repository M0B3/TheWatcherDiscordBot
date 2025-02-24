import discord
from discord.ext import commands, tasks
import sqlite3
import datetime

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.leaderboard_channel_id = 1245676190434328658  # ID du salon leaderboard

        self.role_ids = {
            "🥇 1er": 1336645452514328687,  # Remplace par l'ID réel du rôle 1er
            "🥈 2ème": 1336645782438154271,  # Remplace par l'ID réel du rôle 2ème
            "🥉 3ème": 1336646105881907201   # Remplace par l'ID réel du rôle 3ème
        }

        # Démarrer la tâche automatique
        self.update_leaderboard.start()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"🥇{__name__} is ready.")

    def cog_unload(self):
        self.update_leaderboard.cancel()  # cancel the task when the cog is unloaded

    @tasks.loop(minutes=1)  # verify every minute
    async def update_leaderboard(self):
        now = datetime.datetime.now()
        if now.hour == 12 and now.minute == 00:  # 12h00 
            guilds = self.bot.guilds  

            for guild in guilds:
                leaderboard_channel = self.bot.get_channel(self.leaderboard_channel_id)
                if leaderboard_channel:
                    await self.send_leaderboard(leaderboard_channel, guild)

    async def send_leaderboard(self, channel, guild):
        connexion = sqlite3.connect("./database/levels.db")
        cursor = connexion.cursor()
        cursor.execute("SELECT user_id, level, xp FROM Users WHERE guild_id = ? ORDER BY level DESC, xp DESC LIMIT 10", (guild.id,))
        top_users = cursor.fetchall()
        connexion.close()

        if not top_users:
            await channel.send("Aucun joueur n'est encore classé.")
            return

        LB_embed = discord.Embed(
            title="🏆 Classement des joueurs 🏆",
            description="Top 10 des joueurs avec le plus d'XP",
            color=discord.Color.blue()
        )

        medals = ["🥇", "🥈", "🥉"] + ["🔹"] * 7
        new_top_users = []

        for index, (user_id, level, xp) in enumerate(top_users):
            user = guild.get_member(user_id) or await guild.fetch_member(user_id)
            mention = user.display_name if user else "Utilisateur introuvable"
            
            LB_embed.add_field( name=f"{medals[index]} {mention}", value=f"Niveau **{level}** | XP: `{xp}`", inline=False)

            if index < 3 and user:
                new_top_users.append(user)

        LB_embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/1330848782312538123/1330851613404958752/White_and_Grey_Square_Curvy_Photography_Brand_Logo.png?ex=6792c766&is=679175e6&hm=9b4201b675a5acf264d1ef013a7924667bc356b175150fbc26b425ff26d1973a&')
        LB_embed.set_footer(text="Continuez à chatter pour monter dans le classement ! 🚀")

        await channel.send(embed=LB_embed)

        await self.assign_roles(guild, new_top_users)

    async def assign_roles(self, guild, new_top_users):
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

    @update_leaderboard.before_loop
    async def before_update_leaderboard(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))