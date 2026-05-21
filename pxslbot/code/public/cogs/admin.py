import discord
from discord.ext import commands
import json
import os
import sys
import random
from cogs.utils import *
import asyncio

DATA_FILE = "data.json"

def is_admin():
    async def predicate(ctx):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE) as f:
                data = json.load(f)
            admin_ids = data.get("perms", {}).get("admin", [])
        else:
            admin_ids = []
        if ctx.author.id not in admin_ids:
            raise commands.CheckFailure("You are not allowed to use this command.")
        return True
    return commands.check(predicate)

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def dm_only(self, ctx, embed: discord.Embed = None, file: discord.File = None):
        try:
            if file:
                msg = await ctx.author.send(file=file)
            else:
                msg = await ctx.author.send(embed=embed)

            link = f"https://discord.com/channels/@me/{msg.channel.id}/{msg.id}"

            try:
                await ctx.reply(embed=discord.Embed(
                    description=f"📬 {ctx.author.mention}, I sent you the admin output via [DM]({link})!",
                    color=discord.Color.purple()
                ))
            except discord.NotFound:
                pass
                log("[DMLOG] Could not send DM confirmation message in channel.")

        except discord.Forbidden:
            await ctx.reply(embed=discord.Embed(
                description=f"⚠️ {ctx.author.mention}, I can't DM you. Please enable DMs.",
                color=discord.Color.red()
            ))

    @commands.command(name="admin")
    @is_admin()
    async def admin(self, ctx):
        embed = discord.Embed(
            title="🛠️ Admin Commands",
            description=(
                "`;shutdown` - Shut down the bot\n"
                "`;restart` - Restart the bot\n"
                "`;update` - Restart + update mode\n"
                "`;log <text>` - Log text to console\n"
                "`;servers` - List all servers & members\n"
                "`;showdata` - Upload data.json\n"
                "`;reload <cog>` - Reload a cog\n"
                "`;load <cog>` - Load a cog\n"
                "`;unload <cog>` - Unload a cog\n"
                "`;say <channel_id/random> <message>` - Speak as the bot\n\n"
                "`;perms add <perms> <member>` - Add perms to a user\n"
                "`;perms remove <perms> <member>` - Remove perms from a user\n"
                "`;perms list` - List all users in each perms bracket\n\n"
                "`;loggingdm enable/disable` - Enable or disable logging DMs for yourself"
            ),
            color=discord.Color.purple()
        )
        await self.dm_only(ctx, embed=embed)
    
    @commands.group(name="perms", invoke_without_command=True)
    @is_admin()
    async def perms(self, ctx):
        embed = discord.Embed(
            title="Permissions",
            description="Use `;perms add/remove/list <type> [member]`\nExample: `;perms add shitpost @User`",
            color=discord.Color.purple()
        )
        await self.dm_only(ctx, embed=embed)
    
    @perms.command(name="add")
    @is_admin()
    async def perms_add(self, ctx, perm_type: str, member: discord.Member):
        perm_type = perm_type.lower()

        if os.path.exists(DATA_FILE):
            with open(DATA_FILE) as f:
                data = json.load(f)
        else:
            data = {}

        data.setdefault("perms", {})
        data["perms"].setdefault(perm_type, [])

        if perm_type != "shitpost" and ctx.author.id not in data["perms"].get("admin", []):
            return await self.dm_only(ctx, discord.Embed(
                description=f"⚠️ Only admins can assign `{perm_type}` perms.",
                color=discord.Color.red()
            ))
        if perm_type == "shitpost" and perm_type != "admin":
            if ctx.author.id not in data["perms"].get("shitpost", []) and ctx.author.id not in data["perms"].get("admin", []):
                return await self.dm_only(ctx, discord.Embed(
                    description=f"⚠️ You don't have `{perm_type}` perms to assign it.",
                    color=discord.Color.red()
                ))

        if member.id in data["perms"][perm_type]:
            embed = discord.Embed(
                description=f"⚠️ {member.mention} already has `{perm_type}` perms.",
                color=discord.Color.orange()
            )
        else:
            data["perms"][perm_type].append(member.id)
            embed = discord.Embed(
                description=f"✅ Added `{perm_type}` perms to {member.mention}.",
                color=discord.Color.green()
            )

            with open(DATA_FILE, "w") as f:
                json.dump(data, f, indent=4)

        await self.dm_only(ctx, embed=embed)

    @perms.command(name="remove")
    @is_admin()
    async def perms_remove(self, ctx, perm_type: str, member: discord.Member):
        perm_type = perm_type.lower()

        if os.path.exists(DATA_FILE):
            with open(DATA_FILE) as f:
                data = json.load(f)
        else:
            data = {}

        data.setdefault("perms", {})
        data["perms"].setdefault(perm_type, [])

        if perm_type != "shitpost" and ctx.author.id not in data["perms"].get("admin", []):
            return await self.dm_only(ctx, discord.Embed(
                description=f"⚠️ Only admins can remove `{perm_type}` perms.",
                color=discord.Color.red()
            ))
        if perm_type == "shitpost" and perm_type != "admin":
            if ctx.author.id not in data["perms"].get("shitpost", []) and ctx.author.id not in data["perms"].get("admin", []):
                return await self.dm_only(ctx, discord.Embed(
                    description=f"⚠️ You don't have `{perm_type}` perms to remove it.",
                    color=discord.Color.red()
                ))

        if member.id not in data["perms"][perm_type]:
            embed = discord.Embed(
                description=f"⚠️ {member.mention} does not have `{perm_type}` perms.",
                color=discord.Color.orange()
            )
        else:
            data["perms"][perm_type].remove(member.id)
            embed = discord.Embed(
                description=f"✅ Removed `{perm_type}` perms from {member.mention}.",
                color=discord.Color.green()
            )

            with open(DATA_FILE, "w") as f:
                json.dump(data, f, indent=4)

        await self.dm_only(ctx, embed=embed)

    @perms.command(name="list")
    @is_admin()
    async def perms_list(self, ctx):
        if not os.path.exists(DATA_FILE):
            return await self.dm_only(ctx, discord.Embed(
                description="❌ data.json not found!",
                color=discord.Color.red()
            ))

        with open(DATA_FILE) as f:
            data = json.load(f)

        if "perms" not in data:
            return await self.dm_only(ctx, discord.Embed(
                description="❌ No permissions found.",
                color=discord.Color.orange()
            ))

        embed = discord.Embed(title="Permissions List", color=discord.Color.purple())
        for perm_type, ids in data["perms"].items():
            members = [ctx.guild.get_member(uid).name if ctx.guild.get_member(uid) else str(uid) for uid in ids]
            embed.add_field(name=perm_type.capitalize(), value=", ".join(members) or "None", inline=False)

        await self.dm_only(ctx, embed=embed)

    @commands.command(name="shutdown")
    @is_admin()
    async def shutdown(self, ctx):
        log(f"[ADMIN LOG] {ctx.author} initiated shutdown.")
        await dmlog(self.bot, f"⚠️ **{ctx.author}** has shut down the bot!")

        asyncio.create_task(set_status_channel(self.bot, "🟠"))
        asyncio.create_task(self.dm_only(ctx, discord.Embed(
            description="🛑 Bot is shutting down.",
            color=discord.Color.red()
        )))
        
        await self.bot.close()
        os._exit(0)

    @commands.command(name="restart")
    @is_admin()
    async def restart(self, ctx):
        log(f"[ADMIN LOG] {ctx.author} initiated restart.")
        await dmlog(self.bot, f"⚠️ **{ctx.author}** has restarted the bot!")

        asyncio.create_task(set_status_channel(self.bot, "🟠"))
        asyncio.create_task(self.dm_only(ctx, discord.Embed(
            description="🔄 Bot is restarting.",
            color=discord.Color.purple()
        )))
        
        os.execv(sys.executable, ["python"] + sys.argv)

    @commands.command(name="update")
    @is_admin()
    async def update(self, ctx):
        log(f"[ADMIN LOG] {ctx.author} initiated update.")
        await dmlog(self.bot, f"⚠️ **{ctx.author}** has updated the bot!")

        asyncio.create_task(set_status_channel(self.bot, "🟡"))
        asyncio.create_task(self.dm_only(ctx, discord.Embed(
            description="🟡 Bot is updating and restarting.",
            color=discord.Color.gold()
        )))
        
        os.execv(sys.executable, ["python"] + sys.argv)

    @commands.command(name="log")
    @is_admin()
    async def log(self, ctx, *, text: str):
        log(f"[ADMIN LOG] {ctx.author} :: {text}")
        await dmlog(self.bot, f"📝 **{ctx.author}** logged: {text}")
        embed = discord.Embed(
            description="📝 Logged to console and sent to admins.",
            color=discord.Color.purple()
        )
        await self.dm_only(ctx, embed)

    @commands.command(name="servers")
    @is_admin()
    async def servers(self, ctx):
        sorted_guilds = sorted(self.bot.guilds, key=lambda g: g.member_count, reverse=True)

        chunks = [sorted_guilds[i:i + 10] for i in range(0, len(sorted_guilds), 10)]

        pages = []
        for page_idx, chunk in enumerate(chunks, start=0):
            description_lines = []
            for i, guild in enumerate(chunk):
                global_idx = page_idx * 10 + i + 1
                description_lines.append(f"{global_idx}. **{guild.name}** — {guild.member_count} members")
            
            embed = discord.Embed(
                title=f"🌍 Servers ({page_idx + 1}/{len(chunks)})",
                description="\n".join(description_lines),
                color=discord.Color.purple()
            )
            pages.append(embed)

        class ServersView(discord.ui.View):
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

        view = ServersView()

        try:
            msg = await ctx.author.send(embed=pages[0], view=view)
            link = f"https://discord.com/channels/@me/{msg.channel.id}/{msg.id}"
            await ctx.reply(embed=discord.Embed(
                description=f"📬 {ctx.author.mention}, I sent you the servers list via [DM]({link})!",
                color=discord.Color.purple()
            ))
        except discord.Forbidden:
            await ctx.reply(embed=discord.Embed(
                description=f"⚠️ {ctx.author.mention}, I can't DM you. Please enable DMs to receive the servers list.",
                color=discord.Color.red()
            ))

    @commands.command(name="showdata")
    @is_admin()
    async def showdata(self, ctx):
        if not os.path.exists("data.json"):
            embed = discord.Embed(
                description="❌ data.json not found!",
                color=discord.Color.red()
            )
            await self.dm_only(ctx, embed)
            return

        file = discord.File("data.json", filename="data.json")
        await self.dm_only(ctx, file=file)

    @commands.command(name="reload")
    @is_admin()
    async def reload(self, ctx, cog: str):
        await self.bot.reload_extension(f"cogs.{cog}")
        await self.dm_only(ctx, discord.Embed(
            description=f"🔁 Reloaded `cogs.{cog}`",
            color=discord.Color.purple()
        ))

    @commands.command(name="load")
    @is_admin()
    async def load(self, ctx, cog: str):
        await self.bot.load_extension(f"cogs.{cog}")
        await self.dm_only(ctx, discord.Embed(
            description=f"📥 Loaded `cogs.{cog}`",
            color=discord.Color.purple()
        ))

    @commands.command(name="unload")
    @is_admin()
    async def unload(self, ctx, cog: str):
        await self.bot.unload_extension(f"cogs.{cog}")
        await self.dm_only(ctx, discord.Embed(
            description=f"📤 Unloaded `cogs.{cog}`",
            color=discord.Color.purple()
        ))

    @commands.command(name="say")
    @is_admin()
    async def say(self, ctx, target: str, *, message: str):
        await ctx.message.delete()

        if target.lower() == "random":
            guild = random.choice(self.bot.guilds)
            channels = [c for c in guild.text_channels if c.permissions_for(guild.me).send_messages]
            if not channels:
                await self.dm_only(ctx, discord.Embed(
                    description=f"⚠️ No valid text channels found in `{guild.name}`.",
                    color=discord.Color.red()
                ))
                return
            channel = random.choice(channels)
            await channel.send(message)
            embed = discord.Embed(
                description=f"✅ Message sent in random channel **{channel.name}** of **{guild.name}**.",
                color=discord.Color.purple()
            )
            await self.dm_only(ctx, embed)
            return

        try:
            channel_id = int(target)
            channel = self.bot.get_channel(channel_id)
            if not channel or not isinstance(channel, discord.TextChannel):
                raise ValueError
            await channel.send(message)
            embed = discord.Embed(
                description=f"✅ Message sent in <#{channel_id}>.",
                color=discord.Color.purple()
            )
            await self.dm_only(ctx, embed)
        except Exception:
            embed = discord.Embed(
                description=f"❌ Could not send message. Make sure the channel ID is valid and I can send messages there.",
                color=discord.Color.red()
            )
            await self.dm_only(ctx, embed)
        
    @commands.group(name="loggingdm", invoke_without_command=True)
    @is_admin()
    async def loggingdm(self, ctx):
        if not os.path.exists(DATA_FILE):
            data = {"loggingdm_disabled": []}
            with open(DATA_FILE, "w") as f:
                json.dump(data, f, indent=4)
        else:
            with open(DATA_FILE) as f:
                data = json.load(f)
            if "loggingdm_disabled" not in data:
                data["loggingdm_disabled"] = []

        status = "disabled" if ctx.author.id in data["loggingdm_disabled"] else "enabled"
        embed = discord.Embed(
            title="Admin DM Logging",
            description=f"Your logging DMs are currently **{status}**.\nUse `;loggingdm enable` or `;loggingdm disable` to change it.",
            color=discord.Color.purple()
        )
        await self.dm_only(ctx, embed=embed)

    @loggingdm.command(name="disable")
    @is_admin()
    async def loggingdm_disable(self, ctx):
        with open(DATA_FILE) as f:
            data = json.load(f)
        if "loggingdm_disabled" not in data:
            data["loggingdm_disabled"] = []

        if ctx.author.id not in data["loggingdm_disabled"]:
            data["loggingdm_disabled"].append(ctx.author.id)
            with open(DATA_FILE, "w") as f:
                json.dump(data, f, indent=4)

        embed = discord.Embed(
            description="❌ You will no longer receive logging DMs.",
            color=discord.Color.orange()
        )
        await self.dm_only(ctx, embed=embed)

    @loggingdm.command(name="enable")
    @is_admin()
    async def loggingdm_enable(self, ctx):
        with open(DATA_FILE) as f:
            data = json.load(f)
        if "loggingdm_disabled" not in data:
            data["loggingdm_disabled"] = []

        if ctx.author.id in data["loggingdm_disabled"]:
            data["loggingdm_disabled"].remove(ctx.author.id)
            with open(DATA_FILE, "w") as f:
                json.dump(data, f, indent=4)

        embed = discord.Embed(
            description="✅ You will now receive logging DMs again.",
            color=discord.Color.green()
        )
        await self.dm_only(ctx, embed=embed)

async def setup(bot):
    await bot.add_cog(Admin(bot))
