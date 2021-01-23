import discord
from discord.ext import commands
import csv

class DataCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def sayWord(self):
        print("AAAAAAAAAAHHHHHHHHHHHHHHHH")
        return

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        with open('message_logs.csv', 'a') as csvfile:
            #Field names have already been written to the file. 
            fieldnames = ['author', 'message', 'created_at']
            writer = csv.DictWriter(csvfile, 
            fieldnames=fieldnames,
            quoting = csv.QUOTE_ALL)

            writer.writerow({'author': message.author.id, 'message': message.content, 'created_at': message.created_at})
        

def setup(bot):
    bot.add_cog(DataCog(bot))