import json
import os
import io

import discord
from discord.ext import commands
import chat_exporter


from databases.tickets.userInfo import Ticket


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.config = json.load(open(os.getcwd() + '/config/config.json'))
        self.bot = bot

    def cog_check(self, ctx):
        self.config = json.load(open(os.getcwd() + '/config/config.json'))
        return True

    @commands.command(name='add', aliases=[], help='Adds a user to the ticket', usage='add <user>')
    async def cmd_add(self, ctx, adding: discord.User):
        await ctx.message.delete()
        ticket = Ticket(self.bot, ctx).find_ticket(ticket_id=ctx.channel.id)
        if ticket:
            extras = eval(ticket.extras)
            if adding.id not in extras:
                extras.append(adding.id)
            extras = str(extras)

            ticket.update_value(ticket.id, "extras", extras)

            roles = [discord.utils.get(ctx.guild.roles, name=self.config['Server']['Roles'][role]['Role Name']) for role in self.config['Server']['Roles']]
            users = [discord.utils.get(ctx.guild.members, id=user_id) for user_id in [ticket.creator_id] + eval(extras)]
            overwrites = {role: discord.PermissionOverwrite(read_messages=self.config['Server']['Roles'][conf_role]['Can View Tickets']) for role, conf_role in zip(roles, self.config['Server']['Roles'])}
            extras = {user: discord.PermissionOverwrite(read_messages=True) for user in users}
            overwrites.update(extras)

            embed = discord.Embed(description=f"Added {adding.mention}", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
            await ctx.channel.edit(overwrites=overwrites)
            await ctx.send(embed=embed)
            temp = await ctx.send(adding.mention)
            await temp.delete()

    @commands.command(name='remove', aliases=[], help='Removes a user from the ticket', usage='remove <user>')
    async def cmd_remove(self, ctx, removing: discord.User):
        await ctx.message.delete()
        ticket = Ticket(self.bot, ctx).find_ticket(ticket_id=ctx.channel.id)
        if ticket:
            extras = eval(ticket.extras)
            if removing.id in extras:
                extras.remove(removing.id)
            extras = str(extras)

            ticket.update_value(ticket.id, "extras", extras)

            roles = [discord.utils.get(ctx.guild.roles, name=self.config['Server']['Roles'][role]['Role Name']) for role in self.config['Server']['Roles']]
            users = [discord.utils.get(ctx.guild.members, id=user_id) for user_id in [ticket.creator_id] + eval(extras)]
            overwrites = {role: discord.PermissionOverwrite(read_messages=self.config['Server']['Roles'][conf_role]['Can View Tickets']) for role, conf_role in zip(roles, self.config['Server']['Roles'])}
            extras = {user: discord.PermissionOverwrite(read_messages=True) for user in users}
            overwrites.update(extras)

            embed = discord.Embed(description=f"Removed {removing.mention}", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
            await ctx.channel.edit(overwrites=overwrites)
            await ctx.send(embed=embed)
            temp = await ctx.send(removing.mention)
            await temp.delete()


def setup(bot):
    bot.add_cog(Tickets(bot))
