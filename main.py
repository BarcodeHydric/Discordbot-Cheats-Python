import asyncio
import io
import json
import os
import traceback

import chat_exporter
import discord
from discord.ext import commands
from discord_components import ComponentsBot, Button

from databases.api import API
from databases.tickets.userInfo import Ticket

initial_extensions = [
        "cogs.giveaway.commands",
        "cogs.moderation.commands",
        "cogs.owner.commands",
        "cogs.sales.commands",
        "cogs.tickets.commands",
        "cogs.invites.commands",

        "cogs.general",
        "cogs.error"
    ]


class AC(ComponentsBot):
    config = json.load(open(os.getcwd() + '/config/config.json'))
    prefix = config['Bot']['Prefix']

    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or(self.get_prefix), case_insensitive=True, intents=discord.Intents.all())

        self.load_commands()

    def load_commands(self):
        for extension in initial_extensions:
            try:
                self.load_extension(extension)
            except Exception:
                print(f"Failed to load extension {extension}.")
                traceback.print_exc()
        self.load_extension("jishaku")

    async def get_prefix(self, message):
        return commands.when_mentioned_or(self.prefix)(self, message)

    async def on_message(self, message):
        if message.author.id == self.user.id:
            return

        if message.guild:
            banned_words = ["cheat", "cheating", "hack", "hacking", "spoof", "spoofer", "spoofing", "dox", "ddos"]
            if discord.utils.get(message.guild.roles, name="Team") not in message.author.roles:
                if any(word in message.content.lower() for word in banned_words):
                    try:
                        await message.author.send("Your message contains a blacklisted word, review it and resend it when you have removed any blacklisted words")
                        await message.author.send(f"```{message.content}```")
                    except discord.errors.Forbidden:
                        pass
                    await message.delete()
                    return

        await self.process_commands(message)

    async def on_button_click(self, interaction):
        if interaction.responded:
            return

        if interaction.custom_id == "tos-button":
            await interaction.respond(type=6)

        elif interaction.custom_id == "verification-pass":
            await interaction.respond(type=6)

        elif interaction.custom_id in ["general-support", "payment-support", "product-support"]:
            ticket = Ticket(self, interaction).find_ticket(ticket_creator_id=interaction.author.id, ticket_type=interaction.custom_id)

            if not ticket:
                return await self.create_ticket(interaction)

            return await interaction.send(f"You already have an active {interaction.custom_id.replace('-', ' ')} ticket - {discord.utils.get(interaction.guild.text_channels, id=ticket.id).mention}", delete_after=10)

        elif interaction.custom_id == "close-ticket":
            await self.close_ticket(interaction)
            await interaction.respond(type=6)

        elif interaction.custom_id == "open-ticket":
            await self.reopen_ticket(interaction)
            await interaction.respond(type=6)

        elif interaction.custom_id == "delete-ticket":
            await self.delete_ticket(interaction)
            await interaction.respond(type=6)

    async def create_ticket(self, interaction):
        ticket = Ticket(self, interaction)

        roles = [discord.utils.get(interaction.guild.roles, name=self.config['Server']['Roles'][role]['Role Name']) for role in self.config['Server']['Roles']]
        users = [discord.utils.get(interaction.guild.members, id=user_id) for user_id in [interaction.author.id]]
        overwrites = {role: discord.PermissionOverwrite(read_messages=self.config['Server']['Roles'][conf_role]['Can View Tickets']) for role, conf_role in zip(roles, self.config['Server']['Roles'])}
        extras = {user: discord.PermissionOverwrite(read_messages=True) for user in users}
        overwrites.update(extras)

        category_channel = discord.utils.get(interaction.guild.categories, name=self.config['Ticket']['Types'][interaction.custom_id]['Category'])
        ticket_channel = await category_channel.create_text_channel(name=f"ticket-{interaction.author.name}", overwrites=overwrites)
        ticket.create_ticket(ticket_creator_id=interaction.author.id, ticket_id=ticket_channel.id, ticket_type=interaction.custom_id)

        embed = discord.Embed(title="AC Support", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        embed.add_field(name="Support will be here soon", value=self.config['Ticket']['Types'][interaction.custom_id]['Embed Message'])
        embed.set_footer(text=f"AC Tickets - {interaction.custom_id.replace('-', ' ').title()}", icon_url="attachment://logo_trans.png")
        file = discord.File("images/logo_trans.png")

        temp = await ticket_channel.send(" ".join([item.mention for item in roles + users]))
        await temp.delete()
        await ticket_channel.send(embed=embed, file=file, components=[[Button(label="Close Ticket", custom_id="close-ticket", style=3, emoji="🚫")]])

        await interaction.send(f"Ticket Created - {ticket_channel.mention}")

    async def close_ticket(self, interaction):
        ticket = Ticket(self, interaction).find_ticket(ticket_id=interaction.channel.id)
        category_channel = discord.utils.get(interaction.guild.categories, name=self.config['Ticket']['Types']['close-ticket']['Category'])

        roles = [discord.utils.get(interaction.guild.roles, name=self.config['Server']['Roles'][role]['Role Name']) for role in self.config['Server']['Roles']]
        overwrites = {role: discord.PermissionOverwrite(read_messages=self.config['Server']['Roles'][conf_role]['Can View Tickets']) for role, conf_role in zip(roles, self.config['Server']['Roles'])}

        embed = discord.Embed(description=f"Ticket Closed by {interaction.author.mention}", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))

        await interaction.channel.edit(category=category_channel, overwrites=overwrites)
        ticket.update_value(ticket.id, "type", f"closed_{ticket.type}")
        await interaction.message.edit(components=[[Button(label="Close Ticket", custom_id="close-ticket", style=3, emoji="🚫", disabled=True)]])
        await interaction.channel.send(embed=embed, components=[[
            Button(label="Open Ticket", custom_id="open-ticket", style=3, emoji="✅"),
            Button(label="Delete Ticket", custom_id="delete-ticket", style=1, emoji="❌")
        ]])

        transcript = await chat_exporter.raw_export(interaction.channel, messages=await interaction.channel.history().flatten())
        transcript_file = discord.File(io.BytesIO(transcript.encode()), filename=f"transcript-{interaction.channel.name}.html")
        transcript_channel = discord.utils.get(interaction.guild.text_channels, name="transcripts")
        transcript_message = await transcript_channel.send(file=transcript_file)

        embed = discord.Embed(title="Ticket Closed", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        embed.add_field(name="Ticket Type", value=interaction.custom_id.replace("-", " ").title())
        embed.add_field(name="Opened By", value=discord.utils.get(interaction.guild.members, id=ticket.creator_id).mention)
        embed.add_field(name="Closed By", value=discord.utils.get(interaction.guild.members, id=interaction.author.id).mention)
        embed.add_field(name="Transcript", value=f"[Here]({transcript_message.attachments[0].url})")
        try:
            await discord.utils.get(interaction.guild.members, id=ticket.creator_id).send(embed=embed)
        except:
            pass

    async def reopen_ticket(self, interaction):
        ticket = Ticket(self, interaction).find_ticket(ticket_id=interaction.channel.id)

        roles = [discord.utils.get(interaction.guild.roles, name=self.config['Server']['Roles'][role]['Role Name']) for role in self.config['Server']['Roles']]
        users = [discord.utils.get(interaction.guild.members, id=user_id) for user_id in [ticket.creator_id] + eval(ticket.extras)]
        overwrites = {role: discord.PermissionOverwrite(read_messages=self.config['Server']['Roles'][conf_role]['Can View Tickets']) for role, conf_role in zip(roles, self.config['Server']['Roles'])}
        extras = {user: discord.PermissionOverwrite(read_messages=True) for user in users}
        overwrites.update(extras)

        category_channel = discord.utils.get(interaction.guild.categories, name=self.config['Ticket']['Types'][ticket.type.replace('closed_', '')]['Category'])
        await interaction.channel.edit(overwrites=overwrites, category=category_channel)

        embed = discord.Embed(description=f"Ticket Opened by {interaction.author.mention}", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        await interaction.channel.send(embed=embed, components=[[Button(label="Close Ticket", custom_id="close-ticket", style=3, emoji="🚫")]])

        await interaction.message.edit(components=[[
            Button(label="Open Ticket", custom_id="open-ticket", style=3, emoji="✅", disabled=True),
            Button(label="Delete Ticket", custom_id="delete-ticket", style=1, emoji="❌", disabled=True)
        ]])
        ticket.update_value(ticket.id, "type", f"{ticket.type.replace('closed_', '')}")

    async def delete_ticket(self, interaction):
        ticket = Ticket(self, interaction).find_ticket(ticket_id=interaction.channel.id)
        ticket.delete_ticket()
        await interaction.channel.delete()

    async def on_ready(self):
        print("------------------------------------")
        print("Bot Name: " + self.user.name)
        print("Bot ID: " + str(self.user.id))
        print("Discord Version: " + discord.__version__)
        print("------------------------------------")

    def run(self):
        super().run(self.config['Bot']['Token'], reconnect=True)


if __name__ == "__main__":
    ac = AC()
    ac.run()
