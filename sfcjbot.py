import discord
import asyncio

client = discord.Client()

@client.event
async def on_message(message):
	#don't reply to myself
	if message.author == client.user:
		return

	if message.content.startswith('<@'+client.user.id+'>') or message.content.startswith('SFCJbot'):
		await client.send_message(message.channel, 'received.')
		return

	#remove this bit after all debugging is done
	print (message.content)

@client.event
async def on_ready():
	print('logged in as '+client.user.name)

f = open('.token', 'r')
token = f.readline().strip('\n')
f.close()
client.run(token)
