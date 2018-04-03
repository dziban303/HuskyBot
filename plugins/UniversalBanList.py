import logging

import discord
from discord.ext import commands

from WolfBot import WolfUtils

LOG = logging.getLogger("DiyBot.Plugin." + __name__)


# noinspection PyMethodMayBeStatic
class UniversalBanList:
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot

        # Universal Ban List of phrases used by the bot. Any phrases here will trigger an instant ban.
        self._ubl_phrases = [
            "\u5350"  # Swastika unicode
        ]

        LOG.info("Loaded plugin!")

    async def filter_message(self, message: discord.Message, context: str = "new_message"):
        if not isinstance(message.channel, discord.TextChannel):
            return

        if not WolfUtils.should_process_message(message):
            return

        if message.author.permissions_in(message.channel).manage_messages:
            return

        for ubl_term in self._ubl_phrases:
            if ubl_term.lower() in message.content.lower():
                await message.author.ban(reason="[AUTOMATIC BAN - UBL Module] User used UBL keyword `{}`"
                                         .format(ubl_term), delete_message_days=5)
                LOG.info("Banned UBL triggering user (context %s, keyword %s, from %s in %s): %s", context,
                         message.author, ubl_term, message.channel, message.content)

    async def on_message(self, message):
        await self.filter_message(message)

    # noinspection PyUnusedLocal
    async def on_message_edit(self, before, after):
        await self.filter_message(after, "edit")

    async def on_member_join(self, member: discord.Member):
        if member.guild_permissions.manage_guild:
            return

        for ubl_term in self._ubl_phrases:
            if ubl_term.lower() in member.display_name.lower():
                await member.ban(reason="[AutoBan - UBL Module] New user's name contains UBL keyword `{}`"
                                 .format(ubl_term),
                                 delete_message_days=0)
                LOG.info("Banned UBL triggering new join of user %s (matching UBL %s)", member, ubl_term)

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if after.guild_permissions.manage_guild:
            return

        if before.nick == after.nick and before.name == after.name:
            return

        for ubl_term in self._ubl_phrases:
            if after.nick is not None and ubl_term.lower() in after.nick.lower():
                u_type = 'nickname'
            elif after.name is not None and ubl_term.lower() in after.name.lower():
                u_type = 'username'
            else:
                continue

            await after.ban(reason="[AutoBan - UBL Module] User {} changed {} to include UBL keyword {}"
                            .format(after, u_type, ubl_term))
            LOG.info("Banned UBL triggering %s change of user %s (matching UBL %s)", u_type, after, ubl_term)


def setup(bot: discord.ext.commands.Bot):
    bot.add_cog(UniversalBanList(bot))