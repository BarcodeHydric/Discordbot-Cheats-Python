import asyncio
import json
import os

import discord
from discord.ext import commands


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.config = json.load(open(os.getcwd() + '/config/config.json'))
        self.bot = bot

    def cog_check(self, ctx):
        self.config = json.load(open(os.getcwd() + '/config/config.json'))
        return True

    @commands.command(name="kick", aliases=[], help="Kicks a user from the server", usage="kick <user1> [user2] [user3] ... [reason]")
    @commands.has_permissions(manage_guild=True)
    async def cmd_kick(self, ctx, users: commands.Greedy[discord.Member], *, reason="No Reason Provided"):
        kicked_users = []
        failed_users = []
        for user in users:
            try:
                await ctx.guild.kick(user, reason=reason)
                kicked_users.append(user.name)
            except discord.errors.Forbidden:
                failed_users.append(user.name)
        embed = discord.Embed(title="Kicked Users", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        if kicked_users:
            embed.add_field(name="Successful Kicks", value='\n'.join(kicked_users))
        if failed_users:
            embed.add_field(name="Failed Kicks", value='\n'.join(failed_users))
        embed.set_footer(text=f'Reason: {reason}')
        await ctx.send(embed=embed)

    @commands.command(name="ban", aliases=[], help="Ban a user from the server", usage="ban <user1> [user2] [user3] ... [reason]")
    @commands.has_permissions(manage_guild=True)
    async def cmd_ban(self, ctx, users: commands.Greedy[discord.Member], *, reason="No Reason Provided"):
        banned_users = []
        failed_users = []
        for user in users:
            try:
                await ctx.guild.ban(user, reason=reason)
                banned_users.append(user.name)
            except discord.errors.Forbidden:
                failed_users.append(user.name)
        embed = discord.Embed(title="Banned Users", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        if banned_users:
            embed.add_field(name="Successful Bans", value='\n'.join(banned_users))
        if failed_users:
            embed.add_field(name="Failed Bans", value='\n'.join(failed_users))
        embed.set_footer(text=f'Reason: {reason}')
        await ctx.send(embed=embed)

    @commands.command(name="unban", aliases=[], help="Unban a user from the server", usage="unban <user> [reason]")
    @commands.has_permissions(manage_guild=True)
    async def cmd_unban(self, ctx, user, *, reason="No Reason Provided"):
        embed = discord.Embed(title="Un-Banned Users", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        bans = await ctx.guild.bans()
        try:
            for user_reason in bans:
                original_reason, banned_user = user_reason
                if banned_user.id == int(user):
                    await ctx.guild.unban(banned_user, reason=reason)
                    embed.add_field(name="Successful Un-Bans", value=banned_user.name)
        except discord.errors.Forbidden:
            embed.add_field(name="Failed Un-Bans", value=user)
        embed.set_footer(text=f'Reason: {reason}')
        await ctx.send(embed=embed)

    @commands.command(name="mute", aliases=[], help="Mute a user from speaking in the server", usage="mute <user1> [user2] [user3] ... [reason]")
    @commands.has_permissions(manage_guild=True)
    async def cmd_mute(self, ctx, users: commands.Greedy[discord.Member], *, reason="No Reason Provided"):
        muted_users = []
        failed_users = []
        for user in users:
            try:
                perms = {user: discord.PermissionOverwrite(send_messages=False, read_messages=True)}
                for channel in ctx.guild.channels:
                    await channel.edit(overwrites=perms)
                muted_users.append(user.name)
            except discord.errors.Forbidden:
                failed_users.append(user.name)

        embed = discord.Embed(title="Muted Users", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        if muted_users:
            embed.add_field(name="Successful Mutes", value='\n'.join(muted_users))
        if failed_users:
            embed.add_field(name="Failed Mutes", value='\n'.join(failed_users))
        embed.set_footer(text=f'Reason: {reason}')
        await ctx.send(embed=embed)

    @commands.command(name="unmute", aliases=[], help="Unmute a user from speaking in the server", usage="unmute <user1> [user2] [user3] ... [reason]")
    @commands.has_permissions(manage_guild=True)
    async def cmd_unmute(self, ctx, users: commands.Greedy[discord.Member], *, reason="No Reason Provided"):
        unmuted_users = []
        failed_users = []
        for user in users:
            try:
                perms = {user: discord.PermissionOverwrite(send_messages=True, read_messages=True)}
                for channel in ctx.guild.channels:
                    await channel.edit(overwrites=perms)
                unmuted_users.append(user.name)
            except discord.errors.Forbidden:
                failed_users.append(user.name)

        embed = discord.Embed(title="UnMuted Users", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        if unmuted_users:
            embed.add_field(name="Successful UnMutes", value='\n'.join(unmuted_users))
        if failed_users:
            embed.add_field(name="Failed UnMutes", value='\n'.join(failed_users))
        embed.set_footer(text=f'Reason: {reason}')
        await ctx.send(embed=embed)

    @commands.command(name="tempmute", aliases=[], help="Mutes a user and auto-unmutes them at a later time", usage="tempmute <user1> [user2] [user3] ... [reason]")
    @commands.has_permissions(manage_guild=True)
    async def cmd_tempmute(self, ctx, users: commands.Greedy[discord.Member], time, *, reason="No Reason Provided"):
        time = int(time)

        tempmuted_users = []
        failed_users = []
        for user in users:
            try:
                perms = {user: discord.PermissionOverwrite(send_messages=True, read_messages=True)}
                for channel in ctx.guild.channels:
                    await channel.edit(overwrites=perms)
                tempmuted_users.append(user.name)
            except discord.errors.Forbidden:
                failed_users.append(user.name)

        embed = discord.Embed(title="TempMuted Users", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        if tempmuted_users:
            embed.add_field(name="Successful TempMutes", value='\n'.join(tempmuted_users))
        if failed_users:
            embed.add_field(name="Failed TempMutes", value='\n'.join(failed_users))
        embed.set_footer(text=f'Reason: {reason}\nTime: {time} minute(s)')
        await ctx.send(embed=embed)

        await asyncio.sleep(time * 60)

        unmuted_users = []
        failed_users = []
        for user in users:
            try:
                perms = {user: discord.PermissionOverwrite(send_messages=True, read_messages=True)}
                for channel in ctx.guild.channels:
                    await channel.edit(overwrites=perms)
                unmuted_users.append(user.name)
            except discord.errors.Forbidden:
                failed_users.append(user.name)

        embed = discord.Embed(title="UnMuted Users", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        if unmuted_users:
            embed.add_field(name="Successful UnMutes", value='\n'.join(unmuted_users))
        if failed_users:
            embed.add_field(name="Failed UnMutes", value='\n'.join(failed_users))
        embed.set_footer(text=f'Reason: Auto-Unmute')
        await ctx.send(embed=embed)

    @commands.command(name='lock', aliases=[], help='Locks the specified channel', usage='lock [channel]')
    @commands.has_permissions(manage_guild=True)
    async def cmd_lock(self, ctx, channel: discord.TextChannel = None):
        if channel is None:
            channel = ctx.channel

        perms = {}
        for user in ctx.guild.members:
            perms[user] = discord.PermissionOverwrite(send_messages=False, read_messages=True)
        await channel.edit(overwrites=perms)

        embed = discord.Embed(title="Channel Locked", color=discord.Color.red())
        embed.add_field(name="This channel has been locked", value="You have not been muted, this lock will last for an indefinite amount of time")
        embed.set_footer(text="Messaging any staff or support members regarding this may result in a kick or ban")

        await channel.send(embed=embed)
        await ctx.message.delete()
        await ctx.send(f"{channel.mention} has been locked", delete_after=10)

    @commands.command(name='unlock', aliases=[], help='Unlocks the specified channel', usage='unlock [channel]')
    @commands.has_permissions(manage_guild=True)
    async def cmd_unlock(self, ctx, channel: discord.TextChannel = None):
        if channel is None:
            channel = ctx.channel

        perms = {}
        for user in ctx.guild.members:
            perms[user] = discord.PermissionOverwrite(send_messages=None, read_messages=None)
        await channel.edit(overwrites=perms)

        embed = discord.Embed(title="Channel Unlocked", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        embed.add_field(name="This channel has been unlocked", value="Thank you for your patience!")

        await channel.send(embed=embed)
        await ctx.message.delete()
        await ctx.send(f"{channel.mention} has been unlocked", delete_after=10)


def setup(bot):
    bot.add_cog(Moderation(bot))
