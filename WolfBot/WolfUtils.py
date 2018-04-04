import datetime
import re
import subprocess

import discord

import WolfBot.WolfConfig
from WolfBot import WolfStatics


def memberHasRole(member, role_id):
    for r in member.roles:
        if r.id == role_id:
            return True

    return False


def memberHasAnyRole(member, roles):
    if roles is None:
        return True

    for r in member.roles:
        if r.id in roles:
            return True

    return False


def getFancyGameData(member):
    if member.activity is not None:
        state = {0: "Playing ", 1: "Streaming ", 2: "Listening to ", 3: "Watching "}

        if isinstance(member.activity, discord.Spotify):
            m = "(Listening to Spotify)"

            if member.activity.title is not None and member.activity.artist is not None:
                track_url = "https://open.spotify.com/track/{}"

                m += "\n\n**Now Playing:** [{} by {}]({})".format(member.activity.title, member.activity.artist,
                                                                  track_url.format(member.activity.track_id))

            return m
        elif not isinstance(member.activity, discord.Game) and member.activity.url is not None:
            return "([{}]({}))".format(state[member.activity.type] + member.activity.name, member.activity.url)
        else:
            return "({})".format(state[member.activity.type] + member.activity.name)

    return ""


def tail(filename, n):
    p = subprocess.Popen(['tail', '-n', str(n), filename], stdout=subprocess.PIPE)
    soutput, sinput = p.communicate()
    return soutput.decode('utf-8')


def should_process_message(message):
    if message.guild is not None and message.guild.id in WolfBot.WolfConfig.getConfig().get("ignoredGuilds", []):
        return False

    if message.author.bot:
        return False

    return True


def trim_string(string: str, limit: int, add_ellipses: bool):
    s = string

    if len(string) > limit:
        s = string[:limit]

        if add_ellipses:
            s = s[:-5] + "\n\n..."

    return s


def get_timestamp():
    """
    Get the UTC timestamp in YYYY-MM-DD HH:MM:SS format (Bot Standard)
    """

    return datetime.datetime.utcnow().strftime(WolfStatics.DATETIME_FORMAT)


def get_user_id_from_arbitrary_str(guild: discord.Guild, string: str):
    if string.isnumeric():
        potential_uid = int(string)
    elif string.startswith("<@") and string.endswith(">"):
        potential_uid = int(string.replace("<@", "").replace(">", "").replace("!", ""))
    else:
        potential_user = guild.get_member_named(string)

        if potential_user is None:
            raise ValueError("No member by the name of {} was found.".format(string))

        return potential_user.id

    # if guild.get_member(potential_uid) is None:
    #    raise ValueError("Member ID {} (translated from {}) was not found. ".format(potential_uid, string))

    return potential_uid


def get_timedelta_from_string(timestring: str):
    regex = re.compile(r'((?P<days>\d+?)d)?((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?')

    parts = regex.match(timestring)
    if not parts:
        return
    parts = parts.groupdict()
    time_params = {}
    for (name, param) in parts.items():
        if param:
            time_params[name] = int(param)
    if time_params == {}:
        raise ValueError("Invalid time string! Must be in form #d#h#m#s.")
    return datetime.timedelta(**time_params)
