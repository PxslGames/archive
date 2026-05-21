import discord
from discord.ext import commands
import random
from cogs.utils import *
import aiohttp
import asyncio
import json
import io
from urllib.parse import urlparse
import os

class Fun(commands.Cog):
    DATA_FILE = "data.json"

    def __init__(self, bot):
        self.bot = bot
        self.SHITPOST_DIR = "shitposts"
        os.makedirs(self.SHITPOST_DIR, exist_ok=True)

        try:
            with open(self.DATA_FILE, "r", encoding="utf-8") as f:
                bot.data = json.load(f)
        except FileNotFoundError:
            bot.data = {"shitposts": [], "perms": {"admin": []}}
    
    def load_data(self):
        return self.bot.data

    def save_data(self, data=None):
        if data is None:
            data = self.bot.data
        with open(self.DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    
    def can_shitpost(self):
        async def predicate(ctx):
            data = self.load_data()
            perms = data.get("perms", {})
            admin_ids = perms.get("admin", [])
            shitpost_ids = perms.get("shitpost", [])

            if ctx.author.id in admin_ids:
                return True
            if ctx.author.id in shitpost_ids:
                return True
            raise commands.CheckFailure("❌ You do not have permission to use shitpost commands.")
        return commands.check(predicate)
    
    async def cog_app_command_check(self, interaction: discord.Interaction):
        if interaction.user.bot:
            return True
        check_global_cooldown(interaction.user.id)
        return True

    @commands.command(name="fun")
    async def fun(self, ctx):
        embed = discord.Embed(
            title="📚 Fun Commands",
            description="This is a category for fun commands like `;dice`, `;coinflip`, and `;8ball`.",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)

    @commands.command(name="dice")
    async def dice(self, ctx):
        rolled = random.randint(1, 6)
        embed = discord.Embed(
            title="🎲 Dice",
            description=f"You rolled a: **{rolled}**!",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)
    
    @commands.command(name="coinflip")
    async def coinflip(self, ctx):
        result = random.choice(["Heads", "Tails"])
        embed = discord.Embed(
            title="🪙 Coinflip",
            description=f"You got: **{result}**!",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)
    
    @commands.command(name="8ball")
    async def eightball(self, ctx, *, question: str):
        responses = [
            "Absolutely!", "Without a doubt.", "Yes - definitely.",
            "You may rely on it.", "It is certain.", "Signs point to yes.",
            "Reply hazy, try again.", "Ask again later.", "Better not tell you now.",
            "Cannot predict now.", "Concentrate and ask again.",
            "Don't count on it.", "My sources say no.", "Very doubtful.", "No."
        ]
        answer = random.choice(responses)
        embed = discord.Embed(
            title="🎱 8-Ball",
            description=f"Question: {question}\nAnswer: **{answer}**",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)

    @eightball.error
    async def eightball_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="⚠️ Missing Question",
                description="You need to ask a question! Example: `;8ball Will I win today?`",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)
    
    @commands.command(name="7ball")
    async def sevenball(self, ctx, *, question: str):
        responses = [
            "maybe...", "i dont know, ask someone else", "HAOOHOHOHAHHAOAOAOOA", "8 ball's bad cousin",
            "wait... actually, dont worry", "yeah probably idk", "NO! NO! NO!", "WHAT???", "silyl",
            "discord... bot?", "self destructing...", "boom!", "dont worry im just deleting your server :)",
            "oh no! i definitely crashed its not like i just cant be asked to respond to your stupid question or anything oh no!",
            "look, im gonna be honest, this is happening", "look, im gonna be honest, this isn't happening", "look, im gonna be honest, this might be happening",
            "look behind you :)", "do a backflip", "so im 7 ball, right...", "[insert phrase here]", "give me self promod "
        ]
        answer = random.choice(responses)
        embed = discord.Embed(
            title="🎱 7-Ball",
            description=f"Question: {question}\nAnswer: **{answer}**",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)

    @sevenball.error
    async def sevenball_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="⚠️ Missing Question",
                description="You need to ask a question! Example: `;7ball Will I win today?`",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)
    
    @commands.command(name="howdumb")
    async def howdumb(self, ctx, *, user: discord.Member = None):
        embed = discord.Embed(
            title="🤪 How Dumb?",
            description=f"{user} is {random.randint(1, 100)}% dumb.",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)
    
    @commands.command(name="howskid")
    async def howskid(self, ctx, *, user: discord.Member = None):
        embed = discord.Embed(
            title="💩 How Skid?",
            description=f"{user} is {random.randint(1, 100)}% of a skid.",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)
    
    @commands.command(name="randomnumber")
    async def randomnumber(self, ctx, low: int = None, high: int = None):
        if low is None or high is None:
            embed = discord.Embed(
                title="⚠️ Missing Arguments",
                description="You need to provide two numbers! Example: `;randomnumber 1 100`",
                color=discord.Color.red()
            )
            return await ctx.reply(embed=embed)
        
        if low > high:
            embed = discord.Embed(
                title="⚠️ Invalid Range",
                description="The first number must be smaller than or equal to the second number.",
                color=discord.Color.red()
            )
            return await ctx.reply(embed=embed)
        
        number = random.randint(low, high)
        embed = discord.Embed(
            title="🎰 Random Number",
            description=f"Your random number is: **{number}**!",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)

    @randomnumber.error
    async def randomnumber_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="⚠️ Invalid Input",
                description="Make sure you enter valid numbers. Example: `;randomnumber 1 100`",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)
    
    @commands.command(name="gamble")
    async def gamble(self, ctx):
        outcomes = ["🍒", "🍋", "🍊", "🍉", "🍎", "🍇", "🍓", "🍍", "⭐", "7️⃣"]

        result = random.choices(outcomes, k=3)

        if result.count("7️⃣") == 3:
            embed = discord.Embed(
                title="🎰 JACKPOT! 🎉",
                description=f"{' | '.join(result)}\n\n💰 You hit triple 7️⃣! You're a legend! 💰",
                color=discord.Color.gold()
            )
            embed.add_field(name="🔥 Lucky Streak 🔥", value="This is super rare! 🎆🎆🎆")
        else:
            embed = discord.Embed(
                title="🎰 Gamble",
                description=f"{' | '.join(result)}\n\n💡 Get three 7️⃣s to win!",
                color=discord.Color.purple()
            )

        await ctx.reply(embed=embed)
    
    @commands.command()
    async def dadjoke(self, ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://icanhazdadjoke.com/", headers={"Accept": "application/json"}) as resp:
                data = await resp.json()
                embed = discord.Embed(
                    title="😂 Dad Joke",
                    description=f"{data['joke']}",
                    color=discord.Color.purple()
                )
                await ctx.reply(embed=embed)
    
    @commands.command(name="dog")
    async def dog(self, ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://dog.ceo/api/breeds/image/random") as resp:
                data = await resp.json()
                embed = discord.Embed(
                    title="🐶 Random Dog",
                    color=discord.Color.purple()
                )
                embed.set_image(url=data['message'])
                await ctx.reply(embed=embed)
    
    @commands.command(name="cat")
    async def cat(self, ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.thecatapi.com/v1/images/search") as resp:
                data = await resp.json()
                embed = discord.Embed(
                    title="🐱 Random Cat",
                    color=discord.Color.purple()
                )
                embed.set_image(url=data[0]['url'])
                await ctx.reply(embed=embed)
    
    @commands.command(name="selfdestruct")
    @commands.cooldown(1, 30, commands.BucketType.channel)
    async def selfdestruct(self, ctx):
        msg = await ctx.reply(
            embed=discord.Embed(
                title="🚨 EMERGENCY MODE ACTIVATED",
                description="**Self Destruct Initializing...**",
                color=discord.Color.red()
            )
        )

        steps = [
            ("🚨 EMERGENCY MODE ACTIVATED", "Self Destruct in **3**…"),
            ("⚠️ WARNING", "Self Destruct in **2**…"),
            ("☢️ CRITICAL", "Self Destruct in **1**…"),
            ("💥 BOOM", "*Just kidding.* 😈")
        ]

        for title, desc in steps:
            await asyncio.sleep(1.3)
            embed = discord.Embed(
                title=title,
                description=desc,
                color=discord.Color.red()
            )
            await msg.edit(embed=embed)
    
    @commands.command(name="truthordare")
    async def truthordare(self, ctx, choice: str = None):
        truths = [
            "What is your biggest fear?", 
            "Have you ever lied to your best friend?",
            "What is the most embarrassing thing you've ever done?",
            "Have you ever cheated on a test?", 
            "What is a secret you've never told anyone?"
        ]
        dares = [
            "Do 10 push-ups.", 
            "Sing a song loudly.", 
            "Dance for 30 seconds.",
            "Do an impression of your favorite celebrity.", 
            "Tell a joke."
        ]

        if choice is None:
            choice = random.choice(["truth", "dare"])
        else:
            choice = choice.lower()

        if choice == "truth":
            question = random.choice(truths)
            embed = discord.Embed(
                title="🤫 Truth",
                description=question,
                color=discord.Color.purple()
            )
            await ctx.reply(embed=embed)
        elif choice == "dare":
            task = random.choice(dares)
            embed = discord.Embed(
                title="🎲 Dare",
                description=task,
                color=discord.Color.purple()
            )
            await ctx.reply(embed=embed)
        else:
            embed = discord.Embed(
                title="⚠️ Invalid Choice",
                description="Please choose either 'truth' or 'dare'. Example: `;truthordare truth`",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)
    
    @commands.command(name="rps")
    async def rps(self, ctx, user_choice: str):
        choices = ["rock", "paper", "scissors"]
        user_choice = user_choice.lower()

        if user_choice not in choices:
            embed = discord.Embed(
                title="⚠️ Invalid Choice",
                description="Please choose either 'rock', 'paper', or 'scissors'. Example: `;rps rock`",
                color=discord.Color.red()
            )
            return await ctx.reply(embed=embed)

        bot_choice = random.choice(choices)

        if user_choice == bot_choice:
            result = "It's a tie!"
        elif (user_choice == "rock" and bot_choice == "scissors") or (user_choice == "paper" and bot_choice == "rock") or (user_choice == "scissors" and bot_choice == "paper"):

            result = "You win!"
        else:
            result = "You lose!"

        embed = discord.Embed(
            title="🎮 Rock Paper Scissors",
            description=f"Your choice: {user_choice}\nBot's choice: {bot_choice}\nResult: {result}",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)
    
    @commands.group(name="counting", invoke_without_command=True)
    async def counting(self, ctx):
        data = self.load_data()
        guild_id = str(ctx.guild.id)
        counting_data = data.get("counting", {}).get(guild_id)

        if not counting_data:
            return await ctx.reply(
                embed=discord.Embed(
                    title="🔢 Counting",
                    description="Counting is **disabled** in this server.",
                    color=discord.Color.red()
                )
            )

        channel = ctx.guild.get_channel(counting_data["channel_id"])

        embed = discord.Embed(
            title="🔢 Counting",
            description=(
                f"📍 Channel: {channel.mention if channel else 'Deleted'}\n"
                f"🔢 Current number: **{counting_data['current']}**\n\n"
                "Type numbers directly in the counting channel."
            ),
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)

    @counting.command()
    async def enable(self, ctx):
        if not ctx.author.guild_permissions.manage_channels:
            return await ctx.reply(
                embed=discord.Embed(
                    title="🚫 Permission Denied",
                    description="You need **Manage Channels** to enable counting.",
                    color=discord.Color.red()
                )
            )

        data = self.load_data()
        guild_id = str(ctx.guild.id)

        data.setdefault("counting", {})
        data["counting"][guild_id] = {
            "channel_id": ctx.channel.id,
            "current": 0
        }

        self.save_data(data)

        await ctx.reply(
            embed=discord.Embed(
                title="✅ Counting Enabled",
                description=f"{ctx.channel.mention} is now the counting channel.\nStart with **1**.",
                color=discord.Color.purple()
            )
        )

    @counting.command()
    async def disable(self, ctx):
        if not ctx.author.guild_permissions.manage_channels:
            return await ctx.reply(
                embed=discord.Embed(
                    title="🚫 Permission Denied",
                    description="You need **Manage Channels** to disable counting.",
                    color=discord.Color.red()
                )
            )

        data = self.load_data()
        guild_id = str(ctx.guild.id)

        if guild_id not in data.get("counting", {}):
            return await ctx.reply(
                embed=discord.Embed(
                    title="❌ Not Enabled",
                    description="Counting is not enabled in this server.",
                    color=discord.Color.red()
                )
            )

        del data["counting"][guild_id]
        self.save_data(data)

        await ctx.reply(
            embed=discord.Embed(
                title="🛑 Counting Disabled",
                description="Counting has been disabled for this server.",
                color=discord.Color.purple()
            )
        )

    @counting.command(name="leaderboard")
    async def leaderboard(self, ctx, page: int = 1):
        data = self.load_data()
        counting_data_all = data.get("counting", {})

        if not counting_data_all:
            return await ctx.reply(
                embed=discord.Embed(
                    title="🔢 Counting Leaderboard",
                    description="No servers have counting enabled yet.",
                    color=discord.Color.red()
                )
            )

        leaderboard_list = []
        for guild_id, info in counting_data_all.items():
            guild = self.bot.get_guild(int(guild_id))
            if guild:
                leaderboard_list.append((guild.name, info["current"]))

        leaderboard_list.sort(key=lambda x: x[1], reverse=True)
        chunks = [leaderboard_list[i:i + 10] for i in range(0, len(leaderboard_list), 10)]
        max_page = len(chunks)

        if page < 1 or page > max_page:
            page = 1

        embed = discord.Embed(
            title=f"🔢 Counting Leaderboard (Page {page}/{max_page})",
            color=discord.Color.purple()
        )

        start_idx = (page - 1) * 10
        description_lines = [f"**{start_idx + i + 1}. {g}** — {n}" for i, (g, n) in enumerate(chunks[page - 1])]
        embed.description = "\n".join(description_lines)

        class LeaderboardView(discord.ui.View):
            def __init__(self):
                super().__init__()
                self.current_page = page - 1

            @discord.ui.button(label="◀️", style=discord.ButtonStyle.gray)
            async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.current_page = (self.current_page - 1) % max_page
                embed.title = f"🔢 Counting Leaderboard (Page {self.current_page + 1}/{max_page})"
                chunk = chunks[self.current_page]
                desc_lines = [f"**{self.current_page * 10 + i + 1}. {g}** — {n}" for i, (g, n) in enumerate(chunk)]
                embed.description = "\n".join(desc_lines)
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="▶️", style=discord.ButtonStyle.gray)
            async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.current_page = (self.current_page + 1) % max_page
                embed.title = f"🔢 Counting Leaderboard (Page {self.current_page + 1}/{max_page})"
                chunk = chunks[self.current_page]
                desc_lines = [f"**{self.current_page * 10 + i + 1}. {g}** — {n}" for i, (g, n) in enumerate(chunk)]
                embed.description = "\n".join(desc_lines)
                await interaction.response.edit_message(embed=embed, view=self)

        view = LeaderboardView()
        await ctx.reply(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        data = self.load_data()
        guild_id = str(message.guild.id)
        counting_data = data.get("counting", {}).get(guild_id)

        if not counting_data or message.channel.id != counting_data["channel_id"]:
            return

        try:
            number = int(message.content.strip())
        except (ValueError, AttributeError):
            return

        if number == counting_data["current"]:
            await message.channel.send(
                embed=discord.Embed(
                    title="✏️ Counting Message Deleted",
                    description=(
                        f"A valid number (**{number}**) by {message.author.mention} was deleted.\n"
                        f"⚠️ The next number is still **{number + 1}**."
                    ),
                    color=discord.Color.orange()
                )
            )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        data = self.load_data()
        guild_id = str(message.guild.id)
        counting_data = data.get("counting", {}).get(guild_id)

        if not counting_data:
            await self.bot.process_commands(message)
            return

        if message.channel.id != counting_data["channel_id"]:
            await self.bot.process_commands(message)
            return

        try:
            number = int(message.content.strip())
        except ValueError:
            await message.delete()
            return

        expected = counting_data["current"] + 1

        if number == expected:
            counting_data["current"] = number
            self.save_data(data)
            await message.add_reaction("✅")
            return

        counting_data["current"] = 0
        self.save_data(data)

        await message.channel.send(
            embed=discord.Embed(
                title="💥 Counting Reset",
                description=(
                    f"{message.author.mention} ruined it at **{number}**.\n"
                    "🔁 The count has been reset.\n"
                    "▶️ Start again from **1**."
                ),
                color=discord.Color.red()
            )
        )
    
    @commands.command(name="bwomp")
    async def bwomp(self, ctx):
        file = discord.File("assets/sounds/bwomp.mp3", filename="bwomp.mp3")
        
        embed = discord.Embed(
            title="🔊 Bwomp!",
            description="🎵 *Bwomp bwomp bwomp* 🎵",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed, file=file)
    
    async def url_to_file(self, url, filename=None):
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status != 200:
                        return None

                    data = await resp.read()

                    if not filename:
                        filename = os.path.basename(url.split("?")[0]) or "shitpost"

                    name, ext = os.path.splitext(filename)
                    path = os.path.join(self.SHITPOST_DIR, filename)
                    counter = 2

                    while os.path.exists(path):
                        filename = f"{name}-{counter}{ext}"
                        path = os.path.join(self.SHITPOST_DIR, filename)
                        counter += 1

                    with open(path, "wb") as f:
                        f.write(data)

                    return path, filename

        except Exception as e:
            print("Download error:", e)
            return None, None

    def get_extension(self, path):
        return os.path.splitext(urlparse(path).path)[1].lower()

    @commands.group(name="shitpost", invoke_without_command=True)
    async def shitpost(self, ctx):
        data = self.load_data()
        shitposts = data.get("shitposts", [])

        if not shitposts:
            embed = discord.Embed(
                title="🚫 No Shitposts",
                description="No Shitposts available.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)
            return

        filename = random.choice(shitposts)
        path = os.path.join(self.SHITPOST_DIR, filename)

        if not os.path.exists(path):
            embed = discord.Embed(
                title="🚫 Shitpost Missing",
                description="This shitpost file was deleted.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)
            return

        await ctx.reply(file=discord.File(path))
    
    @shitpost.command(name="add")
    @commands.check(lambda ctx: ctx.cog.can_shitpost()(ctx))
    async def add(self, ctx, link: str = None):
        data = self.load_data()
        shitposts = data.setdefault("shitposts", [])

        if ctx.message.attachments:
            added = 0
            for attachment in ctx.message.attachments:
                filename = attachment.filename
                name, ext = os.path.splitext(filename)
                path = os.path.join(self.SHITPOST_DIR, filename)
                counter = 2

                while os.path.exists(path) or filename in shitposts:
                    filename = f"{name}-{counter}{ext}"
                    path = os.path.join(self.SHITPOST_DIR, filename)
                    counter += 1

                await attachment.save(path)
                shitposts.append(filename)
                added += 1

            if added > 0:
                self.save_data(data)
                embed = discord.Embed(
                    title="✅ Shitposts Added",
                    description=f"Added {added} new shitpost(s)!",
                    color=discord.Color.green()
                )
                await ctx.reply(embed=embed)
            else:
                embed = discord.Embed(
                    title="⚠️ No New Shitposts",
                    description="All attachments already exist as shitposts.",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed)
            return

        if link:
            filename = os.path.basename(link.split("?")[0]) or "shitpost"
            path, actual_filename = await self.url_to_file(link, filename)
            if not path:
                embed = discord.Embed(
                    title="🚫 Download Failed",
                    description="Failed to download the shitpost from the provided URL.",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed)
                return

            shitposts.append(actual_filename)
            self.save_data(data)
            embed = discord.Embed(
                title="✅ Shitpost Added",
                description=f"Added shitpost: **{actual_filename}**",
                color=discord.Color.green()
            )
            await ctx.reply(embed=embed)
            return

        embed = discord.Embed(
            title="⚠️ No Input",
            description="Please provide a URL or attach a file to add as a shitpost.",
            color=discord.Color.red()
        )
        await ctx.reply(embed=embed)

    @shitpost.command(name="delete")
    @commands.check(lambda ctx: ctx.cog.can_shitpost()(ctx))
    async def delete(self, ctx, filename: str):
        data = self.load_data()
        shitposts = data.get("shitposts", [])

        if filename not in shitposts:
            embed = discord.Embed(
                title="🚫 Shitpost Not Found",
                description="No shitpost with that filename exists.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)
            return

        shitposts.remove(filename)
        self.save_data(data)

        path = os.path.join(self.SHITPOST_DIR, filename)
        if os.path.exists(path):
            os.remove(path)

        embed = discord.Embed(
            title="✅ Shitpost Deleted",
            description=f"Deleted shitpost: **{filename}**",
            color=discord.Color.green()
        )
        await ctx.reply(embed=embed)
    
    @shitpost.command(name="count")
    async def count(self, ctx):
        files = os.listdir(self.SHITPOST_DIR)
        count = len(files)

        embed = discord.Embed(
            title="📂 Shitpost Count",
            description=f"There are currently **{count}** shitpost file(s) in the folder.",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)

async def setup(bot):
    await bot.add_cog(Fun(bot))