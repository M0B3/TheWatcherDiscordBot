import discord
from discord.ext import commands
from discord import Embed

import mysql.connector
import os
import math
import random
import time
from dotenv import load_dotenv

load_dotenv('config.env')

def get_connection(): # Connect to the database
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.levelUpChannelID = 1245676190434328658 # Channel ID for level up messages

        self.cooldowns = {}  # last message stocked
        self.create_table()

    def create_table(self): # Create the Users table if it doesn't exist
        db = get_connection()
        cursor = db.cursor()
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS Users
                       (
                           guild_id BIGINT,
                           user_id BIGINT,
                           username VARCHAR(255),
                           level INT,
                           xp INT,
                           level_up_xp INT,
                           PRIMARY KEY (guild_id, user_id)
                           )
                       """)
        db.commit()
        cursor.close()
        db.close()

    @commands.Cog.listener()
    async def on_ready(self): # When the bot is ready
        print(f"📈{__name__} is ready.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message): # When a message is sent in the guild (server)
        if message.author.bot or message.guild is None: # Don't count the bot messages
            return

        user_id = message.author.id
        guild_id = message.guild.id
        username = message.author.name
        current_time = time.time()

        # cooldown verification
        if user_id in self.cooldowns:
            last_time, last_msg = self.cooldowns[user_id]
            if current_time - last_time < 3:  # 3 seconds cooldown
                return  # Ignore the message

            # verify if the message is the same as the last one
            if message.content.strip().lower() == last_msg:
                return  # Ignore the message

        self.cooldowns[user_id] = (current_time, message.content.strip().lower())

        # messages too shorts
        if len(message.content) < 5:
            return  # Ignore the message

        db = get_connection()
        cursor = db.cursor(dictionary=True) # To get results as dictionaries

        cursor.execute("SELECT * FROM Users WHERE guild_id = %s AND user_id = %s", (guild_id, user_id)) # Check if the user is already in the database
        result = cursor.fetchone()

        if result is None : # If the user is not in the database, we add them
            cur_level = 0
            xp = 0
            level_up_xp = 100
            cursor.execute("INSERT INTO Users (guild_id, user_id, username, level, xp, level_up_xp) VALUES (%s, %s, %s, %s, %s, %s)",
                           (guild_id, user_id, username, cur_level, xp, level_up_xp)) # Insert the new user information into the database
        else: # If the user is already in the database, we update their information
            cur_level = result['level']
            xp = result['xp']
            level_up_xp = result['level_up_xp']

        # XP gain based on message length (prevents spamming short messages)
        xp_gain = min(random.randint(5, 15), len(message.content) // 5)
        xp += xp_gain # Add the XP gain to the current XP

        if xp >= level_up_xp: # If the user has enough XP to level up
            cur_level += 1
            xp = 0
            new_level_up_xp = math.ceil(50 * cur_level ** 2 + 100 * cur_level + 50) # New XP needed for the next level

            # Embed creation for level up
            XP_embed = discord.Embed(
                title="🎉 Niveau atteint !",
                description=f"Félicitations {message.author.mention} ! Tu es maintenant niveau **{cur_level}** 🚀",
                color=discord.Color.gold()
            )
            XP_embed.set_thumbnail(url=message.author.avatar.url)
            XP_embed.set_footer(text="Continue comme ça ! 💪")

            # Send it to #info-general
            level_channel = self.bot.get_channel(self.levelUpChannelID) # find a way to get the channel dynamically through discord messages or BDD
            if level_channel:
                await level_channel.send(embed=XP_embed) # Send the embed to the level up channel

            cursor.execute("UPDATE Users SET username = %s, level = %s, xp = %s, level_up_xp = %s WHERE guild_id = %s AND user_id = %s",
                           (username, cur_level, xp, new_level_up_xp, guild_id, user_id)) # Update the user information in the database
        else:
            cursor.execute("UPDATE Users SET xp = %s WHERE guild_id = %s AND user_id = %s", (xp, guild_id, user_id)) # Update only the XP in the database

        db.commit()
        cursor.close()
        db.close()

    @commands.command()
    async def level(self, ctx: commands.Context, member: discord.Member = None): # Command to check the level of a user (!level)
        if member is None:
            member = ctx.author

        db = get_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Users WHERE guild_id = %s AND user_id = %s", (ctx.guild.id, member.id)) # Get the user information from the database  
        result = cursor.fetchone() # Fetch one result

        if result is None:
            await ctx.send(f"{member.mention} n'a pas encore de niveau.") # If user not in the database 
        else:
            level, xp, level_up_xp = result['level'], result['xp'], result['level_up_xp']

            asked_XP_embed = discord.Embed(title="💪 Encore du chemin à faire !", description=f"{member.mention} ! Tu es au niveau **{level}** 🚀", color=discord.Color.gold())
            asked_XP_embed.add_field(name="tu as :", value=f"{xp} d'XP sur {level_up_xp} pour passer au prochain niveau ! :) ", inline=False)
            asked_XP_embed.set_thumbnail(url=member.avatar.url)
            asked_XP_embed.set_footer(text="Continue comme ça ! 💪")

            await ctx.send(embed=asked_XP_embed)


        cursor.close()
        db.close()

async def setup(bot):
    await bot.add_cog(Leveling(bot))