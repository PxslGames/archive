import discord
from discord.ext import commands, tasks
import json
import asyncio
import time
from cogs.utils import *

with open('data.json') as f:
    data = json.load(f)

TOKEN = data['token']
intents = discord.Intents.all()

bot = commands.Bot(command_prefix=';', intents=intents, help_command=None)
initial_extensions = [
    'cogs.basic',
    'cogs.fun',
    'cogs.moderation',
    'cogs.utility',
    'cogs.manipulation',
    'cogs.admin',
    "cogs.topgg_reminder"
]

async def load_cogs():
    for ext in initial_extensions:
        await bot.load_extension(ext)
        log(f"[COGS] Loaded {ext}")

def format_number(num: int) -> str:
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}k"
    else:
        return str(num)

@tasks.loop(minutes=1)
async def rpc():
    total_members = sum(guild.member_count for guild in bot.guilds)
    total_guilds = len(bot.guilds)

    total_members_str = format_number(total_members)
    total_guilds_str = format_number(total_guilds)

    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name=f"{total_guilds_str} servers | {total_members_str} users"
    )
    await bot.change_presence(activity=activity)

    log(f"[RPC] Updated presence: {total_guilds_str} servers, {total_members_str} users")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if isinstance(message.channel, discord.DMChannel):
        return

    await bot.process_commands(message)

@bot.event
async def on_guild_join(guild):
    log(f"[GUILD JOIN] {guild.name} (ID: {guild.id})")

    owner = guild.owner or await bot.fetch_user(guild.owner_id)

    try:
        embed = discord.Embed(
            title="Thanks for inviting PxslBot! 🎉",
            description=(
                f"Hi **{owner.name}**, thanks for adding **PxslBot** to **{guild.name}**!\n\n"
                "If you don't know where to begin:\n"
                "• Use `;help` to see a list of commands.\n"
                "• Join our [support server](https://discord.gg/9QDjPsE7bQ) for help and updates.\n\n"
                "Thanks again for supporting and using PxslBot! We hope it brings fun and utility to your server. 😊"
            ),
            color=discord.Color.purple()
        )

        embed.set_footer(text="PxslBot - the best bot ever created | Support: https://discord.gg/9QDjPsE7bQ")

        await owner.send(embed=embed)

    except discord.Forbidden:
        log(f"[GUILD JOIN] Could not DM owner of {guild.name}")

@bot.event
async def on_command_error(ctx, error):
    if hasattr(ctx.command, "on_error"):
        return

    error = getattr(error, "original", error)

    log(f"[CMD ERROR] {ctx.author} in #{ctx.channel}: {error}")

    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(
            description=f"⏳ Slow down! You can use this again in **{error.retry_after:.1f}s**.",
            color=discord.Color.red()
        )
        return await ctx.reply(embed=embed)

    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            description="⛔ You don’t have permission to use this command.",
            color=discord.Color.red()
        )
        return await ctx.reply(embed=embed)

    if isinstance(error, commands.BotMissingPermissions):
        embed = discord.Embed(
            description="⚠️ I’m missing permissions to run that command.",
            color=discord.Color.red()
        )
        return await ctx.reply(embed=embed)

    if isinstance(error, commands.MemberNotFound):
        embed = discord.Embed(
            description="🔍 Couldn’t find that user. Make sure they’re in the server.",
            color=discord.Color.red()
        )
        return await ctx.reply(embed=embed)

    if isinstance(error, commands.BadArgument):
        embed = discord.Embed(
            description=f"⚠️ Invalid input: **{error}**",
            color=discord.Color.red()
        )
        return await ctx.reply(embed=embed)

    if isinstance(error, commands.CommandNotFound):
        return

    embed = discord.Embed(
        title="⚠️ Error",
        description="Something went wrong while running that command.",
        color=discord.Color.red()
    )
    embed.set_footer(text=str(error))

    await ctx.reply(embed=embed)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    error = getattr(error, "original", error)

    log(f"[APP CMD ERROR] user={interaction.user} error={error}")

    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(
            description=f"⏳ Slow down! You can use this again in **{error.retry_after:.1f}s**.",
            color=discord.Color.red()
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)

    embed = discord.Embed(
        title="⚠️ Error",
        description="Something went wrong while running that command.",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

user_cooldowns = {}
GLOBAL_COOLDOWN = 3

def check_global_cooldown(user_id: int):
    now = time.time()
    last = user_cooldowns.get(user_id, 0)

    if now - last < GLOBAL_COOLDOWN:
        retry_after = GLOBAL_COOLDOWN - (now - last)

        log(
            f"[RATE LIMIT] user_id={user_id}, retry_after={retry_after:.2f}s"
        )

        raise commands.CommandOnCooldown(
            commands.Cooldown(1, GLOBAL_COOLDOWN),
            retry_after
        )

    user_cooldowns[user_id] = now

@bot.check
async def global_rate_limit(ctx: commands.Context):
    if ctx.author.bot:
        return True
    check_global_cooldown(ctx.author.id)
    return True

@bot.event
async def on_ready():
    log(f"[READY] Logged in as {bot.user} ({bot.user.id})")

    await set_status_channel(bot, "🟢")

    if not rpc.is_running():
        rpc.start()
        log("[RPC] Presence loop started")

    try:
        await dmlog(bot, "✅ PxslBot is now online!")
    except Exception as e:
        log(f"[DMLOG ERROR] Failed to notify admins: {e}")

async def main():
    log("[BOOT] Starting PxslBot")
    await load_cogs()
    await bot.start(TOKEN)

asyncio.run(main())