import datetime
import logging

import discord
from discord.ext import commands
from discord.http import Route

from HuskyBot import HuskyBot
from libhusky import HuskyConverters
from libhusky import HuskyUtils
from libhusky.HuskyStatics import *

LOG = logging.getLogger("HuskyBot.Plugin." + __name__)


class Intelligence(commands.Cog):
    """
    Intelligence is a plugin focusing on gathering information from Discord.

    It is used to query data about users (or roles/guilds) from guilds. Commands are generally open to execution for
    all users, and only expose information provided by the Discord API, not information generated by the bot or bot
    commands.

    All commands here query their information directly from the Discord API in near realtime.
    """

    def __init__(self, bot: HuskyBot):
        self.bot = bot
        LOG.info("Loaded plugin!")

    @commands.command(name="guildinfo", aliases=["sinfo", "ginfo"], brief="Get information about the current guild")
    @commands.guild_only()
    async def guild_info(self, ctx: commands.Context):
        """
        This command returns basic core information about a guild for reporting purposes.
        """

        guild = ctx.guild

        guild_details = discord.Embed(
            title="Guild Information for " + guild.name,
            color=guild.owner.color
        )

        guild_details.set_thumbnail(url=guild.icon_url)
        guild_details.add_field(name="Guild ID", value=guild.id, inline=True)
        guild_details.add_field(name="Owner", value=f"{HuskyUtils.escape_markdown(guild.owner.display_name)}"
                                                    f"#{guild.owner.discriminator}",
                                inline=True)
        guild_details.add_field(name="Members", value=str(len(guild.members)) + " users", inline=True)
        guild_details.add_field(name="Text Channels", value=str(len(guild.text_channels)) + " channels", inline=True)
        guild_details.add_field(name="Roles", value=str(len(guild.roles)) + " roles", inline=True)
        guild_details.add_field(name="Voice Channels", value=str(len(guild.voice_channels)) + " channels", inline=True)
        guild_details.add_field(name="Created At", value=guild.created_at.strftime(DATETIME_FORMAT), inline=True)
        guild_details.add_field(name="Region", value=guild.region, inline=True)

        if len(guild.features) > 0:
            guild_details.add_field(name="Features", value=", ".join(guild.features))

        await ctx.send(embed=guild_details)

    @commands.command(name="roleinfo", aliases=["rinfo"], brief="Get information about a specified role.")
    @commands.guild_only()
    async def role_info(self, ctx: discord.ext.commands.Context, *, role: discord.Role):
        """
        This command will dump configuration information (with the exception of permissions) for the selected role. It
        will also attempt to count the number of users with the specified role.

        Parameters
        ----------
            ctx   :: Context <!nodoc>
            role  :: A uniquely identifying role string. This can be a role mention, a role ID, or name.
                    This parameter is case-sensitive, but does not need to be "quoted in case of spaces."

        Examples
        --------
            /roleinfo Admins  :: Get information about the role "Admins"
        """

        role_details = discord.Embed(
            title="Role Information for " + role.name,
            color=role.color
        )

        role_details.add_field(name="Role ID", value=role.id, inline=True)

        if role.color.value == 0:
            role_details.add_field(name="Color", value="None", inline=True)
        else:
            role_details.add_field(name="Color", value=str(hex(role.color.value)).replace("0x", "#"), inline=True)

        role_details.add_field(name="Mention Preview", value=role.mention, inline=True)
        role_details.add_field(name="Hoisted", value=role.hoist, inline=True)
        role_details.add_field(name="Managed Role", value=role.managed, inline=True)
        role_details.add_field(name="Mentionable", value=role.mentionable, inline=True)
        role_details.add_field(name="Position", value=role.position, inline=True)
        role_details.add_field(name="Member Count", value=str(len(role.members)), inline=True)

        await ctx.send(embed=role_details)

    @commands.command(name="userinfo", aliases=["uinfo", "memberinfo", "minfo", "whois"],
                      brief="Get information about self or specified user")
    async def user_info(self, ctx: discord.ext.commands.Context, *,
                        user: HuskyConverters.OfflineMemberConverter = None):
        """
        This command will attempt to return join dates, name status, roles, and the index number of the user in the
        current guild. The bot will attempt to get information for users not in the guild, but information in this case
        is somewhat limited.

        Parameters
        ----------
            ctx   :: Discord context <!nodoc>
            user  :: A uniquely identifying user string, such as a mention, a user ID, a username, or a nickname.
                    This parameter is case-sensitive, but does not need to be "quoted in case of spaces."

        Examples
        --------
            /uinfo SomeUser#1234  :: Get information for user "SomeUser#1234".
        """

        user = user or ctx.author

        if isinstance(user, discord.User):
            member_details = discord.Embed(
                title=f"User Information for {user}",
                color=Colors.INFO,
                description="Currently **not a member of any shared guild!**\nData may be limited."
            )
        elif isinstance(user, discord.Member):
            member_details = discord.Embed(
                title=f"User Information for {user}",
                color=user.color,
                description=f"Currently in **{user.status}** mode " + HuskyUtils.get_fancy_game_data(user)
            )
        else:
            raise ValueError("Illegal state!")

        roles = []
        if isinstance(user, discord.Member) and ctx.guild is not None:
            for r in user.roles:
                if r.name == "@everyone":
                    continue

                roles.append(r.mention)

            if len(roles) == 0:
                roles.append("None")

        member_details.add_field(name="User ID", value=user.id, inline=True)

        if isinstance(user, discord.Member) and ctx.guild is not None:
            member_details.add_field(name="Display Name", value=HuskyUtils.escape_markdown(user.display_name),
                                     inline=True)

        member_details.add_field(name="Joined Discord", value=user.created_at.strftime(DATETIME_FORMAT), inline=True)
        member_details.set_thumbnail(url=user.avatar_url)

        if isinstance(user, discord.Member) and ctx.guild is not None:
            member_details.add_field(name="Joined Guild", value=user.joined_at.strftime(DATETIME_FORMAT), inline=True)
            member_details.add_field(name="Roles", value=", ".join(roles), inline=False)

            index = sorted(ctx.guild.members, key=lambda m: m.joined_at).index(user) + 1
            member_details.set_footer(text=f"Member #{index} on the guild")

        await ctx.send(embed=member_details)

    @commands.command(name="avatar", brief="Get a high-resolution version of a user's avatar")
    async def avatar(self, ctx: commands.Context, *, user: HuskyConverters.OfflineUserConverter = None):
        """
        This command will attempt to find and return the largest possible version of a user's avatar that it can, as
        well as the avatar hash.

        This command takes a single (optional) argument - a member identifier. This may be a User ID, a ping, a
        username, a nickname, etc. If this argument is not specified, the bot will return the avatar of the calling
        user.

        Parameters
        ----------
            ctx   :: Discord context <!nodoc>
            user  :: A uniquely identifying user string, such as a mention, a user ID, a username, or a nickname.
                    This parameter is case-sensitive, but does not need to be "quoted in case of spaces."

        Examples
        --------
            /avatar                :: Get the calling user's avatar.
            /avatar SomeUser#1234  :: Get avatar for user "SomeUser#1234"
        """

        user = user or ctx.author

        embed = discord.Embed(
            title=f"Avatar for {user}",
            color=Colors.INFO
        )

        embed.add_field(name="Avatar ID", value=f"`{user.avatar}`", inline=False)
        embed.add_field(name="Avatar URL", value=f"[Open In Browser >]({user.avatar_url})", inline=False)
        embed.set_image(url=user.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(name="msgcount", brief="Get a count of messages in a given context")
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def message_count(self, ctx: commands.Context,
                            search_context: HuskyConverters.ChannelContextConverter = "public",
                            timedelta: HuskyConverters.DateDiffConverter = "24h"):
        """
        A context/area is defined as a single channel, the keyword "all", or the keyword "public". If a channel name is
        specified, only that channel will be searched. "all" will attempt to search every channel that exists in the
        guild. "public" will search every channel in the guild that can be seen by the @everyone user.

        Timedelta is a time string formatted in 00d00h00m00s format. This may only be used to search back.

        Caveats
        -------
          * It is important to know that this is a *slow* command, because it needs to iterate over every message
            in the search channels in order to successfully operate. Because of this, the "Typing" indicator will
            display. Also note that this command may not return accurate results due to the nature of the search system.
            It should be used for approximation only.

        Parameters
        ----------
            ctx             :: Discord context <!nodoc>
            search_context  :: A search context as described above. Default "public".
            timedelta       :: A timedelta string as described above. Default 24h.

        Examples
        --------
            /msgcount public 7d    :: Get a count of all public messages in the last 7 days
            /msgcount all 2d       :: Get a count of all messages in the last two days.
            /msgcount #general 5h  :: Get a count of all messages in #general within the last 5 hours.

        See Also
        --------
            /help activeusercount  :: Get the count of active users on the guild.
        """

        if search_context == "public":
            converter = HuskyConverters.ChannelContextConverter()
            search_context = await converter.convert(ctx, "public")

        if timedelta == "24h":
            timedelta = datetime.timedelta(hours=24)

        message_count = 0

        now = datetime.datetime.utcnow()
        search_start = now - timedelta

        async with ctx.typing():
            for channel in search_context['channels']:
                if not channel.permissions_for(ctx.me).read_message_history:
                    LOG.info("I don't have permission to get information for channel %s", channel)
                    continue

                LOG.info("Getting history for %s", channel)
                hist = channel.history(limit=None, after=search_start)

                async for _ in hist:
                    message_count += 1

            await ctx.send(embed=discord.Embed(
                title="Message Count Report",
                description=f"Since `{search_start.strftime(DATETIME_FORMAT)}`, the channel context "
                            f"`{search_context['name']}` has seen about **{message_count} messages**.",
                color=Colors.INFO
            ))

    @commands.command(name="activeusercount", brief="Get a count of active users on the guild", aliases=["auc"])
    @commands.has_permissions(view_audit_log=True)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def active_user_count(self, ctx: commands.Context,
                                search_context: HuskyConverters.ChannelContextConverter = "all",
                                delta: HuskyConverters.DateDiffConverter = "24h",
                                threshold: int = 10):
        """
        This command will look back through message history and attempt to find the number of active users in the guild.
        By default, it will look for all users that spoke in the specified search context. By default, it will only find
        users who have sent at least ten messages in the specified search time

        This command operates on "context" logic, much like /msgcount. Context are the same as there - either a channel,
        the word "public", or the word "all".

        Bots do not count towards the "active user" count.

        Caveats
        -------
          * It is important to know that this is a *slow* command, because it needs to iterate over every message
            in the search channels in order to successfully operate. Because of this, the "Typing" indicator will
            display. Also note that this command may not return accurate results due to the nature of the search system.
            It should be used for approximation only.

        Parameters
        ----------
            ctx             :: Discord context <!nodoc>
            search_context  :: A string (or channel ID) that resolves to a channel ctx. See /help msgcount.
                               Default "all"
            delta           :: A string in ##d##h##m##s format to capture. Default 24h.
            threshold       :: The minimum number of messages a user needs to send.

        See Also
        --------
            /usercount  :: Get a count of users on the guild
            /msgcount   :: Get a count of messages in the current context
        """
        if search_context == "all":
            converter = HuskyConverters.ChannelContextConverter()
            search_context = await converter.convert(ctx, "all")

        if delta == "24h":
            delta = datetime.timedelta(hours=24)

        message_counts = {}
        active_user_count = 0

        now = datetime.datetime.utcnow()
        search_start = now - delta

        async with ctx.typing():
            for channel in search_context['channels']:
                if not channel.permissions_for(ctx.me).read_message_history:
                    LOG.info("I don't have permission to get information for channel %s", channel)
                    continue

                LOG.info("Getting history for %s", channel)
                hist = channel.history(limit=None, after=search_start)

                async for m in hist:  # type: discord.Message
                    if m.author.bot:
                        continue

                    message_counts[m.author.id] = message_counts.get(m.author.id, 0) + 1

            for user in message_counts:
                if message_counts[user] >= threshold:
                    active_user_count += 1

        await ctx.send(embed=discord.Embed(
            title="Active User Count Report",
            description=f"Since `{search_start.strftime(DATETIME_FORMAT)}`, the channel context "
                        f"`{search_context['name']}` has seen about **{active_user_count} active "
                        f"{'users' if threshold > 1 else 'user'}** (sending at least {threshold} "
                        f"{'messages' if threshold > 1 else 'message'}).",
            color=Colors.INFO
        ))

    @commands.command(name="prunesim", brief="Get a number of users scheduled for pruning")
    @commands.has_permissions(manage_guild=True)
    async def check_prune(self, ctx: commands.Context, days: int = 7):
        """
        This command will simulate a prune on the server and return a count of members expected to be lost. A member is
        considered for pruning if they have not spoken in the specified number of days *and* they have no roles.

        Parameters
        ----------
            ctx   :: Command context <!nodoc>
            days  :: The "prune cutoff" value for a user to be eligible for pruning. Defaults to 7.

        Examples
        --------
            /prunesim 5  :: Get the count of users who have not talked in the last 5 days, and have no roles
        """

        if days < 1 or days > 180:
            raise commands.BadArgument("The `days` argument must be between 1 and 180.")

        prune_count = await ctx.guild.estimate_pruned_members(days=days)

        if days == 1:
            days = "1 day"
        else:
            days = f"{days} days"

        if prune_count == 1:
            prune_count = "1 user"
        else:
            prune_count = f"{prune_count} users"

        await ctx.send(embed=discord.Embed(
            title="Simulated Prune Report",
            description=f"With a simulated cutoff of {days}, an estimated **{prune_count}** will be pruned from the "
                        f"guild. \n\nThis number represents the count of members who have not spoken in the last "
                        f"{days}, and do not have a role (including self-assigned roles).",
            color=Colors.INFO
        ))

    @commands.command(name="usercount", brief="Get a count of users on the guild", aliases=["uc"])
    async def user_count(self, ctx: commands.Context):
        """
        This command will return a count of all members on the guild. It's really that simple.

        See Also
        --------
            /help activeusercount  :: Get a count of active users on the guild.
        """

        breakdown = {}

        for u in ctx.guild.members:  # type: discord.Member
            breakdown[u.status] = breakdown.get(u.status, 0) + 1

        embed = discord.Embed(
            title=Emojis.WAVE + " User Count Report",
            description=f"{ctx.guild.name} currently has **{sum(breakdown.values())} total users**.\n\n"
                        f"**Online Users:** {breakdown[discord.Status.online]}\n"
                        f"**Idle Users:** {breakdown[discord.Status.idle]}\n"
                        f"**DND Users:** {breakdown[discord.Status.dnd]}\n"
                        f"**Offline Users:** {breakdown[discord.Status.offline]}",
            color=Colors.INFO
        )

        await ctx.send(embed=embed)

    @commands.command(name="invitespy", brief="Find information about Guild invite", aliases=["invspy"])
    @commands.has_permissions(view_audit_log=True)
    async def invitespy(self, ctx: commands.Context, fragment: HuskyConverters.InviteLinkConverter):
        """
        This command allows moderators to pull information about any given (valid) invite. It will display all
        publicly-gleanable information about the invite such as user count, verification level, join channel names,
        the invite's creator, and other such information.

        This command calls the API directly, and will validate an invite's existence. If either the bot's account
        or the bot's IP are banned, the system will act as though the invite does not exist.

        Parameters
        ----------
            ctx       :: Discord context <!nodoc>
            fragment  :: Either a Invite URL or fragment (aa1122) for the invite you wish to target.

        Examples
        --------
            /invitespy aabbcc                              :: Get invite data for invite aabbcc
            /invitespy https://disco\u200brd.gg/someguild  :: Get invite data for invite someguild
        """
        try:
            invite_data: dict = await self.bot.http.request(
                Route('GET', '/invite/{invite_id}?with_counts=true', invite_id=fragment))
            invite_guild = discord.Guild(state=self.bot, data=invite_data['guild'])

            if invite_data.get("inviter") is not None:
                invite_user = discord.User(state=self.bot, data=invite_data["inviter"])
            else:
                invite_user = None
        except discord.NotFound:
            await ctx.send(embed=discord.Embed(
                title="Could Not Retrieve Invite Data",
                description="This invite does not appear to exist, or the bot has been banned from the guild.",
                color=Colors.DANGER
            ))
            return

        embed = discord.Embed(
            description=f"Information about invite slug `{fragment}`",
            color=Colors.INFO
        )

        embed.set_thumbnail(url=invite_guild.icon_url)

        embed.add_field(name="Guild Name", value=f"**{invite_guild.name}**", inline=False)

        if invite_user is not None:
            embed.set_author(
                name=f"Invite for {invite_guild.name} by {invite_user}",
                icon_url=invite_user.avatar_url
            )
        else:
            embed.set_author(name=f"Invite for {invite_guild.name}")

        embed.add_field(name="Invited Guild ID", value=invite_guild.id, inline=True)

        ch_type = {0: "#", 2: "[VC] ", 4: "[CAT] "}
        embed.add_field(name="Join Channel Name",
                        value=ch_type[invite_data['channel']['type']] + invite_data['channel']['name'],
                        inline=True)

        embed.add_field(name="Guild Creation Date",
                        value=invite_guild.created_at.strftime(DATETIME_FORMAT),
                        inline=True)

        if invite_data.get('approximate_member_count', -1) != -1:
            embed.add_field(name="User Count",
                            value=f"{invite_data.get('approximate_member_count', -1)} "
                                  f"({invite_data.get('approximate_presence_count', -1)} online)",
                            inline=True)

        vl_map = {
            0: "No Verification",
            1: "Verified Email Needed",
            2: "User for 5+ minutes",
            3: "Member for 10+ minutes",
            4: "Verified Phone Needed"
        }
        embed.add_field(name="Verification Level", value=vl_map[invite_guild.verification_level], inline=True)

        if invite_user is not None:
            embed.add_field(name="Invite Creator", value=str(invite_user), inline=True)

        if len(invite_guild.features) > 0:
            embed.add_field(name="Guild Features",
                            value=', '.join(list(f'`{f}`' for f in invite_guild.features)))

        if invite_guild.splash is not None:
            embed.add_field(name="Splash Image",
                            value=f"[Open in Browser >]({invite_guild.splash_url})",
                            inline=False)
            embed.set_image(url=invite_guild.splash_url)

        embed.set_footer(text=f"Report generated at {HuskyUtils.get_timestamp()}")

        await ctx.send(embed=embed)

    @commands.command(name="emoji", brief="Get information on a Discord emote", aliases=["einfo"])
    async def emoji_info(self, ctx: commands.Context, emoji: HuskyConverters.SuperEmojiConverter):
        # Custom handling for strings
        if isinstance(emoji, str):
            if emoji.isdigit():
                try:
                    emoji = self.bot.get_emoji(int(emoji))
                except discord.NotFound:
                    await ctx.send(embed=discord.Embed(
                        title="Emoji Info",
                        description="The specified emoji ID could not be found.",
                        color=Colors.ERROR
                    ))
            else:
                await ctx.send(embed=discord.Embed(
                    title="Emoji Info",
                    description="This command may only be used to get information on custom emojis, and not "
                                "default/builtin emojis.",
                    color=Colors.ERROR
                ))

            return

        emoji = emoji  # type: discord.PartialEmoji # duck typing hack for pycharm
        flake = HuskyUtils.TwitterSnowflake.load(emoji.id, DISCORD_EPOCH)

        embed = discord.Embed(
            title=f"Emoji - {emoji.name}",
            description=f"**Emoji ID**: `{emoji.id}`",
            color=Colors.INFO
        )
        embed.add_field(name="Animated", value=emoji.animated, inline=True)
        embed.add_field(name="Create Date", value=flake.get_datetime().strftime(DATETIME_FORMAT))
        embed.set_thumbnail(url=emoji.url)

        if isinstance(emoji, discord.Emoji):
            embed.add_field(name="Integrated", value=emoji.managed, inline=True)
            embed.add_field(name="Require Colons", value=emoji.require_colons, inline=True)
            embed.add_field(name="Guild", value=f"{emoji.guild.name} - ID `{emoji.guild_id}`", inline=False)
            embed.add_field(name="Preview", value=f"Hello world! {emoji}", inline=False)

            if emoji.roles:
                embed.add_field(name="Required Roles", value=", ".join(r.mention for r in emoji.roles))

        await ctx.send(embed=embed)


def setup(bot: HuskyBot):
    bot.add_cog(Intelligence(bot))
