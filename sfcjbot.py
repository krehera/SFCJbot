import asyncio
from datetime import datetime
import random
from sys import argv
import challonge
import discord
import MySQLdb
from db_wrapper import DB_Wrapper

THIS_PROGRAM, DISCORD_CREDENTIALS, MYSQL_CREDENTIALS, CHALLONGE_CREDENTIALS = argv
client = discord.Client()
NEXT_MARVEL_EVENT_DATE = datetime.date(2017, 11, 4)


@client.event
async def on_message(message):
    """Respond to messages"""
    # don't reply to bots
    if message.author.bot:
        return

    # When's Mahvel?
    if "when's mahvel" in message.content.lower() or "whens mahvel" in message.content.lower() or "when is mahvel" in message.content.lower():
        time_to_marvel = NEXT_MARVEL_EVENT_DATE - datetime.date.today()
        if time_to_marvel.days == 0:
            await client.send_message(message.channel, "IT'S MAHVEL TIME, BAYBEE! https://media.giphy.com/media/ToMjGpmBhHxpWpmtFcs/giphy.gif")
        elif time_to_marvel.days > 0:
            await client.send_message(message.channel, message.author.mention + ", the final Battle for the Stones qualifying tournament takes place at Latin America Finals on November 4th, which is in " + str(time_to_marvel.days) + " days.")
        else:
            await client.send_message(message.channel, "Sorry, " + message.author.mention + ", I don't know when the next Mahvel thing is happening.")
        return

    if any(x.id == client.user.id for x in message.mentions) or message.content.lower().startswith('sfcjbot') or message.content.lower().startswith('@sfcjbot'):
        command = message.content

        # TODO find a good pattern to clean all these commands all these up (including after the next comment)

        if "here" in command.lower():
            await add_new_user_if_needed(message)
            result = await DB_WRAPPER.execute(client, message.author, "UPDATE users SET status='here' WHERE discord_id=%s", (message.author.id,))
            if result is None:
                print(str(datetime.now()) + ": failed to set " + message.author.name + " to here.")
                await client.send_message(message.author, "I was unable to set your status to here. Please ask Chish#2578 to check the logs at time " + datetime.now())
                return
            print(str(datetime.now()) + ": set " + message.author.name + " to here.")
            await client.send_message(message.author, "Your status was changed to 'here.'")
            return

        if "afk" in command.lower() or "away" in command.lower():
            await add_new_user_if_needed(message)
            result = await DB_WRAPPER.execute(client, message.author, "UPDATE users SET status='afk' WHERE discord_id=%s", (message.author.id,))
            if result is None:
                time = str(datetime.now())
                print(time + ": failed to set " + message.author.name + " to away.")
                await client.send_message(message.author, "I was unable to set your status to afk. Please ask Chish#2578 to check the logs at time " + time)
                return
            print(str(datetime.now()) + ": set " + message.author.name + " to afk.")
            await client.send_message(message.author, "Your status was changed to 'afk.'")
            return

        if "help" in command.lower():
            await client.send_message(message.author, "I\'m SFCJbot! I help SFCJ members play their favorite fighting games! Check out https://github.com/krehera/SFCJbot for documentation.")
            return

        if "about" in command.lower():
            await client.send_message(message.author, "SFCJbot is running on a Raspberry Pi and is powered by the following technologies:\nRaspbian GNU/Linux 8 (jessie)\nPython 3.5\nDiscord.py\nMySQL and MySQLdb\npychallonge")
            return

        if "set_fightcade" in command.lower() or "set fightcade" in command.lower() or "fightcade" in command.lower():
            await set_secondary(message, "fightcade")
            return

        if "set_challonge" in command.lower() or "set challonge" in command.lower() or "challonge" in command.lower():
            await set_secondary(message, "challonge")
            return

        if "set_region" in command.lower() or "set region" in command.lower() or "region" in command.lower():
            await set_secondary(message, "region")
            return

        if "set_cfn" in command.lower() or "set cfn" in command.lower() or "cfn" in command.lower():
            await set_secondary(message, "cfn")
            return

        # The remainder of commands require a specific server in order to function. (ignore these commands in PMs)
        # Returning here keeps the program from coughing exceptions into the log.
        if message.server is None:
            return

        if "match" in command:
            await match(message)
            return

        if "aliases" in command.lower() or "games" in command.lower():
            await tell_aliases(message)
            return

        if "describe" in command.lower():
            await describe(message)
            return

        if "unqueue" in command.lower():
            await unqueue(message, command.split('unqueue', 1)[-1].lstrip())
            return

        if "queue" in command.lower():
            await queue(message, command.split('queue', 1)[-1].lstrip())
            return

        if "removealias" in command.lower():
            await removealias(command.split('removealias', 1)[-1].lstrip(), message)
            return

        if "alias" in command.lower():
            parse_me = command.split('alias', 1)[-1].lstrip()
            if "to mean" in parse_me:
                parsed = parse_me.split("to mean")
                await addalias(parsed[0].strip(), parsed[1].strip(), message)
            else:
                await client.send_message(message.author, "You need to use \"alias <alias> to mean <game title>\" to set an alias.")
            return

        if "addgame" in command.lower():
            await addgame(command.split('addgame', 1)[-1].lstrip(), message)
            return

        if "removegame" in command.lower():
            await removegame(command.split('removegame', 1)[-1].lstrip(), message)
            return

        if "pairing" in command.lower():
            # await pairing(message)
            return

        if "start" in command.lower():
            # await start_tournament(message)
            return


async def addalias(alias_to_add, game_title, message):
    """Add an alias for a game on this server."""
    if message.author.permissions_in(message.channel).kick_members:
        # Check if that alias already exists
        search_for_alias = "SELECT COUNT(*) FROM %s_games WHERE alias='%s' OR game='%s'"
        search_result = await DB_WRAPPER.execute(client, message.author, search_for_alias, (message.server.id, alias_to_add, alias_to_add), True)
        if search_result[0][0]:
            # Alias already exists.
            print(str(datetime.now()) + ": " + message.author.id + " wanted to add alias " + alias_to_add + " for game " + game_title + " to server " + message.server.id + " but it already existed.")
            await client.send_message(message.author, "That alias already exists for " + message.server.name + ".")
        else:
            # Check if the game they named actually exists.
            game_exist = "SELECT COUNT(*) FROM %s_games WHERE game='%s'"
            does_game_exist = await DB_WRAPPER.execute(client, message.author, game_exist, (message.server.id, game_title,), True)
            if does_game_exist[0][0] == 0:
                print(str(datetime.now()) + ": Failed to create an alias \"" + alias_to_add + "\" for user " + message.author.id + " on server " + message.server.id + " because the game they named (" + game_title + ") didn't exist.")
                await client.send_message(message.author, "I've never heard of " + game_title + ". Perhaps you misspelled it?")
                return
            # Add the new alias.
            add_alias = "INSERT INTO %s_games (game, alias) VALUES ('%s','%s')"
            args = (message.server.id, game_title, alias_to_add)
            await DB_WRAPPER.execute(client, message.author, add_alias, args, True)
            print(str(datetime.now()) + ": " + message.author.id + " added alias " + alias_to_add + " for game " + game_title + " in server " + message.server.id + ".")
            await client.send_message(message.author, "Added the alias \"" + alias_to_add + "\" for " + game_title + " in " + message.server.name + ".")
    else:
        await client.send_message(message.author, "You don't have permission to add aliases in " + message.server.name + ".")
    return


async def addgame(game_to_add, message):
    """Make another game available on the server."""
    if message.author.permissions_in(message.channel).kick_members:
        # Check if that game already exists
        await add_server_specific_tables_if_necessary(message)
        search_for_game = "SELECT game FROM %s_games WHERE game='%s'"
        result = await DB_WRAPPER.execute(client, message.author, search_for_game, (message.server.id, game_to_add), True)
        if str(result) == "()":
            add_game = "INSERT INTO %s_games (game) VALUES ('%s')"
            args = (message.server.id, game_to_add)
            await DB_WRAPPER.execute(client, message.author, add_game, args, True)
            print(str(datetime.now()) + ": added game %s" + game_to_add + " to server " + message.server.id)
            await client.send_message(message.author, "Added game " + game_to_add + ".")
        else:
            print(str(datetime.now()) + ": tried to add game " + game_to_add + " to server " + message.server.id + " but it already existed.")
            await client.send_message(message.author, "That game already exists.")

    else:
        await client.send_message(message.author, "You don't have permission to add games in " + message.server.name + ".")
    return


async def add_new_user_if_needed(message):
    """Create a record to recognize a new user."""
    # This method also catches nickname changes (with the lower part there)
    search_for_user = "SELECT discord_id FROM users WHERE discord_id='%s'"
    result = await DB_WRAPPER.execute(client, message.author, search_for_user, (message.author.id, ), True)
    #print(str(datetime.now())+" add_new_user_if_needed found user: "+str(result))
    if str(result) == "()":
        add_user_query = "INSERT INTO users (discord_id) VALUES ('%s')"
        await DB_WRAPPER.execute(client, message.author, add_user_query, (message.author.id, ), True)
        print(str(datetime.now()) + ": added user: " + message.author.id + " (" + message.author.name + ")")
        set_username_query = "UPDATE users SET username='%s' WHERE discord_id='%s'"
        await DB_WRAPPER.execute(client, message.author, set_username_query, (message.author.name, message.author.id), True)
        print(str(datetime.now()) + ": set discord_id " + message.author.id + " to username " + message.author.name)
        return
    search_for_user = "SELECT username FROM users WHERE discord_id='%s'"
    result = await DB_WRAPPER.execute(client, message.author, search_for_user, (message.author.id, ), True)
    print(str(datetime.now()) + ": " + str(result[0][0]) + " already exists in the DB.")
    if str(result[0][0]) != message.author.name:
        change_username_query = "UPDATE users SET username='%s' WHERE discord_id='%s'"
        args = (message.author.name, message.author.id)
        await DB_WRAPPER.execute(client, message.author, change_username_query, args, True)
        print(str(datetime.now()) + ": discord_id " + message.author.id + " changed to username " + message.author.name)
    return

async def add_server_specific_tables_if_necessary(message):
    """Create new database tables sepcific to this server if necessary."""
    # Check if the server this message came from has its own games and pools tables.
    # If not, then add them.
    search_for_games_table = "SELECT count(*) FROM information_schema.TABLES WHERE (TABLE_SCHEMA = '" + DB_DB + "') AND (TABLE_NAME = '" + message.server.id + "_games')"
    table_exists = await DB_WRAPPER.execute(client, message.author, search_for_games_table, None, True)
    if table_exists[0][0] == 0:
        create_table = "CREATE TABLE %s_games (UID INT(11) NOT NULL PRIMARY KEY AUTO_INCREMENT, game VARCHAR(250), alias VARCHAR(50) UNIQUE, platform VARCHAR(25))"
        table_created = await DB_WRAPPER.execute(client, message.author, create_table, (message.server.id, ), True)
        print(str(datetime.now()) + ": created games table for server " + message.server.id + ".")

    search_for_pools_table = "SELECT count(*) FROM information_schema.TABLES WHERE (TABLE_SCHEMA = '" + DB_DB + "') AND (TABLE_NAME = '" + message.server.id + "_pools')"
    table_exists = await DB_WRAPPER.execute(client, message.author, search_for_pools_table, None, True)
    if table_exists[0][0] == 0:
        create_table = "CREATE TABLE %s_pools (UID INT(11) NOT NULL PRIMARY KEY AUTO_INCREMENT, game VARCHAR(250), player VARCHAR(50))"
        table_created = await DB_WRAPPER.execute(client, message.author, create_table, (message.server.id, ), True)
        print(str(datetime.now()) + ": created pools table for server " + message.server.id + ".")
    return


async def describe(message):
    """Output information about a specific user."""
    discord_user = message.content.split('describe', 1)[-1].lstrip().rstrip()
    games_query = "SELECT DISTINCT game FROM %s_pools INNER JOIN users ON %s_pools.player = users.discord_id WHERE username='%s'"
    args = (message.server.id, message.server.id, discord_user)
    users_games = await DB_WRAPPER.execute(client, message.author, games_query, args, True)
    user_description = ""
    if users_games:
        list_of_users_games = []
        for game_tuple in users_games:
            list_of_users_games.append(game_tuple[0])
        user_description = discord_user + " is queued up for " + ", ".join(list_of_users_games) + "\n"
    else:
        user_description = discord_user + " isn't queued up for any games.\n"
    user_description_query = "SELECT challonge, fightcade, cfn FROM users WHERE username='%s'"
    user_description_result = await DB_WRAPPER.execute(client, message.author, user_description_query, (discord_user, ), True)
    if str(user_description_result) == "()":
        await client.send_message(message.author, "I don't know anyone named " + discord_user + ".")
        return
    user_description_tuple = user_description_result[0]
    if user_description_tuple[0]:
        user_description += "Their Challonge username is " + user_description_tuple[0] + "."
    if user_description_tuple[1]:
        user_description += " Their Fightcade username is " + user_description_tuple[1] + "."
    if user_description_tuple[2]:
        user_description += " Their CFN is " + user_description_tuple[2] + "."
    await client.send_message(message.author, user_description)
    print(str(datetime.now()) + ": gave " + discord_user + "'s description to " + message.author.name + ".")
    return


async def get_discord_and_secondary_using_challonge(message, tournament, challonge_id):
    """Get Discord and Fightcade/CFN/Steam/Whatever information about a Challonger username."""
    # We have a Challonge ID and we need a Discord user and a username for Fightcade/CFN/Steam/whatever.
    # if we can't get that, we'll just print the Challonge username.
    # First, we use the name of the game to find what Secondary username we need.
    secondary_query = "SELECT platform FROM %s_games WHERE game = '%s' or alias = '%s'"
    args = (message.server.id, str(tournament["game-name"]), str(tournament["game-name"]))
    secondary = await DB_WRAPPER.execute(client, message.author, secondary_query, args, True)
    if str(secondary) == "()":
        # this means the database did not have the data we were looking for.
        # realistically, this should probably throw an exception.
        return "I don't know how to find user info for this game."
    getDiscordAndSecondaryQuery = "SELECT discord_id, %s FROM users WHERE challonge_id = '%s'"
    d_s_args = (secondary[0][0], str(challonge_id))
    discordAndSecondaryTuple = await DB_WRAPPER.execute(client, message.author, getDiscordAndSecondaryQuery, d_s_args, True)
    fallbackChallongeUsername = "Mystery User"
    if str(discordAndSecondaryTuple) == "()":
        participants = await challonge.participants.index(tournament["id"])
        for participant in participants:
            if participant["id"] == challonge_id:
                newIDquery = "UPDATE users SET challonge_id = '%s' WHERE challonge = '%s'"
                args = str(challonge_id, str(participant["username"]))
                await DB_WRAPPER.execute(client, message.author, newIDquery, args, True)
                discordAndSecondaryTuple = await DB_WRAPPER.execute(client, message.author, getDiscordAndSecondaryQuery, d_s_args, True)
                fallbackChallongeUsername = str(participant["username"])
                break
        if str(discordAndSecondaryTuple) == "()":
            # at this point, we know we do not know which Discord user the Challonge ID we have corresponds to, so we just return their Challonge username.
            return fallbackChallongeUsername
    return message.server.get_member(discordAndSecondaryTuple[0][0]).mention + " (" + discordAndSecondaryTuple[0][1] + ")"


async def is_member_queued_for_game(message, game):
    """Find out of a user is queued for a specific game."""
    print("is_member_queued_for_game called with member: " + message.author.name + " and game: " + game)
    query = "SELECT UID FROM %s_pools WHERE game='%s' AND player='%s'"
    args = (message.server.id, game, message.author.id)
    dbresult = await DB_WRAPPER.execute(client, message.author, query, args, True)
    if str(dbresult) != "()":
        print(str(datetime.now()) + ": " + message.author.name + " was found to be queued for " + game)
        return True
    print(str(datetime.now()) + ": " + message.author.name + " was found to NOT be queued for " + game)
    return False


async def match(message):
    """Find a match for a user.
    If the user specific a specific game, only find matches for that game.
    """
    hopefully_a_game = message.content.split('match', 1)[-1].lstrip()
    if hopefully_a_game == '':
        await match_random_game(message)
        return
    get_players_marked_here = "SELECT discord_id, username FROM users JOIN %s_pools WHERE discord_id = player AND game = (SELECT DISTINCT game FROM %s_games WHERE game = '%s' OR ALIAS = '%s') AND status='here' AND discord_id <> '%s'"
    args = (message.server.id, message.server.id, hopefully_a_game, hopefully_a_game, message.author.id)
    results = await DB_WRAPPER.execute(client, message.author, get_players_marked_here, args, True)
    print(str(datetime.now()) + ": " + message.author.name + " requested a match in " + hopefully_a_game + " and found: " + str(results))
    if results is None:
        await client.send_message(message.channel, 'Sorry, I couldn\'t find a match for you.\nDed gaem lmao')
        return
    mentions_list = []
    usernames_list = []
    for i in results:
        if message.server.get_member(i[0]):
            if message.server.get_member(i[0]).status == discord.Status.online:
                mentions_list.append(message.server.get_member(i[0]).mention)
                usernames_list.append(i[1])

    if len(mentions_list) < 1:
        await client.send_message(message.channel, 'Sorry, I couldn\'t find a match for you.\nDed gaem lmao')
        return

    challenge_message = 'Hey, ' + ", ".join(mentions_list) + ' let\'s play some ' + hopefully_a_game + ' with ' + message.author.mention
    await client.send_message(message.channel, challenge_message)
    print(str(datetime.now()) + ": final match list for " + hopefully_a_game + ": " + ", ".join(usernames_list))
    return


async def match_random_game(message):
    """Find a match for the user for any game."""
    await add_new_user_if_needed(message)
    # first, we make a list of all the games the member is queued for.
    find_games = "SELECT game FROM %s_pools WHERE player ='%s'"
    args = (message.server.id, message.author.id)
    users_games = await DB_WRAPPER.execute(client, message.author, find_games, args, True)
    print("matching random game for: " + message.author.name)
    print("users_games: " + str(users_games))
    games_to_players = {}
    if users_games != ():
        users_games = users_games[0]
        for game in users_games:
            get_other_players = "SELECT discord_id, username FROM users JOIN %s_pools WHERE discord_id=player AND game='%s' AND status='here' AND discord_id<>'%s'"
            args = (message.server.id, game, message.author.id)
            temp = await DB_WRAPPER.execute(client, message.author, get_other_players, args, True)
            print("match_random_game match result: " + str(temp))
            if temp:
                players = []
                for player in temp:
                    if message.server.get_member(player[0]):
                        if message.server.get_member(player[0]).status == discord.Status.online:
                            players.append(str(message.server.get_member(player[0]).mention))
                if message.author.mention in players:
                    players.remove(message.author.mention)
                games_to_players[game] = players
        # Now we have a map of {games the user is queued for, all other matched players}
        # We choose a random game (that actually has players) and match for that game.
        #print(str(datetime.now())+": games_to_players: "+str(games_to_players))
        if games_to_players.keys():
            print(str(datetime.now()) + ": failed to find a random game for " + message.author.name + ".")
            await client.send_message(message.channel, "Sorry, I couldn't find a match for you.")
            return
        chosen_game = random.choice(list(games_to_players.keys()))
        while games_to_players[chosen_game]:
            del games_to_players[chosen_game]
            if games_to_players.keys():
                print(str(datetime.now()) + ": failed to find a random game for " + message.author.name + ".")
                await client.send_message(message.channel, "Sorry, I couldn't find a match for you.")
                return
            chosen_game = random.choice(list(games_to_players.keys()))
            print(str(datetime.now()) + ": randomly matched " + message.author.name + " in " + chosen_game + " with " + str(games_to_players[chosen_game]))
            challenge_message = 'Hey, ' + ", ".join(games_to_players[chosen_game]) + ' let\'s play some ' + chosen_game + ' with ' + message.author.mention
            await client.send_message(message.channel, challenge_message)
    else:
        print(str(datetime.now()) + ": " + message.author.name + " tried to match a random game, but wasn't queued for anything.")
        await client.send_message(message.channel, "You'll have to queue up for some games before I can match you, " + message.author.mention)
    return


async def pairing(message):
    """Output pairings for currently running tournaments."""
    discord_output = ""
    tournaments = []
    print(str(datetime.now()) + ": getting tournaments from Challonge API")
    tournaments_unfiltered = await challonge.tournaments.index(state="underway")
    # the challonge library I'm using currently doesn't perform that indexing correctly in python 3.5.
    # it doesn't actually filter out tournaments or matches with any other state. It just returns all of them.
    # it does have a unit test for this, but it fails on python 3.5.
    # so, for now, I filter the tournaments manually.
    for i in tournaments_unfiltered:
        if i["state"] == "underway":
            tournaments.append(i)
    for tournament in tournaments:
        discord_output += "\nPairings for " + str(tournament["game-name"]) + ": \n"
        match_params = {'state': "open"}
        matches = await challonge.matches.index(tournament["id"], **match_params)
        for match in matches:
            if str(match["state"]) == "open":
                # should not need that conditional. same filter problem mentioned above.
                player1 = await get_discord_and_secondary_using_challonge(message, tournament, match["player1-id"])
                player2 = await get_discord_and_secondary_using_challonge(message, tournament, match["player2-id"])
                if message.author.permissions_in(message.channel).kick_members or message.author.mention in player1 or message.author.mention in player2:
                    discord_output += player1 + " vs. " + player2 + "\n"
    print(str(datetime.now()) + ": gave pairings to " + message.author.name)
    if discord_output == "":
        discord_output = "I don't have any pairings available for you right now."
    await client.send_message(message.channel, discord_output)
    return


async def queue(message, command):
    """Users can use this to queue for a game."""
    await add_new_user_if_needed(message)
    find_game = "SELECT game FROM %s_games WHERE game='%s' OR alias='%s'"
    args = (message.server.id, command, command)
    game = await DB_WRAPPER.execute(client, message.author, find_game, args, True)
    if str(game) != "()":
        game = game[0][0]
        already_queued = await is_member_queued_for_game(message, game)
        if not already_queued:
            queue_query = "INSERT INTO %s_pools (game, player) VALUES ('%s', '%s')"
            args = (message.server.id, game, message.author.id)
            await DB_WRAPPER.execute(client, message.author, queue_query, args, True)
            print(str(datetime.now()) + ": added " + message.author.name + " to the queue for " + game)
            await client.send_message(message.author, "Added you to the queue for " + game)
        else:
            print(str(datetime.now()) + ": " + message.author.name + " was already queued for " + game)
            await client.send_message(message.author, "You're already queued up for " + game + ".")
    else:
        await client.send_message(message.author, "I\'ve never heard of a game called " + game)
        print(str(datetime.now()) + ": " + message.author.name + " searched for " + game + " on server " + message.server.id + " but found nothing.")
    return


async def removealias(alias_to_remove, message):
    """Removes an alias for a game from a specific server."""
    # TODO hopefully this isn't the only record of that game in the table, huh?
    if message.author.permissions_in(message.channel).kick_members:
        remove_alias_query = "DELETE FROM %s_games WHERE alias='%s'"
        args = (message.server.id, alias_to_remove)
        result = await DB_WRAPPER.execute(client, message.author, remove_alias_query, args, True)
        print(str(datetime.now()) + ": deleted the alias " + alias_to_remove + " from server " + message.server.id + "'")
        await client.send_message(message.author, "Removed the alias " + alias_to_remove + " from " + message.server.name + ".")
    else:
        await client.send_message(message.author, "You don't have permission to remove aliases on " + message.server.name + ".")
    return


async def removegame(game_to_remove, message):
    """Remove a game from a server's lists of available games."""
    # TODO this doesn't have a way of telling if anything actually happened yet.
    if message.author.permissions_in(message.channel).kick_members:
        remove_game_query = "DELETE FROM %s_games WHERE game='%s' OR alias='%s'"
        args = (message.server.id, game_to_remove, game_to_remove)
        result = await DB_WRAPPER.execute(client, message.author, remove_game_query, args, True)
        print(str(datetime.now()) + ": removed " + game_to_remove + " from server " + message.server.id + ".")
        await client.send_message(message.author, "Removed " + game_to_remove + " from " + message.server.name + ".")

        # Also unqueue any users that were queued for that game!
        # TODO First we make a list of all users that were queued for that game on that server (so we can notify them they were dequeued)
        unqueue = "DELETE FROM %s_pools WHERE game='%s'"
        args = (message.server.id, game_to_remove)
        result = await DB_WRAPPER.execute(client, message.author, unqueue, args, True)
        print(str(datetime.now()) + ": foribly dequeued users for " + game_to_remove + " on server " + message.server.id + ".")
        # TODO consider sending a message to the server or users about this.
    else:
        await client.send_message(message.author, "You don't have permission to remove games on " + message.server.name + ".")
    return


async def set_secondary(message, thing_to_set):
    """Set a users Fightcade/CFN/Steam/whatever username."""
    # Be careful with the second argument you give this method. No input sanitization is performed.
    # Preferably, call it with a string. Do NOT take the argument directly from user input!
    # FIXME check that the second argument is actually a valid column.
    hopefully_a_valid_input = message.content.split(thing_to_set, 1)[-1].lstrip()
    await add_new_user_if_needed(message)
    query = "UPDATE users SET %s = '%s' WHERE discord_id = '%s'"
    args = (thing_to_set, hopefully_a_valid_input, message.author.id)
    result = await DB_WRAPPER.execute(client, message.author, query, args, True)
    if result is None:
        time = str(datetime.now())
        print(time + ": failed to set " + message.author.name + "'s " + thing_to_set + " to " + hopefully_a_valid_input + ".")
        await client.send_message(message.author, "I was unable to set your " + thing_to_set + ". Please ask Chish#2578 to check the logs at time " + time)
        return
    print(str(datetime.now()) + ": Set " + message.author.name + "'s " + thing_to_set + " to " + hopefully_a_valid_input)
    await client.send_message(message.author, "Set your " + thing_to_set + " to " + hopefully_a_valid_input + ".")
    return


async def start_tournament(message):
    """Start a Challonge tournament."""
    # check to see if requester has permission to start a tournament
    if message.author.permissions_in(message.channel).kick_members:
        # first, get all tournaments that are not yet started
        tournaments = []
        print(str(datetime.now()) + ": getting tournaments from Challonge")
        tournaments_unfiltered = await challonge.tournaments.index()
        for i in tournaments_unfiltered:
            if i["state"] == "checking_in" or i["state"] == "checked_in" or i["state"] == "pending":
                tournaments.append(i)
        # print("tournaments: " + str(tournaments) + "\n\n\n")
        discord_output = ""
        for tournament in tournaments:
            # determine which tournaments needs to be started via user-provided URL
            if tournament["full-challonge-url"] in message.content or tournament["full-challonge-url"].split("challonge.com/", 1)[1] in message.content:
                # if needed, process check-ins
                if tournament["state"] == "checking_in":
                    print(str(datetime.now()) + ": processing check-ins for " + str(tournament["id"]))
                    # await challonge.tournaments.process_check_ins(tournament["id"])
                # start the tournament
                print(str(datetime.now()) + ": starting tournament " + str(tournament["id"]))
                await challonge.tournaments.start(tournament["id"])
                # report round 1 pairings
                discord_output += "\nPairings for " + str(tournament["game-name"]) + ": \n"
                match_params = {'state': "open"}
                matches = await challonge.matches.index(tournament["id"], **match_params)
                for match in matches:
                    if str(match["state"]) == "open":
                        # should not need that conditional. This is a problem with the API or API library?
                        player1 = await get_discord_and_secondary_using_challonge(message, tournament, match["player1-id"])
                        player2 = await get_discord_and_secondary_using_challonge(message, tournament, match["player2-id"])
                        discord_output += player1 + " vs. " + player2 + "\n"
        if discord_output:
            await client.send_message(message.channel, discord_output)
        else:
            await client.send_message(message.author, "I couldn't start any tournaments. Be sure to specify which ones you want started using their URL.")
    else:
        await client.send_message(message.author, "Sorry, you don't have permission to start tournaments.")
    return


async def tell_aliases(message):
    """Output all games and their aliases."""
    # aquire map of (full game name) to (list of all aliases for that game)
    get_games = "SELECT game, alias FROM " + message.server.id + "_games ORDER BY game"
    sql_games_and_aliases = await DB_WRAPPER.execute(client, message.author, None, True)
    #print(str(datetime.now())+ ": games and aliases: "+str(sql_games_and_aliases))
    game_alias_map = {}
    for game_alias_pair in sql_games_and_aliases:
        if game_alias_pair[0] in game_alias_map:
            game_alias_map[game_alias_pair[0]].append(game_alias_pair[1])
        else:
            game_alias_map[game_alias_pair[0]] = [game_alias_pair[1]]

    # make it human-readable and give it to them
    readable_aliases = ""
    for game in sorted(game_alias_map):
        readable_aliases += "**" + game + "**: "
        if not game_alias_map[game]:
            readable_aliases += "No aliases so far.\n"
            continue
        for alias in game_alias_map[game]:
            if alias is not None:
                readable_aliases += alias + ", "
        # there are no aliases left, so remove that last comma + space
        readable_aliases = readable_aliases[:-2]
        readable_aliases += "\n"

    print(str(datetime.now()) + ": gave game/alias map to " + str(message.author.name))
    await client.send_message(message.author, "Here are all the aliases available for games I have available on " + message.server.name + ": \n" + readable_aliases)
    return


async def unqueue(message, command):
    """Users use this to unqueue for specific games."""
    #FIXME spaces should not be a separator here.
    await add_new_user_if_needed(message)
    hopefully_list_of_games = command.split(" ")
    for hopefully_game in hopefully_list_of_games:
        is_queued = "SELECT game FROM %s_games WHERE (game='%s' OR alias='%s')"
        args = (message.server.id, hopefully_game, hopefully_game)
        game = await DB_WRAPPER.execute(client, message.author, is_queued, args, True)
        if str(game) != "()":
            already_queued = await is_member_queued_for_game(message, game[0][0])
            if already_queued:
                unqueue_query = "DELETE FROM %s_pools WHERE game='%s' AND player='%s'"
                args = (message.server.id, game[0][0], message.author.id)
                await DB_WRAPPER.execute(client, message.author, unqueue_query, args, True)
                print(str(datetime.now()) + ": removed " + message.author.name + " from the queue for " + game[0][0])
                await client.send_message(message.author, "Removed you from the queue for " + hopefully_game)
            else:
                await client.send_message(message.author, "You aren't in the queue for " + hopefully_game)
        else:
            await client.send_message(message.author, "I\'ve never heard of a game called " + hopefully_game)
    return


@client.event
async def on_ready():
    print(str(datetime.now()) + ": logged in as " + client.user.name)
    return

# This is probably not the best way to do these things, but that's ok
f = open(DISCORD_CREDENTIALS, 'r')
token = f.readline().strip('\n')
f.close()
f = open(CHALLONGE_CREDENTIALS, 'r')
CHALLONGE_USERNAME = f.readline().rstrip()
CHALLONGE_KEY = f.readline().rstrip()
f.close()
challonge = challonge.Account(CHALLONGE_USERNAME, CHALLONGE_KEY)
f = open(MYSQL_CREDENTIALS, 'r')
DB_USER = f.readline().strip('\n')
DB_PWD = f.readline().strip('\n')
DB_HOST = f.readline().strip('\n')
DB_DB = f.readline().strip('\n')
DB_WRAPPER = DB_Wrapper(DB_USER, DB_PWD, DB_HOST, DB_DB)
client.run(token)
