import os
import json
import discord
from discord.ext import commands, tasks
from discord.ext.commands import BucketType
import random
from PIL import Image, ImageDraw, ImageFont
import io
import asyncio
import re
import threading
import tempfile
from datetime import datetime, timedelta, timezone
import re
import unicodedata
import pytz
import time

bot_start_time = datetime.now(timezone.utc)

with open("data.json", "r") as f:
    data = json.load(f)

if "vc_last_xp" not in data:
    data["vc_last_xp"] = {}
vc_last_xp = data["vc_last_xp"]

TOKEN = data["token"]

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=";", intents=intents, help_command=None)

user_command_cooldowns = {}
COMMAND_COOLDOWN = 3

active_giveaways = {}

MODERATORS = 1358887446045134918
DM_CHANNEL_ID = 1358864799991205908
LOGGING_CHANNEL_ID = 1358864754424152244

SERVER_STATS_CHANNEL_ID = 1444067583346086063
previous_member_count = None

last_67_roast_time = 0
ROAST_COOLDOWN = 3

last_spam_warning = {}
SPAM_WARNING_COOLDOWN = 5

MENTION_LIMIT = 5
MENTION_INTERVAL = 10
mention_history = {}

last_mention_warning = {}
MENTION_WARNING_COOLDOWN = 5

dm_last_response = {}
DM_RESPONSE_COOLDOWN = 10

sticky_messages = {}
sticky_message_ids = {}
last_update = {}

STICKY_COOLDOWN = 5

@bot.group(invoke_without_command=True)
@commands.has_permissions(administrator=True)
async def stickymsg(ctx):
    embed = discord.Embed(
        title="📌 Sticky Message",
        description="Usage: ;stickymsg create <message> | ;stickymsg delete",
        color=discord.Color.purple()
    )
    await ctx.reply(embed=embed)

@stickymsg.command()
@commands.has_permissions(administrator=True)
async def create(ctx, *, content: str):
    channel_id = ctx.channel.id
    sticky_messages[channel_id] = content
    await post_sticky(ctx.channel)
    embed = discord.Embed(
        title="📌 Sticky Message",
        description="Sticky Message Set!",
        color=discord.Color.purple()
    )
    await ctx.reply(embed=embed)

@stickymsg.command()
@commands.has_permissions(administrator=True)
async def delete(ctx):
    channel_id = ctx.channel.id
    if channel_id in sticky_message_ids:
        try:
            msg = await ctx.channel.fetch_message(sticky_message_ids[channel_id])
            await msg.delete()
        except:
            pass
        sticky_messages.pop(channel_id, None)
        sticky_message_ids.pop(channel_id, None)
        embed = discord.Embed(
            title="📌 Sticky Message",
            description="Sticky Message Deleted!",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)
    else:
        embed = discord.Embed(
            title="📌 Sticky Message",
            description="No Sticky Message Set!",
            color=discord.Color.red()
        )
        await ctx.reply(embed=embed)

async def post_sticky(channel):
    channel_id = channel.id
    now = time.time()
    
    if channel_id in last_update and now - last_update[channel_id] < STICKY_COOLDOWN:
        return
    last_update[channel_id] = now
    
    if channel_id in sticky_message_ids:
        try:
            old_msg = await channel.fetch_message(sticky_message_ids[channel_id])
            await old_msg.delete()
        except:
            pass

    embed = discord.Embed(
        description=sticky_messages[channel_id],
        color=discord.Color.purple()
    )
    msg = await channel.send(embed=embed)
    sticky_message_ids[channel_id] = msg.id

@bot.before_invoke
async def apply_user_cooldown(ctx):
    user_id = ctx.author.id
    if not can_run_command(user_id):
        raise commands.CommandOnCooldown(
            commands.Cooldown(1, COMMAND_COOLDOWN),
            retry_after=COMMAND_COOLDOWN,
            type=BucketType.user
        )

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        return
    raise error

def can_run_command(user_id):
    now = datetime.now().timestamp()
    last = user_command_cooldowns.get(user_id, 0)
    if now - last >= COMMAND_COOLDOWN:
        user_command_cooldowns[user_id] = now
        return True
    return False

def is_happy_hour():
    est = pytz.timezone("US/Eastern")
    now = datetime.now(est)
    return now.hour == 12

def get_multiplier():
    return 2 if is_happy_hour() else 1

def add_xp(user_id: str, amount: int):
    if "xp" not in data:
        data["xp"] = {}

    if user_id not in data["xp"]:
        data["xp"][user_id] = 0

    data["xp"][user_id] += amount * get_multiplier()

    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

def is_moderator():
    async def predicate(ctx):
        return any(role.id == MODERATORS for role in ctx.author.roles)
    return commands.check(predicate)

def parse_time(time_str):
    match = re.match(r"(\d+)([smhd])", time_str.lower())
    if not match:
        return None
    value, unit = match.groups()
    value = int(value)
    if unit == "s": return value
    if unit == "m": return value * 60
    if unit == "h": return value * 3600
    if unit == "d": return value * 86400
    return None

async def end_giveaway(ctx, giveaway_data):
    msg = await ctx.channel.fetch_message(giveaway_data["msg"].id)
    users = []
    for reaction in msg.reactions:
        if str(reaction.emoji) == "🎉":
            async for user in reaction.users():
                if not user.bot:
                    users.append(user)
    users = list(set(users))
    if not users:
        embed = discord.Embed(
            title="Giveaway Ended",
            description=f"No one entered the giveaway for **{giveaway_data['title']}** 😢",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc)
        )
        await ctx.send(embed=embed)
        return
    winners_count = min(giveaway_data["winners"], len(users))
    winners = random.sample(users, winners_count)
    mentions = ", ".join([u.mention for u in winners])
    embed = discord.Embed(
        title="🏆 Giveaway Ended!",
        description=f"Prize: **{giveaway_data['title']}**\nWinners: {mentions}",
        color=discord.Color.purple(),
        timestamp=datetime.now(timezone.utc)
    )
    await ctx.send(embed=embed)

banned_words = [
    "nigger", "nigga", "fag", "faggot", "chink", "tranny",
    "niga", "igga", "niig", "blacky", "blackies",
    "pornhub.com", "xvideos", "e621.net", "onlyfans.com",
    "childporn", "rape", "raped", "raping", "raper", "rapes", "paki",
    "kys", "kill yourself", "commit suicide", "suicidal", "pedophile",
    "xxx", "incest", "bestiality", "bdsm", "cp", "shota", "loli",
    "gore", "rape", "卍", "卐"
]

LEET_MAP = str.maketrans({
    '0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't',
    '@': 'a', '$': 's', '!': 'i'
})

def normalize_text(text: str) -> str:
    text = text.lower()
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = text.translate(LEET_MAP)
    return text

def is_banned_in_text(message: str, word_list: list = banned_words) -> tuple[bool, str]:
    text = normalize_text(message)
    
    for word in word_list:
        normalized_word = normalize_text(word)
        pattern = rf"\b{re.escape(normalized_word)}\b"
        if re.search(pattern, text):
            return True, word
    return False, None

@bot.event
async def on_member_join(member):
    try:
        to_check = f"{member.name} {member.display_name}"
        matched, matched_word = is_banned_in_text(to_check, banned_words)
        if matched:
            mod_channel = bot.get_channel(DM_CHANNEL_ID)
            reason = f"Auto-banned: matched banned word '{matched_word}' in username/nick."
            try:
                await member.guild.ban(member, reason=reason)
                if mod_channel:
                    await mod_channel.send(f"Auto-banned **{member}** ({member.id}): matched banned word.")
            except Exception as e:
                if mod_channel:
                    await mod_channel.send(f"Failed to ban {member} ({member.id}): {e}")
            return
    except Exception as e:
        print("Error in on_member_join check:", e)

@bot.event
async def on_member_update(before, after):
    try:
        if before.display_name != after.display_name or before.name != after.name:
            to_check = f"{after.name} {after.display_name}"
            matched, matched_word = is_banned_in_text(to_check, banned_words)
            if matched:
                reason = f"Auto-banned: matched banned word '{matched_word}' in username/nick (after update)."
                mod_channel = bot.get_channel(DM_CHANNEL_ID)
                try:
                    await after.guild.ban(after, reason=reason)
                    if mod_channel:
                        await mod_channel.send(f"Auto-banned **{after}** ({after.id}) after name change: matched banned word.")
                except Exception as e:
                    if mod_channel:
                        await mod_channel.send(f"Failed to ban {after} ({after.id}) after update: {e}")
    except Exception as e:
        print("Error in on_member_update check:", e)

@bot.command()
async def giveaway(ctx, title: str = None, winners: int = None, time: str = None):
    allowed_role_id = MODERATORS
    if not any(role.id == allowed_role_id for role in ctx.author.roles):
        embed = discord.Embed(
            title="Permission Denied",
            description="You do not have permission to start a giveaway! ❌",
            color=discord.Color.red()
        )
        await ctx.reply(embed=embed)
        return
    if not title or not winners or not time:
        embed = discord.Embed(
            title="Usage Error",
            description="Usage: `;giveaway <title> <winners> <time>`\nExample: `;giveaway CoolPrize 3 10m`",
            color=discord.Color.red()
        )
        await ctx.reply(embed=embed)
        return
    seconds = parse_time(time)
    if seconds is None:
        embed = discord.Embed(
            title="Time Error",
            description="Invalid time format! Use `s`, `m`, `h`, or `d`. Example: `10m`",
            color=discord.Color.red()
        )
        await ctx.reply(embed=embed)
        return
    embed = discord.Embed(
        title="🎉 Giveaway Started!",
        description=f"Prize: **{title}**\nWinners: **{winners}**\nTime: **{time}**\nReact with 🎉 to enter!",
        color=discord.Color.purple(),
        timestamp=datetime.now(timezone.utc)
    )
    giveaway_msg = await ctx.send(embed=embed)
    await giveaway_msg.add_reaction("🎉")
    async def task():
        await asyncio.sleep(seconds)
        await end_giveaway(ctx, {"msg": giveaway_msg, "winners": winners, "title": title})
    asyncio.create_task(task())

@bot.command(name="hello")
async def hello(ctx):
    embed = discord.Embed(title="👋 Hello!", description=f"Hello {ctx.author.mention}!", color=discord.Color.purple())
    await ctx.reply(embed=embed)

@bot.command(name="ping")
async def ping(ctx):
    embed = discord.Embed(title="🏓 Pong!", description=f"{round(bot.latency * 1000)}ms", color=discord.Color.purple())
    await ctx.reply(embed=embed)

@bot.command(name="8ball")
async def eight_ball(ctx, *, question: str):
    responses = [
        "It is certain ✅", "Without a doubt ✅", "Yes, definitely 👍", "Most likely 🤔",
        "Reply hazy, try again 🔮", "Ask again later ⏳", "Better not tell you now 🤐",
        "Don't count on it ❌", "My sources say no 🛑", "Very doubtful 😅",
        "Absolutely!", "No way!", "Signs point to yes!", "Concentrate and ask again",
        "Yes – in due time", "Cannot predict now", "Outlook not so good", "Very likely",
        "Chances are low", "Definitely not", "Yes, but be careful", "Absolutely not", "Maybe",
        "The stars say yes", "The stars say no", "You will find out soon", "Unclear, try again"
    ]
    answer = random.choice(responses)
    embed = discord.Embed(title="🎱 Magic 8-Ball", description=f"**Question:** {question}\n**Answer:** {answer}", color=discord.Color.purple())
    await ctx.reply(embed=embed)

@bot.command(name="membercount")
async def membercount(ctx):
    guild = ctx.guild
    if guild:
        embed = discord.Embed(title="Server Member Count", description=f"pxsl.dev is sitting at **{guild.member_count}** members!", color=discord.Color.purple())
    else:
        embed = discord.Embed(title="Error", description="This command can only be used in the server.", color=discord.Color.red())
    await ctx.reply(embed=embed)

@bot.command(name="math")
async def math(ctx, *args):
    if len(args) < 3:
        embed = discord.Embed(title="Error", description="You need to provide an operation and two numbers! Example: `;math add 5 10`", color=discord.Color.red())
        await ctx.reply(embed=embed)
        return
    operation = args[0].lower()
    a_input, b_input = args[1], args[2]
    if a_input.lower() == "membercount":
        if ctx.guild:
            a = ctx.guild.member_count
        else:
            embed = discord.Embed(title="Error", description="Membercount can only be used in a server.", color=discord.Color.red())
            await ctx.reply(embed=embed)
            return
    else:
        try:
            a = float(a_input)
        except ValueError:
            embed = discord.Embed(title="Error", description="Invalid first number!", color=discord.Color.red())
            await ctx.reply(embed=embed)
            return
    if b_input.lower() == "membercount":
        if ctx.guild:
            b = ctx.guild.member_count
        else:
            embed = discord.Embed(title="Error", description="Membercount can only be used in a server.", color=discord.Color.red())
            await ctx.reply(embed=embed)
            return
    else:
        try:
            b = float(b_input)
        except ValueError:
            embed = discord.Embed(title="Error", description="Invalid second number!", color=discord.Color.red())
            await ctx.reply(embed=embed)
            return
    try:
        if operation == "add":
            result = a + b
            symbol = "+"
        elif operation == "subtract":
            result = a - b
            symbol = "-"
        elif operation == "multiply":
            result = a * b
            symbol = "×"
        elif operation == "divide":
            if b == 0:
                await ctx.reply("Cannot divide by zero!")
                return
            result = a / b
            symbol = "÷"
        elif operation in ["power", "^", "exp"]:
            result = a ** b
            symbol = "^"
        else:
            embed = discord.Embed(title="Error", description="Invalid operation! Choose add, subtract, multiply, divide, or power.", color=discord.Color.red())
            await ctx.reply(embed=embed)
            return
    except OverflowError:
        embed = discord.Embed(title="Error", description="The result is too big to calculate! 😵", color=discord.Color.red())
        await ctx.reply(embed=embed)
        return
    except Exception as e:
        embed = discord.Embed(title="Error", description=f"An unexpected error occurred: {e}", color=discord.Color.red())
        await ctx.reply(embed=embed)
        return
    embed = discord.Embed(title="Math Result", description=f"{a} {symbol} {b} = {result}", color=discord.Color.purple())
    await ctx.reply(embed=embed)

@bot.command(name="txtimg")
async def txtimg(ctx, font_choice: str = None, *, text: str = None):
    from PIL import Image, ImageDraw, ImageFont
    import io
    import os
    import discord

    if not font_choice or not text:
        embed = discord.Embed(
            title="Error: Missing Arguments",
            description=(
                "You need to provide a font and some text!\n\n"
                "**Usage:** `;txtimg <font> <text>`\n"
                "**Available fonts:** regular, bold, italic"
            ),
            color=discord.Color.red()
        )
        return await ctx.reply(embed=embed)

    width, height = 500, 500
    bg = (0, 0, 0)
    fg = (255, 255, 255)

    font_map = {
        "regular":  "OpenSans-Regular.ttf",
        "bold":     "OpenSans-Bold.ttf",
        "italic":   "OpenSans-Italic.ttf",
    }

    font_choice = font_choice.lower()

    if font_choice not in font_map:
        embed = discord.Embed(
            title="Error: Unknown Font",
            description=f"'{font_choice}' is not available.\n**Available fonts:** {', '.join(font_map.keys())}",
            color=discord.Color.red()
        )
        return await ctx.reply(embed=embed)

    font_path = os.path.join("fonts", font_map[font_choice])

    image = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(image)

    font_size = 200

    while font_size > 10:
        font = ImageFont.truetype(font_path, font_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        if w <= width - 40 and h <= height - 40:
            break

        font_size -= 5

    x = (width - w) // 2
    y = (height - h) // 2

    draw.text((x, y), text, font=font, fill=fg)

    with io.BytesIO() as image_binary:
        image.save(image_binary, "PNG")
        image_binary.seek(0)
        await ctx.reply(file=discord.File(fp=image_binary, filename="text.png"))

@bot.command(name="help")
async def help_command(ctx):
    commands_list = [
        ";help - Show this help menu",
        ";hello - Say hello",
        ";ping - Check the bot's latency",
        ";math <operation> <a> <b> - Do math operations (add, subtract, multiply, divide, power)",
        ";membercount - Show the member count of the server",
        ";links - Get all of Pxsl's links and bio!",
        ";botinfo - Get information about the bot",
        ";txtimg <font> <text> - Generate an image with text using Regular, Bold or Italic font.",
        ";8ball <question> - Ask the magic 8 ball a question",
        ";giveaway <title> <winners> <time> - Start a giveaway (admin only)",
        ";getyap [member] - Get the yap count for a member",
        ";yapboard - Show the top yap senders",
        ";getxp [member] - Get the XP for a member",
        ";xpleaderboard - Show the top XP earners",
        ";givexp <member> <amount> - Give XP to a member (admin only)",
        ";removexp <member> <amount> - Remove XP from a member (admin only)",
        ";resetxp <member> - Reset a member's XP to 0 (admin only)",
        ";stickymsg create <message> - Create a sticky message (admin only)",
        ";stickymsg delete - Delete the sticky message (admin only)",
    ]   
    embed = discord.Embed(title="Bot Commands", description="\n".join(commands_list), color=discord.Color.purple())
    try:
        await ctx.author.send(embed=embed)
        embed = discord.Embed(
            title="📬 Sent Help DM!",
            description=f"I've sent you the help menu in DMs!",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)
    except Exception:
        await ctx.reply(embed=embed)

@bot.command(name="getyap")
async def get_yap(ctx, member: discord.Member = None):
    member = member or ctx.author
    count = data.get("yaps", {}).get(str(member.id), 0)
    embed = discord.Embed(
        title="📊 Yap Count",
        description=f"{member.mention} has sent **{count} messages**!",
        color=discord.Color.purple()
    )
    await ctx.reply(embed=embed)

@bot.command(name="yapboard")
async def yap_board(ctx):
    yaps = data.get("yaps", {})
    if not yaps:
        await ctx.reply("No messages have been counted yet!")
        return

    top = sorted(yaps.items(), key=lambda x: x[1], reverse=True)[:10]

    description = ""
    for i, (user_id, count) in enumerate(top, 1):
        user = ctx.guild.get_member(int(user_id))
        if user:
            description += f"**{i}. {user.display_name}** — {count} messages\n"
        else:
            description += f"**{i}. Unknown User ({user_id})** — {count} messages\n"

    embed = discord.Embed(
        title="🏆 Yapboard",
        description=description,
        color=discord.Color.purple()
    )
    await ctx.reply(embed=embed)

@bot.command(name="getxp")
async def get_xp(ctx, member: discord.Member = None):
    member = member or ctx.author
    uid = str(member.id)

    xp = data.get("xp", {}).get(uid, 0)

    embed = discord.Embed(
        title="⭐ XP Status",
        description=f"{member.mention} has **{xp} XP**!",
        color=discord.Color.purple()
    )
    await ctx.reply(embed=embed)

@bot.command(name="xpleaderboard")
async def xp_leaderboard(ctx):
    xp_data = data.get("xp", {})
    if not xp_data:
        return await ctx.reply("No XP has been earned yet!")

    top = sorted(xp_data.items(), key=lambda x: x[1], reverse=True)[:10]

    desc = ""
    for i, (user_id, xp) in enumerate(top, 1):
        user = ctx.guild.get_member(int(user_id))
        name = user.display_name if user else f"Unknown ({user_id})"
        desc += f"**{i}. {name}** — {xp} XP\n"

    embed = discord.Embed(
        title="🏆 XP Leaderboard",
        description=desc,
        color=discord.Color.purple()
    )
    await ctx.reply(embed=embed)

@bot.command(name="givexp")
@is_moderator()
async def give_xp(ctx, member: discord.Member, amount: int):
    uid = str(member.id)
    add_xp(uid, amount)
    await ctx.reply(f"Gave {amount} XP to {member.mention}!")

@bot.command(name="removexp")
@is_moderator()
async def remove_xp(ctx, member: discord.Member, amount: int):
    uid = str(member.id)
    if "xp" not in data or uid not in data["xp"]:
        return await ctx.reply("User has no XP.")

    data["xp"][uid] = max(0, data["xp"][uid] - amount)

    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

    await ctx.reply(f"Removed {amount} XP from {member.mention}.")

@bot.command(name="resetxp")
@is_moderator()
async def reset_xp(ctx, member: discord.Member):
    uid = str(member.id)
    data["xp"][uid] = 0

    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

    await ctx.reply(f"Reset XP for {member.mention}.")

@bot.command(name="links")
async def links(ctx):
    embed = discord.Embed(title="🌐 Links", description=f"You can find all of my links, and my full bio: [here](https://pxsl.dev/about/)", color=discord.Color.purple())
    await ctx.reply(embed=embed)

@bot.command(name="botinfo")
async def botinfo(ctx):
    now = datetime.now(timezone.utc)
    delta = now - bot_start_time
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)

    ping = round(bot.latency * 1000)

    import psutil, platform
    process = psutil.Process()
    mem = process.memory_info().rss / 1024 / 1024
    cpu = psutil.cpu_percent()

    command_count = len(bot.commands)

    handled = getattr(bot, "messages_handled", "N/A")

    embed = discord.Embed(
        title="🤖 PxslBot Info",
        color=discord.Color.purple()
    )

    embed.add_field(name="📌 Version", value="1.0.5", inline=True)
    embed.add_field(name="⏰ Uptime", value=f"{hours}h {minutes}m {seconds}s", inline=True)
    embed.add_field(name="🏓 Ping", value=f"{ping}ms", inline=True)

    embed.add_field(name="💾 Memory", value=f"{mem:.2f} MB", inline=True)
    embed.add_field(name="🧠 CPU", value=f"{cpu}%", inline=True)
    embed.add_field(name="📚 Commands", value=command_count, inline=True)

    embed.set_footer(text="Made for pxsl.dev, by Pxsl")

    await ctx.reply(embed=embed)

INVITE_ALLOWED_CHANNELS = [
    1358845672610332698,
    1358895695376945346,
    1362164278605516911,
    1391091288652120135
]

INVITE_REGEX = r"(discord\.gg\/[A-Za-z0-9\-]+|discord\.com\/invite\/[A-Za-z0-9\-]+)"

SPAM_LIMIT = 3
SPAM_INTERVAL = 1
user_messages = {}
SPAM_CHANNEL_ID = 1358875244491833495

async def check_spam(message):
    if message.channel.id == SPAM_CHANNEL_ID:
        return
    
    now = datetime.now().timestamp()
    uid = str(message.author.id)
    msgs = user_messages.get(uid, [])
    msgs = [t for t in msgs if now - t < SPAM_INTERVAL]
    msgs.append(now)
    user_messages[uid] = msgs

    if len(msgs) > SPAM_LIMIT:
        try:
            await message.delete()
        except:
            pass

        last = last_spam_warning.get(uid, 0)
        if now - last >= SPAM_WARNING_COOLDOWN:
            last_spam_warning[uid] = now

            spam_embed = discord.Embed(
                title="⚠️ Spam Detected",
                description=f"{message.author.mention}, please stop spamming!",
                color=discord.Color.red()
            )
            await message.channel.send(embed=spam_embed, delete_after=5)

            try:
                await message.author.timeout(timedelta(minutes=5), reason="Spamming messages")
            except:
                pass

TEMP_VC_CATEGORY_ID = 1416889925755994122
MAIN_VC_ID = 1416889927408418817

temp_vcs = {}

@bot.event
async def on_voice_state_update(member, before, after):
    global temp_vcs

    if before.channel == after.channel:
        return

    if after.channel and after.channel.id == MAIN_VC_ID:
        category = bot.get_channel(TEMP_VC_CATEGORY_ID)
        if category is None:
            print("Temp VC category not found.")
            return

        new_vc = await member.guild.create_voice_channel(
            name=f"{member.display_name}'s call",
            category=category
        )

        await member.move_to(new_vc)

        temp_vcs[member.id] = new_vc.id

    if before.channel:
        if before.channel.id in temp_vcs.values():
            if len(before.channel.members) == 0:
                try:
                    await before.channel.delete()
                except Exception as e:
                    print("Failed to delete temp VC:", e)
                temp_vcs = {k: v for k, v in temp_vcs.items() if v != before.channel.id}

def contains_67(text):
    text = text.lower()

    if re.search(r"\b6\s*7\b", text):
        return True

    if re.search(r"\bsixty\s*seven\b", text):
        return True

    if re.search(r"\bs\s*i\s*x\s*(t\s*y)?\s*s\s*e\s*v\s*e\s*n\b", text):
        return True

    return False

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await check_spam(message)

    await bot.process_commands(message)

    content = message.content

    roast_templates = [
        "{mention} just typed **67**… bro’s sense of humor got left behind in a Windows XP loading screen.",
        "{mention}, saying 67 was crazy… I haven’t seen a joke flop that hard since your social life.",
        "{mention} really said **67** like we were all gonna clap. My disappointment is immeasurable and my day is ruined.",
        "{mention} typed *67* so confidently, like their brain didn’t blue-screen halfway through.",
        "{mention} dropping **67** in chat like it’s comedy gold… buddy, that joke expired in 2003.",
        "{mention}, if humor was a battery, you’d be on **–3%** after saying 67.",
        "{mention} saying **67** is wild… you typed that with the swagger of someone who lost an argument to a toaster.",
        "{mention} said **67** and honestly I’m concerned. Blink twice if your last two brain cells divorced.",
        "{mention} really just dropped **67**… somewhere out there, a comedy fairy just died.",
        "{mention}, you said **67**? Bro typed it like it wasn’t the emotional equivalent of wet cardboard.",
        "{mention} with the **67**… you okay? That joke had negative calories.",
        "{mention}, saying **67** is crazy. That joke was so empty it echoed.",
        "{mention} typed **67** and my soul left my body from secondhand embarrassment.",
        "{mention} just deployed **67** like it was a missile… but it landed like a soggy pancake.",
        "{mention}, that **67** joke hit harder than your life choices. And not in a good way.",
        "{mention} saying **67** cured my insomnia. I’m asleep now. Thanks.",
    ]

    global last_67_roast_time
    now_ts = datetime.now().timestamp()

    if contains_67(content):
        if now_ts - last_67_roast_time >= ROAST_COOLDOWN:
            roast = random.choice(roast_templates).format(mention=message.author.mention)
            await message.channel.send(roast)
            last_67_roast_time = now_ts

    matched, word = is_banned_in_text(message.content, banned_words)
    if matched:
        dm_embed = discord.Embed(
            title="🚫 No Banned Phases",
            description=f"You sent a message containing a banned word or phrase: **{word}**.\n"
                        "**You have been permanently banned.**\n\nPlease follow the server rules.",
            color=discord.Color.red()
        )
        try:
            await message.author.send(embed=dm_embed)
        except:
            pass

        try:
            await message.author.ban(reason=f"Sent banned word: {word}")
            embed = discord.Embed(
                title="🚫 Banned Phrase Sent",
                description=f"{message.author.mention} has been **banned** for sending a banned word: **{word}**.",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed, delete_after=5)
        except Exception as e:
            print(f"Failed to ban {message.author}: {e}")
        return

    user_id = str(message.author.id)
    if "yaps" not in data:
        data["yaps"] = {}
    data["yaps"][user_id] = data["yaps"].get(user_id, 0) + 1

    if message.guild:
        if "last_xp" not in data:
            data["last_xp"] = {}
        now_ts = datetime.now(timezone.utc).timestamp()
        last = data["last_xp"].get(user_id, 0)
        if now_ts - last > 30:
            add_xp(user_id, 10)
            data["last_xp"][user_id] = now_ts

    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

    if not message.guild:
        user_id = message.author.id
        now_ts = datetime.now().timestamp()
        
        last_response = dm_last_response.get(user_id, 0)
        if now_ts - last_response >= DM_RESPONSE_COOLDOWN:
            dm_embeds = [
                discord.Embed(title="👋 Hello!", description="I am an automated bot. You cannot DM me directly.", color=discord.Color.red()),
                discord.Embed(title="🤖 Beep Boop", description="I cannot respond like a human. Private messages won't reach anyone.", color=discord.Color.red()),
                discord.Embed(title="❌ Not Human", description="I am a bot. DMs cannot be responded to.", color=discord.Color.red()),
                discord.Embed(title="🚫 Private Message Detected", description="I cannot chat with you in DMs.", color=discord.Color.red())
            ]
            embed = random.choice(dm_embeds)
            await message.channel.send(embed=embed)
            dm_last_response[user_id] = now_ts
        return

    if re.search(INVITE_REGEX, message.content, re.IGNORECASE):
        if message.channel.id not in INVITE_ALLOWED_CHANNELS:
            try:
                await message.delete()
                duration = timedelta(minutes=10)
                try:
                    await message.author.timeout(duration, reason="Advertising / Sending invite links")
                    timed_out = True
                except:
                    timed_out = False

                dm_text = (
                    "You sent a Discord invite in a channel where advertising isn't allowed.\n"
                    "**You were timed out for 10 minutes.**" if timed_out else
                    "You sent a Discord invite in a channel where advertising isn't allowed.\n"
                    "**You were not timed out due to a permissions issue.**"
                )
                dm_embed = discord.Embed(
                    title="🚫 No Advertising Allowed",
                    description=dm_text + "\n\nPlease follow the server rules.",
                    color=discord.Color.red()
                )
                try:
                    await message.author.send(embed=dm_embed)
                except: pass

                warn_text = (
                    f"{message.author.mention} has been **timed out for advertising**."
                    if timed_out else
                    f"{message.author.mention} sent a Discord invite (Timeout failed — missing permissions)."
                )
                warn_embed = discord.Embed(
                    title="🚫 Invite Blocked",
                    description=warn_text,
                    color=discord.Color.red()
                )
                await message.channel.send(embed=warn_embed, delete_after=5)
            except Exception as e:
                print(f"Error handling invite: {e}")

    await bot.process_commands(message)

    if message.author.bot:
        return

    channel_id = message.channel.id
    if channel_id in sticky_messages:
        await post_sticky(message.channel)

VC_XP_COOLDOWN = 60

@tasks.loop(seconds=10)
async def vc_xp_loop():
    for guild in bot.guilds:
        for vc in guild.voice_channels:
            members = [m for m in vc.members if not m.bot]
            if len(members) >= 2:
                now_ts = datetime.now(timezone.utc).timestamp()
                for user in members:
                    uid = str(user.id)
                    last = vc_last_xp.get(uid, 0)
                    if now_ts - last >= VC_XP_COOLDOWN:
                        add_xp(uid, 20)
                        vc_last_xp[uid] = now_ts

    data["vc_last_xp"] = vc_last_xp
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

@tasks.loop(seconds=15)
async def update_server_stats():
    global previous_member_count

    guild = bot.guilds[0] if bot.guilds else None
    if guild is None:
        return

    current_count = guild.member_count

    stats_channel = bot.get_channel(SERVER_STATS_CHANNEL_ID)
    if stats_channel is None:
        print("Stats channel not found (SERVER_STATS_CHANNEL_ID).")
        return

    if previous_member_count is None:
        previous_member_count = current_count
        return

    if current_count != previous_member_count:

        kwargs = {"name": f"🚀 Members: {current_count}"}
        if isinstance(stats_channel, discord.VoiceChannel):
            kwargs["bitrate"] = stats_channel.bitrate

        try:
            await stats_channel.edit(**kwargs)
        except Exception as e:
            print("Failed to update stats channel:", e)

        dm_channel = bot.get_channel(LOGGING_CHANNEL_ID)
        if dm_channel:
            embed = discord.Embed(
                title="📊 Server Stats Updated",
                description=(
                    f"**Previous:** {previous_member_count}\n"
                    f"**Updated to:** {current_count}"
                ),
                color=discord.Color.purple(),
                timestamp=datetime.now(timezone.utc)
            )
            try:
                await dm_channel.send(embed=embed)
            except Exception as e:
                print("Failed to send stats update embed:", e)

        previous_member_count = current_count

light_insults = ["goobers", "numbskulls", "idiots", "dingbats", "dinguses", "doofuses", "knuckleheads", "nitwits", "blockheads", "boneheads"]

async def cycle_status():
    await bot.wait_until_ready()
    guild = bot.guilds[0]

    while not bot.is_closed():
        member_count = guild.member_count

        insult = random.choice(light_insults)
        watching_activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"a server with: {member_count} {insult}"
        )
        await bot.change_presence(activity=watching_activity)
        await asyncio.sleep(5)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")
    vc_xp_loop.start()
    update_server_stats.start()
    bot.loop.create_task(cycle_status())

bot.run(TOKEN)