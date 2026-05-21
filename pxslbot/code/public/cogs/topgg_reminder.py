import random
import discord
from discord.ext import commands

class TopGGPatch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chance = 0.25
        self.titles = ["help me out twin ✌️","Please User I need this, My top.gg page is kinda voteless", "help a clanker out 🤖", "twin don't ignore me 🧍"]
        self.messages = ["cmon, click it:", "please 😭:", "if you fw the bot even A BIT, go vote on", "To Help me and the devs out go vote on"]

        original_send = discord.TextChannel.send

        async def patched_send(channel_self, content=None, **kwargs):
            msg = await original_send(channel_self, content, **kwargs)
            if random.random() < self.chance:
                e = discord.Embed(title=f"{random.choice(self.titles)}", description=f"{random.choice(self.messages)} [Top.gg](https://top.gg/bot/1459261848430837964/vote)!", color=discord.Color.gold())
                e.set_footer(text="Automated Message • Deleting soon")
                await original_send(channel_self, embed=e, delete_after=7)
            return msg

        discord.TextChannel.send = patched_send

        for cls in (commands.Context,):
            original_ctx_send = cls.send

            async def patched_ctx_send(self_ctx, content=None, **kwargs):
                msg = await original_ctx_send(self_ctx, content, **kwargs)
                if random.random() < self.chance:
                    e = discord.Embed(title=f"{random.choice(self.titles)}", description=f"{random.choice(self.messages)} [Top.gg](https://top.gg/bot/1459261848430837964/vote)!", color=discord.Color.gold())
                    e.set_footer(text="Automated Message • Deleting soon")
                    await original_ctx_send(self_ctx, embed=e, delete_after=7)
                return msg

            cls.send = patched_ctx_send

async def setup(bot):
    await bot.add_cog(TopGGPatch(bot))
