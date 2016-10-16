import discord
import asyncio
import MySQLdb
import random
from db_wrapper import DB_Wrapper
from datetime import datetime

client = discord.Client()

@client.event
async def on_message(message):
	#don't reply to myself
	if message.author == client.user:
		return

	if any(x.id == client.user.id for x in message.mentions) or message.content.startswith('SFCJbot'):
		command = message.content

		if "match" in command:
			hopefully_a_game = command.split('match', 1)[-1].lstrip()
			if hopefully_a_game == '':
				await match_random_game(message)
				return
			results = await db_wrapper.execute(client, message.author, "SELECT user FROM users JOIN games ON FIND_IN_SET(user,players) WHERE game='"+hopefully_a_game+"' AND status='here'", True)
			print(str(datetime.now())+": "+message.author.name+" requested a match in "+hopefully_a_game+" and found: "+str(results))
			if results is None:
				await client.send_message(message.channel, 'Sorry, I couldn\'t find a match for you.\nDed gaem lmao')
				return
			results_list=[]
			for i in results:
				if message.server.get_member(i[0]):
					tmp_string = str(message.server.get_member(i[0]).mention)
					results_list.append(tmp_string)
			if message.author.mention in results_list:
				results_list.remove(message.author.mention)

			# remove users based on status (only users present should be pinged)
			for member_id in results_list:
				member_status = ""
				member = message.server.get_member(member_id)
				if member:
					member_status = member.status
				if member_status!=discord.Status.online:
					results_list.remove(member_id)
					print(str(datetime.now())+": removed "+member_id+" from the list because they were not available.")

			if len(results_list)<1:
				await client.send_message(message.channel, 'Sorry, I couldn\'t find a match for you.\nDed gaem lmao')
				return

			challenge_message = 'Hey, ' + ", ".join(results_list) +' let\'s play some '+hopefully_a_game+' with '+message.author.mention
			await client.send_message(message.channel, challenge_message)
			#FIXME make this logging statement log user names of people matched
			print(str(datetime.now())+": final match list for "+hopefully_a_game+": "+", ".join(results_list))
			return

		if "help" in command.lower():
			await client.send_message(message.author, "I\'m SFCJbot! I help SFCJ members play their favorite fighting games! Check out https://github.com/krehera/SFCJbot for documentation.")
			return

		if "here" in command.lower():
			await add_new_user_if_needed(message)
			result = await db_wrapper.execute(client, message.author, "UPDATE users SET status='here' WHERE user=" + message.author.id, False)
			if result is None:
				print(time+": failed to set "+message.author.name+" to here.")
				await client.send_message(message.author, "I was unable to set your status to here. Please ask Chish#2578 to check the logs at time "+time)
				return
			print(str(datetime.now())+": set "+message.author.name+" to here.")
			await client.send_message(message.author, "Your status was changed to 'here.'")
			return

		if "afk" in command.lower() or "away" in command.lower():
			await add_new_user_if_needed(message)
			result = await db_wrapper.execute(client, message.author, "UPDATE users SET status='afk' WHERE user="+message.author.id, False)
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
			sql_command = "UPDATE users SET region='"+hopefully_a_region+"' WHERE user='"+message.author.id+"'"
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
			games = await db_wrapper.execute(client, message.author, "SELECT game FROM games", True)
			print(str(datetime.now())+": found games: "+str(games))
			games_list = []
			for i in games:
				games_list.append(i[0])
			games_message = 'I offer the following games: '+ ", ".join(games_list) + "."
			await client.send_message(message.author, games_message)
			return

		if "describe" in command.lower():
			command = command.split('describe', 1)[-1].lstrip().rstrip()
			users_games = await db_wrapper.execute(client, message.author, "SELECT games FROM users WHERE username ='"+command+"'", False)
			users_games = users_games[0][0]
			#users_games = users_games[0]
			if users_games:
				users_games = users_games.split(",")
				await client.send_message(message.author, command+" is queued up for "+", ".join(users_games))
				print(str(datetime.now())+": told "+message.author.name+" that "+command+" is queued up for "+", ".join(users_games))
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
			await addgame(command.split('addgame',1)[-1].lstrip(), message)
			return

		if "about" in command.lower():
			await client.send_message(message.author, "SFCJbot is running on a Raspberry Pi and is powered by the following technologies:\nRaspbian GNU/Linux 8 (jessie)\nPython 3.5\nDiscord.py\nMySQL and MySQLdb")
			return

async def add_new_user_if_needed(message):
	#This method also catches nickname changes (with the lower part there)
	search_for_user = "SELECT user FROM users WHERE user="+message.author.id
	result = await db_wrapper.execute(client, message.author, search_for_user, True)
	#print(str(datetime.now())+" add_new_user_if_needed found user: "+str(result))
	if str(result) == "()":
		await db_wrapper.execute(client, message.author, "INSERT INTO users (user) VALUES ("+message.author.id+")", True)
		print(str(datetime.now())+": added user "+message.author.id)

	search_for_user = "SELECT username FROM users WHERE user="+message.author.id
	result = await db_wrapper.execute(client, message.author, search_for_user, True)
	if str(result) != message.author.name:
		await db_wrapper.execute(client, message.author, "UPDATE users SET username='"+message.author.name+"' WHERE user='"+message.author.id+"'", True)
		print(str(datetime.now())+": set user "+message.author.id+" to username "+message.author.name)
	return

async def queue(message, command):
	await add_new_user_if_needed(message)
	hopefully_list_of_games = command.split(" ")
	for i in hopefully_list_of_games:
		#print("Searching for "+i)
		a_game = await db_wrapper.execute(client, message.author, "SELECT game FROM games WHERE game='"+i+"'", True)
		#print("found game "+ str(a_game))
		if str(a_game) != "()":
			already_queued = await is_member_queued_for_game(message.author, i)
			if not already_queued:
				await db_wrapper.execute(client, message.author, "UPDATE games SET players = IFNULL(CONCAT(players,',"+message.author.id+"'),'"+message.author.id+"') WHERE game='"+i+"'", True)
				await db_wrapper.execute(client, message.author, "UPDATE users SET games = IFNULL(CONCAT(games,',"+i+"'),'"+i+"') WHERE user="+message.author.id, True)
				print(str(datetime.now())+": added "+message.author.name+" to the queue for "+i)
				await client.send_message(message.author, "Added you to the queue for " + i)
			else:
				print(str(datetime.now())+": "+message.author.name+" was already queued for "+i)
				await client.send_message(message.author, "You're already queued up for "+i+".")
		else:
			await client.send_message(message.author, "I\'ve never heard of a game called " + i)
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
	dbresult = await db_wrapper.execute(client, member, "SELECT players FROM games WHERE game='"+game+"'", True)
	#print("is_member_queued_for_game result: "+str(dbresult))
	playerlist = str(dbresult[0][0]).split(",")
	if str(playerlist) == "None":
		return False
	for i in playerlist:
		if i == member.id:
			return True
	return False

async def unqueue(message, command):
	await add_new_user_if_needed(message)
	hopefully_list_of_games = command.split(" ")
	for i in hopefully_list_of_games:
		a_game = await db_wrapper.execute(client, message.author, "SELECT game FROM games WHERE game='"+i+"'", True)
		if str(a_game) != "()":
			already_queued = await is_member_queued_for_game(message.author, i)
			if already_queued:
				users_games_unformatted = await db_wrapper.execute(client, message.author, "SELECT games FROM users WHERE user='"+message.author.id+"'", True)
				users_games = list(users_games_unformatted)
				#print("user's games: "+str(users_games))
				if users_games:
					#print("user is queued up for: "+str(users_games))
					#print("trying to unqueue: "+i)
					if i in users_games:
						users_games.remove(i)
						#print("new queue list: "+users_games)
						await db_wrapper.execute(client, message.author, "UPDATE users SET games='"+users_games+"' WHERE user='"+message.author.id+"'", True)
				games_players_unformatted = await db_wrapper.execute(client, message.author, "SELECT players FROM games WHERE game='"+i+"'", True)
				print("game's players: "+str(games_players_unformatted))
				games_players = games_players_unformatted[0][0].split(',')
				if games_players:
					#print("games_players: "+str(games_players))
					if message.author.id in games_players:
						games_players.remove(message.author.id)
						#print("new games_players: "+str(games_players))
						if not games_players:
							await db_wrapper.execute(client, message.author, "UPDATE games SET players=NULL WHERE game='"+i+"'", True)
						else:
							new_list_of_players=",".join(games_players)
							update_list_of_players="UPDATE games SET players='"+new_list_of_players+"' WHERE game='"+i+"'"
							await db_wrapper.execute(client, message.author, update_list_of_players, True)
				print(str(datetime.now())+": removed "+message.author.name+" from the queue for "+i)
				await client.send_message(message.author, "Removed you from the queue for "+i)
			else:
				await client.send_message(message.author, "You aren't in the queue for "+i)
		else:
			await client.send_message(message.author, "I\'ve never heard of a game called " + i)
	return

@client.event
async def on_ready():
	print(str(datetime.now()) + ": logged in as "+client.user.name)
	return

async def match_random_game(message):
	#first, we make a list of all the games the member is queued for.
	users_games = await db_wrapper.execute(client, message.author, "SELECT games FROM users WHERE user ='"+message.author.id+"'", False)
	users_games = users_games[0][0].split(",")
	#print("users_games: "+str(users_games))
	games_to_players = {}
	if users_games:
		for game in users_games:
			temp=await db_wrapper.execute(client, message.author, "SELECT user FROM users JOIN games ON FIND_IN_SET(user,players) WHERE game='"+game+"' AND status='here'", True)
			#print("temp: "+str(temp))
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

#This is probably not the best way to do these things, but that's ok
f = open('.token', 'r')
token = f.readline().strip('\n')
f.close()
f = open('.mysql_auth', 'r')
db_user = f.readline().strip('\n')
db_pwd = f.readline().strip('\n')
db_host = f.readline().strip('\n')
db_db = f.readline().strip('\n')
db_wrapper = DB_Wrapper(db_user, db_pwd, db_host, db_db)
client.run(token)

