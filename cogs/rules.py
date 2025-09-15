import discord
from discord.ext import commands
from discord import app_commands
import mysql.connector
import os
from dotenv import load_dotenv

# Load database credentials from .env file
load_dotenv('config.env')

def get_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

MEMBER_ROLE_ID = 1337360310943875113  
MOD_ROLE_NAME = "ModoModo"  
class AgeSelect(discord.ui.Select):
    def __init__(self, member: discord.Member):
        self.member = member
        options = [ # dropdown options for age verification
            discord.SelectOption(label="Moins de 13 ans", description="L'âge requis en europe est 13ans et +, mais l'utilisation de donées est de 15ans et +."),
            discord.SelectOption(label="13-17 ans", description="Vous obtiendrez le rôle Vérifié."),
            discord.SelectOption(label="18 ans et plus", description="Vous obtiendrez le rôle Vérifié.")
        ]
        super().__init__(placeholder="Sélectionnez votre âge", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        role = guild.get_role(MEMBER_ROLE_ID)

        if self.values[0] == "Moins de 13 ans": # if user selects under 13 kick them
            await interaction.user.send("⛔ Vous devez avoir au moins 13 ans pour rejoindre ce serveur. Vous avez été expulsé.")
            await interaction.user.kick(reason="Âge inférieur à 13 ans")
        else:
            if role not in interaction.user.roles:
                await interaction.user.add_roles(role)
                cog = interaction.client.get_cog("Rules")
                if cog:
                    cog.register_acceptance(interaction.user)
                await interaction.response.send_message("✅ Vous avez accepté les règles ! Le rôle **Vérifié** vous a été attribué.", ephemeral=True)
            else:
                await interaction.response.send_message("🔹 Vous avez déjà le rôle **Vérifié**.", ephemeral=True)

class AgeView(discord.ui.View):
    def __init__(self, member: discord.Member):
        super().__init__(timeout=None)
        self.add_item(AgeSelect(member))

class RulesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) #active all times

    @discord.ui.button(label="✅ Accepter les règles", style=discord.ButtonStyle.green, custom_id="accept_rules")
    async def accept_rules(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Veuillez sélectionner votre âge :", view=AgeView(interaction.user), ephemeral=True)

class Rules(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(RulesView())  # reboot percistance
        self.create_rules_table()

    def create_rules_table(self):
        db = get_connection()
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS member_rules_accept (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(255),
                accepted_at DATETIME
                )
            """)
        db.commit()
        cursor.close()
        db.close()

    def register_acceptance(self, user: discord.Member): # log acceptance in database
        db = get_connection()
        cursor = db.cursor()
        cursor.execute("""
                       INSERT INTO member_rules_accept (user_id, username, accepted_at)
                       VALUES (%s, %s, NOW())
                           ON DUPLICATE KEY UPDATE
                                                username = VALUES(username), accepted_at = VALUES(accepted_at)
                       """, (user.id, str(user)))
        db.commit()
        cursor.close()
        db.close()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"📜{__name__} is ready.")

    @app_commands.command(name="rules", description="Affiche les règles du serveur.")
    async def send_rules(self, interaction: discord.Interaction):
        guild = interaction.guild
        owner = guild.owner
        LOGO_URL = "https://cdn.discordapp.com/attachments/1330848782312538123/1330851613404958752/White_and_Grey_Square_Curvy_Photography_Brand_Logo.png"

        # mod role verification
        mod_role = discord.utils.get(guild.roles, name=MOD_ROLE_NAME)
        if mod_role not in interaction.user.roles:
            await interaction.response.send_message("⛔ Vous n'avez pas la permission d'envoyer les règles.", ephemeral=True)
            return

        embed = discord.Embed(
            title="📜 Règles du Serveur",
            description=( # rules description in French
                "**Bienvenue sur LoneComp !**\n"
                "Merci de respecter ces règles pour une bonne ambiance. 🚀\n\n"
                "1️⃣ **Respect** : Pas d'insultes, harcèlement ou discrimination.\n"
                "2️⃣ **Pas de spam** : Évitez le flood et la pub non autorisée.\n"
                "3️⃣ **Contenu approprié** : Pas de NSFW, politique ou sujets sensibles.\n"
                "4️⃣ **Pas de liens suspects** : Toute tentative de phishing est interdite.\n"
                "5️⃣ **Écoutez le staff** : Respectez les décisions des modérateurs.\n\n"
                "*Le non-respect des règles peut entraîner des sanctions.* ⚠️\n\n"
                "👉 **Cliquez sur le bouton ci-dessous pour accepter les règles et accéder au serveur !**"
            ),
            color=discord.Color.purple()
        )
        embed.set_thumbnail(url=LOGO_URL)
        embed.set_footer(text=f"👑 Propriétaire : {owner}", icon_url=owner.display_avatar.url)

        await interaction.response.send_message(embed=embed, view=RulesView())
        print("✅ Message des règles envoyé avec bouton !")

async def setup(bot):
    await bot.add_cog(Rules(bot))
