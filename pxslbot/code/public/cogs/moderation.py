import discord
from discord.ext import commands
from cogs.utils import *

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def cog_app_command_check(self, interaction: discord.Interaction):
        if interaction.user.bot:
            return True
        check_global_cooldown(interaction.user.id)
        return True
    
    @commands.command(name="moderation")
    async def moderation(self, ctx):
        embed = discord.Embed(
            title="📚 Moderation Commands",
            description="This is a category for moderation commands like `;kick`, `;ban`, and `;userinfo`.",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)
    
    @commands.command(name="kick")
    async def kick(self, ctx, member: discord.Member, *, reason="No Reason Provided"):
        if not ctx.author.guild_permissions.kick_members:
            embed = discord.Embed(
                title="🚫 Error",
                description="You don't have permission to kick members!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, delete_after=15)
            return
        try:
            await member.kick(reason=reason)
            embed = discord.Embed(
                title="💨 Successfully Kicked Member",
                description=f"Kicked member: {member}\nReason: {reason}",
                color=discord.Color.purple()
            )
            await ctx.reply(embed=embed, delete_after=15)
        except Exception as e:
            embed = discord.Embed(
                title="🚫 Error",
                description=f"Couldn't complete action. reason: {e}",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, delete_after=15)
    
    @commands.command(name="ban")
    async def ban(self, ctx, member: discord.Member, *, reason="No Reason Provided"):
        if not ctx.author.guild_permissions.kick_members:
            embed = discord.Embed(
                title="🚫 Error",
                description="You don't have permission to ban members!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, delete_after=15)
            return
        try:
            await member.ban(reason=reason)
            embed = discord.Embed(
                title="💨 Successfully Banned Member",
                description=f"Banned member: {member}\nReason: {reason}",
                color=discord.Color.purple()
            )
            await ctx.reply(embed=embed, delete_after=15)
        except Exception as e:
            embed = discord.Embed(
                title="🚫 Error",
                description=f"Couldn't complete action. reason: {e}",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, delete_after=15)
    
    @commands.command(name="userinfo")
    async def userinfo(self, ctx, *, user: discord.Member = None):
        user = user or ctx.author

        embed = discord.Embed(
            title=f"User Info - {user}",
            color=discord.Color.purple()
        )

        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)

        try:
            user_obj = await ctx.bot.fetch_user(user.id)
            if user_obj.banner:
                embed.set_image(url=user_obj.banner.url)
        except:
            pass

        embed.add_field(name="🧍 Username", value=user.name, inline=True)
        embed.add_field(name="🆔 ID", value=user.id, inline=True)

        created = user.created_at.strftime("%Y-%m-%d %H:%M UTC")
        embed.add_field(name="📅 Created", value=created, inline=True)

        if isinstance(user, discord.Member):
            joined = user.joined_at.strftime("%Y-%m-%d %H:%M UTC")
            embed.add_field(name="📥 Joined Server", value=joined, inline=True)

        if isinstance(user, discord.Member):
            roles = [role.mention for role in user.roles[1:]]
            if roles:
                role_list = ", ".join(roles[:20])
                embed.add_field(name="🎭 Roles", value=role_list, inline=False)
            else:
                embed.add_field(name="🎭 Roles", value="None", inline=False)

        embed.set_footer(text="PxslBot - User Lookup")

        await ctx.reply(embed=embed)
    
    @commands.command(name="slowmode")
    async def slowmode(self, ctx, time: str = None):
        if not ctx.author.guild_permissions.manage_channels:
            embed = discord.Embed(
                title="🚫 Error",
                description="You don't have permission to change slowmode!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, delete_after=15)
            return
        
        if time is None:
            current = ctx.channel.slowmode_delay
            if current == 0:
                desc = f"⏱️ Slowmode is **disabled** in {ctx.channel.mention}."
            else:
                desc = f"⏱️ Current slowmode in {ctx.channel.mention} is **{current} seconds**."

            return await ctx.reply(
                embed=discord.Embed(
                    description=desc,
                    color=discord.Color.purple()
                )
            )

        if time.lower() in ["disable", "off", "0"]:
            await ctx.channel.edit(slowmode_delay=0)
            return await ctx.reply(
                embed=discord.Embed(
                    description=f"⏱️ Slowmode **disabled** in {ctx.channel.mention}.",
                    color=discord.Color.purple()
                )
            )

        seconds = parse_time(time)

        if seconds is None:
            return await ctx.reply(
                embed=discord.Embed(
                    description="❌ Invalid format!\nUse: `10s`, `5m`, `1h`, `disable`.",
                    color=discord.Color.red()
                )
            )

        await ctx.channel.edit(slowmode_delay=seconds)

        return await ctx.reply(
            embed=discord.Embed(
                description=f"⏱️ Slowmode set to **{time}** in {ctx.channel.mention}.",
                color=discord.Color.purple()
            )
        )
    
    @commands.command(name="purge")
    async def purge(self, ctx, amount: int):
        if not ctx.author.guild_permissions.manage_messages:
            embed = discord.Embed(
                title="🚫 Error",
                description="You don't have permission to delete messages!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, delete_after=15)
            return
        
        if amount < 1:
            embed = discord.Embed(
                title="🚫 Error",
                description="Please enter a number of messages to delete!",
                color=discord.Color.red()
            )
            return await ctx.reply(embed=embed, delete_after=15)
        
        deleted = await ctx.channel.purge(limit=amount + 1)
        
        embed = discord.Embed(
            title="🧹 Purge Completed!",
            description=f"Deleted {len(deleted)-1} messages successfully.",
            color=discord.Color.purple()
        )
        await ctx.reply(embed=embed)
    
    @commands.command(name="nick")
    async def nick(self, ctx, member: discord.Member, *, nickname: str = None):
        if not ctx.author.guild_permissions.manage_nicknames:
            embed = discord.Embed(
                title="🚫 Error",
                description="You don't have permission to change nicknames!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, delete_after=15)
            return

        if nickname is None:
            await member.edit(nick=None)
            embed = discord.Embed(
                title="👤 Nickname Changed",
                description=f"Reset {member.mention}'s nickname.",
                color=discord.Color.purple()
            )
        else:
            await member.edit(nick=nickname)
            embed = discord.Embed(
                title="👤 Nickname Changed",
                description=f"Changed {member.mention}'s nickname to `{nickname}`.",
                color=discord.Color.purple()
            )

        await ctx.reply(embed=embed)
    
    
    @commands.command(name="lock")
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        overwrites = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrites.send_messages = False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrites)

        embed = discord.Embed(
            title="🔒 Channel Locked",
            description=f"{ctx.channel.mention} is now locked for everyone!",
            color=discord.Color.red()
        )
        await ctx.reply(embed=embed)

    @commands.command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        overwrites = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrites.send_messages = None
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrites)

        embed = discord.Embed(
            title="🔓 Channel Unlocked",
            description=f"{ctx.channel.mention} is now unlocked for everyone!",
            color=discord.Color.purple()
        )
        await ctx.replyd (embed=embed)

    @lock.error
    @unlock.error
    async def lock_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="⛔ Permission Denied",
                description="You need **Manage Channels** permission to do that.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))