import json
import os

import discord
from discord.ext import commands


class General(commands.Cog):
    def __init__(self, bot):
        self.config = json.load(open(os.getcwd() + '/config/config.json'))
        self.bot = bot

    def cog_check(self, ctx):
        self.config = json.load(open(os.getcwd() + '/config/config.json'))
        return True

    @commands.command(name='say', aliases=[], help='Sends a message as the bot', usage='say <message>')
    @commands.has_permissions(manage_guild=True)
    async def cmd_say(self, ctx, *, message):
        await ctx.send(message)
        await ctx.message.delete()

    @commands.command(name='embed', aliases=[], help='Sends an embed message as the bot', usage='embed')
    @commands.has_permissions(manage_guild=True)
    async def cmd_embed(self, ctx):
        ask_url = None
        url = None
        ask_field_value = None
        field_value = None

        ask_title = await ctx.send("What will the embeds title be? (Say 'skip' to skip)")
        title = await self.bot.wait_for('message', check=lambda check: check.author.id == ctx.author.id)

        if title.content.lower() != 'skip':
            ask_url = await ctx.send("What will the URL for the title be? (Say 'skip' to skip)")
            url = await self.bot.wait_for('message', check=lambda check: check.author.id == ctx.author.id)

        ask_field_name = await ctx.send("What will the embeds field name be? (Say 'skip' to skip)")
        field_name = await self.bot.wait_for('message', check=lambda check: check.author.id == ctx.author.id)

        if field_name.content.lower() != 'skip':
            ask_field_value = await ctx.send("What will the embeds field value be? (Say 'skip' to skip)")
            field_value = await self.bot.wait_for('message', check=lambda check: check.author.id == ctx.author.id)

        ask_footer = await ctx.send("What will the footer be? (Say 'skip' to skip)")
        footer = await self.bot.wait_for('message', check=lambda check: check.author.id == ctx.author.id)

        embed = discord.Embed(color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))

        if title.content.lower() != 'skip':
            embed.title = title.content
            if url.content.lower() != 'skip':
                embed.url = url.content

        if field_name.content.lower() != 'skip':
            embed.add_field(name=field_name.content, value=field_value.content)

        if footer.content.lower() != 'skip':
            embed.set_footer(text=footer.content)

        await ctx.send(embed=embed)
        await ctx.message.delete()

        await ask_footer.delete()
        await footer.delete()
        try:
            await ask_url.delete()
            await url.delete()
        except AttributeError:
            pass
        await ask_field_name.delete()
        await field_name.delete()
        try:
            await ask_field_value.delete()
            await field_value.delete()
        except AttributeError:
            pass
        await ask_title.delete()
        await title.delete()


def setup(bot):
    bot.add_cog(General(bot))
