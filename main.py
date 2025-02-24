import discord
from discord.ext import commands

from dotenv import load_dotenv
import os
import asyncio

from keep_alive import keep_alive

load_dotenv('config.env') # Load the environment variables from the .env file

token = os.getenv('DISCORD_TOKEN') # Get the token from the environment variables

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all()) # Create a new bot with the intents

@bot.event
async def on_ready():
    print("Logged !") # Print a message when the bot is ready

    try:
        synced = await bot.tree.sync() # Sync the commands with the guild
        print(f'Synced {len(synced)} commands') # Print the number of synced commands

    except Exception as e:
        print(f'An error occurred: {e}') # Print an error if one occurs
    
async def Load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f'cogs.{filename[:-3]}')

async def main():
    async with bot:
        await Load()
        await bot.start(token)

keep_alive() # Start the keep_alive server
asyncio.run(main())

