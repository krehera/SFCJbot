import discord
import asyncio
import MySQLdb
from datetime import datetime

client = discord.Client()

@client.event
async def on_message(message):
	#don't reply to myself
	if message.author == client.user:
		return

	if any(x.id == client.user.id for x in message.mentions) or message.content.startswith('SFCJbot'):
		db_connection.ping()
		command = message.content

		if "match" in command:
			hopefully_a_game = command.split('match', 1)[-1].lstrip()
			if hopefully_a_game == '':
				await client.send_message(message.channel, 'If you need help, too bad.')
				return
			results = await db_wrapper.execute(message.author, "SELECT user FROM users JOIN games ON FIND_IN_SET(user,players) WHERE game="+hopefullly_a_game+" AND status='here'")
			print("match results: "+str(results))
			#FIXME should remove message.author from list and then check if < 1
			if len(results) < 2:
				await client.send_message(message.channel, 'Sorry, I couldn\'t find a match for you.\nDed gaem lmao')
				return
			results_list=[]
			for i in results:
				tmp_string = str(message.server.get_member(i[0]).mention)
				results_list.append(tmp_string)
			if message.author.mention in results_list:
				results_list.remove(message.author.mention)
			challenge_message = 'Hey, ' + ", ".join(results_list) +' let\'s play some '+hopefully_a_game+' with '+message.author.mention
			await client.send_message(message.channel, challenge_message)
			return

		if "help" in command.lower():
			await client.send_message(message.author, "I\'m SFCJbot! I help SFCJ members play their favorite fighting games! Check out https://github.com/krehera/SFCJbot for documentation.")
			return

		if "here" in command.lower():
			await add_new_user_if_needed(message)
			await db_wrapper(message.author, "UPDATE users SET status='here' WHERE user=" + message.author.id)
			print(str(datetime.now())+": set "+message.author.name+" to here.")
			await client.send_message(message.author, "Your status was changed to 'here.'")
			return

		if "afk" in command.lower() or "away" in command.lower():
			await add_new_user_if_needed(message)
			await db_wrapper(message.author, "UPDATE users SET status='afk' WHERE user="+message.author.id)
			print(str(datetime.now())+": set "+message.author.name+" to afk.")
			await client.send_message(message.author, "Your status was changed to 'afk.'")
			return
		
		if "region" in command.lower():
			hopefully_a_region = command.split('region', 1)[-1].lstrip()
			await add_new_user_if_needed(message)
			db_cursor = db_connection.cursor()
			db_cursor.execute("""UPDATE users SET region=%s WHERE user=%s""",(hopefully_a_region,message.author.id))
			db_connection.commit()
			db_cursor.close()
			await client.send_message(message.author, "Your region has been set to "+hopefully_a_region+".")
			return

		if "games" in command.lower():
			games = await db_wrapper(message.author, "SELECT game FROM games")
			print(str(datetime.now())+": found games: "+str(games))
			games_list = []
			for i in games:
				games_list.append(i[0])
			games_message = 'I offer the following games: '+ ", ".join(games_list) + "."
			await client.send_message(message.author, games_message)
			return

		if "unqueue" in command.lower():
			command = command.split('unqueue', 1)[-1].lstrip()
			await unqueue(message, command)
			return

		if command.startswith('Q '):
			command = command[2:]
			await queue(message, command)
			return

		if "queue" in command.lower():
			command = command.split('queue', 1)[-1].lstrip()
			await queue(message, command)
			return

		if command.startswith('unQ '):
			command = command[4:]
			await unqueue(message, command)
			return

		if command.startswith('addgame '):
			command = command[8:]
			if message.author.permissions_in(message.channel).kick_members:
				game_to_add = command
				add_game="INSERT INTO games (game) VALUES ("+game_to_add+")"
				await db_wrapper(message.author, add_game)
				print(str(datetime.now())+": added game "+game_to_add)
				await client.send_message(message.author, "added game "+game_to_add+". If you messed up, ping the bot owner!")
			else:
				await client.send_message(message.author, "You don't have permission to add games.")
			return

		if "about" in command.lower():
			await client.send_message(message.author, "SFCJbot is running on a Raspberry Pi and is powered by the following technologies:\nRaspbian GNU/Linux 8 (jessie)\nPython 3.5\nDiscord.py\nMySQL and MySQLdb\ngit (of course)\nand my preferred text editor, vim")
			return

async def add_new_user_if_needed(message):
	search_for_user = "SELECT user FROM users WHERE user="+message.author.id
	result = await db_wrapper(message.author, search_for_user)
	#print("add_new_user_if_needed found user: "+str(result[0][0]))
	if str(result) == 'None':
		await db_wrapper(message.author, "INSERT INTO users (user) VALUES ("+message.author.id+")")
		print("added user "+message.author.name+" as "+message.author.id)
	return

async def queue(message, command):
	await add_new_user_if_needed(message)
	hopefully_list_of_games = command.split(" ")
	for i in hopefully_list_of_games:
		#print("Searching for "+i)
		a_game = await db_wrapper(message.author, "SELECT game FROM games WHERE game='"+i+"'")
		print("found game "+ str(a_game))
		if str(a_game) != "None":
			already_queued = await is_member_queued_for_game(message.author, i)
			if not already_queued:
				await db_wrapper(message.author, "UPDATE games SET players = IFNULL(CONCAT(players,',"+message.author.id+"'),'"+message.author.id+"') WHERE game='"+i+"'")
				await db_wrapper(message.author, "UPDATE users SET games = IFNULL(CONCAT(games,',"+i+"'),'"+i+"') WHERE user="+message.author.id)
				print(str(datetime.now())+": added "+message.author.name+" to the queue for "+i)
				await client.send_message(message.author, "Added you to the queue for " + i)
			else:
				print(str(datetime.now())+": "+message.author.name+" was already queued for "+i)
				await client.send_message(message.author, "You're already queued up for "+i+".")
		else:
			await client.send_message(message.author, "I\'ve never heard of a game called " + i)
	return

async def is_member_queued_for_game(member, game):
	dbresult = await db_wrapper(member, "SELECT players FROM games WHERE game='"+game+"'")
	#print("is_member_queued_for_game result: "+str(dbresult))
	if str(dbresult) == "None":
		return False
	dbresult = str(dbresult[0])
	playerlist = dbresult.split(",")
	for i in playerlist:
		if i == member.id:
			return True
	return False

async def unqueue(message, command):
	await add_new_user_if_needed(message)
	hopefully_list_of_games = command.split(" ")
	for i in hopefully_list_of_games:
		a_game = await db_wrapper(message.author, "SELECT game FROM games WHERE game='"+i+"'")
		if str(a_game) != "None":
			already_queued = await is_member_queued_for_game(message.author, i)
			if already_queued:
				users_games_unformatted = await db_wrapper("SELECT games FROM users WHERE user='"+message.author.id+"'")
				users_games = list(users_games_unformatted)
				print("user's games: "+str(users_games))
				if users_games:
					#print("user is queued up for: "+str(users_games))
					#print("trying to unqueue: "+i)
					if i in users_games:
						users_games.remove(i)
						#print("new queue list: "+users_games)
						await db_wrapper(message.author, "UPDATE users SET games='"+users_games+"' WHERE user='"+message.author.id+"'")
				db_cursor.execute("""SELECT players FROM games WHERE game=%s""",(a_game,))
				games_players_unformatted = await db_wrapper(message.author, "SELECT players FROM games WHERE game='"+a_game+"'")
				print("game's players: "+str(games_players_unformatted))
				games_players = games_players_unformatted[0].split(',')
				if games_players:
					#print("games_players: "+str(games_players))
					if message.author.id in games_players:
						games_players.remove(message.author.id)
						#print("new games_players: "+str(games_players))
						if not games_players:
							await db_wrapper(message.author, "UPDATE games SET players=NULL WHERE game='"+i+"'")
						else:
							new_list_of_players=",".join(games_players)
							update_list_of_players="UPDATE games SET players='"+new_list_of_players+"' WHERE game='"+i+"'"
							await db_wrapper(message.author, update_list_of_players)
				print(str(datetime.now())+": removed "+message.author.name+" from the queue for "+i)
				await client.send_message(message.author, "Removed you from the queue for "+a_game)
			else:
				await client.send_message(message.author, "You aren't in the queue for "+i)
		else:
			await client.send_message(message.author, "I\'ve never heard of a game called " + i)
	return

@client.event
async def on_ready():
	print('logged in as '+client.user.name)
	return

async def db_wrapper(member, execute):
	try:
		db_connection = MySQLdb.connect(user=db_user, passwd = db_pwd, host=db_host, db=db_db)
		cursor = db_connection.cursor()
		cursor.execute(execute)
		result = cursor.fetchall()
		db_connection.commit()
		cursor.close()
		db_connection.close()
	except:
		print(str(datetime.now())+": failed to properly execute DB command: "+execute)
		await client.send_message(member, "I had some trouble with a database query, please contact Chish#2578") 
		return
	return result

global db_connection
#This is probably not the best way to do these things, but that's ok
f = open('.token', 'r')
token = f.readline().strip('\n')
f.close()
f = open('.mysql_auth', 'r')
db_user = f.readline().strip('\n')
db_pwd = f.readline().strip('\n')
db_host = f.readline().strip('\n')
db_db = f.readline().strip('\n')
db_connection = MySQLdb.connect(user=db_user, passwd = db_pwd, host=db_host, db=db_db)
client.run(token)

