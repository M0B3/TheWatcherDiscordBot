import discord
from discord.ext import commands

class SelfRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.role_messages = {}  # ID Storage and role mapping

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"📮{__name__} is ready.")

    @commands.command()
    async def selfrole(self, ctx, category: str):
        role_categories = {
            "role-divider": {
                "1️⃣": "ㅤㅤㅤ╚>ㅤLD Winnersㅤ<╝ㅤㅤㅤ",
                "2️⃣": "ㅤㅤㅤ╚>ㅤCréateursㅤ<╝ㅤㅤㅤ",
                "3️⃣": "ㅤㅤㅤ╚>ㅤLevelㅤ<╝ㅤㅤㅤ",
                "4️⃣": "ㅤㅤㅤ╚>ㅤDiscord Relatedㅤ<╝ㅤㅤㅤ"
            },
            "notify-me": {
                "🔔": "Notif ON"
            }
        }

        if category not in role_categories:
            await ctx.send("Catégorie invalide. Choisissez parmi: " + ", ".join(role_categories.keys()))
            return

        embed = discord.Embed(title=f"Choisissez votre rôle ({category})",
                              description="\n".join([f"{emoji} - {role}" for emoji, role in role_categories[category].items()]),
                              color=discord.Color.blue())

        message = await ctx.send(embed=embed)

        # Save message id and role mapping
        self.role_messages[message.id] = role_categories[category]

        # add reactions to the message
        for emoji in role_categories[category]:
            await message.add_reaction(emoji)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id in self.role_messages:
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)

            if member and not member.bot:
                role_name = self.role_messages[payload.message_id].get(str(payload.emoji))
                if role_name:
                    role = discord.utils.get(guild.roles, name=role_name)
                    if role:
                        await member.add_roles(role)
                        print(f"Rôle {role_name} attribué à {member.display_name}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.message_id in self.role_messages:
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)

            if member and not member.bot:
                role_name = self.role_messages[payload.message_id].get(str(payload.emoji))
                if role_name:
                    role = discord.utils.get(guild.roles, name=role_name)
                    if role:
                        await member.remove_roles(role)
                        print(f"Rôle {role_name} retiré de {member.display_name}")

async def setup(bot):
    await bot.add_cog(SelfRoles(bot))