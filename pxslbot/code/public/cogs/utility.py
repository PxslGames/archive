import discord
from discord.ext import commands, tasks
import json
import os
import asyncio
from PIL import Image, ImageDraw, ImageFont
import io
import aiohttp
import base64
import qrcode
from cogs.utils import *
from datetime import datetime, timezone
import time
import random

DATA_FILE = "data.json"

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminder_loop.start()
        self.server_stats_loop.start()

    @tasks.loop(seconds=30)
    async def server_stats_loop(self):
        data = self.load_data()
        stats_data = data.get("serverstats", {})

        for guild_id, stats in list(stats_data.items()):
            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                del stats_data[guild_id]
                continue

            for stat_type, channel_id in list(stats.items()):
                channel = guild.get_channel(channel_id)
                if not channel:
                    del stats_data[guild_id][stat_type]
                    continue

                if stat_type == "members":
                    value = sum(1 for m in guild.members if not m.bot)
                    name = f"Members: {value}"

                elif stat_type == "bots":
                    value = sum(1 for m in guild.members if m.bot)
                    name = f"Bots: {value}"

                elif stat_type == "members_and_bots":
                    value = guild.member_count
                    name = f"Total: {value}"

                elif stat_type == "boosts":
                    value = guild.premium_subscription_count or 0
                    name = f"Boosts: {value}"

                else:
                    continue

                if channel.name != name:
                    try:
                        await channel.edit(name=name)
                    except discord.Forbidden:
                        pass

        self.save_data(data)

    @tasks.loop(seconds=30)
    async def reminder_loop(self):
        now = int(time.time())

        with open("data.json", "r") as f:
            data = json.load(f)

        reminders = data.get("reminders", [])
        remaining = []

        for r in reminders:
            if now >= r["remind_at"]:
                user = self.bot.get_user(r["user_id"])
                channel = self.bot.get_channel(r["channel_id"])

                embed = discord.Embed(
                    title="⏰ Reminder!",
                    description=r["message"],
                    color=discord.Color.purple(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed.set_footer(text="You asked me to remind you.")

                sent = False

                if channel:
                    try:
                        await channel.send(
                            content=f"<@{r['user_id']}>",
                            embed=embed
                        )
                        sent = True
                    except discord.Forbidden:
                        pass

                if not sent and user:
                    try:
                        await user.send(
                            content="⏰ Reminder!",
                            embed=embed
                        )
                    except discord.Forbidden:
                        pass
            else:
                remaining.append(r)

        data["reminders"] = remaining

        with open("data.json", "w") as f:
            json.dump(data, f, indent=4)

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            return {"token": "", "version": "1.0.0", "servers": {}}
        with open(DATA_FILE, "r") as f:
            return json.load(f)

    def save_data(self, data):
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
    
    @commands.command(name="utility")
    async def utility(self, ctx):
        embed = discord.Embed(
            title="📚 Utility Commands",
            description="This is a category for utility commands like `;servericon`, `;sticky`, and `;qrcode`.",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)
    
    @commands.command(name="servericon")
    async def servericon(self, ctx):
        guild = ctx.guild
        if guild.icon is None:
            await ctx.reply("This server has no icon!")
            return

        embed = discord.Embed(
            title=f"{guild.name}'s Server Icon",
            color=discord.Color.purple()
        )
        embed.set_image(url=guild.icon.url)
        await ctx.reply(embed=embed)

    @commands.group(name="sticky", invoke_without_command=True)
    async def sticky(self, ctx):
        await ctx.reply(
            embed=discord.Embed(
                description="Use `;sticky create <message>` to set a sticky or `;sticky delete` to remove it.",
                color=discord.Color.purple()
            ),
            delete_after=20
        )

    @sticky.command(name="create")
    async def sticky_create(self, ctx, *, message: str):
        if not ctx.author.guild_permissions.manage_messages:
            return await ctx.reply(
                embed=discord.Embed(
                    title="🚫 Permission Denied",
                    description="You need **Manage Messages** to create sticky messages.",
                    color=discord.Color.red()
                ),
                delete_after=15
            )

        data = self.load_data()
        server_id = str(ctx.guild.id)
        channel_id = str(ctx.channel.id)

        data.setdefault("servers", {})
        data["servers"].setdefault(server_id, {})
        data["servers"][server_id].setdefault("sticky", {})

        data["servers"][server_id]["sticky"][channel_id] = message
        self.save_data(data)

        await ctx.reply(
            embed=discord.Embed(
                description=f"📌 Sticky message **created** in {ctx.channel.mention}:\n> {message}",
                color=discord.Color.purple()
            )
        )

    @sticky.command(name="delete")
    async def sticky_delete(self, ctx):
        if not ctx.author.guild_permissions.manage_messages:
            return await ctx.reply(
                embed=discord.Embed(
                    title="🚫 Permission Denied",
                    description="You need **Manage Messages** to delete sticky messages.",
                    color=discord.Color.red()
                ),
                delete_after=15
            )

        data = self.load_data()
        server_id = str(ctx.guild.id)
        channel_id = str(ctx.channel.id)

        sticky_data = data.get("servers", {}).get(server_id, {}).get("sticky", {})

        if channel_id not in sticky_data:
            return await ctx.reply(
                embed=discord.Embed(
                    description="❌ There is no sticky message in this channel.",
                    color=discord.Color.red()
                )
            )

        del sticky_data[channel_id]
        self.save_data(data)

        await ctx.reply(
            embed=discord.Embed(
                description=f"🗑️ Sticky message **deleted** from {ctx.channel.mention}.",
                color=discord.Color.purple()
            )
        )
    
    @commands.command(name="poll")
    async def poll(self, ctx, *, raw_input: str):
        parts = [p.strip() for p in raw_input.split("|")]

        if len(parts) < 4:
            return await ctx.reply(
                embed=discord.Embed(
                    description="❌ Invalid format! Use: `;poll 10s | Question | Option1 | Option2 | ...` (max 10 options)",
                    color=discord.Color.red()
                )
            )

        time_str = parts[0]
        question = parts[1]
        answers = parts[2:]

        if len(answers) > 10:
            return await ctx.reply(
                embed=discord.Embed(
                    description="❌ 10 Options Maximum!",
                    color=discord.Color.red()
                )
            )

        if len(answers) < 2:
            return await ctx.reply(
                embed=discord.Embed(
                    description="❌ You must provide at least 2 options.",
                    color=discord.Color.red()
                )
            )

        seconds = parse_time(time_str)
        if seconds is None or seconds <= 0:
            return await ctx.reply(
                embed=discord.Embed(
                    description="❌ Invalid time! Use something like `10s`, `5m`, or `1h`.",
                    color=discord.Color.red()
                )
            )

        number_emojis = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]

        description = ""
        for i, answer in enumerate(answers):
            description += f"{number_emojis[i]} {answer}\n"

        embed = discord.Embed(
            title=f"📊 {question}",
            description=description,
            color=discord.Color.purple()
        )
        embed.set_footer(text=f"Poll ends in {time_str}")

        poll_msg = await ctx.reply(embed=embed)

        for i in range(len(answers)):
            await poll_msg.add_reaction(number_emojis[i])

        await asyncio.sleep(seconds)

        poll_msg = await ctx.channel.fetch_message(poll_msg.id)
        reaction_counts = [0] * len(answers)

        for reaction in poll_msg.reactions:
            if reaction.emoji in number_emojis:
                idx = number_emojis.index(reaction.emoji)
                reaction_counts[idx] = reaction.count - 1

        max_votes = max(reaction_counts)
        winners = [answers[i] for i, count in enumerate(reaction_counts) if count == max_votes]

        result_desc = ""
        for i, answer in enumerate(answers):
            result_desc += f"{number_emojis[i]} {answer} — {reaction_counts[i]} votes\n"

        result_embed = discord.Embed(
            title=f"📊 Poll Results: {question}",
            description=result_desc + f"\n🏆 Winner: {', '.join(winners)}",
            color=discord.Color.purple()
        )

        await ctx.reply(embed=result_embed)
    
    @commands.group(name="base64", invoke_without_command=True)
    async def base64(self, ctx):
        embed = discord.Embed(
            title="⚠️ Base64 Usage",
            description="Use `;base64 encode <text>` to encode text\nUse `;base64 decode <text>` to decode Base64 text",
            color=discord.Color.red()
        )
        await ctx.reply(embed=embed)

    @base64.command(name="encode")
    async def base64_encode(self, ctx, *, text: str):
        encoded = base64.b64encode(text.encode()).decode()
        embed = discord.Embed(
            title="🔐 Base64 Encode",
            description=f"**Original:**\n```{text}```\n**Encoded:**\n```{encoded}```",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)

    @base64.command(name="decode")
    async def base64_decode(self, ctx, *, text: str):
        try:
            decoded = base64.b64decode(text.encode()).decode()
            embed = discord.Embed(
                title="🔓 Base64 Decode",
                description=f"**Base64:**\n```{text}```\n**Decoded:**\n```{decoded}```",
                color=discord.Color.purple()
            )
            await ctx.reply(embed=embed)
        except Exception:
            embed = discord.Embed(
                title="❌ Error",
                description="Invalid Base64 string provided!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)
    
    @commands.command(name="qr")
    async def qr(self, ctx, *, text: str):
        qr_img = qrcode.make(text)

        buffer = io.BytesIO()
        qr_img.save(buffer, format="PNG")
        buffer.seek(0)

        embed = discord.Embed(
            title="📱 QR Code",
            description=f"QR code for: `{text}`",
            color=discord.Color.purple()
        )
        file = discord.File(fp=buffer, filename="qr.png")
        embed.set_image(url="attachment://qr.png")

        await ctx.reply(embed=embed, file=file)
    
    @commands.command()
    async def remindme(self, ctx, time_arg: str, *, reminder: str):
        seconds = parse_time(time_arg)

        if seconds is None:
            embed = discord.Embed(
                title="❌ Invalid Time Format",
                description=(
                    "Use one of the following:\n"
                    "`10s` seconds\n"
                    "`5m` minutes\n"
                    "`2h` hours\n"
                    "`3d` days\n"
                    "`1w` weeks\n"
                    "`2mo` months\n"
                    "`1y` years"
                ),
                color=discord.Color.red()
            )
            return await ctx.reply(embed=embed, mention_author=False)

        now = int(time.time())
        remind_at = now + seconds

        with open("data.json", "r") as f:
            data = json.load(f)

        data.setdefault("reminders", []).append({
            "user_id": ctx.author.id,
            "channel_id": ctx.channel.id,
            "guild_id": ctx.guild.id if ctx.guild else None,
            "message": reminder,
            "created_at": now,
            "remind_at": remind_at
        })

        with open("data.json", "w") as f:
            json.dump(data, f, indent=4)

        embed = discord.Embed(
            title="⏰ Reminder Set!",
            color=discord.Color.purple()
        )

        embed.add_field(name="📝 Reminder", value=reminder, inline=False)
        embed.add_field(
            name="⏳ When",
            value=f"<t:{remind_at}:F>\n(<t:{remind_at}:R>)",
            inline=False
        )

        embed.set_footer(text=f"Requested by {ctx.author}")
        embed.timestamp = datetime.now(timezone.utc)

        await ctx.reply(embed=embed, mention_author=False)
    
    def cog_unload(self):
        self.reminder_loop.cancel()
        self.server_stats_loop.cancel()

    def load_data(self):
        with open("data.json", "r") as f:
            return json.load(f)

    def save_data(self, data):
        with open("data.json", "w") as f:
            json.dump(data, f, indent=4)

    @commands.group(name="stats", invoke_without_command=True)
    async def stats(self, ctx):
        embed = discord.Embed(
            title="📊 Server Stats",
            description=(
                "Use `;stats create <type>` to create a stat channel or "
                "`;stats delete <type>` to remove it.\n\n"
                "**Available stat types:**\n"
                "• `members` — Only human members\n"
                "• `bots` — Only bots\n"
                "• `members_and_bots` — Total members\n"
                "• `boosts` — Server boosts"
            ),
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)


    @stats.command()
    async def create(self, ctx, stat_type: str):
        if not ctx.author.guild_permissions.manage_guild:
            embed = discord.Embed(
                title="🚫 Permission Denied",
                description="You need the **Manage Server** permission to create server stats.",
                color=discord.Color.red()
            )
            return await ctx.reply(embed=embed)

        stat_type = stat_type.lower()
        valid_types = ["members", "bots", "members_and_bots", "boosts"]
        if stat_type not in valid_types:
            embed = discord.Embed(
                title="❌ Invalid Stat Type",
                description=f"Choose from: {', '.join(valid_types)}",
                color=discord.Color.red()
            )
            return await ctx.reply(embed=embed)

        overwrites = {ctx.guild.default_role: discord.PermissionOverwrite(connect=False)}
        channel = await ctx.guild.create_voice_channel(f"{stat_type}: 0", overwrites=overwrites)

        data = self.load_data()
        guild_id = str(ctx.guild.id)
        data.setdefault("serverstats", {})
        data["serverstats"].setdefault(guild_id, {})
        data["serverstats"][guild_id][stat_type] = channel.id
        self.save_data(data)

        embed = discord.Embed(
            title="✅ Stat Created",
            description=f"Server stat `{stat_type}` has been created in {channel.mention}!",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)


    @stats.command()
    async def delete(self, ctx, stat_type: str):
        if not ctx.author.guild_permissions.manage_guild:
            embed = discord.Embed(
                title="🚫 Permission Denied",
                description="You need the **Manage Server** permission to delete server stats.",
                color=discord.Color.red()
            )
            return await ctx.reply(embed=embed)

        stat_type = stat_type.lower()
        data = self.load_data()
        guild_id = str(ctx.guild.id)

        if (
            "serverstats" not in data
            or guild_id not in data["serverstats"]
            or stat_type not in data["serverstats"][guild_id]
        ):
            embed = discord.Embed(
                title="❌ Stat Not Found",
                description=f"No stat `{stat_type}` exists in this server.",
                color=discord.Color.red()
            )
            return await ctx.reply(embed=embed)

        channel_id = data["serverstats"][guild_id][stat_type]
        channel = ctx.guild.get_channel(channel_id)
        if channel:
            await channel.delete()

        del data["serverstats"][guild_id][stat_type]
        self.save_data(data)

        embed = discord.Embed(
            title="🗑️ Stat Deleted",
            description=f"Server stat `{stat_type}` has been deleted.",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)
    
    @commands.command(name="bsmap")
    async def beatsaver(self, ctx):
        url = "https://api.beatsaver.com/maps/latest"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return await ctx.send(
                        embed=discord.Embed(
                            title="❌ Error",
                            description="Could not reach BeatSaver API.",
                            color=discord.Color.red()
                        )
                    )

                data = await resp.json()

        maps = data.get("docs", [])
        if not maps:
            return await ctx.send("No maps found 😭")

        map_data = random.choice(maps)

        name = map_data["name"]
        map_id = map_data["id"]
        uploader = map_data["uploader"]["name"]
        bpm = map_data["metadata"]["bpm"]
        duration = map_data["metadata"]["duration"]
        cover = map_data["versions"][0].get("coverURL")

        link = f"https://beatsaver.com/maps/{map_id}"

        embed = discord.Embed(
            title="🎵 Random Beat Saber Map",
            description=f"**{name}**\nby **{uploader}**",
            color=discord.Color.purple(),
            url=link
        )

        embed.add_field(name="🎶 BPM", value=bpm, inline=True)
        embed.add_field(name="⏱️ Length", value=f"{duration}s", inline=True)
        embed.add_field(name="🔗 Link", value=f"[Open on BeatSaver]({link})", inline=False)

        if cover:
            embed.set_thumbnail(url=cover)

        await ctx.reply(embed=embed)
    
    @commands.command(name="avatar")
    async def avatar(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(
            title=f"🖼️ {member.display_name}'s Avatar",
            color=discord.Color.purple()
        )
        embed.set_image(url=member.avatar.url)
        await ctx.reply(embed=embed)

    @commands.command(name="txtimg")
    async def txtimg(self, ctx, font_choice: str = None, *, text: str = None):
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

        font_path = os.path.join("assets/fonts", font_map[font_choice])

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
            file = discord.File(fp=image_binary, filename="text.png")

            embed = discord.Embed(
                title="🖼️ Generated Text Image",
                color=discord.Color.purple()
            )
            embed.set_image(url="attachment://text.png")
            embed.set_footer(text=f"Font: {font_choice}")

            await ctx.reply(embed=embed, file=file)
    
    @commands.command(name="password")
    async def password(self, ctx, length: int = 12):
        if length < 4 or length > 100:
            embed = discord.Embed(
                title="❌ Invalid Length",
                description="Password length must be between 4 and 100 characters.",
                color=discord.Color.red()
            )
            return await ctx.reply(embed=embed)

        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_=+[]{}|;:,.<>?/~`"
        password = "".join(random.choice(chars) for _ in range(length))

        embed = discord.Embed(
            title="🔐 Generated Password",
            description=f"```\n{password}\n```",
            color=discord.Color.purple()
        )

        class DeleteButtonView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)

            @discord.ui.button(label="🗑️ Delete", style=discord.ButtonStyle.red)
            async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("❌ You cannot delete this message.", ephemeral=True)
                    return
                await interaction.message.delete()

        view = DeleteButtonView()
        await ctx.reply(embed=embed, view=view)
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        data = self.load_data()

        data.setdefault("yapcount", {})
        data["yapcount"].setdefault("users", {})

        user_id = str(message.author.id)
        guild_id = str(message.guild.id)

        user_data = data["yapcount"]["users"].setdefault(user_id, {
            "global": 0,
            "servers": {}
        })

        user_data["global"] += 1
        user_data["servers"][guild_id] = user_data["servers"].get(guild_id, 0) + 1

        server_id = str(message.guild.id)
        channel_id = str(message.channel.id)

        sticky_data = data.get("servers", {}).get(server_id, {}).get("sticky", {})

        if channel_id in sticky_data:
            sticky_text = sticky_data[channel_id]

            try:
                async for msg in message.channel.history(limit=10):
                    if msg.author == self.bot.user and msg.content == sticky_text:
                        await msg.delete()
                        break
            except:
                pass

            await message.channel.send(sticky_text)

        self.save_data(data)

    @commands.command(name="yapcount")
    async def yapcount(self, ctx, scope: str = None, extra: str = None):
        if scope not in ("server", "global"):
            return await ctx.reply(
                embed=discord.Embed(
                    title="❌ Invalid Usage",
                    description="Usage: `;yapcount <server/global> [leaderboard]`",
                    color=discord.Color.red()
                )
            )

        data = self.load_data()
        users = data.get("yapcount", {}).get("users", {})
        user_id = str(ctx.author.id)

        if extra != "leaderboard":
            user_data = users.get(user_id)

            if not user_data:
                count = 0
            elif scope == "global":
                count = user_data.get("global", 0)
            else:
                count = user_data.get("servers", {}).get(str(ctx.guild.id), 0)

            embed = discord.Embed(
                title="🗣️ Yapcount",
                color=discord.Color.purple()
            )
            embed.add_field(name="Scope", value=scope.capitalize(), inline=True)
            embed.add_field(name="Messages Sent", value=str(count), inline=True)
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

            await ctx.reply(embed=embed)
            return

        leaderboard = []

        if scope == "global":
            for uid, info in users.items():
                leaderboard.append((uid, info.get("global", 0)))
        else:
            guild_id = str(ctx.guild.id)
            for uid, info in users.items():
                leaderboard.append((uid, info.get("servers", {}).get(guild_id, 0)))

        leaderboard = [x for x in leaderboard if x[1] > 0]
        leaderboard.sort(key=lambda x: x[1], reverse=True)

        if not leaderboard:
            return await ctx.reply(
                embed=discord.Embed(
                    title="🗣️ Yapcount Leaderboard",
                    description="No data available yet.",
                    color=discord.Color.red()
                )
            )

        chunks = [leaderboard[i:i + 10] for i in range(0, len(leaderboard), 10)]

        def make_embed(page: int):
            lines = []
            for i, (uid, count) in enumerate(chunks[page]):
                if scope == "server":
                    member = ctx.guild.get_member(int(uid))
                    name = member.display_name if member else "Unknown User"
                else:
                    user = self.bot.get_user(int(uid))
                    name = user.name if user else "Unknown User"

                lines.append(f"**{page * 10 + i + 1}. {name}** — `{count}`")

            embed = discord.Embed(
                title=f"🗣️ Yapcount Leaderboard ({scope.capitalize()})",
                description="\n".join(lines),
                color=discord.Color.purple()
            )
            embed.set_footer(text=f"Page {page + 1}/{len(chunks)} • Top Yappers")
            return embed

        class YapView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.page = 0

            @discord.ui.button(label="◀️", style=discord.ButtonStyle.gray)
            async def prev(self, interaction: discord.Interaction, _):
                self.page = (self.page - 1) % len(chunks)
                await interaction.response.edit_message(embed=make_embed(self.page), view=self)

            @discord.ui.button(label="▶️", style=discord.ButtonStyle.gray)
            async def next(self, interaction: discord.Interaction, _):
                self.page = (self.page + 1) % len(chunks)
                await interaction.response.edit_message(embed=make_embed(self.page), view=self)

        await ctx.reply(embed=make_embed(0), view=YapView())

async def setup(bot):
    await bot.add_cog(Utility(bot))