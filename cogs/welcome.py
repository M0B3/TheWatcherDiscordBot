import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.create_welcome_table()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"📮{__name__} is ready.")

    def create_welcome_table(self):
        with sqlite3.connect("./database/welcome.db") as db:
            cursor = db.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS welcome_message (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    message TEXT,
                    field1_name TEXT,
                    field1_value TEXT,
                    field2_name TEXT,
                    field2_value TEXT,
                    field3_name TEXT,
                    field3_value TEXT,
                    footer TEXT,
                    image_url TEXT
                )
            """)
            db.commit()

    def get_welcome_message(self):
        with sqlite3.connect("./database/welcome.db") as db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM welcome_message WHERE id = 1")
            result = cursor.fetchone()
        
        if result:
            return {
                "title": result[1] or "Bienvenue !",
                "message": result[2] or "Bienvenue sur le serveur, {user.mention}! 🎉",
                "fields": [
                    {"name": result[3], "value": result[4]},
                    {"name": result[5], "value": result[6]},
                    {"name": result[7], "value": result[8]}
                ],
                "footer": result[9] or "Merci de faire partie de la communauté !",
                "image_url": result[10] or None
            }
        else:
            return {
                "title": "Bienvenue chez {guild.name}",
                "message": "Bienvenue sur le serveur, {user.mention}! 🎉",
                "fields": [
                    {"name": "Rôle", "value": "{user.top_role}"},
                    {"name": "Date d'adhésion", "value": "{user.joined_at}"},
                    {"name": "Info supplémentaire", "value": "Bienvenue sur {guild.name}"}
                ],
                "footer": "Merci de faire partie de la communauté !",
                "image_url": None
            }
    
    def update_welcome_message(self, title, message, field1_name, field1_value, field2_name, field2_value, field3_name, field3_value, footer, image_url):
        with sqlite3.connect("./database/welcome.db") as db:
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO welcome_message (id, title, message, field1_name, field1_value, field2_name, field2_value, field3_name, field3_value, footer, image_url)
                VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = ?, message = ?,
                    field1_name = ?, field1_value = ?,
                    field2_name = ?, field2_value = ?,
                    field3_name = ?, field3_value = ?,
                    footer = ?, image_url = ?
            """, (title, message, field1_name, field1_value, field2_name, field2_value, field3_name, field3_value, footer, image_url,
                  title, message, field1_name, field1_value, field2_name, field2_value, field3_name, field3_value, footer, image_url))
            db.commit()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member): #with debug print, somehow it crash the bot

        print(f"🔹 Nouveau membre détecté: {member}")

        welcome_channel = member.guild.get_channel(1245723587747381310)
        if not welcome_channel:
            print("❌ Erreur : Salon de bienvenue introuvable.")
            return

        if not welcome_channel.permissions_for(member.guild.me).send_messages:
            print("❌ Erreur : Le bot ne peut pas envoyer de messages ici.")
            return
        if not welcome_channel.permissions_for(member.guild.me).embed_links:
            print("❌ Erreur : Le bot ne peut pas envoyer d'embed ici.")
            return
        
        data = self.get_welcome_message()

        try:
            embed = discord.Embed(
            title=str(data["title"]).format(guild=member.guild),
            description=str(data["message"]).format(user=member, guild=member.guild),
            color=discord.Color.purple()
            )

            if member.guild.icon:
                embed.set_thumbnail(url=member.display_avatar.url)
            if data["image_url"]:
                embed.set_image(url=data["image_url"])

            for field in data["fields"]:
                if field["name"] and field["value"]:
                    try:
                        embed.add_field(name=str(field["name"]), value=str(field["value"]).format(user=member), inline=False)
                    except Exception as e:
                        print(f"❌ Erreur en ajoutant un champ: {e}")

            embed.set_footer(text=data["footer"])
            await welcome_channel.send(embed=embed)
            print("✅ Message de bienvenue envoyé !")

        except Exception as e:
            print(f"❌ Erreur lors de l'envoi du message de bienvenue: {e}")
 
    @app_commands.command(name="setwelcome", description="Définit un nouveau message de bienvenue (Réservé aux admins)")
    @app_commands.checks.has_role("ModoModo")
    async def set_welcome(self, interaction: discord.Interaction, title: str, message: str, field1_name: str = None, field1_value: str = None, field2_name: str = None, field2_value: str = None, field3_name: str = None, field3_value: str = None, footer: str = None, image_url: str = None):
        self.update_welcome_message(title, message, field1_name, field1_value, field2_name, field2_value, field3_name, field3_value, footer, image_url)
        await interaction.response.send_message("✅ Message de bienvenue mis à jour avec succès !", ephemeral=True)

    @app_commands.command(name="simulate_join", description="Simule l'arrivée d'un nouveau membre (Admin uniquement)")
    @app_commands.checks.has_role("ModoModo")
    async def simulate_join(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("❌ Erreur : Impossible de simuler pour un utilisateur hors du serveur.", ephemeral=True)
            return
    
        await self.on_member_join(interaction.user)
        await interaction.response.send_message("✅ Simulation de bienvenue effectuée !", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
