import discord
import challonge
import asyncio
import MySQLdb
import random
import datetime
from sys import argv
from db_wrapper import DB_Wrapper

this_program, discord_credentials, mysql_credentials, challonge_credentials = argv
client = discord.Client()
marvel_release_date = datetime.date(2017, 7, 16)

@client.event
async def on_message(message):
	#don't reply to bots
	if message.author.bot:
		return

	# When's Mahvel?
	if "when's mahvel" in message.content.lower() or "whens mahvel" in message.content.lower() or "when is mahvel" in message.content.lower():
		time_to_marvel = marvel_release_date - datetime.date.today()
		if time_to_marvel.days == 0:
			await client.send_message(message.channel, "IT'S MAHVEL TIME, BAYBEE! https://media.giphy.com/media/ToMjGpmBhHxpWpmtFcs/giphy.gif")
		elif time_to_marvel.days > 0:
			await client.send_message(message.channel, message.author.mention + ", Ultimate Marvel vs Capcom 3 Evo finals are on Sunday July 16th, which is in " + str(time_to_marvel.days) + " days.")
		else:
			await client.send_message(message.channel, "Sorry, " + message.author.mention + ", I don't know when the next Mahvel thing is happening.")
		return


	if any(x.id == client.user.id for x in message.mentions) or message.content.lower().startswith('sfcjbot') or message.content.lower().startswith('@sfcjbot'):
		command = message.content

		# TODO find a good pattern to clean this up

		if "match" in command:
			await match(message)
			return

		if "help" in command.lower():
			await client.send_message(message.author, "I\'m SFCJbot! I help SFCJ members play their favorite fighting games! Check out https://github.com/krehera/SFCJbot for documentation.")
			return

		if "here" in command.lower():
			await add_new_user_if_needed(message)
			result = await db_wrapper.execute(client, message.author, "UPDATE users SET status='here' WHERE discord_id=" + message.author.id, False)
			if result is None:
				print(time+": failed to set "+message.author.name+" to here.")
				await client.send_message(message.author, "I was unable to set your status to here. Please ask Chish#2578 to check the logs at time "+time)
				return
			print(str(datetime.datetime.now())+": set "+message.author.name+" to here.")
			await client.send_message(message.author, "Your status was changed to 'here.'")
			return

		if "afk" in command.lower() or "away" in command.lower():
			await add_new_user_if_needed(message)
			result = await db_wrapper.execute(client, message.author, "UPDATE users SET status='afk' WHERE discord_id="+message.author.id, False)
			if result is None:
				time = str(datetime.datetime.now())
				print(time+": failed to set "+message.author.name+" to away.")
				await client.send_message(message.author, "I was unable to set your status to afk. Please ask Chish#2578 to check the logs at time "+time)
				return
			print(str(datetime.datetime.now())+": set "+message.author.name+" to afk.")
			await client.send_message(message.author, "Your status was changed to 'afk.'")
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

		if "alias" in command.lower() or "games" in command.lower():
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

		if "addgame" in command:
	#		await addgame(command.split('addgame',1)[-1].lstrip(), message)
			return

		if "about" in command.lower():
			await client.send_message(message.author, "SFCJbot is running on a Raspberry Pi and is powered by the following technologies:\nRaspbian GNU/Linux 8 (jessie)\nPython 3.5\nDiscord.py\nMySQL and MySQLdb\npychallonge")
			return

		if "pairing" in command.lower():
			#await pairing(message)
			return

		if "start" in command.lower():
			#await start_tournament(message)
			return


async def addgame(game_to_add, message):
	# FIXME see GitHub issue about this.
	if message.author.permissions_in(message.channel).kick_members:
		add_game="INSERT INTO games (game) VALUES ('"+game_to_add+"')"
		await db_wrapper.execute(client, message.author, add_game, True)
		print(str(datetime.datetime.now())+": added game "+game_to_add)
		await client.send_message(message.author, "added game "+game_to_add+". If you messed up, ping Chish#2578!")
	else:
		await client.send_message(message.author, "You don't have permission to add games.")
	return

async def add_new_user_if_needed(message):
	#This method also catches nickname changes (with the lower part there)
	search_for_user = "SELECT discord_id FROM users WHERE discord_id='"+message.author.id+"'"
	result = await db_wrapper.execute(client, message.author, search_for_user, True)
	#print(str(datetime.datetime.now())+" add_new_user_if_needed found user: "+str(result))
	if str(result) == "()":
		await db_wrapper.execute(client, message.author, "INSERT INTO users (discord_id) VALUES ('"+message.author.id+"')", True)
		print(str(datetime.datetime.now())+": added user: "+message.author.id+" ("+message.author.name+")")
		await db_wrapper.execute(client, message.author, "UPDATE users SET username='"+message.author.name+"' WHERE discord_id='"+message.author.id+"'", True)
		print(str(datetime.datetime.now())+": set discord_id "+message.author.id+" to username "+message.author.name)
		return
	search_for_user = "SELECT username FROM users WHERE discord_id='"+message.author.id+"'"
	result = await db_wrapper.execute(client, message.author, search_for_user, True)
	print(str(datetime.datetime.now())+": " + str(result[0][0]) + " already exists in the DB.")
	if str(result[0][0]) != message.author.name:
		await db_wrapper.execute(client, message.author, "UPDATE users SET username='"+message.author.name+"' WHERE discord_id='"+message.author.id+"'", True)
		print(str(datetime.datetime.now())+": discord_id "+message.author.id+" changed to username "+message.author.name)
	return

async def describe(message):
	discord_user = message.content.split('describe', 1)[-1].lstrip().rstrip()
	games_query = "SELECT DISTINCT game FROM pools INNER JOIN users ON pools.player = users.discord_id WHERE username='" + discord_user + "'"
	users_games = await db_wrapper.execute(client, message.author, games_query, True)
	user_description = ""
	if users_games:
		list_of_users_games=[]
		for game_tuple in users_games:
			list_of_users_games.append(game_tuple[0])
		user_description = discord_user + " is queued up for " + ", ".join(list_of_users_games) + "\n"
	else:
		user_description = discord_user + " isn't queued up for any games.\n"
	user_description_query = "SELECT challonge, fightcade, cfn FROM users WHERE username='" + discord_user + "'"
	user_description_result = await db_wrapper.execute(client, message.author, user_description_query, True)
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
	print(str(datetime.datetime.now())+": gave " + discord_user + "'s description to " + message.author.name + ".")
	return


async def getDiscordAndSecondaryUsingChallonge(message, tournament, challonge_id):
	# We have a Challonge ID and we need a Discord user and a username for Fightcade/CFN/Steam/whatever.
	# if we can't get that, we'll just print the Challonge username.
	# First, we use the name of the game to find what Secondary username we need.
	secondary_query = "SELECT platform FROM games WHERE game = '" + str(tournament["game-name"]) + "' or alias = '" + str(tournament["game-name"]) + "'"
	secondary = await db_wrapper.execute(client, message.author, secondary_query, True)
	if str(secondary) == "()":
		# this means the database did not have the data we were looking for.
		# realistically, this should probably throw an exception.
		return "I don't know how to find user info for this game."
	getDiscordAndSecondaryQuery = "SELECT discord_id, " + secondary[0][0] + " FROM users WHERE challonge_id = '" + str(challonge_id) + "'"
	discordAndSecondaryTuple = await db_wrapper.execute(client, message.author, getDiscordAndSecondaryQuery, True)
	fallbackChallongeUsername = "Mystery User"
	if str(discordAndSecondaryTuple) == "()":
		participants = await challonge.participants.index(tournament["id"])
		for participant in participants:
			if participant["id"] == challonge_id:
				newIDquery = "UPDATE users SET challonge_id = '" + str(challonge_id) + "' WHERE challonge = '" + str(participant["username"]) + "'"
				await db_wrapper.execute(client, message.author, newIDquery, True)
				discordAndSecondaryTuple = await db_wrapper.execute(client, message.author, getDiscordAndSecondaryQuery, True)
				fallbackChallongeUsername = str(participant["username"])
				break
		if str(discordAndSecondaryTuple) == "()":
			# at this point, we know we do not know which Discord user the Challonge ID we have corresponds to, so we just return their Challonge username.
			return fallbackChallongeUsername
	return message.server.get_member(discordAndSecondaryTuple[0][0]).mention + " (" + discordAndSecondaryTuple[0][1] + ")"

async def is_member_queued_for_game(member, game):
	print("is_member_queued_for_game called with member: "+member.name+" and game: "+game)
	query = "SELECT UID FROM pools WHERE game='"+game.replace("'","''")+"' AND player='"+member.id+"'"
	dbresult = await db_wrapper.execute(client, member, query, True)
	if str(dbresult) != "()":
		print(str(datetime.datetime.now())+": "+member.name+" was found to be queued for "+game)
		return True
	print(str(datetime.datetime.now())+": "+member.name+" was found to NOT be queued for "+game)
	return False

async def match(message):
	hopefully_a_game = message.content.split('match', 1)[-1].lstrip()
	if hopefully_a_game == '':
		await match_random_game(message)
		return
	get_players_marked_here = "SELECT discord_id, username FROM users JOIN pools WHERE discord_id = player AND game = (SELECT DISTINCT game FROM games WHERE game = '"+hopefully_a_game.replace("'","''")+"' OR ALIAS = '"+hopefully_a_game.replace("'","''")+"') AND status='here' AND discord_id <> '"+message.author.id+"'"
	results = await db_wrapper.execute(client, message.author, get_players_marked_here, True)
	print(str(datetime.datetime.now())+": "+message.author.name+" requested a match in "+hopefully_a_game+" and found: "+str(results))
	if results is None:
		await client.send_message(message.channel, 'Sorry, I couldn\'t find a match for you.\nDed gaem lmao')
		return
	mentions_list=[]
	usernames_list=[]
	for i in results:
		if message.server.get_member(i[0]):
			if message.server.get_member(i[0]).status == discord.Status.online:
				mentions_list.append(message.server.get_member(i[0]).mention)
				usernames_list.append(i[1])

	if len(mentions_list)<1:
		await client.send_message(message.channel, 'Sorry, I couldn\'t find a match for you.\nDed gaem lmao')
		return

	challenge_message = 'Hey, ' + ", ".join(mentions_list) +' let\'s play some '+hopefully_a_game+' with '+message.author.mention
	await client.send_message(message.channel, challenge_message)
	print(str(datetime.datetime.now())+": final match list for "+hopefully_a_game+": "+", ".join(usernames_list))
	return

async def match_random_game(message):
	await add_new_user_if_needed(message)
	#first, we make a list of all the games the member is queued for.
	users_games = await db_wrapper.execute(client, message.author, "SELECT game FROM pools WHERE player ='"+message.author.id+"'", False)
	print("matching random game for: "+message.author.name)
	print("users_games: "+str(users_games))
	games_to_players = {}
	if users_games != ():
		users_games = users_games[0]
		for game in users_games:
			get_players_marked_here_not_requester="SELECT discord_id, username FROM users JOIN pools WHERE discord_id=player AND game='"+game.replace("'","''")+"' AND status='here' AND discord_id<>'"+message.author.id+"'"
			temp = await db_wrapper.execute(client, message.author, get_players_marked_here_not_requester, True)
			print("match_random_game match result: "+str(temp))
			if temp:
				players = []
				for player in temp:
					if message.server.get_member(player[0]):
						if message.server.get_member(player[0]).status == discord.Status.online:
							players.append(str(message.server.get_member(player[0]).mention))
				if message.author.mention in players:
					players.remove(message.author.mention)
				games_to_players[game]=players
		# Now we have a map of {games the user is queued for, all other matched players}
		# We choose a random game (that actually has players) and match for that game.
		#print(str(datetime.datetime.now())+": games_to_players: "+str(games_to_players))
		if len(games_to_players.keys()) == 0:
			print(str(datetime.datetime.now())+": failed to find a random game for "+message.author.name+".")
			await client.send_message(message.channel, "Sorry, I couldn't find a match for you.")
			return
		chosen_game=random.choice(list(games_to_players.keys()))
		while (len(games_to_players[chosen_game]) == 0):
			del games_to_players[chosen_game]
			if len(games_to_players.keys()) == 0:
				print(str(datetime.datetime.now())+": failed to find a random game for "+message.author.name+".")
				await client.send_message(message.channel, "Sorry, I couldn't find a match for you.")
				return
			chosen_game=random.choice(list(games_to_players.keys()))
		print(str(datetime.datetime.now())+": randomly matched "+message.author.name+" in "+chosen_game+" with "+str(games_to_players[chosen_game]))
		challenge_message = 'Hey, ' + ", ".join(games_to_players[chosen_game]) +' let\'s play some '+chosen_game+' with '+message.author.mention
		await client.send_message(message.channel, challenge_message)
	else:
		print(str(datetime.datetime.now())+": "+message.author.name+" tried to match a random game, but wasn't queued for anything.")
		await client.send_message(message.channel, "You'll have to queue up for some games before I can match you, "+message.author.mention)
	return

async def pairing(message):
	discord_output = ""
	tournaments = []
	print(str(datetime.datetime.now())+": getting tournaments from Challonge API")
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
		match_params = {'state':"open"}
		matches = await challonge.matches.index(tournament["id"], **match_params)
		for match in matches:
			if str(match["state"]) == "open":
				# should not need that conditional. same filter problem mentioned above.
				player1 = await getDiscordAndSecondaryUsingChallonge(message, tournament, match["player1-id"])
				player2 = await getDiscordAndSecondaryUsingChallonge(message, tournament, match["player2-id"])
				if message.author.permissions_in(message.channel).kick_members or message.author.mention in player1 or message.author.mention in player2:
					discord_output += player1 + " vs. " + player2 + "\n"
	print(str(datetime.datetime.now())+": gave pairings to " + message.author.name)
	if discord_output == "":
		discord_output = "I don't have any pairings available for you right now."
	await client.send_message(message.channel, discord_output)
	return

async def queue(message, command):
	await add_new_user_if_needed(message)
	hopefully_list_of_games = command.split(" ")
	for hopefully_game in hopefully_list_of_games:
		game = await db_wrapper.execute(client, message.author, "SELECT game FROM games WHERE game='"+hopefully_game.replace("'","''")+"' OR alias='"+hopefully_game.replace("'","''")+"'", True)
		if str(game) != "()":
			game = game[0][0]
			already_queued = await is_member_queued_for_game(message.author, game)
			if not already_queued:
				await db_wrapper.execute(client, message.author, "INSERT INTO pools (game, player) VALUES ('"+game.replace("'","''")+"', '"+message.author.id+"')", True)
				print(str(datetime.datetime.now())+": added "+message.author.name+" to the queue for "+game)
				await client.send_message(message.author, "Added you to the queue for " + hopefully_game)
			else:
				print(str(datetime.datetime.now())+": "+message.author.name+" was already queued for "+game)
				await client.send_message(message.author, "You're already queued up for "+hopefully_game+".")
		else:
			await client.send_message(message.author, "I\'ve never heard of a game called " + hopefully_game)
			print(str(datetime.datetime.now())+": "+message.author.name+" searched for "+hopefully_game+" but found nothing.")
	return

async def set_secondary(message, thing_to_set):
	# Be careful with the second argument you give this method. No input sanitization is performed.
	# Preferably, call it with a string. Do NOT take the argument directly from user input!
	# FIXME check that the second argument is actually a valid column.
	hopefully_a_valid_input= message.content.split(thing_to_set, 1)[-1].lstrip()
	await add_new_user_if_needed(message)
	query = "UPDATE users SET " + thing_to_set + " = '" + hopefully_a_valid_input + "' WHERE discord_id = '" + message.author.id + "'"
	result = await db_wrapper.execute(client, message.author, query, True)
	if result is None:
		time = str(datetime.datetime.now())
		print(time+": failed to set "+message.author.name+"'s " + thing_to_set + " to "+hopefully_a_valid_input+".")
		await client.send_message(message.author, "I was unable to set your " + thing_to_set +". Please ask Chish#2578 to check the logs at time "+time)
		return
	print(str(datetime.datetime.now())+": Set " + message.author.name + "'s " + thing_to_set + " to " + hopefully_a_valid_input)
	await client.send_message(message.author, "Set your " + thing_to_set + " to " + hopefully_a_valid_input+".")
	return

async def start_tournament(message):
	# check to see if requester has permission to start a tournament
	if message.author.permissions_in(message.channel).kick_members:
		# first, get all tournaments that are not yet started
		tournaments = []
		print(str(datetime.datetime.now())+": getting tournaments from Challonge")
		tournaments_unfiltered = await challonge.tournaments.index()
		for i in tournaments_unfiltered:
			if i["state"] == "checking_in" or i["state"] == "checked_in" or i["state"] == "pending":
				tournaments.append(i)
		# print("tournaments: " + str(tournaments) + "\n\n\n")
		discord_output = ""
		for tournament in tournaments:
			# determine which tournaments needs to be started via user-provided URL
			if tournament["full-challonge-url"] in message.content or tournament["full-challonge-url"].split("challonge.com/",1)[1] in message.content:
				# if needed, process check-ins
				if tournament["state"] == "checking_in":
					print(str(datetime.datetime.now()) + ": processing check-ins for " + str(tournament["id"]))
					# await challonge.tournaments.process_check_ins(tournament["id"])
				# start the tournament
				print(str(datetime.datetime.now()) + ": starting tournament " + str(tournament["id"]))
				await challonge.tournaments.start(tournament["id"])
				# report round 1 pairings
				discord_output += "\nPairings for " + str(tournament["game-name"]) + ": \n"
				match_params = {'state':"open"}
				matches = await challonge.matches.index(tournament["id"], **match_params)
				for match in matches:
					if str(match["state"]) == "open":
					# should not need that conditional. This is a problem with the API or API library?
						player1 = await getDiscordAndSecondaryUsingChallonge(message, tournament, match["player1-id"])
						player2 = await getDiscordAndSecondaryUsingChallonge(message, tournament, match["player2-id"])
						discord_output += player1 + " vs. " + player2 + "\n"
		if discord_output:
			await client.send_message(message.channel, discord_output)
		else:
			await client.send_message(message.author, "I couldn't start any tournaments. Be sure to specify which ones you want started using their URL.")
	else:
		await client.send_message(message.author, "Sorry, you don't have permission to start tournaments.")
	return

async def tell_aliases(message):
	# aquire map of (full game name) to (list of all aliases for that game)
	sql_games_and_aliases = await db_wrapper.execute(client, message.author, "SELECT game, alias FROM games ORDER BY game", True)
	#print(str(datetime.datetime.now())+ ": games and aliases: "+str(sql_games_and_aliases))
	game_alias_map = {}
	for game_alias_pair in sql_games_and_aliases:
		if game_alias_pair[0] in game_alias_map:
			game_alias_map[game_alias_pair[0]].append(game_alias_pair[1])
		else:
			game_alias_map[game_alias_pair[0]] = [game_alias_pair[1]]

	# make it human-readable and give it to them
	readable_aliases = ""
	for game in sorted(game_alias_map):
		readable_aliases += "**"+game+"**: "
		if not game_alias_map[game]:
			readable_aliases+= "No aliases so far.\n"
			continue
		for alias in game_alias_map[game]:
			readable_aliases += alias+", "
		readable_aliases = readable_aliases[:-2] # there are no aliases left, so remove that last comma + space
		readable_aliases += "\n"

	print(str(datetime.datetime.now())+ ": gave game/alias map to "+str(message.author.name))
	await client.send_message(message.author, "Here are all the aliases available for games I have available: \n" + readable_aliases)
	return

async def unqueue(message, command):
	await add_new_user_if_needed(message)
	hopefully_list_of_games = command.split(" ")
	for hopefully_game in hopefully_list_of_games:
		game = await db_wrapper.execute(client, message.author, "SELECT game FROM games WHERE (game='"+hopefully_game.replace("'","''")+"' OR alias='"+hopefully_game.replace("'","''")+"')", True)
		if str(game) != "()":
			already_queued = await is_member_queued_for_game(message.author, game[0][0])
			if already_queued:
				await db_wrapper.execute(client, message.author, "DELETE FROM pools WHERE game='"+game[0][0].replace("'","''")+"' AND player='"+message.author.id+"'", True)
				print(str(datetime.datetime.now())+": removed "+message.author.name+" from the queue for "+game[0][0])
				await client.send_message(message.author, "Removed you from the queue for "+hopefully_game)
			else:
				await client.send_message(message.author, "You aren't in the queue for "+hopefully_game)
		else:
			await client.send_message(message.author, "I\'ve never heard of a game called " + hopefully_game)
	return

@client.event
async def on_ready():
	print(str(datetime.datetime.now()) + ": logged in as "+client.user.name)
	return

# This is probably not the best way to do these things, but that's ok
f = open(discord_credentials, 'r')
token = f.readline().strip('\n')
f.close()
f = open(challonge_credentials, 'r')
challonge_username = f.readline().rstrip()
challonge_key = f.readline().rstrip()
f.close()
challonge = challonge.Account(challonge_username, challonge_key)
f = open(mysql_credentials, 'r')
db_user = f.readline().strip('\n')
db_pwd = f.readline().strip('\n')
db_host = f.readline().strip('\n')
db_db = f.readline().strip('\n')
db_wrapper = DB_Wrapper(db_user, db_pwd, db_host, db_db)
client.run(token)

