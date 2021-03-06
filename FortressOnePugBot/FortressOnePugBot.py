import asyncio
import logging
import os
import sys
import time
from pprint import pprint
from random import randrange
# https://docs.python.org/3/library/threading.html#timer-objects
from datetime import datetime, timedelta
from pytz import timezone

import discord
from discord.ext import commands

# PUG SPAM
# @here and @channel-region used on !startpug
#	There should be PUG regions, where people are happy to pug in. Those regions will be pinged only when a game starts.
# @channel-region used when 3, 2, or 1 players are needed to get the game going.
# reset the timer whenever someone joins
# DM the player when the pug has started due to having enough players to play.
# When displaying channel message, if player.nick != None use it, else player.name.
# duel mode

# switch message to embed
# Remove HH:MM:SS from pug start message
# replace crappy text with nicely formatted stuff
# rewrite default help
# qw://sydney.fortressone.org:27503 connect string links

# KNOWN ISSUES
# if someone disconnects it doesnt remove them from the pug
# @KABUTO has been added to the blue team. 9/8 current players.

# Enable debugging messages - https://docs.python.org/3/library/asyncio-dev.html#logging
debugging = False
if debugging:
	logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - [%(levelname)s] - %(message)s')
else:
	logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger("asyncio")

if debugging:
	MIN_TEAM_SIZE = 1
	DEFAULT_TEAM_SIZE = 1
else:
	MIN_TEAM_SIZE = 2
	DEFAULT_TEAM_SIZE = 4
MAX_TEAM_SIZE = 8
DEFAULT_MAX_PLAYERS = DEFAULT_TEAM_SIZE * 2
SECONDS_IN_MINUTE = 60
MINUTES_IN_HOUR = 60
HOURS_UNTIL_TIMEOUT = 4 # Change this to adjust timer
if debugging:
	TIME_OUT_SECONDS = SECONDS_IN_MINUTE * 5
else:
	TIME_OUT_SECONDS = SECONDS_IN_MINUTE * MINUTES_IN_HOUR * HOURS_UNTIL_TIMEOUT
TIME_OUT_HUMAN_READABLE = timedelta(seconds=TIME_OUT_SECONDS)


# Print start message and delay slightly
logging.info('Starting ' + os.path.relpath(sys.argv[0]))
time.sleep(.001)

time_zones = {
	"au_aest": "Australia/Brisbane",
	"au_aedt": "Australia/Sydney",
	"eu_est": "EST",
	"nz_auck": "Pacific/Auckland",
	"kr_seoul": "Asia/Seoul",
	"jp_tokyo": "Asia/Tokyo",
	"us_pst": "America/Los_Angeles",
	"us_cst": "America/Mexico_City",
	"us_est": "America/New_York",
	"us_bra": "America/Sao_Paulo"
	#TODO !gmt, convert current timeout time to user's locale
}

# Memes
all_memes = {
	"clans": {
		"a": [],
		"dacc": [],
		"fabb": [],
		"sobar": []
	},
	"players": {
		"basss": [],
		"bigdal": [],
		"loki": [],
		"seano": [],
		"wolv": []
	}
}

# Pugs for each region
if debugging:
	game_channels = ["bot-testing", "bot-testing-one", "bot-testing-two"]
else:
	game_channels = [
		"bot-testing",
		"bot-testing-one",
		"bot-testing-two",
		"oceania",
		"north-america",
		"brazil",
		"europe",
		"east-asia",
		"pick-up-games" # for Action Quake 2
	]

all_pugs = {}
for channel in game_channels:
	# Hard code the role IDs which I got from the !g command below
	if channel == "oceania":
		role_id = 427655970177548288
	elif channel == "north-america":
		role_id = 522695282887229440
	elif channel == "south-america":
		role_id = 531050407246561280
	elif channel == "europe":
		role_id = 533995292975038479
	elif channel == "east-asia":
		role_id = 543039259133739028
	elif channel == "bot-testing":
		role_id = 595880090131365888
	elif channel == "bot-testing-one":
		role_id = 646638599269384193
	elif channel == "bot-testing-two":
		role_id = 646645808053092362
	elif channel == "pick-up-games":
		role_id = None
	else:
		role_id = None

	# Set up the data structure for each channel.
	all_pugs[channel] = {
		"active": False,
		"timeoutTimer": None,
		"timeoutTimes": [],
		"teams": {
			"red": [],
			"blue": [],
			"lastAdded": "",
			"size": DEFAULT_TEAM_SIZE,
			"maxPlayers": DEFAULT_MAX_PLAYERS
		},
		# TODO test role mentions via role ID
		"roleId": role_id
	}


async def mention_role(context):
	channel = context.message.channel
	await context.send(discord.utils.get(context.guild.roles, name=all_pugs[channel.name]["roleName"]).mention)


async def get_timeout_times(context):
	channel = context.message.channel
	timeout_times = ""
	for a_time in all_pugs[channel.name]['timeoutTimes']:
		timeout_times += "\t" + a_time + "\n"
	return timeout_times


async def get_player_counts(context):
	channel = context.message.channel
	player_counts = {
		"blue": 0,
		"red": 0,
	}
	count = 0
	for player in all_pugs[channel.name]['teams']['blue']:
		count += 1
	player_counts["blue"] = count

	count = 0
	for player in all_pugs[channel.name]['teams']['red']:
		count += 1
	player_counts["red"] = count

	return player_counts


async def get_player_counts_string(context):
	channel = context.message.channel
	player_counts = {
		"blue": 0,
		"red": 0,
	}
	count = 0
	for player in all_pugs[channel.name]['teams']['blue']:
		count += 1
	player_counts["blue"] = count

	count = 0
	for player in all_pugs[channel.name]['teams']['red']:
		count += 1
	player_counts["red"] = count

	return str(player_counts["blue"] + player_counts["red"]) + "/" + str(all_pugs[channel.name]["teams"]["size"] * 2) + " current players."


async def get_red_players(context):
	channel = context.message.channel
	red_players = []
	for player in all_pugs[channel.name]['teams']['red']:
		red_players.append(player)
	return red_players


async def get_red_players_display_names(context):
	channel = context.message.channel
	red_players = ""
	for existing_player in all_pugs[channel.name]['teams']['red']:
		red_players += str(existing_player.mention) + ", "
	if not red_players:
		red_players = "no one"
	else:
		# Remove the last , and space
		red_players = red_players[:-2]
	return red_players


async def get_red_players_mention_names(context):
	channel = context.message.channel
	red_players = ""
	for existing_player in all_pugs[channel.name]['teams']['red']:
		red_players += str(existing_player.mention) + ", "
	if not red_players:
		red_players = "no one"
	else:
		# Remove the last , and space
		red_players = red_players[:-2]
	return red_players


async def get_blue_players(context):
	channel = context.message.channel
	blue_players = []
	for player in all_pugs[channel.name]['teams']['blue']:
		blue_players.append(player)
	return blue_players


async def get_blue_players_display_names(context):
	channel = context.message.channel
	blue_players = ""
	for existing_player in all_pugs[channel.name]['teams']['blue']:
		blue_players += str(existing_player.mention) + ", "
	if not blue_players:
		blue_players = "no one"
	else:
		# Remove the last , and space
		blue_players = blue_players[:-2]
	return blue_players


async def get_blue_players_mention_names(context):
	channel = context.message.channel
	blue_players = ""
	for existing_player in all_pugs[channel.name]['teams']['blue']:
		blue_players += str(existing_player.mention) + ", "
	if not blue_players:
		blue_players = "no one"
	else:
		# Remove the last , and space
		blue_players = blue_players[:-2]
	print(str(blue_players))
	print(blue_players)
	return blue_players


async def set_team_sizes(context, argument):
	channel = context.message.channel
	logging.debug(f"set_team_sizes entered - #{channel.name}")
	if argument.isdigit():
		player = context.message.author
		if int(argument) < MIN_TEAM_SIZE or int(argument) > MAX_TEAM_SIZE:
			# await means to wait until this command has been executed, then continue.
			await context.send(
				f"{player.mention}, your inputs aren't sensible. Must be between {MIN_TEAM_SIZE} and {MAX_TEAM_SIZE}, inclusive.")
		elif all_pugs[context.message.channel.name]["active"]:
			await context.send("Team sizes can only be updated before a PUG has get_ed.")
		else:
			all_pugs[context.message.channel.name]["teams"]["size"] = int(argument)
			all_pugs[context.message.channel.name]["teams"]["maxPlayers"] = int(argument) * 2
			await context.send(
				f"{player.mention} set team sizes set to " + argument + ". Total players allowed is " + str(int(argument) * 2))
	else:
		await context.send("Invalid argument. Must be an Integer.")
	logging.debug(f"set_team_sizes exited - #{channel.name}")


async def start_pug_command(context):
	channel = context.message.channel
	logging.debug(f"start_pug_command entered - #{channel.name}")
	player = context.message.author
	# Check if a PUG is already active for that channel.
	if all_pugs[channel.name]['active']:
		await context.send(
			f"`#{channel.name}` has an existing PUG, {player.mention}. Type `{bot.command_prefix}join` to join a team.")
	else:
		# start the PUG
		all_pugs[channel.name]['active'] = True
		# add the player to a random team in the PUG
		prn = randrange(0, 2)
		if prn == 0:
			all_pugs[channel.name]['teams']['red'].append(player)
			all_pugs[channel.name]['teams']['lastAdded'] = "red"
		else:
			all_pugs[channel.name]['teams']['blue'].append(player)
			all_pugs[channel.name]['teams']['lastAdded'] = "blue"
		team_colour = all_pugs[channel.name]['teams']['lastAdded']
		# Using channel.mention here to notify all people in the channel that a PUG has started.
		#TODO Use @here and channel's region.
		#await context.send(f"@here, {player.mention} started a PUG for {channel.mention} and has joined team {team_colour}.\nThis PUG will automatically end in {TIME_OUT_HUMAN_READABLE} HH:MM:SS")
		channel_name = f"{channel.name}"
		await context.send(f"{player.mention} started a PUG for @here and has joined team {team_colour}.")
		logging.info(f"#{channel.name} PUG started. Ending PUG after {TIME_OUT_SECONDS} seconds.")
		await start_timer(context)
	logging.debug(f"start_pug_command exited - #{channel.name}")


async def end_pug_command(context, pug_timed_out):
	channel = context.message.channel
	logging.debug(f"end_pug_command entered - #{channel.name}")
	player = context.message.author

	if all_pugs[channel.name]['active']:
		# TODO test cancel timer
		#await cancel_timer(context)
		timer_task = all_pugs[channel.name]['timeoutTimer']
		await reset_pug(channel)

		if pug_timed_out:
			await context.send(f"`#{channel.name}` PUG ended due to timeout after {TIME_OUT_HUMAN_READABLE} HH:MM:SS")
			logging.info(f"#{channel.name}` PUG ended due to timeout.")
		else:
			await context.send(f"{player.mention} stopped the PUG for `#{channel.name}`")
			logging.info(f"#{channel.name}` PUG ended due to players.")

		pprint(all_pugs[channel.name]['active'])
	else:
		timer_task = None
		await context.send(
			f"{player.mention}, there is no PUG for `#{channel.name}`. Type `{bot.command_prefix}startpug` to start one.")

	logging.debug(f"end_pug_command exited - #{channel.name}")
	if timer_task is not None and timer_task is not True:
		# TODO fix this cancelling of the timer
		timer_task.cancel()


async def join_pug_command(context):
	channel = context.message.channel
	player = context.message.author
	logging.debug(f"join_pug_command entered - #{channel.name}")
	team_colour = ""
	already_joined = False
	# Check if the PUG is active for the channel, if not start one
	if not all_pugs[channel.name]['active']:
		await context.send(f"There is no PUG for this channel, starting one now.")
		await start_pug_command(context)
		#await context.send(f"{player.mention}, there is no PUG for #`#{channel.name}`. Type `{bot.command_prefix}startpug` to start one.",	help="Start PUG.")
	else:
		# Check if the player has already joined a team.
		for existing_player in all_pugs[channel.name]['teams']['red']:
			if existing_player == player:
				already_joined = True
				team_colour = 'red'
				break
		if not already_joined:
			for existing_player in all_pugs[channel.name]['teams']['blue']:
				if existing_player == player:
					already_joined = True
					team_colour = 'blue'
					break
		# Add the player if they haven't already joined a team
		if not already_joined:
			# Add to blue if red has more players.
			if len(all_pugs[channel.name]['teams']['red']) > len(all_pugs[channel.name]['teams']['blue']):
				all_pugs[channel.name]['teams']['blue'].append(player)
				all_pugs[channel.name]['teams']['lastAdded'] = "blue"
			# Add to red if blue has more players.
			elif len(all_pugs[channel.name]['teams']['red']) < len(all_pugs[channel.name]['teams']['blue']):
				all_pugs[channel.name]['teams']['red'].append(player)
				all_pugs[channel.name]['teams']['lastAdded'] = "red"
			# Add to the next team, the opposite of the last team that got a player.
			else:
				if all_pugs[channel.name]['teams']['lastAdded'] == 'red':
					all_pugs[channel.name]['teams']['blue'].append(player)
					all_pugs[channel.name]['teams']['lastAdded'] = "blue"
				else:
					all_pugs[channel.name]['teams']['red'].append(player)
					all_pugs[channel.name]['teams']['lastAdded'] = "red"
			team_colour = all_pugs[channel.name]['teams']['lastAdded']
			pprint(all_pugs[channel.name])
			# Update player counts
			player_count_str = await get_player_counts_string(context)
			await context.send(f"{player.mention} has been added to the {team_colour} team. {player_count_str}")
			# Start the timer if they are the first player to join
			if len(all_pugs[channel.name]['teams']['red']) == 0 and len(all_pugs[channel.name]['teams']['blue']) == 1 or \
				len(all_pugs[channel.name]['teams']['red']) == 1 and len(all_pugs[channel.name]['teams']['blue']) == 0:
				await start_timer(context)
			# TODO test restart timer
			# Restart the timer if they aren't the first player to join
			else:
				logging.debug(f"timer would be restarted here - #{channel.name}")
				# await restart_timer(context)
			if await are_teams_full(channel):
				all_players = await start_the_game(context)
				await context.send("Game has started! Time to join the server. " + all_players)
				# TODO silently reset the pug as it has started
			else:
				# TODO use region mention for last 3 players
				player_count = await get_player_counts(context)
				if player_count["blue"] + player_count["red"] == 5:
					await context.send(f"@here, 3 more needed.")
				elif player_count["blue"] + player_count["red"] == 6:
					await context.send(f"@here, 2 more needed.")
				elif player_count["blue"] + player_count["red"] == 7:
					await context.send(f"@here, 1 more needed.")
		else:
			await context.send(f"You are on the {team_colour} team already {player.mention}")
	logging.debug(f"join_pug_command exited - #{channel.name}")


async def leave_pug_command(context):
	channel = context.message.channel
	player = context.message.author
	logging.debug(f"leave_pug_command entered.- #{channel.name}")
	team_colour = ""
	already_joined = False
	# Check if a pug exists for this channel
	if not all_pugs[context.message.channel.name]["active"]:
		await context.send(f"{player.mention}, there is no PUG for #`#{channel.name}`. Type `{bot.command_prefix}startpug` to start one.")
	else:
	# Check if the player has already joined
		for existing_player in all_pugs[channel.name]['teams']['red']:
			if existing_player == player:
				already_joined = True
				team_colour = "red"
				break
		if not already_joined:
			for existing_player in all_pugs[channel.name]['teams']['blue']:
				if existing_player == player:
					already_joined = True
					team_colour = "blue"
					break
		if already_joined:
			all_pugs[channel.name]['teams'][team_colour].remove(player)
			if await are_teams_empty(channel):
				# await reset_pug(channel)
				#await context.send(f"{player.mention} has left the {team_colour} team and ended the PUG for `#{channel.name}`. Type `{bot.command_prefix}startpug` to start one.")
				await context.send(f"The PUG is ending because you were the last player.")
				msg = f"{player.mention} stopped the PUG for `#{channel.name}`"
				await end_pug_command(context, False)
				pprint(all_pugs[channel.name])
			else:
				# Reset the last added colour so the correct team gets the next player
				if team_colour == 'red':
					all_pugs[channel.name]['teams']['lastAdded'] = 'blue'
				else:
					all_pugs[channel.name]['teams']['lastAdded'] = 'red'
				player_count = await get_player_counts_string(context)
				await context.send(f"{player.mention} has left the {team_colour} team. {player_count}.")
				# TODO use region mention for last 3 players
		else:
			await context.send(f"You can't leave since you aren't in a team {player.mention}.")
	logging.debug(f"leave_pug_command exited - #{channel.name}")


async def team_pug_status_command(context):
	channel = context.message.channel
	player = context.message.author
	logging.debug(f"team_pug_status_command entered.- #{channel.name}")
	if not all_pugs[channel.name]['active']:
		await context.send(
			f"{player.mention}, there is no PUG for `#{channel.name}`. Type `{bot.command_prefix}startpug` to start one.")
	else:
		# Get the players from both teams
		blue_players = await get_blue_players_display_names(context)
		red_players = await get_red_players_display_names(context)

		player_counts = await get_player_counts(context)
		pprint(player_counts)
		blue = player_counts["blue"]
		red = player_counts["red"]
		team_size = all_pugs[channel.name]["teams"]["size"]
		current_count = blue + red
		expire_times = await get_timeout_times(context)
		max_players = all_pugs[channel.name]["teams"]["maxPlayers"]
		await context.send(f"For the PUG in `#{channel.name}`, there are {current_count}/{max_players} players, and it will currently expire at\n{expire_times}" +
							f"Blue team currently has {blue}/{team_size} - " + blue_players +
							f".\nRed team currently has {red}/{team_size} - " + red_players + ".")
		pprint(all_pugs[channel.name])
		logging.debug(f"team_pug_status_command exited - #{channel.name}")


async def are_teams_empty(channel):
	logging.debug(f"are_teams_empty entered and exited.- #{channel.name}")
	# Check the length of both teams, if they are both 0 we will return True.
	return len(all_pugs[channel.name]['teams']['red']) == 0 and \
		   len(all_pugs[channel.name]['teams']['blue']) == 0


async def are_teams_full(channel):
	logging.debug(f"are_teams_full entered and exited.- #{channel.name}")
	# Check the length of both teams, if they both match team size then return True
	return len(all_pugs[channel.name]['teams']['red']) == all_pugs[channel.name]['teams']['size'] and \
		   len(all_pugs[channel.name]['teams']['blue']) == all_pugs[channel.name]['teams']['size']


#TODO UPDATE THIS WITH NEW FIELDS
async def reset_pug(channel):
	logging.debug(f"reset_pug entered - #{channel.name}")
	all_pugs[channel.name]['active'] = False
	all_pugs[channel.name]['timeoutTimer'] = None
	all_pugs[channel.name]['timeoutTimes'] = []
	all_pugs[channel.name]['teams']['lastAdded'] = ""
	all_pugs[channel.name]['teams']['blue'] = []
	all_pugs[channel.name]['teams']['red'] = []
	all_pugs[channel.name]['teams']['size'] = DEFAULT_TEAM_SIZE
	all_pugs[channel.name]['teams']['maxPlayers'] = DEFAULT_MAX_PLAYERS
	logging.debug(f"reset_pug exited - #{channel.name}")


async def start_the_game(context):
	channel = context.message.channel
	logging.debug(f"start_the_game entered - #{channel.name}")
	all_players = await get_blue_players_mention_names(context)
	all_players += ", "
	all_players += await get_red_players_mention_names(context)
	logging.debug(f"start_the_game exited - #{channel.name}")
	return all_players


async def do_function_after(delay, function):
	logging.debug("do_after_function entered.")
	await asyncio.sleep(delay)
	if debugging:
		logging.debug("do_after_function object print.")
		print(function)
	await function
	logging.debug("do_after_function exited.")


async def start_timer(context):
	channel = context.message.channel
	logging.debug(f"start_timer entered - #{channel.name}")
	# Create the async task
	timer_task = asyncio.create_task(
		# Delay running the passed in function
		do_function_after(delay=TIME_OUT_SECONDS, function=end_pug_command(context, True))
	)
	all_pugs[channel.name]['timeoutTimer'] = timer_task
	if channel.name == 'oceania' or channel.name == 'bot-testing' or channel.name == 'bot-testing-two':
		all_pugs[channel.name]['timeoutTimes'].append("Sydney - " + (datetime.now(timezone(time_zones["au_aedt"])) +
			timedelta(seconds=TIME_OUT_SECONDS)).strftime("%Y-%m-%d %H:%M:%S"))
		all_pugs[channel.name]['timeoutTimes'].append("Auckland - " + (datetime.now(timezone(time_zones["nz_auck"])) +
			timedelta(seconds=TIME_OUT_SECONDS)).strftime("%Y-%m-%d %H:%M:%S"))
		all_pugs[channel.name]['timeoutTimes'].append("zelTime - some time way after what was expected.")
	elif channel.name == 'north-america':
		all_pugs[channel.name]['timeoutTimes'].append("L.A. - " + (datetime.now(timezone(time_zones["us_pst"])) +
			timedelta(seconds=TIME_OUT_SECONDS)).strftime("%Y-%m-%d %H:%M:%S"))
		all_pugs[channel.name]['timeoutTimes'].append("Mexico - " + (datetime.now(timezone(time_zones["us_cst"])) +
			timedelta(seconds=TIME_OUT_SECONDS)).strftime("%Y-%m-%d %H:%M:%S"))
		all_pugs[channel.name]['timeoutTimes'].append("N.Y - " + (datetime.now(timezone(time_zones["us_est"])) +
			timedelta(seconds=TIME_OUT_SECONDS)).strftime("%Y-%m-%d %H:%M:%S"))
	elif channel.name == 'east-asia':
		all_pugs[channel.name]['timeoutTimes'].append("Tokyo/Seoul - " + (datetime.now(timezone(time_zones["jp_tokyo"])) +
			timedelta(seconds=TIME_OUT_SECONDS)).strftime("%Y-%m-%d %H:%M:%S"))
	elif channel.name == 'pick-up-games':
		all_pugs[channel.name]['timeoutTimes'].append("Sydney - " + (datetime.now(timezone(time_zones["au_aedt"])) +
			timedelta(seconds=TIME_OUT_SECONDS)).strftime("%Y-%m-%d %H:%M:%S"))
		all_pugs[channel.name]['timeoutTimes'].append("Auckland - " + (datetime.now(timezone(time_zones["nz_auck"])) +
			timedelta(seconds=TIME_OUT_SECONDS)).strftime("%Y-%m-%d %H:%M:%S"))
	else:
		all_pugs[channel.name]['timeoutTimes'].append("No one uses this here so fuck your time.")

	logging.info(f"#{channel.name} timer started.")
	pprint(all_pugs[channel.name])
	await all_pugs[channel.name]['timeoutTimer']
	logging.debug(f"start_timer exited - #{channel.name}")
	

async def cancel_timer(context):
	channel = context.message.channel
	logging.debug(f"cancel_timer entered - #{channel.name}")
	all_pugs[channel.name]['timeoutTimer'].cancel()
	all_pugs[channel.name]['timeoutTimes'] = []
	logging.info(f"#{channel.name} timer cancelled.")
	if debugging:
		print(all_pugs[channel.name]['timeoutTimer'])
	logging.debug(f"cancel_timer exited - #{channel.name}")


async def restart_timer(context):
	channel = context.message.channel
	logging.debug(f"restart_timer entered - #{channel.name}")
	logging.info(f"#{channel.name} timer restarted with {TIME_OUT_SECONDS} seconds.")
	await cancel_timer(context)
	await start_timer(context)
	logging.debug(f"restart_timer exited - #{channel.name}")


# Create a Bot instance - https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#bot
bot = commands.Bot(
	command_prefix='!',
	case_insensitive=True,
	self_bot=False
)
#bot.case_insensitive = True
bot.description = f"FortressOne PUG bot. Type {bot.command_prefix}help to see available commands."
#bot.self_bot = False # Ignore itself

# TODO Create a channel greeter that asks people to add themselves to a region role
# Wait for the bot to login and be ready
@bot.event
async def on_ready():
	print("Logged in as " + str(bot.user.name) + " with the ID " + str(bot.user.id))
	print("The current version of Discord is " + str(discord.version_info))
	if debugging:
		print("The all_pugs dictionary currently is:\n")
		pprint(all_pugs)


# TODO use cogs to group commands into categories (PUG and meme)
# https://discordpy.readthedocs.io/en/latest/ext/commands/cogs.html#quick-example
# This automatically adds the command - https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html#
@bot.command(description=
			 f"Set the amount of players per team for the PUG on this channel."
			 f" Default is {DEFAULT_TEAM_SIZE}, so {DEFAULT_TEAM_SIZE} vs {DEFAULT_TEAM_SIZE}.",
			 aliases=["ts"],
			 help="Change team sizes.")
async def teamsize(context, argument):
	await set_team_sizes(context, argument)


@bot.command(description="Start a PUG for this channel.", aliases=["s", "start"], help="Start PUG.")
async def startpug(context):
	# Allows me to call this function from other areas
	await start_pug_command(context)


@bot.command(description="End the PUG for this channel.", aliases=["e", "end"], help="End PUG.")
async def endpug(context):
	# Allows me to call this function from other areas
	await end_pug_command(context, False)


@bot.command(description="Join a team on the PUG for this channel.", aliases=["j", "joinski"], help="Join team.")
async def join(context):
	await join_pug_command(context)


@bot.command(description="Leave a team on the PUG for this channel.", aliases=["l", "leaveski"], help="Leave PUG.")
async def leave(context):
	await leave_pug_command(context)


@bot.command(description="Print the current teams and PUG status for the PUG on this channel.",
			 aliases=["pug", "p"], help="Print teams/PUG status.")
async def pugstatus(context):
	await team_pug_status_command(context)


@bot.command(description="Print timezones common to FortressOne player regions..", aliases=["t"], help="Print time.")
async def time(context):
	message = ""
	for k,v in time_zones.items():
		message += f"Current time in {v} is " + datetime.now(timezone(v)).strftime("%Y-%m-%d %H:%M:%S\n")

	await context.send(message)


# @bot.command(aliases=["tst"])
# async def test_start_timer(context):
# 	await context.send(f"Start test timer with {TIME_OUT_HUMAN_READABLE} HH:MM:SS")
# 	await start_timer(context)
# 
# 
# @bot.command(aliases=["tct"])
# async def test_cancel_timer(context):
# 	await context.send(f"Cancelling test timer.")
# 	await cancel_timer(context)
# 
# 
# @bot.command(aliases=["trt"])
# async def test_restart_timer(context):
# 	await context.send(f"Restarting test timer with {TIME_OUT_HUMAN_READABLE} HH:MM:SS")
# 	await restart_timer(context)

# https://discordpy.readthedocs.io/en/latest/api.html#guild
#@bot.command(aliases=["g"])
#async def guild(context):
#	await context.send(f"The current guild (aka server) is {context.guild}")
#	await context.send(f"The current guild categories are {context.guild.categories}")
#	await context.send(f"The current guild roles are {context.guild.roles}")
#	roles = {context.guild.roles.get_role()}
#	for role in roles:
#		await context.send(f"The current guild role is " + role)
#	await context.send(f"The current guild roles are {context.guild.roles.mention('bot-testing', )}")
#	await context.send(f"The current guild region is {context.guild.region}")
#	await context.send(f"The current channel roles are {context.message.channel.changed_roles}")
#	await context.send(f"The current user roles are {context.message.author.roles}")

# The current guild roles are [<Role id=417258901810184192 name='@everyone'>, <Role id=682347089279057983 name='Mops'>, <Role id=648435936656490497 name='FortressOnePugBot'>, <Role id=644655539640598549 name='Server Booster'>, <Role id=595880090131365888 name='bot-testing'>, <Role id=526634530283716619 name='Patreon'>, <Role id=500654379708186626 name='Streamcord'>, <Role id=486517134277607425 name='Zapier'>, <Role id=543039259133739028 name='east-asia'>, <Role id=533995292975038479 name='europe'>, <Role id=522695282887229440 name='north-america'>, <Role id=531050407246561280 name='south-america'>, <Role id=427655970177548288 name='oceania'>, <Role id=686568109280460928 name='corona-beerus'>, <Role id=681488106817585162 name='make-it-rain'>, <Role id=674003192505303072 name='huehuehue'>, <Role id=662555934832197635 name='drop2'>, <Role id=581438296094408728 name='clan-a'>, <Role id=522591630155317249 name='fab'>, <Role id=521544601467617280 name='DACC'>, <Role id=522591712606945290 name='SoBaR'>, <Role id=524461308553199626 name='media'>, <Role id=492880265190834187 name='content creators'>, <Role id=427656498332827659 name='developers'>, <Role id=427655861729492992 name='oztf legends'>, <Role id=672046872273092609 name='streamers'>, <Role id=586373595702362112 name='moderators'>, <Role id=513956098403991594 name='team'>, <Role id=475574448389619713 name='command bots'>]

# https://discordpy.readthedocs.io/en/latest/api.html#role
# https://discordpy.readthedocs.io/en/latest/api.html?#utility-functions
# @bot.command(aliases=["tmr"])
# async def test_mention_role(context):
# 	await mention_role(context)


# @bot.command(aliases=["g"])
# async def gmt(context):
# 	await context.send(context.message.author)

# Token goes here.
bot.run(os.environ['FORTRESSONE_PUG_BOT_TOKEN'])
