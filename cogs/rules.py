import discord
from discord.ext import commands
from discord import app_commands

MEMBER_ROLE_ID = 1337360310943875113  
MOD_ROLE_NAME = "ModoModo"  

class RulesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # active all time

    @discord.ui.button(label="✅ Accepter les règles", style=discord.ButtonStyle.green, custom_id="accept_rules")
    async def accept_rules(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user
        role = guild.get_role(MEMBER_ROLE_ID)

        if role is None:
            await interaction.response.send_message("⚠️ Le rôle 'Vérifié' n'existe pas. Contactez un admin.", ephemeral=True)
            return

        if role not in member.roles:
            await member.add_roles(role)
            await interaction.response.send_message("✅ Vous avez accepté les règles ! Le rôle **Vérifié** vous a été attribué.", ephemeral=True)
        else:
            await interaction.response.send_message("🔹 Vous avez déjà le rôle **Vérifié**.", ephemeral=True)

class Rules(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(RulesView())  # reboot percistance

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
            description=(
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
