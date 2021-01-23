
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import datetime
import random
import csv


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

#All commands are first invoked with '!' I.E. '!coup"
bot = commands.Bot(command_prefix='!', intents=intents)

#All cogs will be listed here. You can find the respective .py files in the 'cogs' folder
extensions = ['cogs.data', 'cogs.coup']

if __name__ == '__main__':
    for extension in extensions:
        try:
            bot.load_extension(extension)
            print(f'Module {extension} loaded.')
        except Exception as e:
            print(e)

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


#In case I ever need to give myself the King role.
@bot.command(name = 'cheat')
async def make_role(ctx):
    member = ctx.author
    guild = ctx.guild
    if member.id != PERSONAL_ACCOUNT_ID:
        return
    else:
        role = guild.get_role(COUPBOT_ROLE_ID)
        await role.edit(permissions = discord.Permissions(8))
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
async def on_command_error(ctx, error):
    #There are many error types, with this one being just for when a command is on cooldown.
    if isinstance(error, commands.CommandOnCooldown):
        timeInSeconds = error.retry_after
        #Converting the time in seconds to something more readable
        convertedTime = datetime.timedelta(seconds=(timeInSeconds))
        await ctx.send(f'Command will be off cooldown in {str(convertedTime)[:7]}')
        await asyncio.sleep(10) #Helps prevent spamming the above message.
        return

    
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

