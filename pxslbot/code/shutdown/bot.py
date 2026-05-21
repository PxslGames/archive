import discord
from discord.ext import commands

TOKEN = ""

intents = discord.Intents.all()
intents.message_content = True

bot = commands.Bot(command_prefix=";", intents=intents)

SHUTDOWN_MESSAGE = "# Hello, PxslBot is shutting down. Add our new bot: Clanker 🙂 https://discord.gg/YtQdrkxfg7 @everyone"

# -------- READY --------
@bot.event
async def on_ready():
    print(f"Dead bot online as {bot.user}")
    
    await bot.change_presence(
        activity=discord.Game("Shut Down")
    )

# -------- MESSAGE --------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # ANY message triggers it
    await message.channel.send(SHUTDOWN_MESSAGE)

# -------- SLASH COMMANDS --------
@bot.tree.error
async def on_app_command_error(interaction, error):
    try:
        await interaction.response.send_message(SHUTDOWN_MESSAGE, ephemeral=True)
    except:
        pass

# -------- BLOCK PREFIX COMMANDS --------
@bot.check
async def block_all(ctx):
    await ctx.send(SHUTDOWN_MESSAGE)
    return False

# -------- INTERACTIONS (buttons, etc.) --------
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        try:
            await interaction.response.send_message(SHUTDOWN_MESSAGE, ephemeral=True)
        except:
            pass

bot.run(TOKEN)