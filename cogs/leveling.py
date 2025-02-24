import discord
from discord.ext import commands
from discord import Embed

import sqlite3
import math
import random
import time

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}  # last message stocked

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"📈{__name__} is ready.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return

        user_id = message.author.id
        guild_id = message.guild.id
        current_time = time.time()

        # cooldown verification
        if user_id in self.cooldowns:
            last_time, last_msg = self.cooldowns[user_id]
            if current_time - last_time < 5:  # 5 seconds cooldown
                return  # Ignore the message

            # verify if the message is the same as the last one
            if message.content.strip().lower() == last_msg:
                return  # Ignore the message

        self.cooldowns[user_id] = (current_time, message.content.strip().lower())

        # messages too shorts
        if len(message.content) < 5:
            return  # Ignore the message

        connexion = sqlite3.connect("./database/levels.db")
        cursor = connexion.cursor()

        cursor.execute("SELECT * FROM Users WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
        result = cursor.fetchone()

        if result is None:
            cur_level = 0
            xp = 0
            level_up_xp = 100
            cursor.execute("INSERT INTO Users (guild_id, user_id, level, xp, level_up_xp) VALUES (?, ?, ?, ?, ?)",
                           (guild_id, user_id, cur_level, xp, level_up_xp))
        else:
            cur_level = result[2]
            xp = result[3]
            level_up_xp = result[4]

        # XP gain based on message length (prevents spamming short messages)
        xp_gain = min(random.randint(5, 15), len(message.content) // 5)
        xp += xp_gain

        if xp >= level_up_xp:
            cur_level += 1
            xp = 0
            new_level_up_xp = math.ceil(50 * cur_level ** 2 + 100 * cur_level + 50)

            # Embed creation for level up
            XP_embed = discord.Embed(
                title="🎉 Niveau atteint !",
                description=f"Félicitations {message.author.mention} ! Tu es maintenant niveau **{cur_level}** 🚀",
                color=discord.Color.gold()
            )
            XP_embed.set_thumbnail(url=message.author.avatar.url)
            XP_embed.set_footer(text="Continue comme ça ! 💪")

            # Send it to #info-general
            level_channel = self.bot.get_channel(1245676190434328658)
            if level_channel:
                await level_channel.send(embed=XP_embed)

            cursor.execute("UPDATE Users SET level = ?, xp = ?, level_up_xp = ? WHERE guild_id = ? AND user_id = ?",
                           (cur_level, xp, new_level_up_xp, guild_id, user_id))
        else:
            cursor.execute("UPDATE Users SET xp = ? WHERE guild_id = ? AND user_id = ?", (xp, guild_id, user_id))

        connexion.commit()
        connexion.close()

    @commands.command()
    async def level(self, ctx: commands.Context, member: discord.Member = None):
        if member is None:
            member = ctx.author

        connexion = sqlite3.connect("./database/levels.db")
        cursor = connexion.cursor()
        cursor.execute("SELECT * FROM Users WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, member.id))
        result = cursor.fetchone()

        if result is None:
            await ctx.send(f"{member.mention} n'a pas encore de niveau.")
        else:
            level, xp, level_up_xp = result[2], result[3], result[4]

            asked_XP_embed = discord.Embed(title="💪 Encore du chemin à faire !", description=f"{member.mention} ! Tu es au niveau **{level}** 🚀", color=discord.Color.gold())
            asked_XP_embed.add_field(name="tu as :", value=f"{xp} d'XP sur {level_up_xp} pour passer au prochain niveau ! :) ", inline=False)
            asked_XP_embed.set_thumbnail(url=member.avatar.url)
            asked_XP_embed.set_footer(text="Continue comme ça ! 💪")

            await ctx.send(embed=asked_XP_embed)
            

        connexion.close()

async def setup(bot):
    await bot.add_cog(Leveling(bot))