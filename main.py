from discord.ext import commands, tasks
import discord
import time
import datamanager
import player
import asyncio
import datetime as dt
import urllib.parse as urlparse
import os

ID_VOICE_CHANNEL = 802917318819577878 #id of voice channel Coppa Dei Secchioni in GSU

class CdSBot(commands.Bot):
    '''
    CdSBot represent the bot that communicate with discord, it inherits attributes and methods
    from commands.Bot(see discord.py API)
    Attributes:
        self.roles is a dict to remember roles associated to each faction: name_faction -> name_role_faction
        self.players is a dict that stores a player.Player instance for each player: user_id -> player class
        self.manager handles comunication with Database
    Methods:
        self.init_roles() load the factions in self.roles
        self.init_players() load the players in self.players
        self.on_ready()  is called when the bot is online, it does nothing more than says that everything went fine and the bot is online
        self.setup_commands() set up the commands of the bots(help, joinfaction, buildfaction and so on)
        Commands method set up in self.setup_commands:
            helpme: parameters: ctx(Context object from discord API), description: it sends the list of commands in #generale
            report: parameters: ctx(Context object from discord API), description: report user to referee
            joinfaction: parameters: ctx(Context object form discord API), description: it allows to a user to join a faction
            buildfaction: parameters: ctx(Context object form discord API), description: it allows to a user to build a faction
            leavefaction: parameters: ctx(Context object form discord API), description: it allows to leaver a faction, if the user is captain of the faction then the faction is deleted
            showfactions: parameters: ctx(Context object form discord API), description: shows all the factions
            mystats     : parameters: ctx(Context object form discord API), description: shows to a users its stats
        on_voice_state_update:
            parameters:
                -member -> member object from discord API
                -before -> before status of member
                -after -> after status of  member
            function:
                this is an override of commands.Bot.on_voice_state_update, this method is called when a member of the guild(the server) change
                its voice state(ie: it enter in VC, mute itself, etc.), we override the method so that we save when the member enter in Coppa Dei Secchioni
        '''
    def __init__(self, command_prefix, self_bot, help_command, intents, dbname, user, password, host, port):
        commands.Bot.__init__(self, command_prefix=command_prefix, self_bot=self_bot, help_command = help_command, intents = intents)
        self.roles = dict()
        self.players = dict()
        self.warned_users = dict()
        self.manager = datamanager.Datamanager(dbname, user, password, host, port)
        self.setup_commands()
        self.init_players()
        self.category_id = 815983980959629322  #ID category "Study factions"

    #  metodi burocratici
        #    def init_roles(self):
        #        factions = self.manager.getAllFactions()
        #        if factions != None:
        #           for faction in factions:
        #                name_faction = faction[0]
        #               name_role_faction = name_faction + " member"
    #                self.roles[name_faction] = name_role_faction

    def init_players(self):
        users = self.manager.query_all_users()
        for user in users:
            player_id = user[0]
            player_class = player.Player(*user)
            self.players[player_id] = player_class

    #metodi per comunicare con discord
    async def on_ready(self):
        print('Online.')
        mybot.updateData.start()

    def setup_commands(self):
        @self.command(name="help")
        async def help(ctx):
            help_str = '''
            ? -> prefix for commands\n\n
            
            Player commands:
            ?buildfaction name_faction -> build a faction named name_faction and receive captain status. name_faction must have 3-18 characters. 
            ?leavefaction              -> leave your current faction. WARNING: if the captain leaves the faction then the faction is automatically deleted.\n
            ?joinfaction  name_faction -> join the faction named name_faction.\n
            ?showfactions              -> show all the current factions.\n
            ?mystats                   -> show your current statistics.\n
            ?report @user              -> report @user to  CdS referees.
            
            Referee commands:
            ?report @user              -> comfirm penality for @user. Warning: @user must have been already reported.\n
            ?rankfactions              -> shows current rank list of factions.\n
            ?rankusers                 -> shows a very bad formatted rank list of users.\n
            
            Admin commands:
            ?referee  @user            ->Name @user  referee for the competion.
            '''
            my_embed = discord.Embed(title="Help", description=help_str,colour=discord.Colour.blue())
            await ctx.channel.send(embed = my_embed)

        @self.command(name = 'referee')
        async def referee(ctx):
            referees = ctx.message.mentions
            print(referees)
            if referees == []:
                my_embed = discord.Embed(title ="You need to mention your referees", colour = discord.Colour.red())
                await ctx.channel.send(embed = my_embed)
                return
            if ctx.message.author.guild_permissions.administrator == True:
                role = discord.utils.get(ctx.guild.roles, name = "CdS Referee")
                if role == None:
                    await ctx.guild.create_role(name = "CdS Referee", colour = discord.Colour.from_rgb(255,255,0))
                    ref_role = discord.utils.get(ctx.guild.roles, name = "CdS Referee")
                    role_bot = discord.utils.get(ctx.guild.roles, name="CdS Bot")
                    overwrites = {
                        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        role_bot: discord.PermissionOverwrite(read_messages=True, send_messages=True,
                                                              manage_channels=True),
                        ref_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                    }
                    #print(discord.utils.get(text_channels, name = "referees"))
                    if discord.utils.get(ctx.guild.text_channels, name = "referees") == None:
                        category = discord.utils.get(ctx.guild.categories, id = self.category_id)
                        await ctx.guild.create_text_channel(name = "referees", overwrites=overwrites, category = category)
                ref_role = discord.utils.get(ctx.guild.roles, name="CdS Referee")
                for referee in referees:
                    await referee.add_roles(ref_role)
                my_embed = discord.Embed(title = "Referees named successfully", colour = discord.Colour.green())
                await ctx.channel.send(embed = my_embed)
            else:
                my_embed = discord.Embed(title = "You need to be an Administrator to name referees", colour = discord.Colour.red())
                await ctx.channel.send(embed = my_embed)

        @self.command(name='report')
        async def report(ctx):
            check_role = discord.utils.get(ctx.guild.roles, name = "CdS Referee")
            if check_role == None:
                my_embed = discord.Embed(title = "Please name a referee first.", colour = discord.Colour.red())
                await ctx.channel.send(embed = my_embed)
                return
            role_ref = discord.utils.get(ctx.message.author.roles, name = "CdS Referee")
            if role_ref == None:
                if str(ctx.author.id) in self.players.keys():
                    for user in ctx.message.mentions:
                        self.warned_users[user.mention] = user
                        my_embed = discord.Embed(title = "Report done succefully")
                        await ctx.channel.send(embed = my_embed)
                    channel = discord.utils.get(ctx.guild.channels, name = "referees")
                    message = f"User reported by {ctx.message.author.mention}: \n"
                    my_embed = discord.Embed(title = "Report:", description = message + '\n'.join(self.warned_users.keys()), colour = discord.Colour.from_rgb(255,255,0))
                    await channel.send(embed = my_embed)
                return
            else:
                for user in ctx.message.mentions:
                    user_id = str(user.id)
                    if user.mention in self.warned_users.keys():
                        if user_id in self.players.keys():
                            self.players[user_id].report()
                        del self.warned_users[user.mention]
                        my_embed = discord.Embed(title="Report done succefully")
                        await ctx.channel.send(embed=my_embed)

        @self.command(name='buildfaction')
        async def buildfaction(ctx):
            referee = discord.utils.get(ctx.guild.roles, name = "CdS Referee" )
            if referee == None:
                my_embed = discord.Embed(title = "Please name a referee first", colour = discord.Colour.red())
                await ctx.channel.send(embed = my_embed)
                return
            user = ctx.message.author
            user_id = str(user.id)
            if user_id in self.players.keys():
                await ctx.channel.send(f'{ctx.message.author} you are already member of a faction.')
            else:
                content = list(filter(lambda word: word != '', ctx.message.content.split(' '))) #split the string with spaces
                if len(content) > 1:
                    name_faction = content[1].lower()
                    if len(name_faction) > 3 and len(name_faction) < 32:
                        check_role = discord.utils.get(ctx.guild.roles, name = name_faction + " member")
                        if check_role != None:
                            my_embed = discord.Embed(title=f'{name_faction} already exists.', colour=discord.Colour.red())
                            await ctx.channel.send(embed = my_embed)
                            return
                        #if name_faction in self.roles.keys():
                        #    my_embed = discord.Embed(title = f'{name_faction} already exists.', color = discord.Color.red())
                        #    await ctx.channel.send(embed = my_embed)
                        #    return

                        #create role
                        name_role_faction = name_faction + " member"
                        await ctx.guild.create_role(name=name_role_faction, colour=discord.Colour.random())
                        #self.roles[name_faction] = name_role_faction
                        role = discord.utils.get(ctx.guild.roles, name=name_role_faction)
                        role_bot = discord.utils.get(ctx.guild.roles, name = "CdS Bot")
                        referee  = discord.utils.get(ctx.guild.roles, name = "CdS Referee")
                        #create private channel
                        overwrites = {
                            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                            role_bot: discord.PermissionOverwrite(read_messages=True,send_messages = True, manage_channels = True),
                            role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                            referee: discord.PermissionOverwrite(read_messages=True, send_messages = True)
                        }
                        category = discord.utils.get(ctx.guild.categories, id=self.category_id)
                        print(category)
                        new_channel = await ctx.guild.create_text_channel(name_faction, category = category, overwrites=overwrites)
                        id_channel = str(new_channel.id)
                        # add faction to database
                        self.manager.add_faction(name_faction, id_channel)
                        #add role to user
                        await user.add_roles(role)
                        #add user to players
                        self.players[user_id] = player.Player(user_id, 1, name_faction)
                        self.manager.add_user(user_id, name_faction, 1)
                        #send messages
                        my_emoji = u"\u263A"
                        my_embed = discord.Embed(title=f"{name_faction} has been built {my_emoji}", description=f'{user.mention} founded {name_faction}',
                                                 colour=discord.Colour.green())
                        await ctx.channel.send(embed=my_embed)
                        #my_embed = discord.Embed(title=f'{user.mention} founded {name_faction}', color = discord.Color.green())
                        #await ctx.channel.send(embed = my_embed)
                    else:
                        my_embed = discord.Embed(title=f'{name_faction} does not meet the standards to be a name faction.',
                            colour=discord.Colour.red())
                        await ctx.channel.send(embed=my_embed)

                else:
                    my_embed = discord.Embed(title=f'You need to specify the name of the faction.', colour=discord.Colour.red())
                    await ctx.channel.send(embed=my_embed)

        @self.command(name='joinfaction')
        async def joinfaction(ctx):
            name_faction = list(filter(lambda word: word != '', ctx.message.content.split(' ')))[1].lower()
            role_name = name_faction + ' member'
            user = ctx.message.author
            check_role = discord.utils.get(ctx.guild.roles, name = role_name)
            if check_role != None:
                check_user_role =  discord.utils.get(user.roles, name = role_name)
                if check_user_role != None:

          #  if name_faction in self.roles.keys():
          #      for role in self.roles.values():
          #          if discord.utils.get(user.roles, name=role):
                        my_embed = discord.Embed(description=f'{user.mention} you are already member of a team.', colour = discord.Colour.red())
                        await ctx.channel.send(embed = my_embed)
                        return
                await user.add_roles(check_role)
                user_id = str(user.id)
                self.manager.add_user(user_id, name_faction, 0)
                self.players[user_id] = player.Player(user_id, 0, name_faction)
                my_embed = discord.Embed(description=f'{user.mention} you joined {name_faction}', colour=discord.Colour.green())
                #await user.add_roles(role)
                await ctx.channel.send(embed = my_embed)
            else:
                my_embed = discord.Embed(description=f'{user.mention} there is no faction named {name_faction}', colour=discord.Colour.red())
                await ctx.channel.send(embed = my_embed)

        @self.command(name='leavefaction')
        async def leavefaction(ctx):
            user = ctx.message.author
            user_id = str(user.id)
            if user_id in self.players.keys():
                name_faction = self.manager.get_faction_from_id(user_id)
                role_name = name_faction + ' member'
                if self.manager.is_captain(user_id):
                    #remove user from database
                    self.manager.remove_user(user_id)
                    del self.players[user_id]
                    #get all user from the faction
                    player_ids = self.manager.get_players_from_faction(name_faction)
                    for player_id in player_ids:
                        self.manager.remove_user(player_id)
                        del self.players[player_id]
                    #delete the role
                    role = discord.utils.get(ctx.guild.roles, name=role_name)
                    await role.delete()
                    #remove faction from database
                    id_channel = self.manager.get_id_channel(name_faction)
                    self.manager.remove_faction(name_faction)
                    #delete
                    #del self.roles[name_faction]
                    #delete channel
                    channel = self.get_channel(int(id_channel))
                    await channel.delete()
                    my_embed = discord.Embed(description = f'{user.mention} you disbanded your faction', colour=discord.Colour.red())
                    await ctx.channel.send(embed=my_embed)
                else:
                    self.manager.remove_user(user_id)
                    role = discord.utils.get(ctx.guild.roles, name=role_name)
                    my_embed = discord.Embed(title = f'{user.mention} you left {name_faction}', colour = discord.Colour.red())
                    del self.players[user_id]
                    await user.remove_roles(role)
                    await ctx.channel.send(embed = my_embed)
            else:
                my_embed = discord.Embed(description=f"{user.mention} your don't belong to any faction", colour=discord.Colour.red())
                await ctx.channel.send(embed=my_embed)

        @self.command(name='showfactions')
        async def showfactions(ctx):
            factions = self.manager.get_all_factions()
            print(factions)
            name_factions  = [faction[0] for faction in factions]
            message = '\n'.join(name_factions)  # che cafonata
            my_embed = discord.Embed(title="Factions", description=message, colour = discord.Colour.green())
            await ctx.channel.send(embed = my_embed)

        @self.command(name='mystats')
        async def mystats(ctx):
            user = ctx.message.author
            user_id = str(user.id)
            if user_id in self.players.keys():
                time_studied = str() #string that represent the time studied by the user
                if self.players[user_id].daily_time >= 1:
                    time_studied = str(self.players[user_id].daily_time) + "h"
                else:
                    time_studied = str(self.players[user_id].daily_time_m) + "m"

                msg = f'''Daily points:{self.players[user_id].daily_points} CFU\n
                          Total points:{self.players[user_id].points} CFU\n
                          Daily session: {time_studied}\n
                          Total time:{self.players[user_id].total_time}h.'''
                my_embed = discord.Embed(title = f'{user.name} statistics', description = msg, colour = discord.Colour.blue())
                await ctx.channel.send(embed = my_embed)
            else:
                my_embed = discord.Embed(title=f"{user.name} you don't belogn to any faction", colour=discord.Colour.red())
                await ctx.channel.send(embed = my_embed)

        @self.command(name = "rankfactions")
        async def rankfactions(ctx):
            check_role = discord.utils.get(ctx.guild.roles, name="CdS Referee")
            if check_role == None:
                my_embed = discord.Embed(title="Please name a referee first. Only referee can use this command.", colour=discord.Colour.red())
                await ctx.channel.send(embed=my_embed)
                return
            role_ref = discord.utils.get(ctx.message.author.roles, name="CdS Referee")
            if role_ref == None:
                my_embed = discord.Embed(title ="Only referees can use this command.", colour = discord.Colour.red())
                await ctx.channel.send(embed = my_embed)
                return
            rank_list = self.manager.get_rank_factions()
            tmp = [f'{x[0]} : {x[1]}' for x in rank_list]
            #perdoname madre por mi codice sporco
            for position in range(len(tmp)):
                tmp[position] = '{}. {}'.format(position+1, tmp[position])

            msg = 'Factions | Points\n' + '\n'.join(tmp);
            my_embed = discord.Embed(title = "Rank factions", description=msg, colour= discord.Colour.blue())
            await ctx.channel.send(embed = my_embed)

        @self.command(name="rankusers")
        async def rankusers(ctx):
            check_role = discord.utils.get(ctx.guild.roles, name="CdS Referee")
            if check_role == None:
                my_embed = discord.Embed(title="Please name a referee first. Only referee can use this command.",
                                         colour=discord.Colour.red())
                await ctx.channel.send(embed=my_embed)
                return
            role_ref = discord.utils.get(ctx.message.author.roles, name="CdS Referee")
            if role_ref == None:
                my_embed = discord.Embed(title="Only referee can use this command.", colour=discord.Colour.red())
                await ctx.channel.send(embed=my_embed)
                return
            rank_list = self.manager.get_rank_users()
            tmp = [f'{ctx.guild.get_member(int(x[0])).mention}\t| {x[1][0]} CFU \t| {x[1][1]} Hours' for x in rank_list]
            # perdoname madre por mi codice lezzo
            for position in range(len(tmp)):
                tmp[position] = '{}. {}'.format(position + 1, tmp[position])
            msg = 'Position\t|User\t|Points\t|Hours|\n' + '\n'.join(tmp);
            my_embed = discord.Embed(title="Rank user list", description=msg, colour=discord.Colour.blue())
            await ctx.channel.send(embed=my_embed)



    async def on_voice_state_update(self, member, before, after):
        #ctx = discord.utils.get(self.get_all_channels(), name='generale')
        if before.channel != None and after.channel != None:
            if before.channel.name == after.channel.name:
                return
        user_id = str(member.id)
        if user_id in self.players.keys():
            faction = self.manager.get_faction_from_id(user_id)
            channel_id = self.manager.get_id_channel(faction)
            ctx = self.get_channel(int(channel_id))
            if before.channel == None:
                after_status_channel = after.channel.id
                if after_status_channel == ID_VOICE_CHANNEL:
                    current_time = round(time.time(), 1)
                    self.players[user_id].start_session(current_time)
                    my_embed = discord.Embed(description=f'{member.mention} connected to {after.channel.name} at {time.ctime(current_time)}.', colour = discord.Colour.green())
                    await ctx.send(embed = my_embed)
            else:
                before_status_channel = before.channel.id
                if before_status_channel == ID_VOICE_CHANNEL:
                    current_time = round(time.time(), 1)
                    self.players[user_id].end_session(current_time)
                    self.players[user_id].updateStudyTime()
                    self.players[user_id].updateDailyTime()
                    self.players[user_id].update_session()
                    my_embed = discord.Embed(description = f'{member.mention} disconnected from {before.channel.name} at {time.ctime(current_time)}.', colour = discord.Colour.green())
                    await ctx.send(embed = my_embed)
                    if self.players[user_id].study_time >= 1:
                        my_embed = discord.Embed(description=f'{member.mention} studied {self.players[user_id].study_time}h.',
                                                 colour = discord.Colour.green())
                        await ctx.send(embed = my_embed)
                    else:
                        my_embed = discord.Embed(
                            description=f'{member.mention} studied {self.players[user_id].study_time}h.',
                            colour=discord.Colour.green())
                        await ctx.send(embed = my_embed)
                else:
                    if after.channel == None:
                        return
                    after_status_channel = after.channel.id
                    if after_status_channel == ID_VOICE_CHANNEL:
                        current_time = round(time.time(), 1)
                        self.players[user_id].start_session(current_time)
                        my_embed = discord.Embed(
                            description=f'{member.mention} connected to {after.channel.anem} at {time.ctime(current_time)}.',
                            colour=discord.Colour.green())
                        await ctx.send(embed = my_embed)

    @tasks.loop(hours = 24)
    async def updateData(self):
        print("In updateData")
        print(self.players.keys())
        if dt.datetime.now().hour == 23:
            for user_id in self.players.keys():
                print(user_id)
                self.players[user_id].updatePoints()
                self.manager.update_user(user_id, self.players[user_id].daily_points, self.players[user_id].points,
                                        self.players[user_id].daily_time,
                                        self.players[user_id].total_time, self.players[user_id].warnings)
        print("end")

    @updateData.before_loop
    async def before_updateData(self):
        for sec in range(60 * 60 * 24):  #loop the hole day
            if dt.datetime.now().hour == 23:  #24 hour format
                #await self.updateData()
                #await self.after_updateData()
                break
            await asyncio.sleep(1)  #wait a second before looping again. You can make it more
        print("out")

#   @updateData.after_loop
#    async def after_updateData(self):
#       print("In after")
#        for sec in range(60*60):
 #           await asyncio.sleep(1)



url = urlparse.urlparse(os.environ['DATABASE_URL'])
dbname = url.path[1:]
user = url.username
password = url.password
host = url.hostname
port = url.port

print(dbname, user, password, host, port)
intents = discord.Intents.default()
intents.members = True

mybot = CdSBot(command_prefix='?', self_bot=False, help_command=None, intents = intents,
                dbname = dbname, user= user, password = password, host = host, port = port)

token_file = open("token", 'r')
token = token_file.readlines()[0]
mybot.run(token)


