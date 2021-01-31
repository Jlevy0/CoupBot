#This cog hosts any methods which track stats from the CoupBot server.
import discord
from discord.ext import commands
import csv

class DataCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    def coupAttempts(self, ctx, king):
        #This will log all attempted coups.
        #Not all coups will be successful. Successful ones will be logged using successfulCoup()
        with open('coup_attempts.csv', 'a') as csvfile:
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
        with open('successful_coup.csv', 'a') as csvfile:
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

        with open('message_logs.csv', 'a') as csvfile:
            #Field names have already been written to the file. 
            fieldnames = ['author', 'message', 'created_at']
            writer = csv.DictWriter(csvfile, 
            fieldnames=fieldnames,
            quoting = csv.QUOTE_ALL)

            writer.writerow({'author': message.author.id, 'message': message.content, 'created_at': message.created_at})
            return
        
    
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        #Audit logs can be a little finnicky. There is unfortunately no event that tracks members being kicked. So, we are only logging bans.
        async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
            with open('ban_logs.csv', 'a') as csvfile:
                fieldnames = ['banned_person', 'banned_by', 'reason']
                writer = csv.DictWriter(csvfile, 
                fieldnames=fieldnames,
                quoting = csv.QUOTE_MINIMAL)
                
                writer.writerow({'banned_person': entry.target, 'banned_by': entry.user, 'reason': entry.reason})
                return


def setup(bot):
    bot.add_cog(DataCog(bot))