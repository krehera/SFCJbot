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
			db_cursor = db_connection.cursor()
			db_cursor.execute("""SELECT user FROM users JOIN games ON FIND_IN_SET(user,players) WHERE game=%s AND status='here'""", (hopefully_a_game,))
			results = db_cursor.fetchall()
			db_cursor.close()
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
			db_cursor = db_connection.cursor()
			db_cursor.execute("""UPDATE users SET status='here' WHERE user=%s""",(message.author.id,))
			db_connection.commit()
			db_cursor.close()
			await client.send_message(message.author, "Your status was changed to 'here.'")
			return

		if "afk" in command.lower() or "away" in command.lower():
			await add_new_user_if_needed(message)
			db_cursor = db_connection.cursor()
			db_cursor.execute("""UPDATE users SET status='afk' WHERE user=%s""",(message.author.id,))
			db_connection.commit()
			db_cursor.close()
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
			db_cursor = db_connection.cursor()
			db_cursor.execute("""SELECT game FROM games""")
			games = db_cursor.fetchall()
			db_cursor.execute("""SELECT game FROM games WHERE players IS NOT NULL""")
			games_with_players = db_cursor.fetchall()
			db_cursor.close()
			games_list = []
			for i in games:
				games_list.append(i[0])
			games_message = 'I offer the following games: '+ ", ".join(games_list) + "."
			await client.send_message(message.author, games_message)
			return

		if "queue" in command.lower():
			command = command.split('queue', 1)[-1].lstrip()
			await queue(message, command)
			return

		if command.startswith('Q '):
			command = command[2:]
			await queue(message, command)
			return

		if "unqueue" in command.lower():
			command = command.split('unqueue', 1)[-1].lstrip()
			await unqueue(message, command)
			return

		if command.startswith('unQ '):
			command = command[4:]
			await unqueue(message, command)
			return

		if command.startswith('addgame '):
			command = command[8:]
			if message.author.permissions_in(message.channel).kick_members:
				game_to_add = command
				db_cursor = db_connection.cursor()
				db_cursor.execute("""INSERT INTO games (game) VALUES (%s)""",(game_to_add,))
				db_connection.commit()
				db_cursor.close()
				await client.send_message(message.author, "added game "+game_to_add+". If you messed up, ping the bot owner!")
			else:
				await client.send_message(message.author, "You don't have permission to add games.")
			return

		print("content: " + message.content)
		print("mention ids: " + ", ".join(str(x.id) for x in message.mentions))
		print("my id::::::: " + client.user.id )
		if any(x.id == client.user.id for x in message.mentions):
			print ("I was mentioned")




async def add_new_user_if_needed(message):
	db_connection.ping()
	db_cursor = db_connection.cursor()
	db_cursor.execute("""SELECT user FROM users WHERE user=%s""",(message.author.id,))
	result = db_cursor.fetchone()
	#print("add_new_user_if_needed found user: "+str(result))
	if str(result) == 'None':
		db_cursor.execute("""INSERT INTO users (user) VALUES (%s)""",(message.author.id,))
		print("added user "+message.author.name+" as "+message.author.id)
	db_connection.commit()
	db_cursor.close()
	return

async def queue(message, command):
	await add_new_user_if_needed(message)
	hopefully_list_of_games = command.split(" ")
	db_cursor = db_connection.cursor()
	for i in hopefully_list_of_games:
		#print("Searching for "+i)
		db_cursor.execute("""SELECT game FROM games WHERE game=%s""",(i,))
		a_game = db_cursor.fetchone()
		#print("found game "+ str(a_game))
		if str(a_game) != "None":
			already_queued = await is_member_queued_for_game(message.author, a_game)
			if not already_queued:
				db_cursor.execute("""UPDATE games SET players = IFNULL(CONCAT(players,%s),%s) WHERE game=%s""",(','+message.author.id,message.author.id,i))
				db_cursor.execute("""UPDATE users SET games = IFNULL(CONCAT(games,%s),%s) WHERE user=%s""",(','+i,i,message.author.id))
				await client.send_message(message.author, "Added you to the queue for " + i)
			else:
				await client.send_message(message.author, "You're already queued up for "+i+".")
		else:
			await client.send_message(message.author, "I\'ve never heard of a game called " + i)
	db_connection.commit()
	db_cursor.close()	
	return

async def is_member_queued_for_game(member,game):
	db_connection.ping()
	db_cursor = db_connection.cursor()
	db_cursor.execute("""SELECT players FROM games WHERE game=%s""",(game,))
	dbresult = db_cursor.fetchone()
	db_cursor.close()
	if str(dbresult) == "None":
		return False
	#print(str(dbresult))
	dbresult = str(dbresult[0])
	playerlist = dbresult.split(",")
	for i in playerlist:
		if i == member.id:
			return True
	return False

async def unqueue(message, command):
	await add_new_user_if_needed(message)
	hopefully_list_of_games = command.split(" ")
	db_cursor = db_connection.cursor()
	for i in hopefully_list_of_games:
		db_cursor.execute("""SELECT game FROM games WHERE game=%s""",(i,))
		a_game = db_cursor.fetchone()[0]
		if str(a_game) != "None":
			already_queued = await is_member_queued_for_game(message.author, a_game)
			if already_queued:
				db_cursor.execute("""SELECT games FROM users WHERE user=%s""",(message.author.id,))
				users_games = list(db_cursor.fetchone())
				if users_games:
					#print("user is queued up for: "+str(users_games))
					#print("trying to unqueue: "+i)
					if i in users_games:
						users_games.remove(i)
						#print("new queue list: "+users_games)
						db_cursor.execute("""UPDATE users SET games=%s WHERE user=%s""",(users_games,message.author.id))
				db_cursor.execute("""SELECT players FROM games WHERE game=%s""",(a_game,))
				games_players = list(db_cursor.fetchone())
				if games_players:
					#print("games_players: "+str(games_players))
					if message.author.id in games_players:
						games_players.remove(message.author.id)
						#print("new games_players: "+str(games_players))
						if not games_players:
							db_cursor.execute("""UPDATE games SET players=NULL WHERE game=%s""",(i,))
						else:
							db_cursor.execute("""UPDATE games SET players=%s WHERE game=%s""",(games_players,i))
				await client.send_message(message.author, "Removed you from the queue for "+a_game)
			else:
				await client.send_message(message.author, "You aren't in the queue for "+i)
		else:
			await client.send_message(message.author, "I\'ve never heard of a game called " + i)
	db_connection.commit()
	db_cursor.close()
	return

@client.event
async def on_ready():
	print('logged in as '+client.user.name)

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

