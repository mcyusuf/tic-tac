import discord
import asyncio
from discord.ext import commands
import stater
from game import Game
import ai

TOKEN_FILE = "secret_token_stuff.txt"

bot = commands.Bot(command_prefix="!")
games = {}
challenges = {} # channel -> (challeger, challenged)

def remove_challenge(channel):
	challenges.pop(channel)

def add_challenge(channel, a, b):
	challenges[channel] = (a, b)

@bot.command()
async def challenge(ctx, m: discord.Member):
	channel = ctx.channel
	if channel in challenges:
		await ctx.send("There is already an challenge in this channel. Go somewhere else!")
		return

	add_challenge(ctx.channel, ctx.author, m)
	await ctx.send("You have been challenged {}, do you have the balls to accept it?".format(m.mention))


@bot.command()
async def accept(ctx):
	if not ctx.channel in challenges or challenges[ctx.channel][1] != ctx.author:
		await ctx.send("Chill, noone is challenging you.")
		return
	
	a, b = challenges[ctx.channel]
	remove_challenge(ctx.channel)
	await start_game(ctx.channel, b, a)
	await ctx.send("The game is on!")
	return


@bot.command()
async def decline(ctx):
	if not ctx.channel in challenges or challenges[ctx.channel][1] != ctx.author:
		await ctx.send("Chill, noone is challenging you.")
		return
	
	remove_challenge(ctx.channel)
	await ctx.send("Run, you coward!")


async def start_game(channel, p1, p2):
	if channel in games:
		await channel.send("Game is already under way you dummy!")
		return

	games[channel] = Game(p1, p2)
	await channel.send( games[channel].draw_board() )
	print(p1.display_name)
	g = games[channel]
	if g.current_player() == bot.user:
		await make_ai_move(channel, games[channel])


async def make_ai_move(channel, g):
	if g.current_player() != bot.user:
		print("Not  ai turn!")
		return

	win = g.player_move( ai.next_move(g) )

	await channel.send( g.draw_board() )
	if win:
		await player_won(channel, g, bot.user)
		end_game(channel)


def end_game(channel):
	games.pop(channel)


async def player_won(channel, g, p):
	stater.write_game_result(channel.guild.name, p.id, g.enemy(p).id)
	await channel.send('{0} won! gg wp!'.format(p.mention))


async def validate_turn(ctx):
	if ctx.channel not in games:
		await ctx.channel.send("No game is gaming, gamer!")
		return False
	g = games[ctx.channel]
	p = ctx.message.author
	if not p in g.players:
		await ctx.channel.send("Not your game!")
		return False
	if not g.has_turn(p):
		await ctx.channel.send("Not your turn!")
		return False
	return True

@bot.command()
async def stats(ctx):
	data = [ ( (await ctx.guild.fetch_member(p)).display_name, st[0], st[1] ) 
				for p, st in stater.get_stats(ctx.guild.name).items() ]

	s = []
	longest = 0
	if data:
		longest = len( max(data, key=lambda x: len(x[0]) )[0] )
	longest += 1

	for usr, wins, loses in data:
		s.append( ('{:<' + str(longest) + '} {:>2} wins {:>2} loses\n').format(usr + ":", wins, loses) )

	await ctx.channel.send( "```" + "".join(s) + "```" )


@bot.command()
async def start(ctx, p1: discord.Member, p2: discord.Member):
	await start_game(ctx.channel, p1, p2)


@bot.command()
async def end(ctx):
	end_game(ctx.channel)
	await ctx.channel.send("Game ended!")


@bot.command()
async def surr(ctx):
	valid = await validate_turn(ctx)
	if not valid:
		return
	g = games[ctx.channel]
	p = ctx.message.author
	await player_won(ctx.channel, g, g.enemy(p))
	end_game(ctx.channel)


@bot.command()
async def put(ctx, x: int):
	if not await validate_turn(ctx):
		return
	g = games[ctx.channel]
	p = ctx.message.author
	win = g.player_move(x)
	await ctx.channel.send( g.draw_board() )
	if win:
		await player_won(ctx.channel, g, p)
		end_game(ctx.channel)
		return

	if g.current_player() == bot.user:
		await make_ai_move(ctx.channel, g)

@bot.command()
async def show(ctx):
	if ctx.channel not in games:
		await ctx.channel.send("No game is gaming, gamer!")
		return
	await ctx.channel.send( games[ctx.channel].draw_board() )

@bot.command()
async def turn(ctx):
	if ctx.channel not in games:
		await ctx.channel.send("No game is gaming, gamer!")
		return
	await ctx.channel.send( games[ctx.channel].current_player().display_name )

"""
@bot.group()
async def tic(ctx):
	pass

@tic.command()
async def put(ctx, ...):
	....
"""

"""
async def put(s, channel):
	tokens = [ int(x) for x in s.split() if x.isdigit() ]
	if (len(tokens) != 1):
		print('Invalid command: {0}'.format(s))
		return False;

	win = await put(tokens[0], mark, channel)
	next_round()

	return win
"""
@bot.event
async def on_ready():
	print('We have logged in as {0.user}'.format(bot))

#@bot.event
#async def on_command_error(ctx, err):
#	await ctx.channel.send("wrong command!")
"""
@client.event
async def on_message(message):
	if message.author == client.user:
		return

	if message.content.startswith('!tic init'):
		init_game()
		await message.channel.send(draw_board())

	if message.content.startswith('!tic put'):
		win = await player_move(message.content, message.channel)
		await message.channel.send(draw_board())
		if win:	
			await message.channel.send('{0} won! gg wp!'.format(message.author.mention))
"""

# run the bad boi
with open(TOKEN_FILE, "r") as file:
	bot.run( file.read().rstrip() )
