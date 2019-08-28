'''
Author: Aaron Peterham
Language: Python 3.7.4

'''
import traceback
from aiohttp import client_exceptions
import discord
import time
import urllib.request
import urllib.error
import asyncio
import sys
import gc

client = discord.Client(max_messages=100)
clients = dict()
chart_messages = dict()
missing_messages = dict()
terr_channels = dict()
alert_channels = dict()
full_missing = dict()


class Territory:
    territory_name = ''
    guild_name = ''
    attacker_name = ''
    aquired = ''

    def __init__(self, guild_name, aquired, attacker_name, territory_name):
        '''
        create a territory object
        :param guild_name: the owner of the territory
        :param aquired: when the territory was captured
        :param attacker_name: the attacker of Territory atm
        :param territory_name: the name of the territory (For debugging mostly)
        :return nuffin
        '''
        self.territory_name = territory_name
        self.guild_name = guild_name
        self.attacker_name = attacker_name
        self.aquired = aquired

    def time_owned(self, time_now):
        '''
        make a message of how long the territory has been owned based on
        when it was captured and the current time
        :param time_now: the current time
        :return: message of how long the territory has been owned
        '''
        ans = list()
        sub = False
        sub2 = False
        # min
        ans.append(int(time_now[14:16]) - int(self.aquired[14:16]))
        if ans[-1] < 0:
            ans[-1] += 60
            sub = True
        if ans[-1] < 0:
            ans[-1] += 60
            sub2 = True
        # hours
        ans.append(int(time_now[11:13]) - int(self.aquired[11:13]) - 4)
        if sub:
            sub = False
            ans[-1] -= 1
        if sub2:
            sub2 = False
            ans[-1] -= 1

        if ans[-1] < 0:
            ans[-1] += 24
            sub = True
        if ans[-1] < 0:
            ans[-1] += 24
            sub2 = True
        # days
        ans.append(int(time_now[8:10]) - int(self.aquired[8:10]))
        if sub:
            ans[-1] -= 1
        if sub2:
            ans[-1] -= 1
        # month
        if int(time_now[5:7]) - int(self.aquired[5:7]) > 0:
            ans[-1] += 30 * (int(time_now[5:7]) - int(self.aquired[5:7]))

        # year
        ans.append(int(time_now[:4]) - int(self.aquired[:4]))
        if int(time_now[5:7]) - int(self.aquired[5:7]) > 0:
            ans[-1] += 365 * (int(time_now[5:7]) - int(self.aquired[5:7]))

        return "{:<2}".format(str(ans[2])) + " d " + "{:<2}".format(str(ans[1])) + " h " + "{:<2}".format(
            str(ans[0]) + " m ")


territories_cache = [[Territory('past', 'time_aquired', 'attacker_name', 'territory_name')],
                     [Territory('now', 'time_aquired', 'attacker_name', 'territory_name')],
                     {'guild_count': 1},
                     'time_now']
begun = [False]

bot_user = ['bot_user']

with open('config.txt') as file:
    i = 0
    for line in file:
        line = line.split("#")[0].strip()
        if i == 0:
            line = line.split(",")
            color = discord.colour.Color.from_rgb(int(line[0]), int(line[1]), int(line[2]))
        elif i == 1:
            AppleBot = int(line)
        elif i == 2:
            test_AppleBot = int(line)
        elif i == 3:
            login = line
        elif i == 4:
            test_login = line
        elif i == 5:
            begin_channel = int(line)
        elif i == 6:
            debug_person = int(line)
        elif i == 7:
            respects = int(line)
        else:
            break
        i += 1


async def start(message):
    '''
    The code to keep everything restarting if somefin goes wrong
    :param message: the !begin message for some reason
    :return: never
    '''
    while True:
        try:
            if not begun[0]:
                begun[0] = True
                await on_command_read_lists()
                await on_command_begin()
            else:
                break
        except DisconnectException:
            while True:
                try:
                    await client.get_channel(respects).send("Disconnected from the internet")
                except client_exceptions.ClientOSError:
                    await asyncio.sleep(2)
                    continue
                break
        except MemoryError:
            print("ME")
        except:
            try:
                await client.get_channel(respects).send("F")
            except client_exceptions.ClientOSError:
                pass

            def send_trace():
                string = traceback.format_exc()
                traceback.print_exc()
                msgs = list()
                while True:
                    if len(string) < 1998:
                        msgs.append(string)
                        break
                    else:
                        msgs.append(str(string[:1998]))
                        string = string[1997:]
                for i in msgs:
                    try:
                        await client.get_user(debug_person).send(i)
                    except client_exceptions.ClientOSError:
                        await asyncio.sleep(1)
                        continue

            send_trace()
            await asyncio.sleep(5)
            on_command_write_lists()
            for j in range(2):
                def del_messages():
                    for cl in chart_messages:
                        for list_name in list(chart_messages[cl].keys()):
                            try:
                                await chart_messages[cl][list_name][0].channel.delete_messages(
                                    [chart_messages[cl][list_name][0]])
                            except client_exceptions.ClientOSError:
                                raise DisconnectException
                            except:
                                continue
                        for list_name in list(missing_messages[cl].keys()):
                            try:
                                await missing_messages[cl][list_name][0].channel.delete_messages(
                                    [missing_messages[cl][list_name][0]])
                            except:
                                pass

                del_messages()

            try:
                await client.get_user(debug_person).send("Ended")
            except:
                pass

            await asyncio.sleep(30)

            while True:
                try:
                    chan = client.get_channel(begin_channel)
                    begun[0] = False
                    a = await chan.send("!begin")
                    del a
                except:
                    continue
                break
            break


@client.event
async def on_ready():
    '''
    once logged in, start everything
    :return: nuffin
    '''
    chan = client.get_channel(begin_channel)
    try:
        a = await chan.send("!begin")
        del a
    except client_exceptions.ClientOSError:
        raise DisconnectException
    bot_user[0] = client.get_user(AppleBot)


@client.event
async def on_reaction_add(reaction, user):
    '''
    On a reaction in discord see if it's on one of our messages with pages
    If so, change the page
    :param reaction: the reaction object
    :param user: the user who reacted
    :return:
    '''
    if reaction.count == 1 or reaction.emoji not in ("➡", "⬅"):
        return
    left = True
    if reaction.emoji == "➡":
        left = False

    for cl in clients:
        for list_name in missing_messages[cl]:
            if missing_messages[cl][list_name][0].id == reaction.message.id:
                if left:
                    missing_messages[cl][list_name][1] = max(missing_messages[cl][list_name][1] - 1, 0)

                else:
                    missing_messages[cl][list_name][1] += 1

                terrs_missing = list()
                try:
                    territories_now, guild_count, time_now = territories_cache[1], territories_cache[2], \
                                                             territories_cache[3]
                    for terr in clients[cl][list_name][1]:
                        if terr not in territories_now:
                            continue
                        if territories_now[terr].guild_name != clients[cl][list_name][0]:
                            terrs_missing.append(territories_now[terr])
                    await missing_messages[cl][list_name][0].edit(
                        content=make_message_terrs_missing(terrs_missing, time_now, missing_messages[cl][list_name][1]))
                    if left:
                        await missing_messages[cl][list_name][0].remove_reaction("⬅", user)
                    else:
                        await missing_messages[cl][list_name][0].remove_reaction("➡", user)
                    return

                except client_exceptions.ClientOSError:
                    raise DisconnectException
        else:
            continue
    for cl in clients:
        for list_name in chart_messages[cl]:
            if chart_messages[cl][list_name][0].id == reaction.message.id:
                try:
                    if left:
                        chart_messages[cl][list_name][1] = max(chart_messages[cl][list_name][1] - 1, 0)
                        await chart_messages[cl][list_name][0].remove_reaction("⬅", user)

                    else:
                        chart_messages[cl][list_name][1] += 1
                        await chart_messages[cl][list_name][0].remove_reaction("➡", user)

                    territories_now, a, time_now = territories_cache[1], territories_cache[2], territories_cache[3]
                    await chart_messages[cl][list_name][0].edit(
                        content=make_message(territories_now, cl, list_name, time_now,
                                             chart_messages[cl][list_name][1]))
                except (ConnectionError, client_exceptions.ClientOSError):
                    raise DisconnectException
                finally:
                    return
    for cl in full_missing:
        if full_missing[cl][2].id == reaction.message.id:
            try:
                if left:
                    await full_missing[cl][2].remove_reaction("⬅", user)
                    full_missing[cl][3] = max(full_missing[cl][3] - 1, 0)

                else:
                    await full_missing[cl][2].remove_reaction("➡", user)
                    full_missing[cl][3] += 1

                territories_now, a, time_now = territories_cache[1], territories_cache[2], territories_cache[3]

                terrs_missing = list()
                for terr in full_missing[cl][0]:
                    if terr not in territories_now:
                        continue
                    if territories_now[terr].guild_name not in full_missing[cl][1]:
                        terrs_missing.append(territories_now[terr])

                await full_missing[cl][2].edit(
                    content=make_message_terrs_missing(terrs_missing, time_now, full_missing[cl][3]))
            except (ConnectionError, client_exceptions.ClientOSError):
                raise DisconnectException
            finally:
                return


@client.event
async def on_message(message):
    '''
    on any message sent in the discord I'm in, figure out what command it is if it is one
    :param message: the message sent in discord
    :return:
    '''
    try:
        if not message.content.startswith("!"):
            return
        if message.content.lower().startswith('!begin') and message.author.id == AppleBot:
            await start(message)
        if not begun[0] or message.author.id == AppleBot:
            return
        if message.author.id not in clients:
            await on_new_client(message)
        if message.content.lower().startswith('!list'):
            a = await on_command_list(message)
            del a
        elif message.content.lower().startswith('!full_missing'):
            a = await on_command_full_missing(message)
            del a
        elif message.content.lower().startswith("!info"):
            a = await on_command_info(message)
            del a
        elif message.content.lower().startswith('!help'):
            a = await on_command_help(message)
            del a
        elif message.content.lower().startswith("!start"):
            a = await on_command_start(message)
            del a
        elif message.content.lower().startswith("!remove"):
            a = await on_command_remove(message)
            del a
        elif message.content.lower().startswith("!instructions"):
            a = await on_command_instructions(message)
            del a
        elif message.content.lower().startswith('!write_lists'):
            on_command_write_lists()
        elif message.content.lower().startswith('!read_lists'):
            a = await on_command_read_lists()
            del a
        elif message.content.lower().startswith('!role_reaction'):
            a = await message.channel.send("This is not implemented yet")
            del a
        elif message.content.lower().startswith('!show'):
            a = await on_command_show_stuff(message)
            del a
        elif message.content.lower() == '!end' and message.author.id == debug_person:
            on_command_write_lists()
            for cl in chart_messages:
                for list_name in list(chart_messages[cl].keys()):
                    try:
                        await chart_messages[cl][list_name][0].channel.delete_messages(
                            [chart_messages[cl][list_name][0]])
                    except discord.errors.NotFound:
                        chart_messages[cl].__delitem__(list_name)
                for list_name in list(missing_messages[cl].keys()):
                    try:
                        await missing_messages[cl][list_name][0].channel.delete_messages(
                            [missing_messages[cl][list_name][0]])
                    except discord.errors.NotFound:
                        missing_messages[cl].__delitem__(list_name)
                if full_missing[cl] is not None:
                    try:
                        await full_missing[cl][2].channel.delete_messages([full_missing[cl][2]])
                    except discord.errors.NotFound:
                        full_missing[cl] = None

            await client.get_user(debug_person).send("Ended")
            sys.exit(0)

    except discord.errors.Forbidden:
        pass
    except client_exceptions.ClientOSError:
        raise DisconnectException





async def on_command_instructions(message):
    '''
    send an instructions message to the location of message
    :param message: the message that requested this message
    :return:
    '''
    try:
        a = await message.channel.send("```Each individual has their own set of lists\n\n" +
                                       "1. Create a list with the !list command\n" +
                                       "    + Make an empty list\n" +
                                       "        - !list create <list name> <rightful owner>\n" +
                                       "        - !list (add/remove) <list name> <territory name>\n" +
                                       "    + Make a list from existing ownership of an area\n" +
                                       "        - !list copyterritories <list name> <guild name>\n" +
                                       "        - !list (add/remove) <list name> <territory name>\n" +
                                       "\n" +
                                       "2. Start a feature with the !start command\n" +
                                       "    + Make a single message chart that will update as time goes on\n" +
                                       "        - !start chart <list name>\n" +
                                       "        - !start missing <list name>\n" +
                                       "    + Make a territory exchanges feed for the list\n" +
                                       "        - !start territories <list name>\n" +
                                       "    + Make a mention whenever the list loses a defined number of territories\n" +
                                       "        - !start alert <list name> \@<role name> <threshold (number)>\n" +
                                       "3. Remove a feed (removing the message doesn't work\n" +
                                       "    + !remove (chart/missing/territories/alert/full_missing) <list name>\n```")
        del a
    except client_exceptions.ClientOSError:
        raise DisconnectException


async def on_command_remove(message):
    '''
    remove a chart (but do not delete the message. just makes it not resend)
    :param message: the message that the author sent to delete something
    :return:
    '''
    msg = message.content.split(" ")
    if len(msg) < 2:
        await correct_command_remove(message.channel)
    msg[1] = msg[1].lower()
    if msg[1] == "full_missing":
        full_missing[message.author.id] = None
        try:
            await message.channel.send("full_missing was removed from your charts")
        except client_exceptions.ClientOSError:
            raise DisconnectException
        return
    if len(msg) != 3:
        await correct_command_remove(message.channel)
    if msg[1] == "chart":
        if msg[2] in chart_messages[message.author.id]:
            chart_messages[message.author.id].__delitem__(msg[2])
            try:
                await message.channel.send(msg[2] + " was removed from chart messages.")
            except client_exceptions.ClientOSError:
                raise DisconnectException
        else:
            try:
                await message.channel.send(msg[2] + " is not one of your lists")
            except client_exceptions.ClientOSError:
                raise DisconnectException
    elif msg[1] == "missing":
        if msg[2] in missing_messages[message.author.id]:
            missing_messages[message.author.id].__delitem__(msg[2])
            try:
                await message.channel.send(msg[2] + " was removed from missing messages.")
            except client_exceptions.ClientOSError:
                raise DisconnectException
        else:
            try:
                await message.channel.send(msg[2] + " is not one of your lists")
            except client_exceptions.ClientOSError:
                raise DisconnectException

    elif msg[1] == "territories":
        if msg[2] in terr_channels[message.author.id]:
            terr_channels[message.author.id].__delitem__(msg[2])
            try:
                await message.channel.send(msg[2] + " was removed from territory messages.")
            except client_exceptions.ClientOSError:
                raise DisconnectException
        else:
            try:
                await message.channel.send(msg[2] + " is not one of your lists")
            except client_exceptions.ClientOSError:
                raise DisconnectException
    elif msg[1] == "alert":
        if msg[2] in alert_channels[message.author.id]:
            alert_channels[message.author.id].__delitem__(msg[2])
            try:
                await message.channel.send(msg[2] + " was removed from alert messages.")
            except client_exceptions.ClientOSError:
                raise DisconnectException
        else:
            try:
                await message.channel.send(msg[2] + " is not one of your lists")
            except client_exceptions.ClientOSError:
                raise DisconnectException

    on_command_write_lists()


async def on_command_show_stuff(message):
    '''
    show information about the client's current feeds
    :param message: the message the author just sent
    :return:
    '''
    string = 'chart_messages: '
    for list_name in chart_messages[message.author.id]:
        string += list_name + " in #" + chart_messages[message.author.id][list_name][0].channel.name + " "
    string += '\nmissing_messages: '
    for list_name in missing_messages[message.author.id]:
        string += list_name + " in #" + missing_messages[message.author.id][list_name][0].channel.name + " "
    string += '\nterritories_channels: '
    for list_name in terr_channels[message.author.id]:
        string += list_name + " in #" + terr_channels[message.author.id][list_name].name + " "
    string += '\nalert_channels: '
    for list_name in alert_channels[message.author.id]:
        string += list_name + " in #" + alert_channels[message.author.id][list_name][0].name + " "
    string += '\nfull_missing: '
    if full_missing[message.author.id] is not None:
        string += " in #" + full_missing[message.author.id][2].name
    try:
        await message.channel.send(str(string[:1999]))
    except client_exceptions.ClientOSError:
        raise DisconnectException


async def on_command_start(message):
    '''
    start a feed
    :param message: the message the user just sent
    :return:
    '''
    msg = message.content.split(" ")
    if len(msg) == 1:
        await correct_command_start(message)
        return
    msg[1] = msg[1].lower()
    if msg[1] == "full_missing":
        await on_command_start_full_missing(message)
    elif msg[1] == "territories":
        await on_command_start_tracking_territories(message)
    elif msg[1] == "missing":
        await on_command_start_missing(message)
    elif msg[1] == "chart":
        await on_command_start_chart(message)
    elif msg[1] == "alert":
        await on_command_start_alert(message)
    else:
        await correct_command_start(message.channel)
    try:
        await message.author.send(
            "When using a 'start' command, try to remember to **!remove (missing/chart/territories/alert/full_missing)" +
            " <list_name>** as a courtesy to the bot ^-^ **!show** to see what features you have active")
    except client_exceptions.ClientOSError:
        raise DisconnectException
    on_command_write_lists()


async def on_command_start_full_missing(message):
    '''
    start a full_missing chart in the current channel
    :param message: the message the user just sent
    :return:
    '''
    try:
        m = await message.channel.send("This could take up to 30 seconds to load")
    except client_exceptions.ClientOSError:
        raise DisconnectException
    t_list = list()
    for terr in territories_cache[1]:
        t_list.append(terr)
    full_missing[message.author.id] = [t_list, list(), m, 0, False]


async def on_command_start_missing(message):
    '''
    start a missing chart in the current channel
    :param message: the message the user just sent
    :return:
    '''
    msg = message.content.split(" ")
    if len(msg) != 3:
        await correct_command_start_missing(message.channel)
        return
    if msg[2] not in clients[message.author.id]:
        await is_not_a_list(msg[2], message.channel)
        return
    if message.author.id not in missing_messages:
        missing_messages[message.author.id] = dict()
    missing_messages[message.author.id][msg[2]] = ['msg', 0, False]
    try:
        missing_messages[message.author.id][msg[2]][0] = await message.channel.send(
            "This could take up to 30 seconds to load")
    except client_exceptions.ClientOSError:
        missing_messages[message.author.id].__delitem__(msg[2])
        raise DisconnectException


async def on_command_start_chart(message):
    '''
    start a chart in the current channel
    :param message: the message the user just sent
    :return:
    '''
    msg = message.content.split(" ")
    if len(msg) != 3:
        await correct_command_start_chart(message.channel)
        return
    if message.author.id not in chart_messages:
        chart_messages[message.author.id] = dict()
    if msg[2] not in clients[message.author.id]:
        await is_not_a_list(msg[2], message.channel)
        return
    chart_messages[message.author.id][msg[2]] = ['msg', 0, False]
    try:
        chart_messages[message.author.id][msg[2]][0] = await message.channel.send(
            "This could take up to 30 seconds to load")
    except client_exceptions.ClientOSError:
        chart_messages[message.author.id].__delitem__(msg[2])
        raise DisconnectException


async def on_command_start_alert(message):
    '''
    start an alert feed in the current channel
    :param message: the message the user just sent
    :return:
    '''
    msg = message.content.split(" ")
    if len(msg) != 5:
        if not (len(msg) == 6 and msg[5] == ''):
            await correct_command_start_alert(message.channel)
            return
    if msg[2] not in clients[message.author.id]:
        await is_not_a_list(msg[2], message.channel)
        return
    if str(msg[3][0:4]) != '\\<@&' or msg[3][-1] != '>':
        try:
            await message.channel.send("Did you forget the \\ in \\\\@<role_name>")
        except client_exceptions.ClientOSError:
            raise DisconnectException
        return
    if not msg[4].isdigit():
        try:
            await message.channel.send("not a number")
        except client_exceptions.ClientOSError:
            raise DisconnectException
        return
    alert_channels[message.author.id][msg[2]] = message.channel, msg[3][1:], int(msg[4])
    try:
        await alert_channels[message.author.id][msg[2]][0].send("Alerts for " + msg[2] + " will be sent here")
    except client_exceptions.ClientOSError:
        raise DisconnectException


async def on_command_start_tracking_territories(message):
    '''
    start a tracking territories feed in the current channel
    :param message: the message the user just sent
    :return:
    '''
    msg = message.content.split(" ")
    if len(msg) != 3:
        await correct_command_start_tracking_territories(message.channel)
        return
    if msg[2] not in clients[message.author.id]:
        try:
            await message.channel.send(msg[2] + " is not a list")
        except client_exceptions.ClientOSError:
            raise DisconnectException
        return
    terr_channels[message.author.id][msg[2]] = message.channel
    try:
        await terr_channels[message.author.id][msg[2]].send("territory exchanges will be sent here")

    except client_exceptions.ClientOSError:
        raise DisconnectException


async def on_command_full_missing(message):
    '''
    change parts of the full_missing chart for the current client
    :param message: the message the user just sent
    :return:
    '''
    if full_missing[message.author.id] is None:
        await on_command_start_full_missing(message)
    msg = message.content.split(" ")
    if len(msg) < 4 or msg[1] not in ("guilds", "territories") or msg[2] not in ("add", "remove"):
        await correct_command_full_missing(message.channel)
        return
    if msg[1] == "guilds":
        await on_command_full_missing_guilds(message)
    else:
        await on_command_full_missing_territories(message)
    on_command_write_lists()


async def on_command_full_missing_guilds(message):
    '''
    change guilds of the full_missing chart for the current client
    :param message: the message the user just sent
    :return:
    '''
    msg = message.content.split(" ")

    if msg[2] == "add":
        string = ""
        for a in msg[3:]:
            string += a + " "
        terrs = string.split(",")
        for t in terrs:
            t = t.strip()

            if t in full_missing[message.author.id][1]:
                try:
                    await message.channel.send(t + " is already in your list")
                except client_exceptions.ClientOSError:
                    raise DisconnectException
            else:
                full_missing[message.author.id][1].append(t)
                try:
                    await message.channel.send(t + " added")
                except client_exceptions.ClientOSError:
                    raise DisconnectException
    else:
        string = ""
        for a in msg[3:]:
            string += a + " "
        terrs = string.split(",")
        for t in terrs:
            t = t.strip()

            if t not in full_missing[message.author.id][1]:
                try:
                    await message.channel.send(t + " is not in your list")
                except client_exceptions.ClientOSError:
                    raise DisconnectException
            else:
                full_missing[message.author.id][1].remove(t)
                try:
                    await message.channel.send(t + " removed")
                except client_exceptions.ClientOSError:
                    raise DisconnectException


async def on_command_full_missing_territories(message):
    '''
    change territories of the full_missing chart for the current client
    :param message: the message the user just sent
    :return:
    '''
    msg = message.content.split(" ")
    territories = territories_cache[1]

    if msg[2] == "add":
        string = ""
        for a in msg[3:]:
            string += a + " "
        terrs = string.split(",")
        for t in terrs:
            t = t.strip()

            if t in full_missing[message.author.id][0]:
                try:
                    await message.channel.send(t + " is already in your list")
                except client_exceptions.ClientOSError:
                    raise DisconnectException
            elif t not in territories:
                try:
                    await message.channel.send(t + " is not a territory")
                except client_exceptions.ClientOSError:
                    raise DisconnectException
            else:
                full_missing[message.author.id][0].append(t)
                try:
                    await message.channel.send(t + " added")
                except client_exceptions.ClientOSError:
                    raise DisconnectException
    else:
        string = ""
        for a in msg[3:]:
            string += a + " "
        terrs = string.split(",")
        for t in terrs:
            t = t.strip()

            if t not in full_missing[message.author.id][0]:
                try:
                    await message.channel.send(t + " is not in your list")
                except client_exceptions.ClientOSError:
                    raise DisconnectException
            else:
                full_missing[message.author.id][0].remove(t)
                try:
                    await message.channel.send(t + " removed")
                except client_exceptions.ClientOSError:
                    raise DisconnectException


async def on_command_list(message):
    '''
    change parts of one of the current client's lists
    :param message: the message the user just sent
    :return:
    '''
    try:
        territories = territories_cache[1]
    except ConnectionError:
        try:
            await message.channel.send("An error occurred retrieving the terrritories. Try again soon.")
        except client_exceptions.ClientOSError:
            raise DisconnectException
        return
    msg = message.content.split(" ")

    if len(msg) > 1:
        if msg[1].lower() == "show":
            for lst in clients[message.author.id]:
                string = '***' + lst + ':***\n'
                for terr in clients[message.author.id][lst][1]:
                    string += terr + '\n'

                try:
                    await message.channel.send(embed=discord.Embed(color=color, description=string))
                except client_exceptions.ClientOSError:
                    raise DisconnectException

            return
    else:
        await correct_command_list(message.channel)
        return
    msg[1] = msg[1].lower()

    if msg[1] == "add":
        if len(msg) < 4:
            await correct_command_list_add(message.channel)
            return
        if msg[2] not in clients[message.author.id]:
            try:
                await message.channel.send(msg[2] + " is not one of your lists")
            except client_exceptions.ClientOSError:
                raise DisconnectException
            return
        string = ''
        for i in msg[3:]:
            string += " "
            for j in i:
                if j != '\\':
                    string += j
        string = string.strip()

        for i in string.split(","):
            if i.strip() not in territories:
                try:
                    await message.channel.send(i.strip() + " is not a territory")
                except client_exceptions.ClientOSError:
                    raise DisconnectException
            else:
                if i.strip() in clients[message.author.id][msg[2]][1]:
                    try:
                        await message.channel.send(i.strip() + " is already in your list")
                    except client_exceptions.ClientOSError:
                        raise DisconnectException
                    continue
                clients[message.author.id][msg[2]][1].append(i.strip())
                try:
                    await message.channel.send("added " + i.strip())
                except client_exceptions.ClientOSError:
                    raise DisconnectException
    elif msg[1] == "remove":
        if len(msg) < 3:
            await correct_command_list_remove(message.channel)
            return
        if msg[2] not in clients[message.author.id]:
            try:
                await message.channel.send(msg[2] + " is not one of your lists")
            except client_exceptions.ClientOSError:
                raise DisconnectException
            return
        if len(msg) == 3:
            clients[message.author.id].__delitem__(msg[2])
            if msg[2] in chart_messages[message.author.id]:
                chart_messages[message.author.id].__delitem__(msg[2])
            if msg[2] in missing_messages[message.author.id]:
                missing_messages[message.author.id].__delitem__(msg[2])
            if msg[2] in terr_channels[message.author.id]:
                terr_channels[message.author.id].__delitem__(msg[2])
            if msg[2] in alert_channels[message.author.id]:
                alert_channels[message.author.id].__delitem__(msg[2])
            if msg[2] in full_missing[message.author.id]:
                full_missing[message.author.id].__delitem__(msg[2])
            try:
                await message.channel.send(msg[2] + " was removed from your lists")
            except client_exceptions.ClientOSError:
                raise DisconnectException
            return
        if len(msg) < 4:
            await correct_command_list_remove(message.channel)
            return
        string = ''
        for i in msg[3:]:
            string += " "
            for j in i:
                if j != '\\':
                    string += j
        string = string.strip()
        for i in string.split(","):
            if i.strip() not in clients[message.author.id][msg[2]][1]:
                try:
                    await message.channel.send(i.strip() + " is not a territory")
                except client_exceptions.ClientOSError:
                    raise DisconnectException
            else:
                clients[message.author.id][msg[2]][1].remove(i.strip())
                try:
                    await message.channel.send("removed " + i.strip())
                except client_exceptions.ClientOSError:
                    raise DisconnectException
    elif msg[1] == "create":
        if len(msg) != 4:
            try:
                await correct_command_list_create(message.channel)
            except client_exceptions.ClientOSError:
                raise DisconnectException
            return
        clients[message.author.id][msg[2]] = [msg[3], [], True]
        try:
            await message.channel.send(msg[2] + " list created")
        except client_exceptions.ClientOSError:
            raise DisconnectException
    elif msg[1] == "copyterritories":
        if len(msg) < 4:
            await correct_command_list_copyterritories(message.channel)
            return
        try:
            territories, guild_count, time_now = territories_cache[1], territories_cache[2], territories_cache[3]
        except ConnectionError:
            await message.channel.send("Failed. Try again.")
            return
        string = ''
        for i in msg[3:]:
            string += " " + i
        string = string.strip()
        msg[3] = string
        if msg[3] not in guild_count:
            try:
                await message.channel.send("Guild " + msg[2] + " not found or does not have territories")
            except client_exceptions.ClientOSError:
                raise DisconnectException
            return
        clients[message.author.id][msg[2]] = [msg[3], [], True]
        for terr in territories:
            if territories[terr].guild_name == msg[3]:
                clients[message.author.id][msg[2]][1].append(terr)

        string = '***' + msg[3] + ':***\n'
        for terr in clients[message.author.id][msg[2]][1]:
            string += '- ' + terr + '\n'
        string = string[:1999]
        try:
            await message.channel.send(embed=discord.Embed(color=color, description=string))
        except client_exceptions.ClientOSError:
            raise DisconnectException
    else:
        await correct_command_list(message.channel)
    on_command_write_lists()


async def on_command_read_lists():
    '''
    update current lists and charts from the text file
    :return:
    '''
    keys = list(clients.keys())
    for lst in keys:
        clients.__delitem__(lst)
    keys = list(chart_messages.keys())
    for lst in keys:
        chart_messages.__delitem__(lst)
    keys = list(missing_messages.keys())
    for lst in keys:
        missing_messages.__delitem__(lst)
    keys = list(terr_channels.keys())
    for lst in keys:
        terr_channels.__delitem__(lst)
    keys = list(alert_channels.keys())
    for lst in keys:
        alert_channels.__delitem__(lst)
    keys = list(full_missing.keys())
    for lst in keys:
        full_missing.__delitem__(lst)

    at_messages = 0
    clnt = 0
    with open("data.txt") as file:
        for line in file:
            line = line.strip()
            if line == "message":
                at_messages = 1
                continue
            if at_messages == 0:
                if line.isdigit():
                    clnt = int(line)
                    clients[clnt] = dict()

                else:
                    line = line.split(":")
                    clients[clnt][line[0]] = [line[1], list(), bool(line[2])]
                    for l in line[3].split(','):
                        if l != '':
                            if "'" in l:
                                a = ''
                                for i in l:
                                    a += i
                                    # TODO
                                l = a
                            clients[clnt][line[0]][1].append(l)
            elif at_messages == 4:

                line = line.split(":")
                part = 0
                chans = dict()
                while part + 1 < len(line):
                    c = line[part + 1].split(",")
                    if len(c) == 1:
                        alert_channels[int(line[part])] = dict()
                        part += 2
                        continue
                    for i in range(len(c)):
                        if c[i] == '':
                            alert_channels[int(line[part])] = dict()
                            continue
                        dis = c[i].split(".")
                        b = dis[1].split("-")
                        chans[dis[0]] = (int(b[0]), b[1], int(b[2]))
                    if line[part] == '':
                        part += 2
                        continue
                    alert_channels[int(line[part])] = chans
                    chans = dict()
                    part += 2
                at_messages += 1

            elif at_messages == 5:
                line = line.split(":")
                for l in line:
                    if l == '':
                        pass
                    elif l.isdigit():
                        full_missing[int(l)] = None
                    else:
                        l = l.split(",")
                        cl_name = int(l[0])
                        if l[1] == 'N':
                            full_missing[cl_name] = None
                            continue
                        terrs = l[1].split(".")
                        if '' in terrs:
                            terrs.remove('')
                        guilds = l[2].split(".")
                        if '' in guilds:
                            guilds.remove('')
                        channel = int(l[3])
                        try:
                            m = await client.get_channel(channel).send("This could take up to 30 seconds to load")
                        except discord.errors.NotFound:
                            full_missing[cl_name] = None
                            continue
                        except discord.errors.Forbidden:
                            full_missing[cl_name] = None
                            continue
                        except client_exceptions.ClientOSError:
                            raise DisconnectException

                        full_missing[cl_name] = [terrs, guilds, m, 0, False]

            else:
                line = line.split(":")
                part = 0
                chans = dict()
                while part + 1 < len(line):
                    c = line[part + 1].split(",")
                    if len(c) == 1:

                        if at_messages == 1:
                            chart_messages[int(line[part])] = dict()
                        elif at_messages == 2:
                            missing_messages[int(line[part])] = dict()
                        elif at_messages == 3:
                            terr_channels[int(line[part])] = dict()
                        elif at_messages == 5:
                            full_missing[int(line[part])] = None
                        part += 2
                        continue
                    for i in range(len(c)):
                        if c[i] == '':
                            if at_messages == 1:
                                chart_messages[int(line[part])] = dict()
                            elif at_messages == 2:
                                missing_messages[int(line[part])] = dict()
                            elif at_messages == 3:
                                terr_channels[int(line[part])] = dict()
                            elif at_messages == 5:
                                full_missing[int(line[part])] = None
                            continue
                        dis = c[i].split(".")
                        chans[dis[0]] = dis[1]
                    if line[part] == '':
                        part += 2
                        continue
                    if at_messages == 1:
                        chart_messages[int(line[part])] = chans
                    elif at_messages == 2:
                        missing_messages[int(line[part])] = chans
                    elif at_messages == 3:
                        terr_channels[int(line[part])] = chans
                    elif at_messages == 5:
                        full_missing[int(line[part])] = chans
                    chans = dict()
                    part += 2
                at_messages += 1

    for cl in chart_messages:
        for list_name in list(chart_messages[cl].keys()):
            while True:
                try:
                    chart_messages[cl][list_name] = [await client.get_channel(int(chart_messages[cl][list_name])).send(
                        "This could take up to 30 seconds to load"), 0, False]

                except AttributeError:
                    chart_messages[cl].__delitem__(list_name)

                except discord.errors.NotFound:
                    continue
                except discord.errors.Forbidden:
                    continue
                except client_exceptions.ClientOSError:
                    await asyncio.sleep(2)
                    continue
                break
        for list_name in missing_messages[cl]:
            while True:
                try:
                    missing_messages[cl][list_name] = [
                        await client.get_channel(int(missing_messages[cl][list_name])).send(
                            "This could take up to 30 seconds to load"), 0, False]
                except AttributeError:
                    chart_messages[cl].__delitem__(list_name)
                except discord.errors.NotFound:
                    continue
                except discord.errors.Forbidden:
                    continue
                except client_exceptions.ClientOSError:
                    await asyncio.sleep(2)
                    continue
                break

        for list_name in terr_channels[cl]:
            terr_channels[cl][list_name] = client.get_channel(int(terr_channels[cl][list_name]))
        for list_name in alert_channels[cl]:
            alert_channels[cl][list_name] = [client.get_channel(int(alert_channels[cl][list_name][0])),
                                             alert_channels[cl][list_name][1], alert_channels[cl][list_name][2]]


def on_command_write_lists():
    '''
    write the current lists and charts to the text file to be read later
    :return:
    '''
    try:
        string = ''
        for c in clients:
            string += str(c)
            for lst in clients[c]:
                string += ('\n')
                string += (lst + ":")
                string += (clients[c][lst][0] + ":")
                string += (str(clients[c][lst][2]) + ":")

                for terr in clients[c][lst][1]:
                    string += (terr + ",")
            string += ('\n')
        string += ("message\n")
        for c in chart_messages:
            string += (str(c) + ":")
            for list_name in chart_messages[c]:
                string += (list_name + "." + str(chart_messages[c][list_name][0].channel.id) + ",")
            string += (":")
        string += ('\n')

        for c in missing_messages:
            string += (str(c) + ":")
            for list_name in missing_messages[c]:
                string += (list_name + "." + str(missing_messages[c][list_name][0].channel.id) + ",")
            string += (":")
        string += ('\n')
        for c in terr_channels:
            string += (str(c) + ":")
            for list_name in terr_channels[c]:
                string += (list_name + "." + str(terr_channels[c][list_name].id) + ",")
            string += (":")
        string += ('\n')
        for c in alert_channels:
            string += (str(c) + ":")
            for list_name in alert_channels[c]:
                try:
                    string += (list_name + "." + str(alert_channels[c][list_name][0].id) + '-' + str(
                        alert_channels[c][list_name][1]) + "-" + str(alert_channels[c][list_name][2]) + ",")
                except IndexError:
                    pass
            string += (":")
        string += ('\n')
        for c in full_missing:
            string += (str(c) + ",")
            if full_missing[c] is None:
                string += "N"
            else:
                for terr in full_missing[c][0]:
                    string += terr
                    string += '.'
                string += ','
                for guild_name in full_missing[c][1]:
                    string += guild_name
                    string += '.'
                string += ','
                string += str(full_missing[c][2].channel.id)

            string += (":")
        string += ('\n')
        with open("data.txt", 'w') as file:
            file.write(string)
    except IOError:
        on_command_write_lists()
        print("IOERROR WRITING LISTS!")


async def on_command_info(message):
    '''
    sends some info about the bot to the user in the current channel
    :param message: the message the user just sent
    :return:
    '''
    try:
        await message.channel.send(embed=discord.Embed(
            color=color, description="__**AppleBot:**__\n" +
                                     "**Author:** appleptr16#5054\n" +
                                     "**AppleBot's discord:** https://discord.gg/XEyUWu9\n" +
                                     "Some commands are inspired by moto-bot\n" +
                                     "Another bot that I found out about after I finished AppleBot\n" +
                                     " (similar to my bot) is HydroBot: https://discord.gg/6p2m7An\n" +
                                     "**Release version:** 1.2\n" +
                                     "**Testing status:** Alpha (expect bugs)\n" +
                                     "**Server count:** " + str(len(client.guilds)) + '\n' +
                                     "**bot invite below**\n" +
                                     "https://bit.ly/31liFdF"))
    except client_exceptions.ClientOSError:
        raise DisconnectException
    except discord.errors.Forbidden:
        pass


async def on_command_begin():
    '''
    start a round of the bot working
    shouldnt ever throw an error, but bugs
    :return:
    '''
    chan = client.get_channel(607750451731103754)
    while True:
        try:
            await chan.send("begun")
        except client_exceptions.ClientOSError:
            await asyncio.sleep(2)
            continue
        break
    past = time.time()
    now = 0
    g = 1
    try:
        territories_cache[0], territories_cache[2], territories_cache[3] = fetch_territories()
    except urllib.error.HTTPError:
        again = True
        while True:
            if not again:
                break
            again = False
            await asyncio.sleep(100)
            try:
                urllib.request.urlopen('https://api.wynncraft.com/public_api.php?action=territoryList').readline()
            except:
                again = True
    except ConnectionError:
        raise DisconnectException

    while True:
        try:
            territories_cache[1], territories_cache[2], territories_cache[3] = fetch_territories()
        except urllib.error.HTTPError:
            again = True
            while True:
                if not again:
                    break
                again = False
                await asyncio.sleep(100)
                try:
                    urllib.request.urlopen('https://api.wynncraft.com/public_api.php?action=territoryList').readline()
                except:
                    again = True
        except ConnectionError:
            raise DisconnectException

        for cl in list(clients.keys()):
            if full_missing[cl] is not None:
                try:
                    await run_full_missing(cl, territories_cache[1], territories_cache[3])
                except KeyError:
                    pass
            for list_name in list(clients[cl].keys()):
                try:
                    await run(cl, list_name, territories_cache[1], territories_cache[0], territories_cache[2],
                              territories_cache[3])
                except KeyError:
                    pass
        territories_cache[0] = territories_cache[1]

        del now
        if g % 5 == 0:
            gc.collect()
            if g > 20:
                del g
                g = 1

        now = time.time()
        await asyncio.sleep(max(5, 30 - int(now - past)))
        del past
        past = time.time()


async def on_command_help(message):
    '''
    sends a list of commands to the user in the current channel
    :param message: the message the user just sent
    :return:
    '''
    try:
        await message.channel.send(embed=discord.Embed(
            color=color,
            description='**!help** - Shows a list of commands\n' +
                        '**!info** - Shows basic information on AppleBot\n' +
                        '**!instructions** - Gives some instructions for how to use the bot\n'
                        '\n' +
                        '**!list create <list name> <rightful owner>** - Creates an empty list\n' +
                        '**!list copyterritories <list name> <guild name>** - Creates a list and adds all territories owned by a guild to the list\n' +
                        '**!list (add/remove) <list name> <territory name>** - Adds/removes a single specific territory to/from a list\n' +
                        '\n' +
                        '**!start chart <list name>** - Creates an updating table that shows territories on a list and what guild owns them\n' +
                        '**!start missing <list name>** - Creates an updating table that shows territories that are not owned by the guild that owns the list\n' +
                        '**!start territories <list name>** - Creates a continuous feed of war activity in territories on a list\n' +
                        '**!start alert <list name> <\\ \\@role name> <threshold #>** - Pings a specific role when a territory from a list has been taken from the guild that owns said list\n' +
                        'threshold # is the amount of territories you\'re allowed to lose before being pinged\n' +
                        '\n' +
                        "**!start full_missing** - starts your full_missing chart in the message's channel\n" +
                        "**!full_missing guilds (add/remove) <guild_name>** - add or remove guilds to the full_missing chart\n" +
                        "**!full_missing territories (add/remove) <territory_name>** - add or remove territories to the full_missing chart"
                        '\n' +
                        '**!remove (chart/missing/territories/alert) <list name>** - removes the feed from the list name (use this instead of deleting the message)\n'

        ))
    except client_exceptions.ClientOSError:
        raise DisconnectException


async def on_new_client(message):
    '''
    a new client sent an command and is registered with empty lists and charts
    :param message: the message the user just sent
    :return:
    '''
    if message.author.id in clients:
        return
    clients[message.author.id] = dict()
    chart_messages[message.author.id] = dict()
    missing_messages[message.author.id] = dict()
    terr_channels[message.author.id] = dict()
    alert_channels[message.author.id] = dict()
    full_missing[message.author.id] = None
    on_command_write_lists()


async def correct_command_list_remove(channel):
    '''
    sends a correct usage of the !list remove command
    :param channel: the channel to send the message to
    :return:
    '''
    try:
        a = await channel.send("!list remove <list name> territory,territory...")
        del a
    except client_exceptions.ClientOSError:
        raise DisconnectException


async def correct_command_list_add(channel):
    '''
    sends a correct usage of the !list add command
    :param channel: the channel to send the message to
    :return:
    '''
    try:
        a = await channel.send("!list add <list name> territory,territory...")
        del a
    except client_exceptions.ClientOSError:
        raise DisconnectException


async def correct_command_list_copyterritories(channel):
    '''
    sends a correct usage of the !list copyterritories command
    :param channel: the channel to send the message to
    :return:
    '''
    try:
        a = await channel.send("!list copyterritories <list name> <guild name>")
        del a
    except client_exceptions.ClientOSError:
        raise DisconnectException


async def correct_command_list_create(channel):
    '''
    sends a correct usage of the !list create command
    :param channel: the channel to send the message to
    :return:
    '''
    try:
        a = await channel.send("!list create <list name> <rightful owner of terrs>")
        del a
    except client_exceptions.ClientOSError:
        raise DisconnectException


async def correct_command_list(channel):
    '''
    sends a correct usage of the  !list command
    :param channel: the channel to send the message to
    :return:
    '''
    try:
        a = await channel.send("!list (create/copyterritories/add/remove)")
        del a
    except client_exceptions.ClientOSError:
        raise DisconnectException


async def correct_command_full_missing(channel):
    '''
    sends a correct usage of the !full_missing command
    :param channel: the channel to send the message to
    :return:
    '''
    try:
        a = await channel.send("!full_missing (guilds/territories) (add/remove) <territory/guild name>")
        del a
    except client_exceptions.ClientOSError:
        raise DisconnectException


async def correct_command_start(channel):
    '''
    sends a correct usage of the !start command
    :param channel: the channel to send the message to
    :return:
    '''
    try:
        a = await channel.send("!start (chart/missing/territories/alert/full_missing)")
        del a
    except client_exceptions.ClientOSError:
        raise DisconnectException


async def correct_command_remove(channel):
    '''
    sends a correct usage of the !remove command
    :param channel: the channel to send the message to
    :return:
    '''
    try:
        a = await channel.send("!remove (chart/missing/territories/alert) <list name>")
        del a
    except client_exceptions.ClientOSError:
        raise DisconnectException


async def correct_command_start_tracking_territories(channel):
    '''
    sends a correct usage of the !start territories command
    :param channel: the channel to send the message to
    :return:
    '''
    try:
        a = await channel.send("!start territories <list name>")
        del a
    except client_exceptions.ClientOSError:
        raise DisconnectException


async def correct_command_start_missing(channel):
    '''
    sends a correct usage of the !start missing command
    :param channel: the channel to send the message to
    :return:
    '''
    try:
        a = await channel.send("!start missing <list name>")
        del a
    except client_exceptions.ClientOSError:
        raise DisconnectException


async def correct_command_start_chart(channel):
    '''
    sends a correct usage of the !start chart command
    :param channel: the channel to send the message to
    :return:
    '''
    try:
        a = await channel.send("!start chart <list name>")
        del a
    except client_exceptions.ClientOSError:
        raise DisconnectException


async def correct_command_start_alert(channel):
    '''
    sends a correct usage of the !start alert command
    :param channel: the channel to send the message to
    :return:
    '''
    try:
        a = await channel.send("!start alert <list name> <\\\\@role name> <threshold>")
        del a
    except client_exceptions.ClientOSError:
        raise DisconnectException




async def is_not_a_list(list_name, chan):
    '''
    tells the user that list_name is not one of thier lists
    :param list_name: the list name they are trying to use
    :param chan: the channel to send the message to
    :return:
    '''
    try:
        a = await chan.send(list_name + " is not a list")
        del a
    except client_exceptions.ClientOSError:
        raise DisconnectException


def fetch_territories():
    '''
    gets all the territories from the wynncraft API
    :return: (dict(Terrritory)) territories, (String) currentTime
    '''
    while True:
        try:
            file = list(
                urllib.request.urlopen('https://api.wynncraft.com/public_api.php?action=territoryList').readline())[
                   16:-1]
        except ConnectionError:
            asyncio.sleep(5)
            continue
        break
    guild_territories = dict()

    for i in range(len(file)):
        file[i] = chr(file[i])
    i = 0

    territories = dict()

    def read_string(at):
        '''
        reads a word inside '""'
        :param at: current index
        :return: the new index, the word
        '''
        at += 2
        string = ''
        while file[at] != "\"":
            if file[at] == 'â':
                string += "'"
                at += 1
                continue
            if file[at] not in ("\\", "\x80", "\x99"):
                string += file[at]
            at += 1
            if file[at] in ("\x80", "\x99"):
                a = 3

        return at, string

    done = False
    while not done:
        # continue until open bracket
        if file[i] == "{":
            # in a territory
            for a in "\"territory\":":
                i += 1
                if file[i] != a:
                    raise IndexError

            i, territory_name = read_string(i)
            for a in ",\"guild\":":
                i += 1
                if file[i] != a:
                    raise IndexError

            i, guild_name = read_string(i)
            for a in ",\"acquired\":":
                i += 1
                if file[i] != a:
                    raise IndexError
            i, aquired = read_string(i)
            for a in ",\"attacker\":":
                i += 1
                if file[i] != a:
                    raise IndexError
            if file[i + 1] == "n":
                attacker_name = "null"
                i += 6
            else:
                i, attacker_name = read_string(i)
            i -= 1
            skip = False
            for a in "\"location\":{":
                i += 1
                if file[i] != a:
                    skip = True
                    break
                # skip location
            if not skip:
                while file[i] != "}":
                    i += 1
            skip = True
            for a in "},":
                i += 1
                if file[i] != a:
                    i -= 1
                    skip = False
                    break
            if not skip:
                if file[i] == '}':
                    i += 1
                    done = True
            territories[territory_name] = Territory(guild_name, aquired, attacker_name, territory_name)
            if guild_name in guild_territories:
                guild_territories[guild_name] += 1
            else:
                guild_territories[guild_name] = 1
        else:
            i += 1

    for a in ',"request":{"timestamp":':
        i += 1
        if file[i] != a:
            if file[i + 1] == a:
                i += 1
                continue
            if file[i - 1] == a:
                i -= 1
                continue
            raise IndexError
    i += 1

    epoch = ''
    while file[i].isdigit():
        epoch += file[i]
        i += 1
    time_now = time.gmtime(int(epoch))
    time_now = str(time_now.tm_year) + '-' + '{:02}'.format(time_now.tm_mon) + '-' + '{:02}'.format(
        time_now.tm_mday) + ' ' + '{:02}'.format(
        time_now.tm_hour) + ':' + '{:02}'.format(time_now.tm_min) + ':' + '{:02}'.format(time_now.tm_sec)
    return territories, guild_territories, time_now


async def run_full_missing(author_id, territories_now, time_now):
    '''
    update the full_missing chart of the current client
    :param author_id: the client's id
    :param territories_now: the current list of Territory
    :param time_now: the current time
    :return:
    '''
    terrs_missing = list()
    for terr in full_missing[author_id][0]:
        if terr not in territories_now:
            continue
        if territories_now[terr].guild_name not in full_missing[author_id][1]:
            terrs_missing.append(territories_now[terr])
    try:
        await full_missing[author_id][2].edit(
            content=make_message_terrs_missing(terrs_missing, time_now, full_missing[author_id][3]))
        if len(terrs_missing) > 19 and not full_missing[author_id][4]:
            full_missing[author_id][4] = True
            await full_missing[author_id][2].add_reaction('⬅')
            await full_missing[author_id][2].add_reaction('➡')
        elif len(terrs_missing) < 20 and full_missing[author_id][4]:
            full_missing[author_id][4] = False
            await full_missing[author_id][2].remove_reaction('⬅', bot_user[0])
            await full_missing[author_id][2].remove_reaction('➡', bot_user[0])

    except client_exceptions.ClientOSError:
        raise DisconnectException
    except discord.errors.NotFound:
        try:
            full_missing[author_id][2] = await full_missing[author_id][
                2].channel.send(
                make_message_terrs_missing(terrs_missing, time_now, full_missing[author_id][3]))
            if len(full_missing) > 19:
                full_missing[author_id][4] = True
                full_missing[author_id][2].add_reaction('⬅')
                full_missing[author_id][2].add_reaction('➡')
            else:
                full_missing[author_id][4] = False
        except client_exceptions.ClientOSError:
            raise DisconnectException
        except discord.errors.NotFound:
            full_missing[author_id] = None
        except discord.errors.Forbidden:
            full_missing[author_id] = None


async def run(author_id, list_name, territories_now, territories_past, guild_count, time_now):
    '''
    run and see if any updates need to happen the current feeds for the current list
    :param author_id: the current client's id
    :param list_name: the current list name we are checking
    :param territories_now: the current list of Territory
    :param territories_past: the list of Territory in the last 30 seconds
    :param guild_count: the list of guilds and thier number of territories
    :param time_now: the current time
    :return:
    '''
    terrs_missing = list()
    for terr in clients[author_id][list_name][1]:
        if terr not in territories_past or terr not in territories_now:
            continue
        if territories_now[terr].guild_name != clients[author_id][list_name][0]:
            terrs_missing.append(territories_now[terr])
        # terr tracker
        if territories_past[terr].guild_name != territories_now[terr].guild_name:
            if list_name in list(terr_channels[author_id].keys()):

                num1 = 0
                num2 = 0
                if territories_past[terr].guild_name in guild_count:
                    num1 = guild_count[territories_past[terr].guild_name]
                if territories_now[terr].guild_name in guild_count:
                    num2 = guild_count[territories_now[terr].guild_name]
                if territories_now[terr].guild_name == clients[author_id][list_name][0]:
                    c = discord.Color.green()
                elif territories_past[terr].guild_name == clients[author_id][list_name][0]:
                    c = discord.Color.red()
                else:
                    c = discord.Color.orange()
                try:
                    await terr_channels[author_id][list_name].send(embed=discord.Embed(color=c, description=
                    terr + ": " + territories_past[terr].guild_name + " (" + str(num1) + ") → **" + territories_now[
                        terr].guild_name + "**(" + str(num2) + ")"))
                except client_exceptions.ClientOSError:
                    raise DisconnectException
                except discord.errors.NotFound:
                    terr_channels[author_id].__delitem__(list_name)
                except discord.errors.Forbidden:
                    terr_channels[author_id].__delitem__(list_name)

    if len(terrs_missing) == 0:
        clients[author_id][list_name][2] = True
    else:
        if clients[author_id][list_name][2]:
            if list_name in alert_channels[author_id] and len(terrs_missing) > alert_channels[author_id][list_name][2]:
                clients[author_id][list_name][2] = False
                try:
                    message = await alert_channels[author_id][list_name][0].send(
                        str(alert_channels[author_id][list_name][1]) + ", " + clients[author_id][list_name][0]
                        + " is in danger!")

                    await message.channel.delete_messages([message])
                except client_exceptions.ClientOSError:
                    raise DisconnectException
                except discord.errors.NotFound:
                    terr_channels[author_id].__delitem__(list_name)
                except discord.errors.Forbidden:
                    terr_channels[author_id].__delitem__(list_name)

    if list_name in missing_messages[author_id]:
        try:
            await missing_messages[author_id][list_name][0].edit(
                content=make_message_terrs_missing(terrs_missing, time_now, missing_messages[author_id][list_name][1]))
            if len(terrs_missing) > 19 and not missing_messages[author_id][list_name][2]:
                missing_messages[author_id][list_name][2] = True
                await missing_messages[author_id][list_name][0].add_reaction('⬅')
                await missing_messages[author_id][list_name][0].add_reaction('➡')
            elif len(terrs_missing) < 20 and missing_messages[author_id][list_name][2]:
                missing_messages[author_id][list_name][2] = False
                await missing_messages[author_id][list_name][0].remove_reaction('⬅', bot_user[0])
                await missing_messages[author_id][list_name][0].remove_reaction('➡', bot_user[0])

        except client_exceptions.ClientOSError:
            raise DisconnectException
        except discord.errors.NotFound:
            try:
                missing_messages[author_id][list_name][0] = await missing_messages[author_id][list_name][
                    0].channel.send(
                    make_message_terrs_missing(terrs_missing, time_now, missing_messages[author_id][list_name][1]))
                if len(terrs_missing) > 19:
                    missing_messages[author_id][list_name][2] = True
                    missing_messages[author_id][list_name][0].add_reaction('⬅')
                    missing_messages[author_id][list_name][0].add_reaction('➡')
                else:
                    missing_messages[author_id][list_name][2] = False
            except client_exceptions.ClientOSError:
                raise DisconnectException
            except discord.errors.NotFound:
                missing_messages[author_id].__delitem__(list_name)
            except discord.errors.Forbidden:
                missing_messages[author_id].__delitem__(list_name)
    if list_name in chart_messages[author_id]:
        try:
            await chart_messages[author_id][list_name][0].edit(
                content=make_message(territories_now, author_id, list_name, time_now,
                                     chart_messages[author_id][list_name][1]))
            if len(clients[author_id][list_name][1]) > 19 and not chart_messages[author_id][list_name][2]:
                chart_messages[author_id][list_name][2] = True
                try:
                    await chart_messages[author_id][list_name][0].add_reaction('⬅')
                    await chart_messages[author_id][list_name][0].add_reaction('➡')
                except discord.errors.Forbidden:
                    chart_messages[author_id].__delitem__(list_name)
            elif len(clients[author_id][list_name][1]) < 20 and chart_messages[author_id][list_name][2]:
                chart_messages[author_id][list_name][2] = False
                try:
                    await chart_messages[author_id][list_name][0].remove_reaction('⬅', bot_user[0])
                    await chart_messages[author_id][list_name][0].remove_reaction('➡', bot_user[0])
                except discord.errors.Forbidden:
                    chart_messages[author_id].__delitem__(list_name)
        except client_exceptions.ClientOSError:
            raise DisconnectException
        except discord.errors.NotFound:
            try:
                chart_messages[author_id][list_name][0] = await chart_messages[author_id][list_name][0].channel.send(
                    make_message(territories_now, author_id, list_name, time_now,
                                 chart_messages[author_id][list_name][1]))
                if len(clients[author_id][list_name][1]) > 19:
                    chart_messages[author_id][list_name][2] = True
                    try:
                        chart_messages[author_id][list_name][0].add_reaction('⬅')
                        chart_messages[author_id][list_name][0].add_reaction('➡')
                    except discord.errors.Forbidden:
                        chart_messages[author_id].__delitem__(list_name)
                else:
                    chart_messages[author_id][list_name][2] = False
            except client_exceptions.ClientOSError:
                return
            except discord.errors.NotFound:
                chart_messages[author_id].__delitem__(list_name)
            except discord.errors.Forbidden:
                chart_messages[author_id].__delitem__(list_name)


def make_message_terrs_missing(terrs_missing, time_now, page):
    '''
    make a missing message given the following information
    :param terrs_missing: the terrs the the guild(s) don't own
    :param time_now: the current time
    :param page: the current page of terrs
    :return:
    '''
    if len(terrs_missing) == 0:
        return "No territories missing ^-^\n :white_check_mark:"
    string_message = '```ml\n'
    string_message += '|   ' + "{:<30}".format(
        "Territories Missing (" + str(len(terrs_missing)) + ")") + '|  ' + "{:<23}".format(
        "Owner") + '|  ' + "{:<23}".format("Time Owned") + '|' + '\n'
    string_message += ('+----' + '-' * 29 + '+' + '-' * 25 + '+' + '-' * 25 + '+\n')
    count = 1 + page * 19
    while count > len(terrs_missing):
        count -= 19
    for terr in terrs_missing[count - 1:]:
        if len(terr.territory_name) > 23:
            t = terr.territory_name[:23]
        else:
            t = terr.territory_name
        string_message += "{:<3}".format(str(count) + '.') + " " + "{:<30}".format(t) + '|'
        string_message += '  ' + "{:<23}".format(terr.guild_name) + '|'
        string_message += '  ' + "{:<23}".format(terr.time_owned(time_now)) + '|'
        string_message += '\n'
        count += 1
        if count % 19 == 1:
            break
    string_message += ('-' * 34 + '+' + '-' * 25 + '+' + '-' * 25 + '+\n')
    string_message += '```'
    if len(string_message) > 1958:
        string_message = string_message[:1958] + "\n```Message too long"
    return string_message


def make_message(territories, author_id, list_name, time_now, page):
    '''
    make a chart message of the current list's territories
    :param territories: the current territory list
    :param author_id: the current client's id
    :param list_name: the current list's name
    :param time_now: the current time
    :param page: the current page
    :return:
    '''
    string_message = '```ml\n'
    string_message += '|   ' + "{:<30}".format(
        "Territories (" + str(len(clients[author_id][list_name][1])) + ")") + '|  ' + "{:<23}".format(
        "Owner") + '|  ' + "{:<23}".format(
        "Time Owned") + '|' + '\n'
    string_message += ('+----' + '-' * 29 + '+' + '-' * 25 + '+' + '-' * 25 + '+\n')
    count = 1 + 19 * page
    while count > len(clients[author_id][list_name][1]):
        count -= 19
    for terr in clients[author_id][list_name][1][count - 1:]:
        if len(terr) > 23:
            t = terr[:23]
        else:
            t = terr
        string_message += "{:<3}".format(str(count) + '.') + " " + "{:<30}".format(t) + '|'
        try:
            string_message += '  ' + "{:<23}".format(territories[terr].guild_name) + '|'
            string_message += '  ' + "{:<23}".format(territories[terr].time_owned(time_now)) + '|'
            string_message += '\n'
        except KeyError:
            try:
                string_message += "  " + "{:<23}".format(territories[terr].guild_name) + '|'
                string_message += '  ' + "{:<23}".format(territories[terr].time_owned(time_now)) + '|\n'
            except KeyError:
                string_message += "null\n"
        count += 1
        if count % 19 == 1:
            break
    string_message += ('-' * 34 + '+' + '-' * 25 + '+' + '-' * 25 + '+\n')
    string_message += '```'
    if len(string_message) > 1958:
        string_message = string_message[:1958] + "\n```Message too long"
    return string_message


def destroy_everything():
    '''
    In case of emergency call this message before the call to client_runner() and the information recorded will be deleted
    :return:
    '''
    on_command_write_lists()


class DisconnectException(Exception):
    '''
    Just a custom Exception
    '''
    pass


def client_runner():
    '''
    start the bot
    :return: never
    '''
    while True:
        try:
            client.run(login)
            print("Wow")
            # TODO
        except DisconnectException:
            print("DCed")
        except MemoryError:
            print("ME")
        except Exception as e:
            print(e)
        finally:
            begun[0] = False


if __name__ == "__main__":
    client_runner()
