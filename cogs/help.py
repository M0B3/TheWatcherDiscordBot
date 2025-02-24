import discord
from discord.ext import commands
from discord import app_commands
from discord import Embed


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"❓{__name__} is ready.")

    @app_commands.command(name="help", description="besoin d'aide à propos du jeu ou du discord ?")
    async def sayHelp(self, interaction: discord.Interaction):
        embed_help = Embed(title=" **👋 Hello survivant ! Besoin d'un coup de main ?** ", description=" *Pas de panique*, la communauté et l’équipe sont là pour toi !\n Voici quelques étapes pour t’aider rapidement :", color=0x800080)
        embed_help.set_author(name=interaction.user.name, url="https://www.youtube.com/watch?v=xvFZjo5PgG0", icon_url=interaction.user.display_avatar.url)
        embed_help.set_thumbnail(url='https://cdn.discordapp.com/attachments/1330848782312538123/1330851613404958752/White_and_Grey_Square_Curvy_Photography_Brand_Logo.png?ex=6792c766&is=679175e6&hm=9b4201b675a5acf264d1ef013a7924667bc356b175150fbc26b425ff26d1973a&')
        embed_help.add_field(name="**1️⃣ Explique clairement ta question ou ton problème :**", value="- Dans le salon <#1331647140229021766> , pour des questions liées au jeu \n- Dans le salon <#1331649740718473370> , pour des questions liées au discord", inline=False)
        embed_help.add_field(name="__Que veux tu résoudre ?__", value="Fournis un maximum de détails (capture d’écran, description précise, etc.).", inline=False)
        embed_help.add_field(name="**2️⃣ Tag un rôle si nécessaire :**", value="- <@&1245673756958134314> si tu as une question autre que sur le jeu, ou une personne désagréable à bannir. \n- <@&1245672044088000593> si tu as une question sur le jeu !", inline=False)
        embed_help.add_field(name="**3️⃣ Patiente un peu :**", value="Un membre ou un membre de l’équipe te répondra dès que possible. On fait toujours de notre mieux pour être **rapides et efficaces !**", inline=False)
        embed_help.add_field(name="💡 Astuce :", value="Pense à vérifier le salon <#1331649740718473370> ou <#1331647140229021766> pour voir si ta réponse n’y est pas déjà.", inline=False)
        embed_help.set_footer(text="Merci de faire partie de la communauté Survive the HordeZ ! Ensemble, on surmonte toutes les épreuves. 🧟‍♂️💪")
    
        await interaction.response.send_message(embed=embed_help)

async def setup(bot):
    await bot.add_cog(Help(bot))