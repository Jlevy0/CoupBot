
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import datetime
import random


#API keys are safely held within a local .env file.
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
KING_ROLE_ID = int(os.getenv('KING_ROLE_ID'))
COUPBOT_ROLE_ID = int(os.getenv('COUPBOT_ROLE_ID'))
PERSONAL_ACCOUNT_ID=int(os.getenv('PERSONAL_ACCOUNT_ID'))
DUMMY_ACCOUNT_ID = int(os.getenv('DUMMY_ACCOUNT_ID'))
#The announcement channel is where coups are held, along with any bot-related announcements.
ANNOUNCEMENT_CHANNEL_ID = int(os.getenv('ANNOUNCEMENT_CHANNEL_ID'))

#Owing to the fact that it actually owns the server, Coupbot has all intents activated. 
intents = discord.Intents.all()

#Giving it an initial definition. votingEvent() can change that value.
votingEventFlag = None

#All commands are first invoked with '!' I.E. '!coup"
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    for guild in bot.guilds:
        if guild.name == GUILD:
            break

    print(
        f'{bot.user.name} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )
    await bot.change_presence(activity = discord.Activity(
                          type = discord.ActivityType.watching, 
                          name = 'old tyrants be deposed!'))

    print("Current people in guild:")
    members = '\n - '.join([member.name for member in guild.members])
    print(f'Guild Members:\n - {members}')


def votingEvent(intention):
    #During the voting process, this will be set to true and limit the king's abilities on pain of automatic coup
    #To be clear,this function has three roles. It can set the voting event flag to true, false, or merely check on its status.
    #Due to that being three options, the parameter is a string.
    
    #global is used here because it was already declared above, and we want to use that one.
    global votingEventFlag
    if intention  == 'MakeFalse':
        votingEventFlag = False
        return
    elif intention == 'MakeTrue':
        #Setting voting flag to true, which should limit the king's abilities during the period.
        votingEventFlag = True
        return
    elif intention == 'Check':
        #Lastly, for when we need to check the status of the flag without changing it.
        if votingEventFlag == True:
            return True
        elif votingEventFlag == False or None:
            return False


@commands.cooldown(1.0, 50, commands.BucketType.guild)
@bot.command(name='server')
async def fetchServerInfo(context):
	guild = context.guild
	
	await context.send(f'Server Name: {guild.name}')
	await context.send(f'Server Size: {len(guild.members)}')


@commands.cooldown(1.0, 50, commands.BucketType.guild)
@bot.command(name='leader')
async def showLeader(ctx):
    guild = ctx.guild
    role = guild.get_role(KING_ROLE_ID) #"King" role's ID.
    print(role)
    king = role.members[0]
    await ctx.send(f'Our current glorious leader is: {king.display_name}')

async def roleFreeze(ctx):
    #In the interest of making sure everyone is able to vote during the voting phase, permissions will
    # temporarily be changed such that all roles may see and react to posts, and posts/reactions cannot be removed.       
    guild = ctx.guild
    #All pre-coup permissions will be saved in a list of permission values and re-instated with it.
    permissionValues = []
    for r in guild.roles:
        #A list of every permission for each role. 
        #See https://discordapi.com/permissions.html#268435624 for an idea as to what the role values look like.

        permissionValues.append(r.permissions.value)
    
         #36818624 gives the ability to read and send posts as well as and add reactions to each role. 
         #It also removes admin abilities.
         #Remember to use discord.Permissions() if you're going to utilize this. 
        await r.edit(permissions = discord.Permissions(36818624), reason = 'Roles temporarily changed during voting period.')

    return permissionValues


async def roleUnfreeze(ctx, permissionValues):
    guild = ctx.guild
    #Returning our permissions to how they were pre-coup.
    for count, r in enumerate(guild.roles):
        await r.edit(permissions = discord.Permissions(permissionValues[count]))

    return


@commands.cooldown(1.0, 14400, commands.BucketType.guild)
@bot.command(name= 'coup')
async def startCoup(ctx): #https://discordpy.readthedocs.io/en/rewrite/ext/commands/api.html#discord.ext.commands.Context shows what you can combine "ctx." with

    guild = ctx.guild
    command = ctx.command
    channel = guild.get_channel(ANNOUNCEMENT_CHANNEL_ID) #The coup message will be posted in the protected coupbot channel, which has that ID.

    role = guild.get_role(KING_ROLE_ID) #"King" role's ID.
    king = role.members[0]
    
    permissionValues = await roleFreeze(ctx)

    message = await channel.send(f"@here Should {king} be deposed?")

    votingEvent('MakeTrue')

    for emoji in ('✅', '❎'): #Gotta find the text version of the emoji and paste it in here like so if you wanna do it this way. codepoints.net gives them
        await message.add_reaction(emoji)

    await asyncio.sleep(900) #Waiting for reactions to come in.

    await channel.send("*Timer done.*")
    #Variables to hold the number of votes. 
    yay = 0
    nay = 0 
    message = await message.channel.fetch_message(message.id) #Refreshes the message to include reaction information

    for reaction in message.reactions:
        if reaction.emoji == '✅':
            yay = reaction.count - 1 #not including the bot's reaction to the counter.
        elif reaction.emoji == '❎':
            nay = reaction.count - 1 

    print(f'The votes for yay are {yay}, the votes for nay are {nay}.')
    #Nay votes subtract from the yay votes, we need at least 3 yay votes for the coup to be successful. 
    if (yay - nay) >= 3:
        await coup(ctx, permissionValues)
    else:
        await channel.send("The current leader remains! Long live the king!")
        votingEvent('MakeFalse')
        await roleUnfreeze(ctx, permissionValues)


async def coup(ctx, permissionValues):
    guild = ctx.guild
    channel = guild.get_channel(ANNOUNCEMENT_CHANNEL_ID)
    role = guild.get_role(KING_ROLE_ID) #"King" role's ID.
    votingEvent('MakeFalse')
    #The deposition portion; wherein we remove anyone with the "King" role.
    for member in role.members:
        await member.remove_roles(role)
    await channel.send("**THE KING IS DEAD**")
    #Dramatic timing.
    await channel.send("*DECIDING NEW LEADER...*")
    await asyncio.sleep(10)

    #The namesake of this project: We'll now pick a random member - minus my spare account - to make as our leader.
    guildRoster = guild.members
    for member in guildRoster:
        if member.id == DUMMY_ACCOUNT_ID:
            guildRoster.remove(member)
    chosenKing = random.choice(guildRoster)
    #Now that we have our leader, we can add the role and inform the server of their ascension.
    await chosenKing.add_roles(role)
    await channel.send(f'{chosenKing} IS OUR NEW LEADER!')
    await channel.send("LONG LIVE THE KING")

    #Fixing roles to how they were pre-coup
    await roleUnfreeze(ctx, permissionValues)


#In case I ever need to give myself the King role.
@bot.command(name = 'cheat')
async def make_role(ctx):
    member = ctx.author
    guild = ctx.guild
    if member.id != PERSONAL_ACCOUNT_ID:
        return
    else:
        role = guild.get_role(KING_ROLE_ID)
        await member.add_roles(role)

@commands.has_permissions(administrator = True)
@bot.command(name = 'cleanslate')
async def reset_roles(ctx):
    #This should wipe the roles for the incumbent king. Essentially giving a fresh start to each reign in terms of permissions/roles.
    guild = ctx.guild
    kingRole = guild.get_role(KING_ROLE_ID) #"King" role's ID.
    botRole = guild.get_role(COUPBOT_ROLE_ID) #CoupBot's unique role ID.
    #Checking each role, if it doesn't match the king's role ID, it gets deleted.
    for role in guild.roles:
        if role.id == 774866743201103892: #The @everyone role, which the bot cannot delete and borks up the loop when it tries.
            continue
        if role.id != kingRole.id and role.id != botRole.id:
            await role.delete()


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    print(message.author.id,message.content, message.created_at)
    #Keep this as the last line in on_message
    await bot.process_commands(message) #Necessary to do in on_message, otherwise it won't process commands based on the message the user sent.

@bot.event
async def on_command_error(ctx, error):
    #There are many error types, with this one being just for when a command is on cooldown.
    if isinstance(error, commands.CommandOnCooldown):
        timeInSeconds = error.retry_after
        #Converting the time in seconds to something more readable
        convertedTime = datetime.timedelta(seconds=(timeInSeconds))
        await ctx.send(f'Command will be off cooldown in {str(convertedTime)[:7]}')
        await asyncio.sleep(10) #Helps prevent spamming the above message.
        return

#Tracking what member leaves. If the king leaves, it automatically coups.
@bot.event
async def on_member_remove(member):
    kingRole = member.guild.get_role(KING_ROLE_ID)
    for role in member.roles:
        if kingRole.id == role.id:
            print("King role matched one of the member roles.")
            announcementChannel = guild.get_channel(ANNOUNCEMENT_CHANNEL_ID) 
            message = await announcementChannel.send("The king has abdicated his position! He shall be replaced!")
            #Taking the abdication message, we'll use that to grab the context we need for our coup function.
            ctx = (await bot.get_context(message))
            await coup(ctx)

    
@bot.event
async def on_message_delete(message):
    pass
    #Below is the way to check who deleted what message. Commented out to clear up the output. 

    #ctx = (await bot.get_context(message))
    # async for message in message.guild.audit_logs(action=discord.AuditLogAction.message_delete, limit=1):
    #      deletedBy = "{0.user}".format(message)
    #      print(f"A message was deleted by {deletedBy}.") 


@bot.event
async def on_member_ban(guild, user):
#Not in use right now, but that should change later.
    pass
        

bot.run(TOKEN)

