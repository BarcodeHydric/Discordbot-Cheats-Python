import json
import os
import itertools

import discord
from discord.ext import commands

from databases.invites.userInfo import Invite


class Invites(commands.Cog):
    def __init__(self, bot):
        self.config = json.load(open(os.getcwd() + '/config/config.json'))
        self.bot = bot

    def cog_check(self, ctx):
        self.config = json.load(open(os.getcwd() + '/config/config.json'))
        return True

    @commands.command(name="invites", aliases=[], help="", usage="")
    async def cmd_invites(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author

        invites = Invite(self.bot, user)

        leaderboard = {}
        for i in await ctx.guild.invites():
            if i.inviter not in leaderboard:
                leaderboard[i.inviter] = 0
            leaderboard[i.inviter] += 1

        if user not in leaderboard:
            leaderboard[user] = 0

        if ctx.author not in leaderboard:
            leaderboard[ctx.author] = 0

        leaderboard = dict(sorted(leaderboard.items(), key=lambda item: item[1], reverse=True))
        top = 10 if len(leaderboard) > 10 else len(leaderboard)
        top_list = [f"{invite.mention} - {leaderboard[invite]:,}" for invite in dict(itertools.islice(leaderboard.items(), top))]

        embed = discord.Embed(title="Leaderboard", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        embed.add_field(name=f"Top {top}", value='\n'.join(top_list), inline=False)
        embed.add_field(name=f"Your Invites" if ctx.author == user else f"{user.display_name}'s Invites", value=f"{leaderboard[user]:,}", inline=True)
        embed.add_field(name=f"Claimed Invites", value=f"{invites.claimed_invites:,}", inline=True)
        embed.add_field(name=f"Unclaimed Invites", value=f"{leaderboard[user] - invites.claimed_invites:,}", inline=True)
        embed.set_footer(text=f"You are currently #{list(leaderboard.keys()).index(user)+1:,} on the leaderboard" if ctx.author == user else f"{user.display_name} is currently #{list(leaderboard.keys()).index(user)+1:,} on the leaderboard")
        await ctx.send(embed=embed)

    @commands.command(name="claim", aliases=[], help="", usage="")
    @commands.has_permissions(manage_guild=True)
    async def cmd_claim(self, ctx, user: discord.User, claimed: int):
        invites = Invite(self.bot, user)
        invites.update_value("claimed_invites", invites.claimed_invites + claimed)
        await ctx.send(f"{user.mention} has claimed {claimed:,} invites")


def setup(bot):
    bot.add_cog(Invites(bot))
