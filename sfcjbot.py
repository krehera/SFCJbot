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
		await client.send_message(message.channel, 'received.')
		command = message.content
		if command.startswith('<@'+client.user.id+'>'):
			idlength = len(client.user.id) + 3
			command = command[idlength:]
		else:
			command = command[7:]
		#remove whitespace from BEGINNING of command
		command = command.lstrip()
		
		return

	#remove this bit after all debugging is done
	print (message.content)

@client.event
async def on_ready():
	print('logged in as '+client.user.name)

#This is probably the wrong way to do these things, but I don't care.
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
