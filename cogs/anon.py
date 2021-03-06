import discord

from io import BytesIO
from discord import File as reportFile
from discord.ext import commands
from utils import globals as GG
from utils import logger

log = logger.logger


class Anon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # report_channel = 574758154110238730
        # delivery_channel = self.bot.get_channel(574886423711186964)
        LordDusk = self.bot.get_user(GG.OWNER)
        channel = message.channel

        if message.author.id != GG.BOT:

            if channel.id in GG.CHANNEL:
                TYPE = GG.CHANNEL[channel.id]

                if TYPE == "ANON":
                    delivery_channel = await GG.MDB['channelinfo'].find_one({"guild": message.guild.id, "type": "DELIVERY"})
                    if delivery_channel is None:
                        await self.noDeliveryChannel(message)
                        await self.notifyOwner(message)
                        await message.delete()
                    else:
                        delivery_channel = self.bot.get_channel(delivery_channel['channel'])
                        content = message.content
                        author = message.author
                        em = discord.Embed(title=f"New report", author=author.display_name, description=content)
                        report = await delivery_channel.send(embed=em)
                        em.set_footer(
                            text=f"You can reply to this report by using the following command ``!reply {report.id} <your reply>``")
                        await report.edit(embed=em)
                        if len(message.attachments) > 0:
                            content = "\nThe report also had the following image/images connected to it:"
                            for a in message.attachments:
                                Bytes = await a.read()
                                await delivery_channel.send(content=content,
                                                            file=reportFile(BytesIO(Bytes), filename="Image.png"))
                        await GG.MDB['channelinfo'].insert_one({"user": author.id, "message": report.id})
                        await message.delete()

                if TYPE == "DELIVERY":
                    content = message.content
                    try:
                        command, msg_id, reply = content.split(" ", 2)
                        if command == "!reply":
                            checkIfExist = await GG.MDB['reports'].find_one({"message": msg_id})
                            if checkIfExist is not None:
                                reporter = self.bot.get_user(int(checkIfExist['user']))
                                if reporter is not None:
                                    if reporter.dm_channel is None:
                                        dm_channel = await reporter.create_dm()
                                    else:
                                        dm_channel = reporter.dm_channel
                                    author = message.author
                                    em = discord.Embed(title=f"A member of staff has a reaction to your report.",
                                                       author=author.display_name, description=reply)
                                    try:
                                        await dm_channel.send(embed=em)
                                        msg = await channel.fetch_message(msg_id)
                                        await msg.add_reaction("✅")
                                        await message.add_reaction("✅")
                                    except discord.errors.Forbidden:
                                        await message.channel.send(
                                            "Sorry, I can't reach this person, they either blocked me, or turned off their "
                                            "DM's for me (more likely).")
                                else:
                                    await message.channel.send(
                                        f"Ths user left the server. So I can't do anything about this. User: <@{reporterDB[0]}>")
                            else:
                                await message.channel.send(
                                    f"[DEBUG] Sorry, reporter not found. I'll DM my owner {LordDusk.mention} for you.")
                    except ValueError as e:
                        return


    async def notifyOwner(self, message):
        ServerOwner = self.bot.get_user(message.guild.owner.id)
        if ServerOwner.dm_channel is None:
            dm_channel = await ServerOwner.create_dm()
        else:
            dm_channel = ServerOwner.dm_channel
        author = message.author
        Embed = discord.Embed(title=f"No delivery channel exists.",
                              author=author.display_name,
                              description=f"Hello, a user of your server {message.guild.name} tried to make an "
                              f"anonymous report, but you have yet to make a delivery channel. You can do this by "
                              f"executing the following command: ``!addchannel <id> DELIVERY``. Thank you!")
        try:
            await dm_channel.send(embed=Embed)
        except discord.errors.Forbidden:
            await message.channel.send(
                f"Hello {message.guild.owner.mention}, a user just tried to make an anonymous report, but you have "
                f"yet to make a delivery channel. You can do this by executing the following command: ``!addchannel "
                f"<id> DELIVERY``. Thank you!")

    async def noDeliveryChannel(self, message):
        Reporter = self.bot.get_user(message.author.id)
        if Reporter.dm_channel is None:
            dm_channel = await Reporter.create_dm()
        else:
            dm_channel = Reporter.dm_channel
        author = message.author
        Embed = discord.Embed(title=f"Error",
                              author=author.display_name, description="Sorry this Server doesnt have "
                                                                      "a delivery channel yet, "
                                                                      "I will notify the Server Owner "
                                                                      "for you if I'm able.")
        try:
            await dm_channel.send(embed=Embed)
        except discord.errors.Forbidden:
            await message.channel.send(
                "@Reporter, you have turned off the ability to let me DM you. I will notify the "
                "Server Owner that they haven't created a delivery channel yet.")


def setup(bot):
    log.info("[Cog] Anon Report")
    bot.add_cog(Anon(bot))
