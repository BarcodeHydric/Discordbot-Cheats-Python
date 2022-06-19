import asyncio
import datetime
import json
import os
import random

import discord
from discord.ext import commands


class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.config = json.load(open(os.getcwd() + '/config/config.json'))
        self.bot = bot

    def cog_check(self, ctx):
        self.config = json.load(open(os.getcwd() + '/config/config.json'))
        return True

    @commands.command(name='giveaway', aliases=['g'], help='Start a giveaway', usage='giveaway')
    @commands.has_permissions(manage_guild=True)
    async def cmd_giveaway(self, ctx):

        ask_length = await ctx.send("How long will the giveaway last (Example: `1d 2h 3m`)")
        length = await self.bot.wait_for('message', check=lambda check: check.author.id == ctx.author.id)

        ask_winner = await ctx.send("How many winners will there be?")
        winner = await self.bot.wait_for('message', check=lambda check: check.author.id == ctx.author.id)

        ask_item = await ctx.send("And what are you giving away?")
        item = await self.bot.wait_for('message', check=lambda check: check.author.id == ctx.author.id)

        date, time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M").split(" ")
        day, month, year = date.split("/")
        hour, minute = time.split(":")
        month, day, year, hour, minute = int(month), int(day), int(year), int(hour), int(minute)

        for value in length.content.split(" "):
            if 'd' in value:
                day += int(value.replace('d', ''))
            elif 'h' in value:
                hour += int(value.replace('h', ''))
            elif 'm' in value:
                minute += int(value.replace('m', ''))

        end = int(datetime.datetime(year, month, day, hour, minute).timestamp())

        embed = discord.Embed(color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        embed.add_field(name=f"Giveaway End: <t:{end}:R>", value=f"{winner.content}x {item.content}", inline=False)
        embed.set_footer(text=f"Giveaway Hosted By {ctx.author.name}", icon_url="attachment://logo_trans.png")

        await ask_length.delete()
        await ask_item.delete()
        await ask_winner.delete()
        await length.delete()
        await item.delete()
        await winner.delete()
        await ctx.message.delete()

        giveaway_channel = discord.utils.get(ctx.guild.text_channels, name=self.bot.config['Giveaway']['Channel'])

        await ctx.send(f"Giveaway started in {giveaway_channel}", delete_after=10)
        giveaway_message = await giveaway_channel.send(embed=embed, content=ctx.guild.roles[0])

        await giveaway_message.add_reaction(self.bot.config['Giveaway']['Reaction'])

        while True:
            if datetime.datetime.now().timestamp() >= end:
                giveaway_end = await giveaway_message.channel.fetch_message(giveaway_message.id)

                all_users = await giveaway_end.reactions[0].users().flatten()
                winners = []

                all_users.remove(self.bot.user)

                for _ in range(int(winner.content)):
                    if all_users:
                        won = random.choice(all_users)
                        all_users.remove(won)
                        winners.append(won)

                embed.title = "Giveaway Ended"
                embed.add_field(name=f"Winner{'s' if int(winner.content) > 1 else ''}", value=", ".join([user.mention for user in winners]), inline=False)
                file = discord.File("images/logo_trans.png")
                await giveaway_message.edit(embed=embed, file=file)

                tmp = await giveaway_channel.send(" ".join([user.mention for user in winners]))
                await tmp.delete()

                return
            await asyncio.sleep(10)

    @commands.command(name="reroll", aliases=[], help='Rerolls a specified giveaway', usage='reroll <giveaway id>')
    @commands.has_permissions(manage_guild=True)
    async def cmd_reroll(self, ctx, giveaway_message: discord.Message):
        winner = int(giveaway_message.embeds[0].fields[0].value.split("x")[0])
        all_users = await giveaway_message.reactions[0].users().flatten()
        winners = []

        all_users.remove(self.bot.user)

        for _ in range(int(winner)):
            if all_users:
                won = random.choice(all_users)
                all_users.remove(won)
                winners.append(won)

        embed = discord.Embed(title="Giveaway Ended - ReRolled", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        embed.add_field(name=giveaway_message.embeds[0].fields[0].name, value=giveaway_message.embeds[0].fields[0].value)
        embed.add_field(name=f"Winner{'s' if int(winner) >= 1 else ''}", value=", ".join([user.mention for user in winners]), inline=False)
        await giveaway_message.edit(embed=embed)

        tmp = await giveaway_message.channel.send(" ".join([user.mention for user in winners]))
        await tmp.delete()
        await ctx.message.delete()

        return


def setup(bot):
    bot.add_cog(Giveaway(bot))
