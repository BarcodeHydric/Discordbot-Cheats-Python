import json
import os
import time

import discord
from discord.ext import commands
from discord_components import Button, Select, SelectOption

from databases.api import Seller, API


class Owner(commands.Cog):
    def __init__(self, bot):
        self.config = json.load(open(os.getcwd() + '/config/config.json'))
        self.bot = bot

    def cog_check(self, ctx):
        self.config = json.load(open(os.getcwd() + '/config/config.json'))
        return True

    @commands.Cog.listener()
    async def on_button_click(self, interaction):
        api = API()
        resellers = api.get_sellers()
        api.close()

        if interaction.custom_id in [str(reseller.id) for reseller in resellers]:
            reseller = Seller(int(interaction.custom_id))
            embed = discord.Embed(title=f"Viewing {reseller.username}", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
            embed.add_field(name="Active Keys", value=f"{len(reseller.get_keys()):,}")
            embed.add_field(name="Amount Owed", value=f"${reseller.owed:,}")
            await interaction.message.edit(embed=embed, components=[
                Button(label="Back", custom_id="reseller-view"),
                Select(placeholder="Unrestricted",
                       options=[SelectOption(label="Unrestricted: True", value=f"{reseller.id}-unrestricted-1", default=reseller.unrestricted == 1), SelectOption(label="Unrestricted: False", value=f"{reseller.id}-unrestricted-0", default=reseller.unrestricted == 0)]),
                Select(placeholder="KeyGen Access",
                       options=[SelectOption(label="KeyGen Access: True", value=f"{reseller.id}-genkeys-1", default=reseller.genkeys == 1), SelectOption(label="KeyGen Access: False", value=f"{reseller.id}-genkeys-0", default=reseller.genkeys == 0)]),
            ])

        if interaction.custom_id == "reseller-view":
            api = API()
            resellers = api.get_sellers()
            api.close()

            components = []
            ar = []
            for enum, reseller in enumerate(resellers):
                if enum % 5 == 0 and enum != 0:
                    components.append(ar)
                    ar = []
                ar.append(Button(label=reseller.username, custom_id=reseller.id))
            if ar:
                components.append(ar)

            embed = discord.Embed(title="Resellers", description="Select the reseller you want to view", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
            await interaction.message.edit(embed=embed, components=components)

    @commands.Cog.listener()
    async def on_select_option(self, interaction):
        if "unrestricted" in interaction.values[0] or "genkeys" in interaction.values[0]:
            reseller_id, access, value = interaction.values[0].split("-")
            reseller = Seller(int(reseller_id))
            reseller.update(access, int(value))

    @commands.command(name="resellers")
    @commands.has_any_role("Team")
    async def cmd_resellers(self, ctx):
        api = API()
        resellers = api.get_sellers()
        api.close()

        components = []
        ar = []
        for enum, reseller in enumerate(resellers):
            if enum % 5 == 0 and enum != 0:
                components.append(ar)
                ar = []
            ar.append(Button(label=reseller.username, custom_id=reseller.id))
        if ar:
            components.append(ar)

        embed = discord.Embed(title="Resellers", description="Select the reseller you want to view", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        await ctx.send(embed=embed, components=components)

    @commands.command(name="paid", aliases=[], usage="", help="")
    @commands.has_any_role("Team")
    async def cmd_paid(self, ctx, reseller: discord.Member, amount: int):
        seller = Seller(reseller.id)
        seller.update("owed", seller.raw_owed - amount)
        await ctx.send(f"Updated {reseller.mention} owed balance to ${seller.owed:,}")

    @commands.command(name="reseller", aliases=[], help="", usage="")
    @commands.has_any_role("Team")
    async def cmd_reseller(self, ctx, user: discord.Member):
        reseller = Seller(user.id)
        embed = discord.Embed(title=f"Reseller {reseller}", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        embed.add_field(name="Active Keys", value=f"{len(reseller.get_keys()):,}")
        embed.add_field(name="Amount Owed", value=f"${reseller.owed:,}")
        await ctx.send(embed=embed)

    @commands.command(name="register", aliases=[], help="", uage="")
    @commands.has_any_role("Team")
    async def cmd_register(self, ctx, reseller: discord.Member):
        api = API()
        api.register_seller(reseller)

        embed = discord.Embed(title="Reseller Registered!", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        embed.add_field(name=f"{reseller} has been registered as a reseller", value="They can now generate and modify keys for all products")

        await ctx.send(embed=embed)

    @commands.command(name="serversetup", aliases=[], help='Sets up a server/backup server based on the config', usage='serversetup')
    @commands.is_owner()
    async def cmd_serversetup(self, ctx):
        for channel in ctx.guild.text_channels:
            try:
                await channel.delete()
            except discord.errors.HTTPException:
                pass
        for channel in ctx.guild.voice_channels:
            await channel.delete()
        for category in ctx.guild.categories:
            await category.delete()
        for role in ctx.guild.roles:
            try:
                await role.delete()
            except discord.errors.HTTPException:
                pass

        for role in list(self.config['Server']['Roles'])[::-1]:
            perms = discord.Permissions(**self.config['Server']['Roles'][role]["Permissions"])
            if self.config['Server']['Roles'][role]["Role Name"] == "@everyone":
                default_role = discord.utils.get(ctx.guild.roles, name="@everyone")
                await default_role.edit(permissions=perms)
                continue
            await ctx.guild.create_role(name=self.config['Server']['Roles'][role]["Role Name"], permissions=perms, color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")), hoist=self.config['Server']['Roles'][role]["Display role separately from online members"], mentionable=self.config['Server']['Roles'][role]["Allow anyone to @mention this role"])

        for category in self.config['Server']['Categories']:
            cat_perms = {}
            for cat_role_perm in self.config['Server']['Categories'][category]['Permissions']:
                role = discord.utils.get(ctx.guild.roles, name=cat_role_perm)
                cat_perms[role] = discord.PermissionOverwrite(
                    **self.config['Server']['Categories'][category]["Permissions"][cat_role_perm])
            cat_channel = await ctx.guild.create_category(name=category, overwrites=cat_perms)

            for channel in self.config['Server']['Categories'][category]['Channels']:
                permissions = {}
                for role_perm in self.config['Server']['Categories'][category]['Channels'][channel]["Permissions"]:
                    role = discord.utils.get(ctx.guild.roles, name=role_perm)
                    permissions[role] = discord.PermissionOverwrite(
                        **self.config['Server']['Categories'][category]['Channels'][channel]["Permissions"][role_perm])
                await cat_channel.create_text_channel(name=channel, overwrites=permissions)

        for channel in self.config['Server']['Misc Channels']:
            permissions = {}
            for role_perm in self.config['Server']['Misc Channels'][channel]["Permissions"]:
                role = discord.utils.get(ctx.guild.roles, name=role_perm)
                permissions[role] = discord.PermissionOverwrite(
                    **self.config['Server']['Misc Channels'][channel]["Permissions"][role_perm])
            await ctx.guild.create_text_channel(name=channel, overwrites=permissions)

        with open(os.getcwd() + self.config['Server']['Icon'], 'rb') as iconfile:
            icon = iconfile.read()
        system_channel = discord.utils.get(ctx.guild.channels,
                                           name=self.config['Server']['System Messages Channel']['Name'])
        await ctx.guild.edit(name=self.config['Server']['Name'], icon=icon, system_channel=system_channel)

        await self.send_status_message(ctx)
        await self.send_ticket_message(ctx)
        await self.send_rules_message(ctx)
        await self.send_tos_message(ctx)
        await self.send_vouch_message(ctx)
        await self.send_media_message(ctx)
        await self.send_verif_message(ctx)
        await self.send_rust_message(ctx)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def send_status_message(self, ctx):
        try:
            await ctx.message.delete()
        except:
            pass

        api = API()
        games = api.get_games()
        api.close()

        status_channel = discord.utils.get(ctx.guild.text_channels, name="status")
        message = None

        if status_channel:
            for msg in await status_channel.history(limit=100).flatten():
                if msg.author.id == self.bot.user.id:
                    message = msg

        status = []
        for game in games:
            status.append(f"{self.config['Status'][game.status]} {discord.utils.get(ctx.guild.text_channels, name=game.channelname).mention}")
        embed = discord.Embed(title="Status", url="https://cheats.ac/status/", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        embed.add_field(name="\n".join([f'{status} {self.config["Status"][status]}' for status in list(self.config['Status'].keys())])+"\n===============", value="\n".join(status))
        embed.set_footer(text=f'We will update the status as often as we can\nLast updated {time.strftime("%m/%d/%Y")}', icon_url="attachment://logo_trans.png")
        file = discord.File("images/logo_trans.png")

        if message is None:
            await status_channel.send(embed=embed, file=file)
        else:
            await message.edit(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def send_ticket_message(self, ctx):
        try:
            await ctx.message.delete()
        except:
            pass
        embed = discord.Embed(title="Create a Ticket", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        embed.add_field(name="General Tickets", value="Have a question? Ask us here!", inline=False)
        embed.add_field(name="Product Issues", value="Having issues with a product? Let us know!", inline=False)
        embed.add_field(name="Alternative Payment Methods",
                        value="Need to use a payment method we don't list? Maybe we can work it out!", inline=False)
        embed.set_footer(text="AC Tickets", icon_url="attachment://logo_trans.png")
        file = discord.File("images/logo_trans.png")

        ticket_channel = discord.utils.get(ctx.guild.channels, name=self.config['Ticket']['Channel'])
        await ticket_channel.send(embed=embed, file=file, components=[
            [
                Button(label="General Support", custom_id="general-support", style=3, emoji="☑️"),
                Button(label="Payment Methods", custom_id="payment-support", style=3, emoji="🪙"),
                Button(label="Product Issues", custom_id="product-support", style=1, emoji="👾")]
        ])

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def send_verif_message(self, ctx):
        try:
            await ctx.message.delete()
        except:
            pass
        rules_channel = discord.utils.get(ctx.guild.channels, name="rules")
        tos_channel = discord.utils.get(ctx.guild.channels, name="terms-of-service")
        verification_channel = discord.utils.get(ctx.guild.channels, name="verify-here")

        embed = discord.Embed(color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        embed.add_field(name="Verification",
                        value=f"By accessing this server you agree to the server {rules_channel.mention} and the {tos_channel.mention}",
                        inline=False)
        embed.set_footer(text="Rules and TOS can change at any time without notice",
                         icon_url="attachment://logo_trans.png")
        file = discord.File("images/logo_trans.png")

        await verification_channel.send(embed=embed, file=file, components=[
            [
                Button(label="I Agree", custom_id="verification-pass", style=5, emoji="☑️",
                       url="https://restorecord.com/verify/Bump/ACmain")
            ]
        ])

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def send_rules_message(self, ctx):
        try:
            await ctx.message.delete()
        except:
            pass
        rules_channel = discord.utils.get(ctx.guild.channels, name="rules")
        embed = discord.Embed(title="Server Rules",
                              color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        embed.add_field(name="1. Be Respectful",
                        value="Treat every user with respect. Bullying, harassment or discrimination to user will get you muted, kicked or banned. This includes any and all forms of racism, sexism, anti-LGBTQ+ or any other type of offensive/hateful speech",
                        inline=False)
        embed.add_field(name="2. No Spamming",
                        value="Dont send random or useless messages and use channels for their intended use",
                        inline=False)
        embed.add_field(name="3. No Advertisements",
                        value="Absolutly no advertisements of any kind. Doing so will get you immediately banned and any services sold to you terminated. This includes DM advertising",
                        inline=False)
        embed.add_field(name="4. No Politics",
                        value="Contrary to popular belief, no, we do not care about who you are voting", inline=False)
        embed.add_field(name="5. Names and Avatars",
                        value="Use an appropriate name and avatar. Change your nickname to be easily mentionable or your permissions to do so will be removed and your nickname will be changed",
                        inline=False)
        embed.add_field(name="6. Mentioning/Pinging Users",
                        value="Do not randomly mention users or roles. Only do so when it is necessary or you will get muted, kicked or banned",
                        inline=False)
        embed.add_field(name="7. SFW content",
                        value="No NSFW/NSFL content of any kind. Doing so will get you muted, kicked or banned without warning",
                        inline=False)
        embed.set_footer(
            text="Rules are subject to common sense. If a rule is not listed here but you know you should not do it...don't do it. You can still get muted/kicked/banned",
            icon_url="attachment://logo_trans.png")
        file = discord.File("images/logo_trans.png")
        await rules_channel.send(embed=embed, file=file)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def send_tos_message(self, ctx):
        try:
            await ctx.message.delete()
        except:
            pass
        tos_channel = discord.utils.get(ctx.guild.channels, name="terms-of-service")
        embed = discord.Embed(color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        embed.add_field(name="Terms of Service Agreement", value=self.config['Server']['TOS'])
        embed.set_footer(
            text="By accessing this server and any product sold by AC Products you agree to these terms of service",
            icon_url="attachment://logo_trans.png")
        file = discord.File("images/logo_trans.png")
        await tos_channel.send(embed=embed, file=file)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def send_vouch_message(self, ctx):
        try:
            await ctx.message.delete()
        except:
            pass
        """"""

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def send_media_message(self, ctx):
        try:
            await ctx.message.delete()
        except:
            pass
        """"""

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def send_spoofer_message(self, ctx):
        try:
            await ctx.message.delete()
        except:
            pass

        day_1 = f'{self.config["Product Price"]["Sell"]["99"]["1"] / 100}0'
        day_3 = f'{self.config["Product Price"]["Sell"]["99"]["3"] / 100}0'
        day_7 = f'{self.config["Product Price"]["Sell"]["99"]["7"] / 100}0'
        day_31 = f'{self.config["Product Price"]["Sell"]["99"]["31"] / 100}0'

        spoofer = discord.utils.get(ctx.guild.text_channels, name="woofer")
        embed = discord.Embed(title="Woofer Public (CLICK ME)", url="https://cheatsac.sellix.io/", description="Features", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        embed.set_image(url="attachment://spoofer.png")
        embed.add_field(name="Works on", value="EAC/BE/Vanguard")
        embed.add_field(name="Pricing", value=f"Day ${day_1}\n3 Day ${day_3}\nWeek ${day_7}\nMonth ${day_31}")
        embed.set_footer(text="Open a ticket for alternative payment methods")
        file = discord.File("images/spoofer.png")
        await spoofer.send(embed=embed, file=file)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def send_rust_message(self, ctx):
        try:
            await ctx.message.delete()
        except:
            pass

        day_1 = f'{self.config["Product Price"]["Sell"]["2"]["1"] / 100}0'
        day_3 = f'{self.config["Product Price"]["Sell"]["2"]["3"] / 100}0'
        day_7 = f'{self.config["Product Price"]["Sell"]["2"]["7"] / 100}0'
        day_31 = f'{self.config["Product Price"]["Sell"]["2"]["31"] / 100}0'

        rust = discord.utils.get(ctx.guild.text_channels, name="rust")
        embed = discord.Embed(title="Rust (CLICK ME)", url="https://cheatsac.sellix.io/", description="Features", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        embed.set_image(url="attachment://rust.png")
        embed.add_field(name="Aim", value="• Aimbot\n• Silent Aim\n• Smooth\n• Fov")
        embed.add_field(name="Player ESP", value="• Box\n• Health\n• Skeleton\n• NPC\n• Sleeper\n• Weapon\n• Distance\n• Animal ESP\n• Stash ESP")
        embed.add_field(name="Location ESP", value="• Radtown (ALL ITEMS)")
        embed.add_field(name="Ore ESP", value="• Sulfur\n• Stone\n• Metal")
        embed.add_field(name="Misc", value="• Spider\n• NoClip\n• Admin Mode\n• Chams\n• Configs\n• Load Config\n• Save Config")
        embed.add_field(name="Pricing", value=f"Day ${day_1}\n3 Day ${day_3}\nWeek ${day_7}\nMonth ${day_31}")
        embed.set_footer(text="Open a ticket for alternative payment methods")
        file = discord.File("images/rust.png")
        await rust.send(embed=embed, file=file)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def send_eft_message(self, ctx):
        try:
            await ctx.message.delete()
        except:
            pass

        day_1 = f'{self.config["Product Price"]["Sell"]["13"]["1"] / 100}0'
        day_3 = f'{self.config["Product Price"]["Sell"]["13"]["3"] / 100}0'
        day_7 = f'{self.config["Product Price"]["Sell"]["13"]["7"] / 100}0'
        day_31 = f'{self.config["Product Price"]["Sell"]["13"]["31"] / 100}0'

        eft = discord.utils.get(ctx.guild.text_channels, name="eft")
        embed = discord.Embed(title="EFT (CLICK ME)", url="https://cheatsac.sellix.io/", description="Features", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        embed.set_image(url="attachment://eft.png")
        embed.add_field(name="Pricing", value=f"Day ${day_1}\n3 Day ${day_3}\nWeek ${day_7}\nMonth ${day_31}")
        embed.set_footer(text="Open a ticket for alternative payment methods")
        file = discord.File("images/eft.png")
        await eft.send(embed=embed, file=file)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def send_fortnite_message(self, ctx):
        try:
            await ctx.message.delete()
        except:
            pass

        day_1 = f'{self.config["Product Price"]["Sell"]["5"]["1"] / 100}0'
        day_3 = f'{self.config["Product Price"]["Sell"]["5"]["3"] / 100}0'
        day_7 = f'{self.config["Product Price"]["Sell"]["5"]["7"] / 100}0'
        day_31 = f'{self.config["Product Price"]["Sell"]["5"]["31"] / 100}0'

        fortnite = discord.utils.get(ctx.guild.text_channels, name="fortnite")
        embed = discord.Embed(title="Fortnite (CLICK ME)", url="https://cheatsac.sellix.io/", description="Features", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        embed.set_image(url="attachment://fortnite.png")
        embed.add_field(name="Pricing", value=f"Day ${day_1}\n3 Day ${day_3}\nWeek ${day_7}\nMonth ${day_31}")
        embed.set_footer(text="Open a ticket for alternative payment methods")
        file = discord.File("images/fortnite.png")
        await fortnite.send(embed=embed, file=file)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def send_apex_message(self, ctx):
        try:
            await ctx.message.delete()
        except:
            pass

        day_1 = f'{self.config["Product Price"]["Sell"]["4"]["1"] / 100}0'
        day_3 = f'{self.config["Product Price"]["Sell"]["4"]["3"] / 100}0'
        day_7 = f'{self.config["Product Price"]["Sell"]["4"]["7"] / 100}0'
        day_31 = f'{self.config["Product Price"]["Sell"]["4"]["31"] / 100}0'

        apex = discord.utils.get(ctx.guild.text_channels, name="apex")
        embed = discord.Embed(title="APEX (CLICK ME)", url="https://cheatsac.sellix.io/", description="Features", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        embed.set_image(url="attachment://apex.png")
        embed.add_field(name="Pricing", value=f"Day ${day_1}\n3 Day ${day_3}\nWeek ${day_7}\nMonth ${day_31}")
        embed.set_footer(text="Open a ticket for alternative payment methods")
        file = discord.File("images/apex.png")
        await apex.send(embed=embed, file=file)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def send_gta_message(self, ctx):
        try:
            await ctx.message.delete()
        except:
            pass

        day_1 = f'{self.config["Product Price"]["Sell"]["15"]["1"] / 100}0'
        day_3 = f'{self.config["Product Price"]["Sell"]["15"]["3"] / 100}0'
        day_7 = f'{self.config["Product Price"]["Sell"]["15"]["7"] / 100}0'
        day_31 = f'{self.config["Product Price"]["Sell"]["15"]["31"] / 100}0'

        gta = discord.utils.get(ctx.guild.text_channels, name="gta-fivem")
        embed = discord.Embed(title="GTA/FiveM (CLICK ME)", url="https://cheatsac.sellix.io/", description="Features", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        embed.set_image(url="attachment://gta.png")
        embed.add_field(name="Pricing", value=f"Day ${day_1}\n3 Day ${day_3}\nWeek ${day_7}\nMonth ${day_31}")
        embed.set_footer(text="Open a ticket for alternative payment methods")
        file = discord.File("images/gta.png")
        await gta.send(embed=embed, file=file)


def setup(bot):
    bot.add_cog(Owner(bot))
