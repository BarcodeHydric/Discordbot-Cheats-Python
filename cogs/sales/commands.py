import json
import os

import discord
from discord.ext import commands
from discord_components import Button, Select, SelectOption

from databases.api import API, Seller, Serial, Game, NoSeller, NoSerial
from utils.payments import Payment


class Sales(commands.Cog):
    def __init__(self, bot):
        self.config = json.load(open(os.getcwd() + '/config/config.json'))
        self.bot = bot

        self.payment = Payment()

        self.api = API()
        self.games = self.api.get_games()

        self.key_gen = {}
        self.key_mod = {}

    def cog_check(self, ctx):
        self.config = json.load(open(os.getcwd() + '/config/config.json'))
        self.games = self.api.get_games()
        return True

    def ensure_keygen_ready(self, interaction):
        if interaction.author.id not in self.key_gen:
            self.key_gen[interaction.author.id] = {}

    def ensure_keymod_ready(self, interaction, serial):
        if interaction.author.id not in self.key_mod:
            self.key_mod[interaction.author.id] = {}

        if serial not in self.key_mod[interaction.author.id]:
            self.key_mod[interaction.author.id][serial] = {}

    @commands.Cog.listener()
    async def on_button_click(self, interaction):
        # KEY GEN ======================================================================================================
        self.ensure_keygen_ready(interaction)

        if interaction.custom_id == "generate-key":
            gameid = self.key_gen[interaction.author.id].get("type")
            duration = self.key_gen[interaction.author.id].get("duration")
            count = self.key_gen[interaction.author.id].get("count")

            if not gameid or not count or not duration:
                await interaction.send("Select the key type, length and duration before generating a key")
                return

            game = Game(int(gameid))

            duration = duration
            count = int(count)
            price = game.reseller_prices[duration]

            if price == 0:
                await interaction.send(f"Key length {duration} not available for {game.name}")
                return

            total_price = price * count

            try:
                seller = Seller(interaction.author.id)
            except NoSeller:
                await interaction.send("You arent a reseller")
                return

            if not seller.genkeys:
                await interaction.send("You have been restricted from keygen access")

            else:
                serials = '\n'.join(seller.gen_key(duration, game.id, count))
                seller.update("owed", seller.raw_owed + total_price)
                embed = None

                if seller.owed > 500 and not seller.unrestricted:
                    seller.update("genkeys", 0)
                    embed = discord.Embed(title="KeyGen Access", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
                    embed.add_field(name=f"Your access has been suspended!", value=f"To continue using AC's KeyGen pay off your balance")
                    embed.set_footer(text=f"All existing keys will be deleted in 5 days if the balance is not paid off")

                elif seller.owed > 350 and not seller.unrestricted:
                    embed = discord.Embed(title="KeyGen Access", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
                    embed.add_field(name=f"You currently owe ${seller.owed:,}", value="At $500 owed your access will be suspended! Pay off your balance using the `!pay` command")

                try:
                    await interaction.author.send(f"Price ${total_price/100:,} - Total Owed ${seller.owed:,}\n"
                                                  f"{self.config['Loader']['Download']}\n"
                                                  f"========================================\n"
                                                  f"```{serials}```", embed=embed)
                    await interaction.send("Check your DM's")
                except discord.Forbidden:
                    await interaction.send(f"**Update your privacy settings so I can send keys to your DM `Server Settings > Privacy Settings > Allow DM's from Members`**\n"
                                           f"Price ${total_price/100:,} - Total Owed ${seller.owed:,}\n"
                                           f"{self.config['Loader']['Download']}\n"
                                           f"========================================\n"
                                           f"```{serials}```", embed=embed)

            seller.close()
            await interaction.respond(type=6)

        # KEY MOD ======================================================================================================
        if interaction.custom_id == "reset-hwid":
            serial = interaction.message.embeds[0].description
            self.ensure_keymod_ready(interaction, serial)
            self.key_mod[interaction.author.id][serial]["reset-hwid"] = 1

        if interaction.custom_id == "delete-key":
            serial = Serial(interaction.message.embeds[0].description)
            seller = Seller(serial.resellerid)

            if serial.resellerid != interaction.author.id and not seller.unrestricted:
                await interaction.send("You can only modify your own keys")
                serial.close()
                seller.close()
                return

            serial.delete()
            serial.close()

            embed = discord.Embed(title="Key Deleted!", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
            await interaction.message.edit(embed=embed, components=[])

        if interaction.custom_id == "save-key":
            serial = Serial(interaction.message.embeds[0].description)
            seller = Seller(serial.resellerid)

            if serial.resellerid != interaction.author.id and not seller.unrestricted:
                await interaction.send("You can only modify your own keys")
                serial.close()
                seller.close()
                return

            self.ensure_keymod_ready(interaction, serial)
            gameid = self.key_mod[interaction.author.id][serial].get("type")
            duration = self.key_mod[interaction.author.id][serial].get("duration")
            reset = self.key_mod[interaction.author.id][serial].get("reset-hwid")

            old_game = Game(serial.gameid)
            new_game = Game(serial.gameid)

            old_price = old_game.reseller_prices[duration]
            new_price = new_game.reseller_prices[duration]

            if new_price == 0:
                serial.close()
                seller.close()
                await interaction.send(f"Key length {duration} not available for {new_game.name}")
                return

            price_diff = new_price - old_price
            seller.update("owed", seller.raw_owed + price_diff)

            if gameid:
                serial.update("gameid", int(gameid))

            if duration:
                serial.update("duration", int(duration))

            if reset:
                serial.update("computerid", None)
                serial.update("resetcount", serial.resetcount + 1)

            serial.close()
            serial = Serial(interaction.message.embeds[0].description)

            embed = discord.Embed(title="Key Modded", description=serial.serial, color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
            embed.add_field(name="Key For", value=self.bot.config["Product ID"][str(serial.gameid)])
            embed.add_field(name="Created By", value=discord.utils.get(interaction.guild.members, id=serial.resellerid))
            embed.add_field(name="Created On", value=serial.created)
            embed.add_field(name="Registered On", value=serial.registered)
            embed.add_field(name="Duration", value=serial.duration)

            all_key_types = [SelectOption(label=game.name, value=f"mod-id-{game.id}", default=serial.gameid == game.id) for game in self.games]

            await interaction.message.edit(embed=embed, components=[
                Select(placeholder="Key Type", options=all_key_types),
                Select(placeholder="Key Length",
                       options=[SelectOption(label="1 Day", value="mod-1-day"),
                                SelectOption(label="3 Day", value="mod-3-day"),
                                SelectOption(label="1 Week", value="mod-7-day"),
                                SelectOption(label="1 Month", value="mod-31-day"),
                                SelectOption(label="Lifetime", value="mod-36500-day")]),
                Button(label="Reset HWID", custom_id="reset-hwid"),
                [Button(label="Delete Key", custom_id="delete-key"), Button(label="Save Key", custom_id="save-key")]
            ])

            serial.close()
            seller.close()

        await interaction.respond(type=6)

    @commands.Cog.listener()
    async def on_select_option(self, interaction):
        # KEY GEN ======================================================================================================
        if interaction.values[0] in [f"id-{game.id}" for game in self.games]:
            self.ensure_keygen_ready(interaction)
            self.key_gen[interaction.author.id]["type"] = interaction.values[0].split("-")[1]

        elif interaction.values[0] in ["1-day", "3-day", "7-day", "31-day", "36500-day"]:
            self.ensure_keygen_ready(interaction)
            self.key_gen[interaction.author.id]["duration"] = interaction.values[0].split("-")[0]

        elif interaction.values[0] in ["1-keys", "5-keys", "10-keys"]:
            self.ensure_keygen_ready(interaction)
            self.key_gen[interaction.author.id]["count"] = interaction.values[0].split("-")[0]

        # KEY MOD ======================================================================================================
        elif interaction.values[0] in [f"mod-id-{game.id}" for game in self.games]:
            serial = interaction.message.embeds[0].description
            self.ensure_keymod_ready(interaction, serial)
            self.key_mod[interaction.author.id][serial]["type"] = interaction.values[0].split("-")[2]

        elif interaction.values[0] in ["mod-1-day", "mod-3-day", "mod-7-day", "mod-31-day", "mod-36500-day"]:
            serial = interaction.message.embeds[0].description
            self.ensure_keymod_ready(interaction, serial)
            self.key_mod[interaction.author.id][serial]["duration"] = interaction.values[0].split("-")[1]

        await interaction.respond(type=6)

    @commands.command(name="redeem", aliases=[], help="", usage="")
    @commands.dm_only()
    async def cmd_redeem(self, ctx, key):
        try:
            serial = Serial(key)
        except NoSerial:
            await ctx.send("That is not a valid key")
            return

        if serial.claimedby is None:
            serial.update("claimedby", ctx.author.id)
            guild = discord.utils.get(self.bot.guilds, name=self.config['Server']['Name'])
            role = discord.utils.get(guild.roles, name="Public User")
            adding = discord.utils.get(guild.members, id=ctx.author.id)
            await adding.add_roles(role)
            await ctx.author.send(f"{self.config['Loader']['Download']}\nYou have been given the role `{role.name}`")
        else:
            await ctx.author.send(f"{self.config['Loader']['Download']}\nThis key was already claimed. Contact support if this wasnt you")

    @commands.command(name="pay", aliases=[], help="", usage="")
    @commands.dm_only()
    async def cmd_pay(self, ctx):
        reseller = Seller(ctx.author.id)
        payment = self.payment.create(reseller.owed)
        embed = discord.Embed(title="KeyGen Access Payment", description="Send the exact amount posted")
        embed.add_field(name="Payment ID", value=f"{payment['id']}", inline=False)
        embed.add_field(name="BTC", value=f"{payment['addresses']['bitcoin']} - {payment['pricing']['bitcoin']['amount']}", inline=False)
        embed.add_field(name="ETH", value=f"{payment['addresses']['ethereum']} - {payment['pricing']['ethereum']['amount']}", inline=False)
        embed.add_field(name="LTC", value=f"{payment['addresses']['litecoin']} - {payment['pricing']['litecoin']['amount']}", inline=False)
        embed.add_field(name="USDC", value=f"{payment['addresses']['usdc']} - {payment['pricing']['usdc']['amount']}", inline=False)
        embed.set_footer(text="After the payment has been sent use `!confirm <payment_id>`")
        await ctx.send(embed=embed)

    @commands.command(name="confirm", aliases=[], help="", usage="")
    @commands.dm_only()
    async def cmd_confirm(self, ctx, payment_id):
        api = API()
        used = api.check_payment_id(payment_id)

        if used:
            await ctx.send("This payment ID has already been used. Contact an admin if this is an issue")

        payment = self.payment.get(payment_id)
        if not payment:
            await ctx.send("No payment was made with that ID, please ensure you entered the right payment ID, if you did contact Bump#8199")

        if payment["timeline"][-1]["status"] == "NEW":
            await ctx.send("You have not yet sent a payment. If you have, wait 5 minutes and try again. If the issue continues contact Bump#8199")

        elif payment["timeline"][-1]["status"] == "PENDING":
            await ctx.send("Your payment has not been confirmed yet, wait ~30-45 minutes and try again")

        elif payment["timeline"][-1]["status"] == "COMPLETED":
            api.use_payment_id(payment_id, ctx.author.id)
            seller = Seller(ctx.author.id)
            seller.update("genkeys", 1)
            seller.update("owed", 0)
            await ctx.send("Your payment has been confirmed and you now have keygen access!")
        api.close()

    @commands.command(name="me", aliases=[], help="", usage="")
    @commands.has_any_role("Team", "Reseller")
    async def cmd_me(self, ctx):
        reseller = Seller(ctx.author.id)
        embed = discord.Embed(title="Your Reseller Profile", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        embed.add_field(name="Active Keys", value=f"{len(reseller.get_keys()):,}")
        embed.add_field(name="Amount Owed", value=f"${reseller.owed:,}")
        await ctx.send(embed=embed)

    @commands.command(name="gen", aliases=[], help="", usage="")
    @commands.has_any_role("Team", "Reseller")
    async def cmd_gen(self, ctx):
        embed = discord.Embed(title="AC KeyGen", color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))

        all_key_types = [SelectOption(label=game.name, value=f"id-{game.id}") for game in self.games]

        await ctx.send(embed=embed, components=[
            Select(placeholder="Key Type", options=all_key_types),
            Select(placeholder="Key Length",
                   options=[SelectOption(label="1 Day", value="1-day"),
                            SelectOption(label="3 Day", value="3-day"),
                            SelectOption(label="1 Week", value="7-day"),
                            SelectOption(label="1 Month", value="31-day"),
                            SelectOption(label="Lifetime", value="36500-day")]),
            Select(placeholder="Key Count",
                   options=[SelectOption(label="1 Key", value="1-keys"),
                            SelectOption(label="5 Keys", value="5-keys"),
                            SelectOption(label="10 Keys", value="10-keys")]),
            Button(label="Generate Key", custom_id="generate-key")
        ])

    @commands.command(name="mod", aliases=[], help="", usage="")
    @commands.has_any_role("Team", "Reseller")
    async def cmd_mod(self, ctx, serial):
        serial = Serial(serial)
        game = Game(serial.gameid)
        embed = discord.Embed(title="Key Mod", description=serial.serial, color=discord.Color(eval(f"0x{self.config['Style']['EmbedColor']}")))
        embed.add_field(name="Key For", value=game.name)
        embed.add_field(name="Created By", value=discord.utils.get(ctx.guild.members, id=serial.resellerid))
        embed.add_field(name="Created On", value=serial.created)
        embed.add_field(name="Registered On", value=serial.registered)
        embed.add_field(name="Duration", value=serial.duration)

        all_key_types = [SelectOption(label=game.name, value=f"mod-id-{game.id}", default=serial.gameid == game.id) for game in self.games]

        await ctx.send(embed=embed, components=[
            Select(placeholder="Key Type", options=all_key_types),
            Select(placeholder="Key Length",
                   options=[SelectOption(label="1 Day", value="mod-1-day", default=serial.duration == 1),
                            SelectOption(label="3 Day", value="mod-3-day", default=serial.duration == 3),
                            SelectOption(label="1 Week", value="mod-7-day", default=serial.duration == 7),
                            SelectOption(label="1 Month", value="mod-31-day", default=serial.duration == 31),
                            SelectOption(label="Lifetime", value="mod-36500-day", default=serial.duration == 36500)]),
            Button(label="Reset HWID", custom_id="reset-hwid"),
            [Button(label="Delete Key", custom_id="delete-key"), Button(label="Save Key", custom_id="save-key")]
        ])
        serial.close()


def setup(bot):
    bot.add_cog(Sales(bot))
