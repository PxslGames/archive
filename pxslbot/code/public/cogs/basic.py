import discord
from discord.ext import commands
import psutil
from datetime import datetime, timezone
import json
from cogs.utils import *
import random

class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot_start_time = datetime.now(timezone.utc)
    
    async def cog_app_command_check(self, interaction: discord.Interaction):
        if interaction.user.bot:
            return True
        check_global_cooldown(interaction.user.id)
        return True

    @commands.command(name="basic")
    async def basic(self, ctx):
        embed = discord.Embed(
            title="📚 Basic Commands",
            description="This is a category for basic commands like `;hello`, `;ping`, and `;invite`.",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)
    
    @commands.command(name="credits")
    async def credits(self, ctx):
        embed = discord.Embed(
            title="📜 Credits",
            description="This bot was created by PxslGames.",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)

    @commands.command(name="hello")
    async def hello(self, ctx):
        embed = discord.Embed(
            title="👋 Hello!",
            description=f"Hello {ctx.author.mention}!",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)

    @commands.command(name="ping")
    async def ping(self, ctx):
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"{round(self.bot.latency * 1000)}ms",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)
    
    @commands.command(name="serverinfo")
    async def serverinfo(self, ctx, *, server_name: str = None):
        if not server_name:
            guild = ctx.guild
        elif server_name.lower() == "random":
            guild = random.choice(self.bot.guilds)
        else:
            guild = discord.utils.find(
                lambda g: g.name.lower() == server_name.lower(),
                self.bot.guilds
            )
            if not guild:
                embed = discord.Embed(
                    description=f"⚠️ Could not find a server named '{server_name}' that I am in.",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed)
                return

        humans = sum(1 for m in guild.members if not m.bot)
        bots = sum(1 for m in guild.members if m.bot)
        total_members = guild.member_count

        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)

        boosts = guild.premium_subscription_count
        boost_level = guild.premium_tier

        embed = discord.Embed(
            title=f"📊 Server Info — {guild.name}",
            color=discord.Color.purple()
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
        embed.add_field(name="💠 Boost Level", value=f"Level {boost_level} ({boosts} boosts)", inline=False)
        embed.add_field(name="👥 Members", value=f"Humans: {humans}\nBots: {bots}\nTotal: {total_members}", inline=False)
        embed.add_field(name="📂 Channels", value=f"Text: {text_channels}\nVoice: {voice_channels}\nCategories: {categories}", inline=False)
        embed.set_footer(text=f"Server ID: {guild.id}")

        await ctx.reply(embed=embed)
    
    @commands.command(name="invite")
    async def invite(self, ctx):
        embed = discord.Embed(
            title="📨 Invite",
            description="If you want PxslBot in your server, you can add it [here](https://discord.com/oauth2/authorize?client_id=1459261848430837964&permissions=8&integration_type=0&scope=bot+applications.commands)!",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed, delete_after=15)
    
    @commands.command(name="botinfo")
    async def botinfo(self, ctx):
        with open("data.json", "r") as f:
            data = json.load(f)
        version = data.get("version", "N/A")

        now = datetime.now(timezone.utc)
        delta = now - self.bot_start_time
        total_seconds = int(delta.total_seconds())

        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        ping = round(self.bot.latency * 1000)

        process = psutil.Process()
        mem = process.memory_info().rss / 1024 / 1024
        cpu = psutil.cpu_percent(interval=0.1)

        command_count = len(self.bot.commands)

        embed = discord.Embed(
            title="🤖 PxslBot Info",
            color=discord.Color.purple()
        )

        embed.add_field(name="📌 Version", value=version, inline=True)
        embed.add_field(name="⏰ Uptime", value=f"{days}d {hours}h {minutes}m {seconds}s", inline=True)
        embed.add_field(name="🏓 Ping", value=f"{ping}ms", inline=True)
        embed.add_field(name="💾 Memory", value=f"{mem:.2f} MB", inline=True)
        embed.add_field(name="🧠 CPU", value=f"{cpu}%", inline=True)
        embed.add_field(name="📚 Commands", value=command_count, inline=True)

        embed.set_footer(text="Made by @pxsldev1")

        await ctx.reply(embed=embed)
    
    @commands.command(name="support")
    async def support(self, ctx):
        embed = discord.Embed(
            title="🛠️ Support Server",
            description="If you need help, join [Pxsl's Discord Server!](https://discord.gg/9QDjPsE7bQ)",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)
    
    @commands.command(name="usercount")
    async def usercount(self, ctx):
        total_members = sum(guild.member_count for guild in self.bot.guilds)
        embed = discord.Embed(
            title="👥 Total User Count",
            description=f"I am currently serving {total_members} users across {len(self.bot.guilds)} servers!",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)
    
    @commands.command(name="changelog")
    async def changelog(self, ctx):
        embed = discord.Embed(
            title="📝 Changelog",
            description="If you want to see changelogs, or get notifications about PxslBot updates, join [Pxsl's Discord Server!](https://discord.gg/9QDjPsE7bQ)",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)
    
    @commands.command(name="vote")
    async def vote(self, ctx):
        embed = discord.Embed(
            title="🗳️ Vote for PxslBot",
            description="If you enjoy using PxslBot, please consider voting for it on [top.gg](https://top.gg/bot/1459261848430837964/vote)! It really helps out the bot and is much appreciated!",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)

    @commands.command(name="help")
    async def help(self, ctx):
        command_count = len(self.bot.commands)

        pages = [
            discord.Embed(
                title="Help - Basic (1/2)",
                description=";hello - Say hi\n;ping - Check latency\n;help - Display this message\n;serverinfo - Get the info about a server!\n;invite - Invite PxslBot to your server",
                color=discord.Color.purple()
            ),
            discord.Embed(
                title="Help - Basic (2/2)",
                description=";botinfo - View information about the bot\n;support - Get the invite link to the support server\n;usercount - View total user count across all servers\n;changelog - View the latest changes to the bot\n;vote - Get the link to vote for the bot on top.gg",
                color=discord.Color.purple()
            ),
            discord.Embed(   
                title="Help - Fun (1/4)",
                description=";dice - Roll a dice\n;coinflip - Flip a coin\n;8ball - Get a magic 8 ball response\n;howdumb - Tells you how dumb a user is\n;randomnumber - Get a random number",
                color=discord.Color.purple()
            ),
            discord.Embed(
                title="Help - Fun (2/4)",
                description=";7ball - Get an... odd 8 ball response...\n;gamble - Try your luck at the slot machine (free to play!)\n;dadjoke - Get a random dad joke\n;dog - Get a random dog image\n;cat - Get a random cat image",
                color=discord.Color.purple()
            ),
            discord.Embed(
                title="Help - Fun (3/4)",
                description=";selfdestruct - AAAAAAAAAAAA\n;truthordare - Get a truth or dare prompt\n;rps - Play rock paper scissors against the bot\n;howskid - Find out how much of a skid someone is\n;counting - Manage the counting game.",
                color=discord.Color.purple()
            ),
            discord.Embed(
                title="Help - Fun (4/4)",
                description=";bwomp - bwomp (thanks milenakos for sound)\n;shitpost - Get a random shitpost/meme",
                color=discord.Color.purple()
            ),
            discord.Embed(
                title="Help - Moderation (1/2)",
                description=";kick - Kick a member\n;ban - Ban a member\n;userinfo - Get information about a user's account\n;slowmode - Set a channel's slowmode\n;purge - Delete a large number of messages",
                color=discord.Color.purple()
            ),
            discord.Embed(
                title="Help - Moderation (2/2)",
                description=";nick - Change a member's nickname\n;lock - Lock a channel\n;unlock - Unlock a channel",
                color=discord.Color.purple()
            ),
            discord.Embed(
                title="Help - Utility (1/3)",
                description=";sticky - Manage sticky messages\n;poll - Start a poll\n;servericon - Show the current server's icon\n;base64 - Encode or decode text in Base64\n;qr - Generate a QR code from text",
                color=discord.Color.purple()
            ),
            discord.Embed(
                title="Help - Utility (2/3)",
                description=";remindme - Set a reminder\n;stats - Manage server stats\n;bsmap - Get a random BeatSaver map.\n;avatar - Get a user's avatar\n;txtimg - Create an image from text",
                color=discord.Color.purple()
            ),
            discord.Embed(
                title="Help - Utility (3/3)",
                description=";password - Generate a random password\n;yapcount - get your message count",
                color=discord.Color.purple()
            ),
            discord.Embed(
                title="Help - Manipulation (1/2)",
                description=";invert - Invert the colors of an image\n;gif - Convert an image to a GIF\n;greyscale - Remove the colour from an image\n;deepfry - Destroy an image\n;blur - Make an image blurry",
                color=discord.Color.purple()
            ),
            discord.Embed(
                title="Help - Manipulation (2/2)",
                description=";bloom - Add bloom to an image\n;pixelate - Make an image pixelated",
                color=discord.Color.purple()
            )
        ]

        for page in pages:
            page.set_footer(text=f"PxslBot - Made by @pxsldev1. | {command_count} commands")

        class HelpView(discord.ui.View):
            def __init__(self):
                super().__init__()
                self.current = 0

            @discord.ui.button(label="◀️", style=discord.ButtonStyle.gray)
            async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.current = (self.current - 1) % len(pages)
                await interaction.response.edit_message(embed=pages[self.current], view=self)

            @discord.ui.button(label="▶️", style=discord.ButtonStyle.gray)
            async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.current = (self.current + 1) % len(pages)
                await interaction.response.edit_message(embed=pages[self.current], view=self)

        view = HelpView()

        try:
            msg = await ctx.author.send(embed=pages[0], view=view)

            link = f"https://discord.com/channels/@me/{msg.channel.id}/{msg.id}"

            await ctx.reply(embed=discord.Embed(
                description=f"📬 {ctx.author.mention}, I sent you the help menu via [DM]({link})!",
                color=discord.Color.purple()
            ))

        except discord.Forbidden:
            await ctx.reply(embed=discord.Embed(
                description=f"⚠️ {ctx.author.mention}, I can't DM you. Please enable DMs to receive the help menu.",
                color=discord.Color.red()
            ))

async def setup(bot):
    await bot.add_cog(Basic(bot))