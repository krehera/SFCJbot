import discord
import asyncio
import MySQLdb
import random
from db_wrapper import DB_Wrapper
from datetime import datetime

client = discord.Client()

@client.event
async def on_message(message):
	#don't reply to bots
	if message.author.bot:
		return

	if any(x.id == client.user.id for x in message.mentions) or message.content.startswith('SFCJbot'):
		command = message.content

		if "match" in command:
			hopefully_a_game = command.split('match', 1)[-1].lstrip()
			if hopefully_a_game == '':
				await match_random_game(message)
				return
			get_players_marked_here = "SELECT discord_id, username FROM users JOIN pools WHERE discord_id = player AND game = (SELECT DISTINCT game FROM games WHERE game = '"+hopefully_a_game.replace("'","''")+"' OR ALIAS = '"+hopefully_a_game.replace("'","''")+"') AND status='here' AND discord_id <> '"+message.author.id+"'" 
			results = await db_wrapper.execute(client, message.author, get_players_marked_here, True)
			print(str(datetime.now())+": "+message.author.name+" requested a match in "+hopefully_a_game+" and found: "+str(results))
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
			print(str(datetime.now())+": final match list for "+hopefully_a_game+": "+", ".join(usernames_list))
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
			print(str(datetime.now())+": set "+message.author.name+" to here.")
			await client.send_message(message.author, "Your status was changed to 'here.'")
			return

		if "afk" in command.lower() or "away" in command.lower():
			await add_new_user_if_needed(message)
			result = await db_wrapper.execute(client, message.author, "UPDATE users SET status='afk' WHERE discord_id="+message.author.id, False)
			if result is None:
				time = str(datetime.now())
				print(time+": failed to set "+message.author.name+" to away.")
				await client.send_message(message.author, "I was unable to set your status to afk. Please ask Chish#2578 to check the logs at time "+time)
				return
			print(str(datetime.now())+": set "+message.author.name+" to afk.")
			await client.send_message(message.author, "Your status was changed to 'afk.'")
			return
		
		if "region" in command.lower():
			hopefully_a_region = command.split('region', 1)[-1].lstrip()
			await add_new_user_if_needed(message)
			sql_command = "UPDATE users SET region='"+hopefully_a_region+"' WHERE discord_id='"+message.author.id+"'"
			result = await db_wrapper.execute(client, message.author, sql_command, False)
			if result is None:
				time = str(datetime.now())
				print(time+": failed to set "+message.author.name+"'s region to "+hopefully_a_region+".")
				await client.send_message(message.author, "I was unable to set your region. Please ask Chish#2578 to check the logs at time "+time)
				return
			print(str(datetime.now())+": set "+message.author.name+"'s region to "+hopefully_a_region+".")
			await client.send_message(message.author, "Your region has been set to "+hopefully_a_region+".")
			return

		if "games" in command.lower():
			games = await db_wrapper.execute(client, message.author, "SELECT DISTINCT game FROM games", True)
			games_list = []
			for i in games:
				games_list.append(i[0])
			games_message = 'I offer the following games: '+ ", ".join(games_list) + "."
			await client.send_message(message.author, games_message)
			print(str(datetime.now())+": found games for"+message.author.name)
			return

		if "alias" in command.lower():
			await tell_aliases(message);
			return

		if "describe" in command.lower():
			command = command.split('describe', 1)[-1].lstrip().rstrip()
			users_games = await db_wrapper.execute(client, message.author, "SELECT distinct game FROM pools INNER JOIN users ON pools.player = users.discord_id WHERE username='"+command+"'", False)
			if users_games:
				list_of_users_games=[]
				for game_tuple in users_games:
					list_of_users_games.append(game_tuple[0])
				await client.send_message(message.author, command+" is queued up for "+", ".join(list_of_users_games))
				print(str(datetime.now())+": told "+message.author.name+" that "+command+" is queued up for "+", ".join(users_games[0]))
			else:
				await client.send_message(message.author, command+" isn't queued up for any games.")
				print(str(datetime.now())+": told "+message.author.name+" that "+command+" is not queued up for any games.")
			return

		if "unqueue" in command.lower():
			await unqueue(message, command.split('unqueue', 1)[-1].lstrip())
			return

		if command.startswith('Q '):
			await queue(message, command[2:])
			return

		if "queue" in command.lower():
			await queue(message, command.split('queue', 1)[-1].lstrip())
			return

		if command.startswith('unQ '):
			await unqueue(message, command[4:])
			return

		if "addgame" in command:
	#		await addgame(command.split('addgame',1)[-1].lstrip(), message)
			return

		if "about" in command.lower():
			await client.send_message(message.author, "SFCJbot is running on a Raspberry Pi and is powered by the following technologies:\nRaspbian GNU/Linux 8 (jessie)\nPython 3.5\nDiscord.py\nMySQL and MySQLdb")
			return

async def add_new_user_if_needed(message):
	#This method also catches nickname changes (with the lower part there)
	search_for_user = "SELECT discord_id FROM users WHERE discord_id='"+message.author.id+"'"
	result = await db_wrapper.execute(client, message.author, search_for_user, True)
	#print(str(datetime.now())+" add_new_user_if_needed found user: "+str(result))
	if str(result) == "()":
		await db_wrapper.execute(client, message.author, "INSERT INTO users (discord_id) VALUES ('"+message.author.id+"')", True)
		print(str(datetime.now())+": added user: "+message.author.id+" ("+message.author.name+")")
		await db_wrapper.execute(client, message.author, "UPDATE users SET username='"+message.author.name+"' WHERE discord_id='"+message.author.id+"'", True)
		print(str(datetime.now())+": set discord_id "+message.author.id+" to username "+message.author.name)
		return
	search_for_user = "SELECT username FROM users WHERE discord_id='"+message.author.id+"'"
	result = await db_wrapper.execute(client, message.author, search_for_user, True)
	print(str(datetime.now())+": add_new_user_if_needed found username: "+str(result))
	if str(result[0][0]) != message.author.name:
		await db_wrapper.execute(client, message.author, "UPDATE users SET username='"+message.author.name+"' WHERE discord_id='"+message.author.id+"'", True)
		print(str(datetime.now())+": discord_id "+message.author.id+" changed to username "+message.author.name)
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
				print(str(datetime.now())+": added "+message.author.name+" to the queue for "+game)
				await client.send_message(message.author, "Added you to the queue for " + hopefully_game)
			else:
				print(str(datetime.now())+": "+message.author.name+" was already queued for "+game)
				await client.send_message(message.author, "You're already queued up for "+hopefully_game+".")
		else:
			await client.send_message(message.author, "I\'ve never heard of a game called " + hopefully_game)
			print(str(datetime.now())+": "+message.author.name+" searched for "+hopefully_game+" but found nothing.")
	return

async def addgame(game_to_add, message):
	if message.author.permissions_in(message.channel).kick_members:
		add_game="INSERT INTO games (game) VALUES ('"+game_to_add+"')"
		await db_wrapper.execute(client, message.author, add_game, True)
		print(str(datetime.now())+": added game "+game_to_add)
		await client.send_message(message.author, "added game "+game_to_add+". If you messed up, ping the bot owner!")
	else:
		await client.send_message(message.author, "You don't have permission to add games.")
	return

async def is_member_queued_for_game(member, game):
	print("is_member_queued_for_game called with member: "+member.name+" and game: "+str(game))
	query = "SELECT UID FROM pools WHERE game='"+game.replace("'","''")+"' AND player='"+member.id+"'"
	dbresult = await db_wrapper.execute(client, member, query, True)
	if str(dbresult) != "()":
		return True
	return False

async def unqueue(message, command):
	await add_new_user_if_needed(message)
	hopefully_list_of_games = command.split(" ")
	for hopefully_game in hopefully_list_of_games:
		game = await db_wrapper.execute(client, message.author, "SELECT game FROM games WHERE (game='"+hopefully_game.replace("'","''")+"' OR alias='"+hopefully_game.replace("'","''")+"')", True)
		if str(game) != "()":
			already_queued = await is_member_queued_for_game(message.author, game)
			if not already_queued:
				await db_wrapper.execute(client, message.author, "DELETE FROM pools WHERE game='"+game.replace("'","''")+"' AND player='"+message.author.id+"'", True)
				print(str(datetime.now())+": removed "+message.author.name+" from the queue for "+game)
				await client.send_message(message.author, "Removed you from the queue for "+hopefully_game)
			else:
				await client.send_message(message.author, "You aren't in the queue for "+hopefully_game)
		else:
			await client.send_message(message.author, "I\'ve never heard of a game called " + hopefully_game)
	return

@client.event
async def on_ready():
	print(str(datetime.now()) + ": logged in as "+client.user.name)
	return

async def match_random_game(message):
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
		#print(str(datetime.now())+": games_to_players: "+str(games_to_players))
		if len(games_to_players.keys()) == 0:
			print(str(datetime.now())+": failed to find a random game for "+message.author.name+".")
			await client.send_message(message.channel, "Sorry, I couldn't find a match for you.")
			return
		chosen_game=random.choice(list(games_to_players.keys()))
		while (len(games_to_players[chosen_game]) == 0):
			del games_to_players[chosen_game]
			if len(games_to_players.keys()) == 0:
				print(str(datetime.now())+": failed to find a random game for "+message.author.name+".")
				await client.send_message(message.channel, "Sorry, I couldn't find a match for you.")
				return
			chosen_game=random.choice(list(games_to_players.keys()))
		print(str(datetime.now())+": randomly matched "+message.author.name+" in "+chosen_game+" with "+str(games_to_players[chosen_game]))
		challenge_message = 'Hey, ' + ", ".join(games_to_players[chosen_game]) +' let\'s play some '+chosen_game+' with '+message.author.mention
		await client.send_message(message.channel, challenge_message)
	else:
		print(str(datetime.now())+": "+message.author.name+" tried to match a random game, but wasn't queued for anything.")
		await client.send_message(message.channel, "You'll have to queue up for some games before I can match you, "+message.author.mention)
	return

async def tell_aliases(message):
	# aquire map of (full game name) to (list of all aliases for that game)
	sql_games_and_aliases = await db_wrapper.execute(client, message.author, "SELECT game, alias FROM games ORDER BY game", True)
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
		#print("game: "+game)
		readable_aliases += "**"+game+"**: "
		if not game_alias_map[game]:
			readable_aliases+= "No aliases so far.\n"
			continue
		for alias in game_alias_map[game]:
			#print("alias: "+alias)
			readable_aliases += alias+", "
		readable_aliases = readable_aliases[:-2] # there are no aliases left, so remove that last comma + space
		readable_aliases += "\n"

	print(str(datetime.now())+ ": gave game/alias map to "+str(message.author.name))
	await client.send_message(message.author, "Here are all the aliases available for games I have available: \n" + readable_aliases)
	return

#This is probably not the best way to do these things, but that's ok
f = open('auth/discord_token', 'r')
token = f.readline().strip('\n')
f.close()
f = open('auth/mysql_auth', 'r')
db_user = f.readline().strip('\n')
db_pwd = f.readline().strip('\n')
db_host = f.readline().strip('\n')
db_db = f.readline().strip('\n')
db_wrapper = DB_Wrapper(db_user, db_pwd, db_host, db_db)
client.run(token)

