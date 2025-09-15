import discord
from discord.ext import commands
from discord import app_commands
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv('config.env')

def get_connection(): # Connect to the database
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
class Help(commands.Cog): # Set up the Help cog
    def __init__(self, bot):
        self.bot = bot
        self.create_help_table()

    def create_help_table(self): # Create the help table (add fields if needed)
        db = get_connection()
        cursor = db.cursor()
        cursor.execute("""
                           CREATE TABLE IF NOT EXISTS help_message
                           (
                               id INTEGER PRIMARY KEY,
                               title TEXT,
                               description TEXT,
                               field1_name TEXT,
                               field1_value TEXT,
                               field2_name TEXT,
                               field2_value TEXT,
                               field3_name TEXT,
                               field3_value TEXT,
                               field4_name TEXT,
                               field4_value TEXT,
                               field5_name TEXT,
                               field5_value TEXT,
                               footer TEXT
                           )
                            """)
        db.commit()

    def get_help_message(self): # Get the help message from the database
        db = get_connection()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM help_message WHERE id = 1")
        result = cursor.fetchone()
        
        if result:
            # Get the help message from the database
            return {
                "title": result[1],
                "description": result[2],
                "fields": [
                    {"name": result[3], "value": result[4]},
                    {"name": result[5], "value": result[6]},
                    {"name": result[7], "value": result[8]},
                    {"name": result[9], "value": result[10]},
                    {"name": result[11], "value": result[12]}
                ],
                "footer": result[13]
            }
        else:
            # Default help message id database is empty
            return {
                "title": " **👋 Hello survivant ! Besoin d'un coup de main ?** ",
                "description": " *Pas de panique*, la communauté et l’équipe sont là pour toi ! \n Voici quelques étapes pour t’aider rapidement :",
                "fields": [
                    {"name": "**1️⃣ Explique clairement ta question ou ton problème :**", "value": "- Dans le salon <#1331647140229021766> , pour des questions liées au jeu \n- Dans le salon <#1331649740718473370> , pour des questions liées au discord"},
                    {"name": "__Que veux tu résoudre ?__", "value": "Fournis un maximum de détails (capture d’écran, description précise, etc.)."},
                    {"name": "**2️⃣ Tag un rôle si nécessaire :**", "value": "- <@&1245673756958134314> si tu as une question autre que sur le jeu, ou une personne désagréable à bannir. \n- <@&1245672044088000593> si tu as une question sur le jeu !"},
                    {"name": "**3️⃣ Patiente un peu :**", "value": "Un membre ou un membre de l’équipe te répondra dès que possible. On fait toujours de notre mieux pour être **rapides et efficaces !**"},
                    {"name": "💡 Astuce :", "value": "Pense à vérifier le salon <#1331649740718473370> ou <#1331647140229021766> pour voir si ta réponse n’y est pas déjà."}
                ],
                "footer": "Merci de faire partie de la communauté Survive the HordeZ ! Ensemble, on surmonte toutes les épreuves. 🧟‍♂️💪"
            }

    def update_help_message(self, title, description, field1_name, field1_value, field2_name, field2_value, field3_name, field3_value, field4_name, field4_value, field5_name, field5_value, footer):
        # Update the help message in the database
        db = get_connection()
        cursor = db.cursor()
        cursor.execute("""
                           INSERT INTO help_message (id, title, description, field1_name, field1_value, field2_name,
                                                     field2_value, field3_name, field3_value, field4_name, field4_value,
                                                     field5_name, field5_value, footer)
                           VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO
                           UPDATE SET
                               title = ?, description = ?,
                               field1_name = ?, field1_value = ?,
                               field2_name = ?, field2_value = ?,
                               field3_name = ?, field3_value = ?,
                               field4_name = ?, field4_value = ?,
                               field5_name = ?, field5_value = ?,
                               footer = ?
                           """, (title, description, field1_name, field1_value, field2_name, field2_value, field3_name,
                                 field3_value, field4_name, field4_value, field5_name, field5_value, footer,
                                 title, description, field1_name, field1_value, field2_name, field2_value, field3_name,
                                 field3_value, field4_name, field4_value, field5_name, field5_value, footer))
        db.commit()

    @app_commands.command(name="sethelp", description="Définit un nouveau message d'aide (Réservé aux admins)")
    @app_commands.checks.has_role("ModoModo")
    async def set_help(self, interaction: discord.Interaction, title: str, description: str, field1_name: str, field1_value: str, field2_name: str, field2_value: str, field3_name: str, field3_value: str, field4_name: str = None, field4_value: str = None, field5_name: str = None, field5_value: str = None, footer: str = None):
        self.update_help_message(title, description, field1_name, field1_value, field2_name, field2_value, field3_name, field3_value, field4_name, field4_value, field5_name, field5_value, footer)
        await interaction.response.send_message("✅ Message d'aide mis à jour avec succès !", ephemeral=True)

    @app_commands.command(name="help", description="Affiche le message d'aide personnalisé")
    async def sayHelp(self, interaction: discord.Interaction):
        help_data = self.get_help_message()
        embed_help = discord.Embed(title=help_data["title"], description=help_data["description"], color=0x800080)
        embed_help.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        embed_help.set_thumbnail(url='https://cdn.discordapp.com/attachments/1330848782312538123/1330851613404958752/White_and_Grey_Square_Curvy_Photography_Brand_Logo.png')
        
        for field in help_data["fields"]:
            if field["name"] and field["value"]:
                embed_help.add_field(name=field["name"], value=field["value"], inline=False) # Add fields only if they are not None
        
        embed_help.set_footer(text=help_data["footer"])
        await interaction.response.send_message(embed=embed_help, ephemeral=True) # Send the help message as an ephemeral message (only visible to the user)

async def setup(bot):
    await bot.add_cog(Help(bot))