#This cog houses all methods related to the Coup feature of CoupBot.
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
DOESNT_WANT_KING_ID=int(os.getenv('DOESNT_WANT_KING_ID'))
DUMMY_ACCOUNT_ID = int(os.getenv('DUMMY_ACCOUNT_ID'))
#The announcement channel is where coups are held, along with any bot-related announcements.
ANNOUNCEMENT_CHANNEL_ID = int(os.getenv('ANNOUNCEMENT_CHANNEL_ID'))
from cogs.data import DataCog

class CoupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        #Giving it an initial definition. votingEvent() can change that value.
        votingEventFlag = None



    def votingEvent(self, intention):
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


    async def roleFreeze(self, ctx):
        #In the interest of making sure everyone is able to vote during the voting phase, permissions will
        # temporarily be changed such that all roles may see and react to posts, and posts/reactions cannot be removed.       
        guild = ctx.guild
        channel = guild.get_channel(ANNOUNCEMENT_CHANNEL_ID)
        overwriteValues = channel.overwrites
        
        #All pre-coup permissions will be saved in a list of permission values and re-instated with it.
        permissionValues = []
        overwriteValues = []
        for r in guild.roles:
            #A list of every permission for each role. 
            #See https://discordapi.com/permissions.html#268435624 for an idea as to what the role values look like.
    
            permissionValues.append(r.permissions.value)
        
            overwriteValues.append(channel.overwrites_for(r))
            #36818624 gives the ability to read and send posts as well as and add reactions to each role. 
            #It also removes admin abilities.
            #Remember to use discord.Permissions() if you're going to utilize this. 
            await r.edit(permissions = discord.Permissions(36818624), reason = 'Roles temporarily changed during voting period.')
            await channel.set_permissions(r, overwrite = None)

        return permissionValues, overwriteValues


    async def roleUnfreeze(self, ctx, permissionValues, overwriteValues):
        #Returning our permissions to how they were pre-coup.
        guild = ctx.guild
        channel = guild.get_channel(ANNOUNCEMENT_CHANNEL_ID)
        #In the cases where the king abdicates or leaves, we may not have any generated Permission values, in which case we can just skip them.
        if permissionValues == None:
            return
        else:
            for count, r in enumerate(guild.roles):
                await r.edit(permissions = discord.Permissions(permissionValues[count]))
            #Resetting the channel overwrites to how they were pre-voting.
            await channel.edit(r, overwrites=overwriteValues[count])

        return


    @commands.cooldown(1.0, 14400, commands.BucketType.guild)
    @commands.command(name= 'coup')
    async def startCoup(self, ctx): #https://discordpy.readthedocs.io/en/rewrite/ext/commands/api.html#discord.ext.commands.Context shows what you can combine "ctx." with
        guild = ctx.guild
        channel = guild.get_channel(ANNOUNCEMENT_CHANNEL_ID) #The coup message will be posted in the protected coupbot channel, which has that ID.

        role = guild.get_role(KING_ROLE_ID) #"King" role's ID.
        king = role.members[0]

        permissionValues, overwriteValues = await self.roleFreeze(ctx)

        message = await channel.send(f"@here Should {king} be deposed?")

        #Logging this coup attempt to a csv.
        DataCog.coupAttempts(self, ctx, king)
        print(message.content, message.id)
        #Restricting permissions while a vote is going on to prevent political skullduggery.
        self.votingEvent('MakeTrue')

        for emoji in ('✅', '❎'): #Gotta find the text version of the emoji and paste it in here like so if you wanna do it this way. codepoints.net gives them
            await message.add_reaction(emoji)

        await asyncio.sleep(900) #Waiting for reactions to come in.

        await channel.send("*Timer done.*")
        #Variables to hold the number of votes. 
        yay = 0
        nay = 0 
        
        message = await message.channel.fetch_message(message.id) #Refreshes the message to include reaction 

        for reaction in message.reactions:
            if reaction.emoji == '✅':
                yay = reaction.count - 1 #not including the bot's reaction to the counter.
            elif reaction.emoji == '❎':
                nay = reaction.count - 1 

        print(f'The votes for yay are {yay}, the votes for nay are {nay}.')
        #Nay votes subtract from the yay votes, we need at least 3 yay votes for the coup to be successful. 
        if (yay - nay) >= 3:
            await self.coup(ctx, permissionValues, overwriteValues)
        else:
            await channel.send("The current leader remains! Long live the king!")
            self.votingEvent('MakeFalse')
            await self.roleUnfreeze(ctx, permissionValues, overwriteValues)


    async def coup(self, ctx, permissionValues, overwriteValues):
        guild = ctx.guild
        channel = guild.get_channel(ANNOUNCEMENT_CHANNEL_ID)
        role = guild.get_role(KING_ROLE_ID) #"King" role's ID.
        self.votingEvent('MakeFalse')
        #The deposition portion; wherein we remove anyone with the "King" role.
        for member in role.members:
            await member.remove_roles(role)
        await channel.send("**THE KING IS DEAD**")
        #Dramatic timing.
        await channel.send("*DECIDING NEW LEADER...*")
        await asyncio.sleep(10)

        #The namesake of this project: We'll now pick a random member - minus my spare account and those that don't want the role - to make as our leader.
        guildRoster = guild.members
        willNotBeLeader = [DOESNT_WANT_KING_ID, DUMMY_ACCOUNT_ID]
        for member in guildRoster:
            if member.id in willNotBeLeader:
                guildRoster.remove(member)
        chosenKing = random.choice(guildRoster)
        #Now that we have our leader, we can add the role and inform the server of their ascension.
        await chosenKing.add_roles(role)
        await channel.send(f'{chosenKing.mention} IS OUR NEW LEADER!')
        message = await channel.send("LONG LIVE THE KING")

        #Logging this successful coup.
        DataCog.successfulCoup(self, message, chosenKing)
        #Fixing roles to how they were pre-coup
        await self.roleUnfreeze(ctx, permissionValues, overwriteValues)


    #Tracking what member leaves. If the king leaves, it automatically coups.
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        kingRole = member.guild.get_role(KING_ROLE_ID)
        for role in member.roles:
            if kingRole.id == role.id:
                print("King role matched one of the member roles.")
                announcementChannel = member.guild.get_channel(ANNOUNCEMENT_CHANNEL_ID) 
                message = await announcementChannel.send("The king has abdicated his position! He shall be replaced!")
                #Taking the abdication message, we'll use that to grab the context we need for our coup function.
                ctx = (await self.bot.get_context(message))
                await self.coup(ctx, None)


    #Sometimes the leader may want to give up their position. This command will allow them to do so.
    @commands.command(name= 'abdicate')
    async def abdicate(self, ctx):
        member = ctx.author
        guild = ctx.guild
        announcementChannel = guild.get_channel(ANNOUNCEMENT_CHANNEL_ID)
        kingRole = guild.get_role(KING_ROLE_ID)

        #Checking to make sure the person who called the command actually has the leadership role.
        for role in member.roles:
            if kingRole.id == role.id:
                await announcementChannel.send("The king has abdicated his position! He shall be replaced!")
                await self.coup(ctx, None)


def setup(bot):
    bot.add_cog(CoupCog(bot))