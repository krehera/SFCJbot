import discord
import asyncio
import MySQLdb

client = discord.Client()

@client.event
async def on_message(message):
	#don't reply to myself
	if message.author == client.user:
		return

	if message.content.startswith('<@'+client.user.id+'>') or message.content.startswith('SFCJbot'):
		command = message.content
		if command.startswith('<@'+client.user.id+'>'):
			idlength = len(client.user.id) + 3
			command = command[idlength:]
		else:
			command = command[7:]
		#remove whitespace from BEGINNING of command
		command = command.lstrip()
		if command.startswith('match '):
			hopefully_a_game = command[6:]
			print( "hopefully_a_game: "+hopefully_a_game)
			if hopefully_a_game == '':
				await client.send_message(message.channel, 'If you need help, too bad.')
				return
			db_cursor = db_connection.cursor()
			db_cursor.execute("""SELECT user FROM users JOIN games ON FIND_IN_SET(user,players) WHERE game=%s""", (hopefully_a_game,))
			results = db_cursor.fetchall()
			db_cursor.close()
			if results == '()':
				await client.send_message(message.channel, 'Sorry, I couldn\'t find a match for you.')
				return
			results_list=[]
			for i in results:
				results_list.append('server.get_member('+i[0]+').mention()')
			if message.author.id in results_list:
				results_list.remove(message.author.id)
			challenge_message = 'Hey, ' + ", ".join(results_list) +' let\'s play some '+hopefully_a_game+' with '+message.author.mention
			await client.send_message(message.channel, challenge_message)
			return

		if command.startswith('here'):
			await add_new_user_if_needed(message)
			db_cursor = db_connection.cursor()
			db_cursor.execute("""UPDATE users SET status='here' WHERE user=%s""",(message.author.id,))
			db_connection.commit()
			db_cursor.close()
			await client.send_message(message.author, "Your status was changed to 'here.'")
			return

		if command.startswith('afk'):
			await add_new_user_if_needed(message)
			db_cursor = db_connection.cursor()
			db_cursor.execute("""UPDATE users SET status='afk' WHERE user=%s""",(message.author.id,))
			db_connection.commit()
			db_cursor.close()
			await client.send_message(message.author, "Your status was changed to 'afk.'")
			return
		
		if command.startswith('region '):
			hopefully_a_region = command[7:]
			await add_new_user_if_needed(message)
			db_cursor = db_connection.cursor()
			db_cursor.execute("""UPDATE users SET region=%s WHERE user=%s""",(hopefully_a_region,message.author.id))
			db_connection.commit()
			db_cursor.close()
			await client.send_message(message.author, "Your region has been set to "+hopefully_a_region+".")
			return

		if command.startswith('games'):
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

		if command.startswith('queue '):
			command = command[6:]
			await queue(message, command)
			return

		if command.startswith('Q '):
			command = command[2:]
			await queue(message, command)
			return

	#remove this bit after all debugging is done
	print (message.content)

async def add_new_user_if_needed(message):
	db_cursor = db_connection.cursor()
	db_cursor.execute("""SELECT user FROM users WHERE user=%s""",(message.author.id,))
	result = db_cursor.fetchone()
	if result == '':
		db_cursor.execute("""INSERT INTO users (user) VALUES (%s)""",(message.author.id,))
	db_connection.commit()
	db_cursor.close()
	return

async def queue(message, command):
	await add_new_user_if_needed(message)
	hopefully_list_of_games = command.split(" ")
	db_cursor = db_connection.cursor()
	for i in hopefully_list_of_games:
		db_cursor.execute("""SELECT game FROM games WHERE game=%s""",(i,))
		a_game = db_cursor.fetchone()[0]
		if a_game != "":
			already_queued = await is_member_queued_for_game(message.author, a_game)
			if not already_queued:
				db_cursor.execute("""UPDATE games SET players = concat(players,%s) WHERE game=%s""",(','+message.author.id,i[0]))
				db_cursor.execute("""UPDATE users SET games = concat(games,%s) WHERE user=%s""",(','+i[0],message.author.id))
				await client.send_message(message.author, "Added you to the queue for " + a_game)
			else:
				await client.send_message(message.author, "You're already queued up for "+a_game+".")
		else:
			await client.send_message(message.author, "I\'ve never heard of a game called " + a_game)
	db_connection.commit()
	db_cursor.close()	
	return

async def is_member_queued_for_game(member,game):
	db_cursor = db_connection.cursor()
	db_cursor.execute("""SELECT players FROM games WHERE game=%s""",(game,))
	dbresult = db_cursor.fetchone()[0]
	db_cursor.close()
	player_list = dbresult.split(",")
	for i in player_list:
		if i == member.id:
			return True
	return False

@client.event
async def on_ready():
	print('logged in as '+client.user.name)

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

