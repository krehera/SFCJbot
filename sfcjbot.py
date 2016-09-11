import discord
import asyncio
import MySQLdb
import re

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
		if command.startswith('match'):
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
				results_list.append('@'+i[0])
			results_list.remove('@'+message.author.name)
			challenge_message = 'Hey, ' + ", ".join(results_list) +' let\'s play some '+hopefully_a_game+' with '+'@'+message.author.name
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

