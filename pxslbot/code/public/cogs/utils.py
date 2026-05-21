import os
import time
from discord.ext import commands
import re
import discord
import asyncio
import json
from datetime import datetime

def log(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

user_cooldowns = {}
GLOBAL_COOLDOWN = 3

def check_global_cooldown(user_id: int):
    now = time.time()
    last = user_cooldowns.get(user_id, 0)
    if now - last < GLOBAL_COOLDOWN:
        retry_after = GLOBAL_COOLDOWN - (now - last)
        raise commands.CommandOnCooldown(
            commands.Cooldown(1, GLOBAL_COOLDOWN),
            retry_after
        )
    user_cooldowns[user_id] = now

TIME_UNITS = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
    "w": 604800,
    "mo": 2592000,
    "y": 31536000
}

def parse_time(time_str: str) -> int:
    match = re.fullmatch(r"(\d+)(s|m|h|d|w|mo|y)", time_str.lower())
    if not match:
        return None

    value, unit = match.groups()
    return int(value) * TIME_UNITS[unit]

STATUS_GUILD_ID = 1358840188469772581
STATUS_CHANNEL_ID = 1459567398234362076

async def set_status_channel(bot, emoji: str, retries=5, delay=1):
    for attempt in range(retries):
        guild = bot.get_guild(STATUS_GUILD_ID)
        if guild:
            channel = guild.get_channel(STATUS_CHANNEL_ID)
            if channel and isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
                try:
                    await channel.edit(name=f"{emoji}│status")
                    log(f"[STATUS] Updated status channel to {emoji}")
                    return True
                except discord.Forbidden:
                    log("[STATUS] Missing permissions to edit channel.")
                    return False
                except discord.HTTPException as e:
                    log(f"[STATUS] Failed to edit channel: {e}")
                    return False
            else:
                log(f"[STATUS] Channel not found or invalid. Attempt {attempt+1}/{retries}")
        else:
            log(f"[STATUS] Guild not found. Attempt {attempt+1}/{retries}")
        await asyncio.sleep(delay)

    log("[STATUS] Could not set status channel after retries.")
    return False

DATA_FILE = "data.json"

async def dmlog(bot: commands.Bot, message: str):
    if not os.path.exists(DATA_FILE):
        log(f"[DMLOG] Could not log: {DATA_FILE} not found")
        return

    with open(DATA_FILE) as f:
        data = json.load(f)

    admin_ids = data.get("perms", {}).get("admin", [])
    logging_disabled = data.get("loggingdm_disabled", [])

    for admin_id in admin_ids:
        if admin_id in logging_disabled:
            continue
        try:
            user = bot.get_user(admin_id)
            if user:
                embed = discord.Embed(
                    title="⚠️ PxslBot Critical Log",
                    description=message,
                    color=discord.Color.red()
                )
                await user.send(embed=embed)
        except Exception as e:
            log(f"[DMLOG] Could not DM admin {admin_id}: {e}")