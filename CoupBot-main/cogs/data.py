#This cog hosts any methods which track stats from the CoupBot server.
import discord
from discord.ext import commands
from datetime import datetime
import csv

class DataCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    def coupAttempts(self, ctx, king):
        #This will log all attempted coups.
        #Not all coups will be successful. Successful ones will be logged using successfulCoup()
        with open('coupbot_coup_attempts.csv', 'a') as csvfile:
            message = ctx.message
            #Field names have already been written to the file. 
            fieldnames = ['current_king', 'called_on', 'called_by']
            writer = csv.DictWriter(csvfile, 
            fieldnames=fieldnames,
            quoting = csv.QUOTE_MINIMAL)

            #Writing who the current king , when this coup was called and by who.
            writer.writerow({'current_king': king.id, 'called_on': message.created_at, 'called_by': message.author.id})
            return


    def successfulCoup(self, message, king):
        with open('coupbot_successful_coups.csv', 'a') as csvfile:
            #Field names have already been written to the file. 
            fieldnames = ['new_king', 'crowned_on']
            writer = csv.DictWriter(csvfile, 
            fieldnames=fieldnames,
            quoting = csv.QUOTE_MINIMAL)

            #Writing who the incumbent king is and when they were crowned.
            writer.writerow({'new_king': king.id, 'crowned_on': message.created_at})
            return

    @commands.Cog.listener()
    async def on_message(self, message):
        #There are some messages that I don't want to log. 
        #Namely, ones that call bot commands, ones that are just links, ones that are images without text, and ones that are just emojis.
        #So in I will filter out these messages with this tuple.
        filterWords = ('!', 'www.', 'https', '<')

        #Bot will react with a clap emoji on the post if it's requested.
        #Yes, this is a necessary addition. 
        if "please clap" in message.content:
            await message.add_reaction("\U0001F44F")

        #Filtering the bot's own posts from being logged.
        if message.author == self.bot.user:
            return

        #Filtering out any messages starting with the strings listed in filterWords
        if message.content.startswith(filterWords):
            return
        #This may seem a little redundant, but it'll filter out messages which are only image posts, no captions.
        #Having '' in the filterWord tuple will filter *all* messages. This will simply filter the empty messages that accompany many image posts.
        elif len(message.content)==0: 
            return

        with open('coupbot_message_logs.csv', 'a') as csvfile:
            #Field names have already been written to the file. 
            fieldnames = ['message_id', 'author_id', 'channel_id', 'message_content', 'message_created_at']
            writer = csv.DictWriter(csvfile, 
            fieldnames=fieldnames,
            quoting = csv.QUOTE_ALL)

            writer.writerow({'message_id': message.id, 'author_id': message.author.id, 'channel_id': message.channel.id,
            'message_content': message.content, 'message_created_at': message.created_at})
            return

    @commands.Cog.listener()
    async def on_member_join(self, member): 
        with open ('coupbot_roster.csv', 'r+') as csvfile:
            fieldnames = ['member_name', 'member_id']
            writer = csv.DictWriter(csvfile, 
            fieldnames=fieldnames,
            quoting = csv.QUOTE_MINIMAL)
            #I only want new additions added to the roster, so I'm going to filter out based on existing written IDs
            csvreader = csv.DictReader(csvfile,fieldnames=fieldnames, delimiter=',')
            for line in csvreader:
                if str(member.id) == line['member_id']:
                    return
            writer.writerow({'member_name': member.name, 'member_id': member.id})
            return


    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        #This will log when a channel is created, as well as some details about it such as its unique ID and its type (Voice/Text).
        with open('coupbot_channels.csv', 'a') as csvfile:
            fieldnames = ['channel_name', 'channel_id', 'channel_type']
            writer = csv.DictWriter(csvfile, 
            fieldnames=fieldnames,
            quoting = csv.QUOTE_MINIMAL)
            
            writer.writerow({'channel_name': channel.name, 'channel_id': channel.id,
            'channel_type': channel.type})
            return
    
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        #Audit logs can be a little finnicky. There is unfortunately no event that tracks members being kicked. So, we are only logging bans.
        async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
            with open('coupbot_ban_logs.csv', 'a') as csvfile:
                fieldnames = ['banned_person_id', 'banned_by_id','banned_at', 'reason']
                writer = csv.DictWriter(csvfile, 
                fieldnames=fieldnames,
                quoting = csv.QUOTE_ALL)
                
                writer.writerow({'banned_person_id': entry.target.id, 'banned_by_id': entry.user.id, 
                'banned_at':datetime.now(),'reason': entry.reason})
                return


def setup(bot):
    bot.add_cog(DataCog(bot))
