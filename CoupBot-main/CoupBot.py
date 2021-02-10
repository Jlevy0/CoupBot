#This is the main file for CoupBot, which runs the bot, connects to the Discord API, and houses some of the general-use commands of this server. 
#More specific functions, such as those related to the coup event and stat logging, can be found in the cog folder. 
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
DISCORD_NITRO_ROLE_ID = int(os.getenv('DISCORD_NITRO_ROLE_ID'))
EVERYONE_ROLE_ID= int(os.getenv('EVERYONE_ROLE_ID'))
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


#In case I ever need to give myself the CoupBot role.
@bot.command(name = 'cheat')
async def make_role(ctx):
    member = ctx.author
    guild = ctx.guild
    if member.id != PERSONAL_ACCOUNT_ID:
        return
    else:
        role = guild.get_role(COUPBOT_ROLE_ID)
        #Assuming I've used !cheat before, this will then remove the role from myself. If I don't have the role, then this command will give it to me.
        for role in member.roles:
            if COUPBOT_ROLE_ID == role.id:
                await member.remove_roles(role)
                return
        #Giving myself the role.
        await role.edit(permissions = discord.Permissions(8))
        await member.add_roles(role)

@commands.has_permissions(administrator = True)
@bot.command(name = 'cleanslate')
async def reset_roles(ctx):
    #This will wipe the roles for the incumbent king. Essentially giving a fresh start to each reign in terms of permissions/roles.
    guild = ctx.guild
    kingRole = guild.get_role(KING_ROLE_ID) #"King" role's ID.
    botRole = guild.get_role(COUPBOT_ROLE_ID) #CoupBot's unique role ID.
    #Checking each role, if it doesn't match the king's role ID, it gets deleted.
    for role in guild.roles:
        #These two roles are undeletable. If the bot tries to delete these two it fails and breaks the loop, so we're skipping them with this.
        if role.id == EVERYONE_ROLE_ID or role.id == DISCORD_NITRO_ROLE_ID: 
            continue
        if role.id != kingRole.id and role.id != botRole.id:
            await role.delete()

@commands.has_permissions(administrator = True)
@bot.command(name = 'rename')
async def rename_bot(ctx):
    #This will allow the king (or any admin) to rename the bot to whatever they want, provided it fits into Discord's 32-character limit.
    message = ctx.message
    #Here we're taking the message, slicing away the '!rename' part, and making the remaining 32 characters (if it goes up to that) the new name.
    newName = message.content[8:40]
    #Changing the bot's nickname.
    await message.guild.me.edit(nick = newName)
    print(f'Name changed to {newName}')

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



bot.run(TOKEN)

