import discord
import os
import json
import random
from replit import db

client = discord.Client()
cmdList = {
  'help': 'lists commands available',
  'add_player': 'adds a player with default role "fill"',
  'get_player': 'returns a players role information',
  'set_player': 'sets a players role preferences',
  'delete_player': 'deletes a player',
  'clear_players': 'clear all players saved in the db',
  'list_players': 'lists all players and their preferred roles',
  'lets_play': 'assigns players roles based on preferences and available roles',
  'lets_play_rng': 'assigns players roles based on available roles',
  'should/do/how/why/what/is/can/does/will': 'have a life question? let yadon help you find an answer...',
  'goodnight': 'let yadon wish you a good night',
  'ruthere': 'check if yadon is listening'}
questionKeywords = ['should', 'do', 'how', 'why', 'what', 'is', 'can', 'does', 'will']
shouldQuestionAnswers = [
  "It is certain",
  "It is decidedly so",
  "Without a doubt",
  "Yes – definitely",
  "You may rely on it",
  "As I see it, yes",
  "Most likely",
  "Outlook good",
  "Yes",
  "Signs point to yes",
  "Don’t count on it",
  "My reply is no",
  "My sources say no",
  "Outlook not so good",
  "Very doubtful",
  "Reply hazy, try again",
  "Ask again later",
  "Better not tell you now",
  "Cannot predict now",
  "Concentrate and ask again"
]
teamRoles = ['jg', 'supp', 'top', 'adc', 'mid']

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if not (message.content.startswith('/yadonhelp') or  message.content.startswith('/yadon')):
      return

    splitMsg = message.content.split()
    if len(splitMsg) <= 1:
      await message.channel.send(get_missing_command_help())
      return

    cmd = splitMsg[1]
    params = splitMsg[2:]
    result = run_command(cmd, params)
    await message.channel.send(result)

def run_command(cmd, params):
  if cmd == 'help':
    return get_missing_command_help()
  if cmd == 'add_player':
    return add_player(params)
  if cmd == 'get_player':
    return get_player(params)
  if cmd == 'set_player':
    return set_player(params)
  if cmd == 'delete_player':
    return delete_player(params)
  if cmd == 'list_players':
    return list_players()
  if cmd == 'lets_play':
    return setup_lets_play(params, False)
  if cmd == 'lets_play_rng':
    return setup_lets_play(params, True)
  if cmd == 'clear_players':
    return clear_players()
  if cmd in questionKeywords:
    return answer_question(params)
  if cmd == 'goodnight':
    return 'Goodnight and sleep well, my friend'
  if cmd == 'ruthere':
    return 'Yadon is always here for you'
  return get_command_help(cmd)

def clear_players():
  db.clear()
  return 'Successfully cleared all players'

def answer_question(params):
  if len(params) < 1:
    return "What's your question? I'll need a little more context to help answer any questions you may have."
  return random.choice(shouldQuestionAnswers)

def setup_lets_play(params, isRng):
  if len(params) <= 0:
    return 'Missing players in the party: "/yadonhelp lets_play <space delimited list of players or roles>"\n - specifying a player means they still need to be assigned an available role\n - specifying a role (i.e. top, mid, jg, supp, adc) means this role has already been claimed by someone else in the queue and cannot be assigned to a player in the party'
  if len(params) > 5:
    return "There are too many players in this party (" + str(len(params)) + "). A game of league can only support up to five champions."

  # remove any roles we do not have to worry about
  rolesToFill = list(teamRoles)
  players = []
  for param in params:
    if param in rolesToFill:
      rolesToFill.remove(param)
    else:
      players.append(param)

  # add players that do not already exist, default to fill role
  for player in players:
    if player not in db.keys():
      add_player([player])

  if isRng:
    return lets_play_rng(players, rolesToFill)
  else:
    return lets_play(players, rolesToFill)

def lets_play_rng(players, rolesToFill):
  fillRolesMap = {
    'fill': players
  }
  roles, found = assign_roles(fillRolesMap, rolesToFill)
  return pretty(roles)

def lets_play(players, rolesToFill):
  rolesMap = get_player_roles_map(players)
  
  for x in range(8):
    roles, found = assign_roles(rolesMap, rolesToFill)
    if found and len(roles.keys()) == len(players):
      return pretty(roles)

  return "Could not accommodate preferences :(. Randomly assigning players based on all available roles:\n" + lets_play_rng(players, rolesToFill)

def assign_roles(playerRoles, roles):
  assignedRoles = {}
  playerRolesCopy = dict(playerRoles)
  random.shuffle(roles)
  for role in roles:
    playerForRole = ''
    if role in playerRoles.keys() and len(playerRolesCopy[role]) > 0:
      playerForRole = random.choice(playerRolesCopy[role])
    elif 'fill' in playerRoles.keys() and len(playerRolesCopy['fill']) > 0:
      playerForRole = random.choice(playerRolesCopy['fill'])
    else:
      continue
    assignedRoles[role] = playerForRole
    removePlayerFromMap(playerForRole, playerRolesCopy)
  return assignedRoles, True

def removePlayerFromMap(player, playerRoleMap):
  for role in playerRoleMap.keys():
    if player in playerRoleMap[role]:
      playerRoleMap[role].remove(player)

def get_player_roles_map(params):
  playerRoles = {}
  for player in params:
    roles = db[player].split(",")
    for role in roles:
      if role in playerRoles.keys():
        playerRoles[role].append(player)
      else:
        playerRoles[role] = [player]
  return playerRoles

def list_players():
  playersList = {}
  for player in db.keys():
    playersList[player] = db[player]
  return pretty(playersList)

def delete_player(params):
  if len(params) != 1:
    return 'Missing player id: "/yadonhelp delete_player <i.e. @slowpokeau>"'
  
  playerid = params[0]
  if playerid not in db.keys():
    return "Player does not exist"
  db.__delitem__(playerid)
  return "Successfully deleted player"


def get_player(params):
  if len(params) != 1:
    return 'Missing player id: "/yadonhelp get_player <i.e. @slowpokeau>"'
 
  playerid = params[0]
  if playerid not in db.keys():
    return "Player does not exist"
  return db[playerid]

def add_player(params):
  if len(params) != 1:
    return 'Missing player id: "/yadonhelp add_player <i.e. @slowpokeau>"'

  playerid = params[0]
  if playerid in db.keys():
    return "Player already exists"
  db[playerid] = "fill"
  return "Successfully add player"

def set_player(params):
  if len(params) < 1:
    return 'Missing player id: "/yadonhelp set_player <i.e. @slowpokeau> <i.e. jg,supp,top>"'
  if len(params) < 2:
    return 'Missing player roles: "/yadonhelp set_player <i.e. @slowpokeau> <i.e. jg,supp,top>"'

  playerid = params[0]
  if playerid not in db.keys():
    return "Player does not exist"

  roles = params[1]
  err = validate_roles_list(roles)
  if err:
    return err

  db[playerid] = roles
  return "Successfully set player with role(s): " + roles


def validate_roles_list(roles):
  validRoles = list(teamRoles)
  validRoles.append('fill')
  roleArr = roles.split(",")
  for role in roleArr:
    if role not in validRoles:
      return role + ' is not a valid role'
  return ''

def get_command_help(cmd):
  helpText = '"' + cmd + '" is not a recognized command, did you mean:\n'
  return helpText + pretty(cmdList)

def get_missing_command_help():
  helpText = 'Please format commands as "/yadonhelp <cmd>". List of available commands:\n'
  return helpText + pretty(cmdList)

def pretty(d, indent=0):
  prettyPrint = ''
  for key, value in d.items():
    prettyPrint = prettyPrint + ('\t' * indent + str(key))
    if isinstance(value, dict):
      pretty(value, indent+1)
    else:
      prettyPrint = prettyPrint + ('\t' * (indent+1) + str(value)) + '\n'
  return prettyPrint

client.run(os.getenv("DISCORD_BOT_TOKEN"))
