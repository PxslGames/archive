import discord
from discord.ext import commands
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageDraw, ImageFont
import io
import aiohttp

class Manipulation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def fetch_image(self, attachment):
        async with aiohttp.ClientSession() as session:
            async with session.get(attachment.url) as resp:
                if resp.status != 200:
                    return None
                data = await resp.read()
        return Image.open(io.BytesIO(data))

    async def send_image(self, ctx, img, title, filename="image.png"):
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        embed = discord.Embed(title=title, color=discord.Color.purple())
        file = discord.File(fp=buffer, filename=filename)
        embed.set_image(url=f"attachment://{filename}")
        await ctx.reply(embed=embed, file=file)
    
    @commands.command(name="invert")
    async def invert(self, ctx):
        if not ctx.message.attachments:
            embed = discord.Embed(
                title="⚠️ Missing Attachment",
                description="You need to provide an image attachment to invert!",
                color=discord.Color.red()
            )
            return await ctx.reply(embed=embed)

        attachment = ctx.message.attachments[0]

        async with aiohttp.ClientSession() as session:
            async with session.get(attachment.url) as resp:
                if resp.status != 200:
                    embed = discord.Embed(
                        title="🚫 Error",
                        description="Failed to download the image.",
                        color=discord.Color.red()
                    )
                    return await ctx.reply(embed=embed)

                data = await resp.read()

        with Image.open(io.BytesIO(data)) as img:
            inverted_image = ImageOps.invert(img.convert("RGB"))

            buffer = io.BytesIO()
            inverted_image.save(buffer, format="PNG")
            buffer.seek(0)

        embed = discord.Embed(
            title="🌀 Inverted Image",
            color=discord.Color.purple()
        )
        file = discord.File(fp=buffer, filename="inverted.png")
        embed.set_image(url="attachment://inverted.png")

        await ctx.reply(embed=embed, file=file)
    
    @commands.command(name="gif")
    async def gif(self, ctx):
        if not ctx.message.attachments:
            embed = discord.Embed(
                title="⚠️ Missing Attachment",
                description="Attach an image to convert into a GIF.",
                color=discord.Color.red()
            )
            return await ctx.reply(embed=embed)

        attachment = ctx.message.attachments[0]

        async with aiohttp.ClientSession() as session:
            async with session.get(attachment.url) as resp:
                if resp.status != 200:
                    embed = discord.Embed(
                        title="🚫 Error",
                        description="Failed to download the image.",
                        color=discord.Color.red()
                    )
                    return await ctx.reply(embed=embed)

                data = await resp.read()

        with Image.open(io.BytesIO(data)) as img:
            img = img.convert("RGBA")

            buffer = io.BytesIO()
            img.save(
                buffer,
                format="GIF",
                save_all=True,
                loop=0
            )
            buffer.seek(0)

        file = discord.File(fp=buffer, filename="image.gif")
        embed = discord.Embed(
            title="🖼️ Image → GIF",
            description="⚠️ GIFs are limited to 256 colors - some quality loss is expected",
            color=discord.Color.purple()
        )
        embed.set_image(url="attachment://image.gif")

        await ctx.reply(embed=embed, file=file)
    
    @commands.command(name="greyscale")
    async def greyscale(self, ctx):
        if not ctx.message.attachments:
            return await ctx.reply("⚠️ You need to attach an image!")
        img = await self.fetch_image(ctx.message.attachments[0])
        if not img:
            return await ctx.reply("🚫 Failed to download the image.")
        grey = ImageOps.grayscale(img)
        await self.send_image(ctx, grey, "⚪ Greyscale Image", "greyscale.png")

    @commands.command(name="deepfry")
    async def deepfry(self, ctx):
        if not ctx.message.attachments:
            return await ctx.reply("⚠️ You need to attach an image!") # schlong
        img = await self.fetch_image(ctx.message.attachments[0])
        if not img:
            return await ctx.reply("🚫 Failed to download the image.")
        img = img.convert("RGB")
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(3.0)
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150))
        await self.send_image(ctx, img, "💥 Deepfried Image", "deepfry.png")

    @commands.command(name="blur")
    async def blur(self, ctx, amount: int = 5):
        if not ctx.message.attachments:
            return await ctx.reply("⚠️ You need to attach an image!")
        img = await self.fetch_image(ctx.message.attachments[0])
        if not img:
            return await ctx.reply("🚫 Failed to download the image.")
        img = img.filter(ImageFilter.GaussianBlur(radius=amount))
        await self.send_image(ctx, img, f"💨 Blurred Image (Amount: {amount})", "blur.png")

    @commands.command(name="bloom")
    async def bloom(self, ctx, amount: float = 1.5):
        if not ctx.message.attachments:
            return await ctx.reply("⚠️ You need to attach an image!")
        img = await self.fetch_image(ctx.message.attachments[0])
        if not img:
            return await ctx.reply("🚫 Failed to download the image.")
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(amount)
        img = img.filter(ImageFilter.GaussianBlur(radius=5))
        await self.send_image(ctx, img, f"✨ Bloom Image (Amount: {amount})", "bloom.png")

    @commands.command(name="pixelate")
    async def pixelate(self, ctx, amount: int = 10):
        if not ctx.message.attachments:
            return await ctx.reply("⚠️ You need to attach an image!")
        img = await self.fetch_image(ctx.message.attachments[0])
        if not img:
            return await ctx.reply("🚫 Failed to download the image.")
        img = img.resize((img.width//amount, img.height//amount), resample=Image.NEAREST)
        img = img.resize((img.width*amount, img.height*amount), Image.NEAREST)
        await self.send_image(ctx, img, f"🟫 Pixelated Image (Amount: {amount})", "pixelate.png")

async def setup(bot):
    await bot.add_cog(Manipulation(bot))