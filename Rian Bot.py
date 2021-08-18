import os, time, discord, threading, sqlite3, re, random, redditapi, uwuowo
import numpy as np
from discord.ext import commands, tasks
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.members = True

# The following are arrays used to keep hold of information.
invites = []
host = ["Party", "Invites", "party message", "host message"]
creation = []
events = []
SERVERID = REDACTED
accept = []
reject = []
channel = ["000", "$", '000', '']
msgcon = ["Message", 'Capacity', 'Time']
rolepending = []
users = []
setup = []
party = []
games = []
temproles = []

global gameslist
gameslist = []

global gamesuser
gamesuser = []

global translate
translate = []
client = commands.Bot(command_prefix=channel[1], intents=intents, help_command = None)


# Registering an event
@client.event
async def on_ready():
    Activity = ["Making a sandwich", "Doing whatever Ryan is doing but better", "Crying in a corner", "Making fun of Lukian", "Finding deals"]
    getChannel()
    await loadEverything()
    loadEvents()
    checktime.start()
    checkDelayedtime.start()
    await checkroleOffline(rolepending)
    print("Bot is ready to be used.")


# Error Catcher
'''
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('You seem to be missing an argument or two....')
'''



'''
Help command that sends a google doc
'''
@client.command()
async def help(ctx):
    await ctx.author.send("Hi heres a underconstruction doc for help... \n" \
                          "https://docs.google.com/document/d/1brDHpbReaP89DvLPR0Z-zqxtvvb6tEFNSTVmbKRyC5c/edit?usp=sharing ")

'''
Creates an invite for a game thats already in that database.
'''


@client.command()
async def startGame(ctx, gamename, capacity, duration):
    # First check if game exists
    for game in games:
        if game[0].upper() == gamename.upper():
            # Create a custom role.
            newRole = await ctx.guild.create_role(name=gamename, mentionable=True)

            # add all people to the role.
            cnt = 1
            while cnt != len(game):
                # we have the user object, we need the member
                await ctx.guild.get_member(game[cnt].id).add_roles(newRole)
                cnt += 1
            conn = sqlite3.connect("members.db")
            Cursor = conn.cursor()
            Cursor.execute("INSERT INTO CustomRoles (Name, id) VALUES(?,?)",(gamename, newRole.id) )
            await createInvite(ctx, gamename, newRole.mention, int(capacity), int(duration))

            conn.commit()
            conn.close()

'''
Creates a game in the database that can be invited upon.
'''

@client.command()
async def removeGameUser(ctx, name, user):
    # Get the player
    guild = client.get_guild(SERVERID)
    members = guild.members
    # find the player object
    player = ''
    for y in members:
        if y.mention.replace("!", '') == user.replace("!", ''):
            # There is a match
            player = y

    if isinstance(player, str):
        await ctx.send("This player doesnt seem to exist")
        return

    # check if this game exists...
    for game in games:
        if game[0].upper() == name.upper():

            # Navigate list, first is always the name
            cnt = 1
            while cnt != len(game):
                # Found the player
                if player.id == game[cnt].id:
                    remove = player.id
                    game.pop(cnt)

                    # Create a new string to put in database
                    ids = ''
                    for x in game:
                        if not isinstance(x, str):
                            ids += x.id + " "

                    # Now we have to erase them from the database.
                    conn = sqlite3.connect("members.db")
                    Cursor = conn.cursor()

                    Cursor.execute("""UPDATE Games SET ids =? WHERE Name =?""",
                                   (ids, name,))

                    conn.commit()
                    conn.close()

                    return

                cnt += 1

    await ctx.send("That game does not exist.")


@client.command()
async def createGame(ctx, name):
    # check if this game exists...
    for game in games:
        if game[0].upper() == name.upper():
            await ctx.send("This game already exists...")
            return

    # Game does not exist, create the game.
    conn = sqlite3.connect("members.db")
    Cursor = conn.cursor()

    # Add the game to list and database.
    Cursor.execute("INSERT INTO Games (Name) VALUES(?)", (name,))
    games.append([name])

    conn.commit()
    conn.close()


'''
Add a new player to the database that plays a certain game.
'''


@client.command()
async def addPlayer(ctx, name, *player):
    # Check if the game exists
    for game in games:
        if game[0].upper() == name.upper():

            ids = ''
            guild = client.get_guild(SERVERID)
            members = guild.members
            # Convert the player list to ids
            players = list(player)
            for x in players:
                for y in members:
                    if y.mention.replace("!", '') == x.replace("!", ''):
                        flag = 0
                        for z in game:
                            if not isinstance(z, str):
                                # The id already exists in this list dont add it
                                if (y.id == z.id):
                                    flag = 1
                                    await ctx.send(
                                        "it seems " + y.name + " is already in this group")
                        # now check if that member is already in the list so we dont have doubles.
                        if flag == 0:
                            ids += str(y.id) + " "

            # Get the current list of players:
            cnt = 1  # First is the name not a player
            while cnt != len(game):
                ids += str(game[cnt].id) + " "
                cnt += 1

            conn = sqlite3.connect("members.db")
            Cursor = conn.cursor()

            # get id of new players
            Cursor.execute("""UPDATE Games SET ids =? WHERE Name =?""",
                           (ids, name,))

            # Get a new list of all memebr object
            gamers = getUserObject(ids)
            # Reset the object and populate.
            game.clear()
            game.append(name)
            game.extend(gamers)
            conn.commit()
            conn.close()

            return

    # game exists.


'''
Deletes a given game from a database
'''


@client.command()
async def deleteGame(ctx, name):
    # check if this game exists...
    for game in games:
        if game[0].upper() == name.upper():

            conn = sqlite3.connect("members.db")
            Cursor = conn.cursor()

            games.remove(game)

            Cursor.execute("DELETE FROM Games WHERE Name = \'" + name + "\'")
            conn.commit()
            conn.close()

            await ctx.send("Deleted " + name + " from the database")
            return

    await ctx.send("This game seems to not exist...")


'''
Shows all the games
'''


@client.command()
async def showGames(ctx):
    if len(games) == 0:
        await ctx.send("Seems no games exist")
        return

    string = ""
    print(games)
    for x in games:
        for y in x:
            # Title
            if isinstance(y, str):
                string += '\n**'+ y + '**' + ":\n" + "Gamers:  \r\n "
            # Member object
            else:
                string += y.name + ", "

    # Send with built String
    await ctx.send("All Games: \n" + string + '\n')


'''
Asks everyone for there prefered role
'''


@client.command()
@commands.has_permissions(administrator=True)
async def askRollEveryone(ctx):
    msg = await ctx.send("Messaging literally everyone.... \n")
    time.sleep(2)
    allusers = ctx.guild.members
    lst = []
    for user in rolepending:
        lst.append(user[1].channel.recipient.id)

    for x in allusers:
        if not x.bot:
            if x.id not in lst:
                await msgRole(x)
                await msg.edit(content="Inviting " + x.mention)
                time.sleep(0.25)


'''
Change the prefix
'''


@client.command()
async def changePrefix(ctx, prefix):
    ctx.send("this doesnt do anything yet")


'''
turns on uwu mode.
'''


@client.command()
async def uwu(ctx):
    if ctx.author in translate:
        return
    translate.append(ctx.author)


'''
Turns of owo mode
'''


@client.command()
async def owo(ctx):
    if ctx.author in translate:
        translate.remove(ctx.author)


'''
If a party exists, then asks party to remove options until one exists
'''


@client.command()
async def chooseGame(ctx, *games):
    if len(party) != 0:
        global gameslist
        gameslist = list(games)  # turn tupple into list.

        # Now we must remove the duplicates..
        gameslist = set(gameslist)
        gameslist = list(gameslist)

        # Create a copy of the list.
        global gamesuser
        gamesuser = party.copy()
        gamesuser.pop(0)

        random.shuffle(gamesuser)

        # Create a string with all games.
        String = ""
        for gm in gameslist:
            String += gm + "\n"

        await gamesuser[0].send(
            "Hi please type the name of the game you do not wish to play: \n" + String)


'''
Deletes the ongoing party.
'''

@client.command()
async def deleteParty(ctx):
    if len(party) != 0:
        await party[0].delete
        party.clear()
        gameslist.clear()


        #Delete the custom role
        conn = sqlite3.connect("members.db")
        Cursor = conn.cursor()
        Cursor.execute("DELETE FROM CustomRoles WHERE Name = \'Party\'")
        await temproles[0].delete()
        conn.commit()
        conn.close()
'''
Gets the deals that are currently available.
'''


@client.command()
async def getDeals(ctx):
    await ctx.message.delete()
    await checkDeals()


'''
Commands that create a party, allows for other options to be used.
'''


@client.command()
async def createParty(ctx, role = True):
    if len(party) == 0:
        # no current party going on
        if role or checkRole(role):
            await ctx.message.delete()
            # Delete the message.
            temproles.clear()
            #Create a temp role and save it, also add the host to it.
            newRole = await ctx.guild.create_role(name="Party", mentionable=True)

            conn = sqlite3.connect("members.db")
            Cursor = conn.cursor()
            Cursor.execute("INSERT INTO CustomRoles (Name, id) VALUES(?,?)",("Party", newRole.id) )
            await ctx.author.add_roles(newRole)
            conn.commit()
            conn.close()

            temproles.append(newRole)

            # Check if the role exists, if so ping everyone with the role.
            # if its a bool
            if type(role) == bool:
                message = await ctx.send(
                    " a party has been started by " + ctx.author.name + \
                    "\nClick on the emojis to join!")

            # if its a role
            else:
                message = await ctx.send(
                    role + " a party has been started by " + ctx.author.name + \
                    "\nClick on the emojis to join!")

            await message.add_reaction('👍')

            # Add party to the list so we can keep track of it.
            party.append(message)
            party.append(ctx.author)
        # Role doesnt exist
        else:
            await ctx.send("Did u have the wrong role?")
    else:
        await ctx.send("There seems to be an ongoing party...")


'''
Performs a coin flip, calls the roll function
'''


@client.command()
async def coinFlip(ctx):
    emoji = ['🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐮', '🐸']
    heads = emoji[random.randint(0, 7)]  # Choose what heads will be

    emoji.remove(heads)  # remove it from list

    tails = emoji[random.randint(0, 6)]
    await ctx.send("Heads =" + heads + " Tails = " + tails)
    await roll(ctx, [heads, tails])


'''
Command used for deleting an event, given its name.
'''


@client.command()
async def deleteEvent(ctx, name: str):
    for event in events:
        # the event exists, continue to delete it
        if name == event[0]:
            conn = sqlite3.connect("members.db")
            Cursor = conn.cursor()

            Cursor.execute(
                "DELETE FROM Events WHERE Name = " "\'" + name + "\'")
            events.remove(x)  # Remove from the data base and list.
            # Commit and Close.
            conn.commit()
            conn.close()

            await ctx.send("Deleted Event.")
            events.remove(event)

            return
    # If its made it here, does not exist in list.
    await ctx.send("It doesnt seem like that event exists...")


'''
Command used for asking a member for their roles.
'''


@client.command()
async def askRole(ctx):
    await msgRole(ctx.author)


@client.command()
async def showEvents(ctx):
    content = 'List of Events:\n'
    for x in events:
        if x[2] == 1:
            content += "name:" + x[0] + 'Occurs at: ' + str(x[1]) + "Pings: " + \
                       x[3] \
                       + "Repeats every: " + x[5] + 'days' + 'Created by: ' + x[
                           6] + '\n'
        else:
            content += "name: " + x[0] + ' Occurs at: ' + str(
                x[1]) + " Pings: " + x[3] \
                       + ' Created by: ' + x[6] + '\n'
    await ctx.send(content)


'''
Event that posts all logged events.
'''


@client.command()
# Command used for inviting a precreated invite.
async def eventInvite(ctx, name: str):
    for x in events:
        if x[0] == name:
            await ctx.send("Starting Event " + name)
            await inviteEvent(x)
            return
            # calls the invite on this event
    await ctx.send("No such event exists")


# Clear event
# can only work if they have the manage messages
@client.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=15)


# The error for the clear command.
@clear.error
async def clear_error(ctx, error):
    await ctx.send('You dont have permissions or you messed up the syntax :(')


'''
Function used to set announcment channel'''


@client.command()
@commands.has_permissions(manage_channels=True)
async def setAnnounce(ctx):
    id = ctx.channel.id
    channel[2] = ctx.channel
    if isinstance(ctx.channel, discord.DMChannel):
        ctx.send("This is a DM Channel >:(")

    conn = sqlite3.connect("members.db")
    Cursor = conn.cursor()
    Cursor.execute(""" DELETE FROM Channel WHERE name = 0""")
    Cursor.execute("INSERT INTO Channel(Id, name) VALUES(?,0)", (str(id),))
    conn.commit()
    # closing
    conn.close()


# Command for setting the default messaging channel.
@client.command()
@commands.has_permissions(manage_channels=True)
async def setChannel(ctx):
    id = ctx.channel.id
    channel[0] = ctx.channel
    if isinstance(ctx.channel, discord.DMChannel):
        ctx.send("This is a DM Channel >:(")

    conn = sqlite3.connect("members.db")
    Cursor = conn.cursor()
    Cursor.execute(""" DELETE FROM Channel WHERE name = 1""")
    Cursor.execute("INSERT INTO Channel(Id, name) VALUES(?,1)", (str(id),))
    conn.commit()
    # closing
    conn.close()


@client.command()
async def createEvent(ctx):
    # This implies they are already trying to create an event.
    if ctx.message.author in creation:
        await ctx.message.author.send(
            "It seems you're already trying to create an event.(Check dms)")
        return

    # They are creating it for the first time.
    await ctx.message.author.send(
        "What is the name of the event you want to create?")
    # Add this to the list of Creation dm's.
    creation.append(ctx.message.author)
    creation.append([])



@client.command()
# The command needed to invite people of a certain role.
async def invite(ctx, activity: str, role, size: int, time: int):
    await createInvite(ctx, activity, role, size, time)


# Client command, for deleting the most recent invites.
@client.command()
async def clearDms(ctx):
    await deleteInvites()


@client.event
async def on_message(msg):
    # if the message is from the bot dont do anything

    if msg.author == client.user and msg.content[0] != channel[1]:
        return

    # Event that triggers when a message is sent to bot.
    if not isinstance(msg.channel, discord.DMChannel):
        await client.process_commands(msg)
        if len(msg.content) > 0:
            if msg.content[0] == "$":
                return
        elif msg.author in translate:
            translator = uwuowo.uwuowo(msg.content)
            string = translator.give()

            context = client.get_channel(msg.channel.id)
            await context.send("*Sent by: " + msg.author.name + "*\n" + string)
            await msg.delete()
        return

    elif msg.content == "Reroll":
        # delete the previous roles.
        guild = client.get_guild(SERVERID)
        user = guild.get_member(msg.author.id)
        roles = user.roles
        for x in roles:
            if (x.name == '🥳'):
                await user.remove_roles(x)
            elif (x.name == '🎮'):
                await user.remove_roles(x)
            elif (x.name == '✉'):
                await user.remove_roles(x)
            elif (x.name == '🚫'):
                await user.remove_roles(x)

        await msgRole(msg.author)
    # This could be a party message.
    elif len(party) != 0:
        global gamesuser
        if msg.author == gamesuser[0]:
            # See if they typed the name of a given game
            global gameslist
            for x in gameslist:
                x.upper()
                msg.content.upper()
                if x == msg.content:

                    gameslist.remove(x)
                    if len(gameslist) == 1:
                        await party[0].channel.send(
                            "The party has decided on: " + str(gameslist[0]))

                        # Clearing everything as the game has been selected.
                        gameslist.clear()
                        gamesuser.clear()
                        return

                    elif len(gamesuser) == 1:
                        # This is the last user in the party, we need to loop...
                        gamesuser = party.copy()
                        gamesuser.pop(0)
                        random.shuffle(gamesuser)

                        String = ""
                        for gm in gameslist:
                            String += gm + "\n"

                        await gamesuser[0].send(
                            "Hi please type the name of the game you do not wish to play: \n" + String)
                        return

                    else:

                        gamesuser.pop(0)
                        String = ""
                        for gm in gameslist:
                            String += gm + "\n"

                        await gamesuser[0].send(
                            "Hi please type the name of the game you do not wish to play: \n" + String)
                        return


    elif msg.author in creation:
        # this implies that they are dming to create an event.
        # Three situations.
        info = creation[creation.index(msg.author) + 1]
        if len(info) == 0:
            # Theyre setting up the name
            info.append(msg.content)
            await msg.author.send("Is this event reoccuring?(Yes / No)")
            # Send next message

        elif len(info) == 1:
            # Setting repeatable
            cont = msg.content.upper()  # Convert text to upper to prevent case sens
            if (cont == "YES"):
                info.append(1)
            elif (cont == "NO"):
                info.append(0)
            else:
                return
            await msg.author.send("What date and time? (YYYY-MM-DD HH:MM)")

        elif len(info) == 2:
            # Setting the date for the event
            cont = msg.content
            # The regular expression for the date and time.
            regx = re.fullmatch("(\d{4})-(\d{2})-(\d{2})\s(\d{2}):(\d{2})",
                                cont)

            if regx:
                # If match continue.
                # now we must validate the months and stuff.
                try:
                    # try the date time... if its valid.

                    eventdate = datetime(int(regx.group(1)), int(regx.group(2)),
                                         int(regx.group(3)), int(regx.group(4)),
                                         int(regx.group(5)))
                except ValueError:
                    await msg.author.send("The date seems to be off....")
                    return
                # not a proper date... please continue
                info.append(eventdate)  # add thing to the list.
                await msg.author.send(
                    "Please give me the role name you'd like to invite.")
            else:  # failed the regx
                await msg.author.send(
                    "Please make sure its in this exact format YYYY-MM-DD HH:MM ")
        elif len(info) == 3:
            cont = msg.content

            # Go through the roles of the guild to find the names of each
            guild = client.get_guild(SERVERID)
            for x in guild.roles:

                if cont.upper() == x.name.upper():
                    # The role exists
                    info.append(cont)
                    await msg.author.send("Set the capacity")
                    return
            # if it makes here could not find a match

            await msg.author.send("That role doesnt seem to exist.")

        elif len(info) == 4:
            cont = msg.content
            # Setting the capacity.
            if cont.isnumeric():
                # it has to be a number
                if int(cont) != 0:
                    # Cannot be 0
                    info.append(int(cont))
                    if info[1] == 1:
                        # this implies that it is reoccuring
                        await msg.author.send(
                            "How often should this occur? (days)")

                    else:
                        # Log the event into the database
                        logEvent(info, str(msg.author))
                        info = creation.pop(creation.index(msg.author))
                        # Remove the user from creator list
                        await msg.author.send("The event has been saved!")
        # will only occur if its reoccuring...
        elif len(info) == 5:
            cont = msg.content
            if cont.isnumeric():
                # it has to be a number
                if int(cont) != 0:
                    # Cannot be 0
                    info.append(int(cont))
                    logEvent(info, str(msg.author))
                    info = creation.pop(creation.index(msg.author))
                    # Remove the user from creator list
                    await msg.author.send("The event has been saved!")

@client.event
async def on_member_join(member):
    await msgRole(member)

# For when a reaction is removed.
@client.event
async def on_reaction_remove(reaction, user):
    # if someone reacts on a message not in a dm
    if not isinstance(reaction.message.channel, discord.DMChannel):
        return


# raw reaction for old messages that no longer exist in cache
@client.event
async def on_raw_reaction_add(payload):
    for x in rolepending:
        if x[1].id == payload.message_id:
            # Implies that this is a welcome message.

            if str(payload.emoji) == '✅':
                # We must get the reaction object and user Object so we can reuse this function.
                channel = await client.fetch_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)

                # Get the message, with the message find the reaction
                listofreaction = message.reactions

                for x in listofreaction:
                    if str(x) == '✅':
                        # We have found the reaction, now call the function

                        await bootRoleCheck(x, await client.fetch_user(
                            payload.user_id))


# handeler for when someone reacts on a message.
@client.event
async def on_reaction_add(reaction, user):
    # if someone reacts on a message not in a dm
    if not isinstance(reaction.message.channel, discord.DMChannel):
        return
    # if the bot did a reaction ignore.
    elif (reaction.message.author == user):
        return
    # This is a party invite
    if len(party) != 0:
        if party[0].id == reaction.message.id:
            if (str(reaction) == '👍'):  # They are joining the party

                guild = client.get_guild(SERVERID)
                await guild.get_member(user.id).add_roles(temproles[0])
                party.append(user)

    # We use this if the message is an invite.
    elif (reaction.message in invites):
        if (str(reaction) == '✅'):
            # This function does all the checking...
            await checkPendEmoji(reaction.message, user)
        # #now we must update the message.
        await hostInvite(host[1])
        Names = buildString()
        for y in invites:
            await y.edit(content=msgcon[0] + Names)

        return


'''
Function used to check the confirmation message
for pending roles
'''


async def bootRoleCheck(reaction, user):
    lst = await checkRoleEmoji(reaction.message, user)
    if 1 in lst:
        # Send the user a confirmation message, depending on which one they selected.
        if lst[3] == 1:
            await user.send(
                "You are now marked DNS, to get another role type Reroll.")
        elif lst[2] == 1:
            await user.send(
                "You are now marked ping for everything, to get another role type Reroll.")
        elif lst[1] and lst[0] == 1:
            await user.send(
                "You are now marked ping for gaming and parties, to get another role type Reroll.")
        elif lst[1] == 1:
            await user.send(
                "You are now marked ping for gaming, to get another role type Reroll.")
        elif lst[0] == 1:
            await user.send(
                "You are now marked ping for parties, to get another role type Reroll.")

        # Remove them from the pool
        for x in rolepending:
            if x[1].id == reaction.message.id:
                rolepending.remove(x)
        await reaction.message.delete()

        # Change the data base.
        conn = sqlite3.connect("members.db")
        Cursor = conn.cursor()

        Cursor.execute("DELETE FROM Users WHERE Id=\'" + user.name + "\'")
        # remove them from the pending as role is created.
        conn.commit()

        # closing
        conn.close()
    else:
        await user.send("Please select an option :/")


async def deleteInvites():
    for x in invites:
        await x.delete()
        # deleting every invite.
    # clearing the list as they no longer exist.
    invites.clear()
    accept.clear()
    reject.clear()
    host = ["Party", "Invites", "party message", "host message"]


# Checks to see if the current message is expired.
async def checkTime():
    # Check the time every second.
    await checkTimeEvents()

    # if there are current invites there must be a date time.
    if (len(invites) != 0):
        curr = datetime.now()

        if (curr > msgcon[2]):
            await deleteInvites()


# Function called when we want to check if an event is going to start.
async def checkTimeEvents():
    curr = datetime.now()
    delta1 = timedelta(minutes=60)
    for x in events:
        # Will only occur if event happened within an hour
        if (curr > x[1] and curr < x[1] + delta1):
            ctx = channel[0]

            await inviteEvent(x)
            await ctx.send("Creating invites for event: " + x[0])
            # Create invites of the event, using invite event..
            conn = sqlite3.connect("members.db")
            Cursor = conn.cursor()

            if x[2] == 1:
                # it is repeatable.

                # modifying the database.
                delta1 = timedelta(
                    days=x[4])  # Represents the amount of days to shift.
                x[4] = x[4] + delta1  # This is the new date
                date = str(x[4].year) + '-' + str(x[4].month) + '-' \
                       + str(x[4].day) + " " + str(x[4].hour) + ":" + str(
                    x[4].minute)
                # The string representation thats needed to save back in the data base.

                Cursor.execute(""" UPDATE Events SET Date=? WHERE Name=?"""), (
                    date, x[0])
                # Update the line.

            else:
                name = x[0]
                Cursor.execute(
                    "DELETE FROM Events WHERE Name = " "\'" + name + "\'")
                events.remove(x)  # Remove from the data base and list.
            # Commit and Close.
            conn.commit()
            conn.close()

        # If the event has passed a while ago and is repeatable, therefore
        # Dont activate just reset the event.
        elif (curr > x[1] and x[2] == 1):

            # it is repeatable.

            # modifying the database.
            delta1 = timedelta(
                days=x[4])  # Represents the amount of days to shift.
            x[4] = x[4] + delta1  # This is the new date
            date = str(x[4].year) + '-' + str(x[4].month) + '-' \
                   + str(x[4].day) + " " + str(x[4].hour) + ":" + str(
                x[4].minute)
            # The string representation thats needed to save back in the data base.
            conn = sqlite3.connect("members.db")
            Cursor = conn.cursor()
            Cursor.execute(""" UPDATE Events SET Date=? WHERE Name=?"""), (
                date, x[0])
            # Update the line.
            # Commit and Close.
            conn.commit()
            conn.close()


# Calculates the expirary of a message given a time.
def calculateTime(time: int):
    now = datetime.now()
    delta1 = timedelta(minutes=time)

    msgcon[2] = now + delta1


# The function used to build the updated string
# Returns a string of everyone who accepted.
def buildString():
    names = ''
    # Build the string with everyones name who accepted
    for x in accept:
        names = names + x.display_name + "\n"

    return names


# loggin the info to the event
def logEvent(info: list, creator: str):
    conn = sqlite3.connect("members.db")
    # Connecting to data base.

    # Create the cursor.
    Cursor = conn.cursor()
    if info[1] == 1:
        # If its a repeatable insert the value
        Cursor.execute(
            "INSERT INTO Events(Name, Date, repeatable, role, occupancy, frequency, Creator) VALUES(?,?,?,?,?,?,?)",
            (info[0], info[2], info[1], info[3], info[4], info[5], creator))
    else:
        # not a repeatable the value is null
        Cursor.execute(
            "INSERT INTO Events(Name, Date, repeatable, role, occupancy, frequency, Creator) VALUES(?,?,?,?,?,null,?)",
            (info[0], info[2], info[1], info[3], info[4], creator))
    conn.commit()
    conn.close()

    # Commit and close the info.

    creation.remove(info)

    # Clear the info once were done with it.


# This function loads all the events from the data base and puts it into a list.
def loadEvents():
    events.clear()
    # Clear event

    conn = sqlite3.connect("members.db")
    Cursor = conn.cursor()

    # Select everything in the events tab
    Cursor.execute(("SELECT * FROM Events"))

    # Put it all in this temp variable...
    temp = Cursor.fetchall()

    # add all of them to the list.
    for x in temp:
        x = np.asarray(x)  # Convert tupple to arary
        x = x.tolist()
        x[1] = datetime.strptime(x[1],
                                 '%Y-%m-%d %H:%M:%S')  # Convert the string to datetime object
        events.append(x)


'''
Function to check if we should post new deals.
'''


async def checkdealtime():
    # Get current time and timedelta to shift
    currtime = datetime.now()
    delta = timedelta(days=1)

    # The time does not exist for some reason.
    if channel[3] == '':
        await checkDeals()

        conn = sqlite3.connect("members.db")
        Cursor = conn.cursor()

        date = str(currtime.year) + '-' + str(currtime.month) + '-' \
               + str(currtime.day) + " " + str(currtime.hour) + ":" + str(
            currtime.minute)

        Cursor.execute("INSERT INTO Channel(Id, name) VALUES(?,2)", (date,))
        channel[3] = currtime

        conn.commit()
        conn.close()
    # Check ifs it been a day since last post.
    if channel[3] + delta < currtime:
        await checkDeals()  # call the api

        # Save the new date
        conn = sqlite3.connect("members.db")
        Cursor = conn.cursor()

        channel[3] = currtime  # Set the new channel time

        date = str(currtime.year) + '-' + str(currtime.month) + '-' \
               + str(currtime.day) + " " + str(currtime.hour) + ":" + str(
            currtime.minute)

        Cursor.execute(""" DELETE FROM Channel WHERE name = 2""")
        Cursor.execute("INSERT INTO Channel(Id, name) VALUES(?,2)", (date,))

        conn.commit()
        conn.close()
        # Close


# The command used to set the default channel on boot up
def getChannel():
    conn = sqlite3.connect("members.db")
    Cursor = conn.cursor()

    Cursor.execute("SELECT * FROM Channel Where name = 1")
    info = Cursor.fetchall()
    # Retrieve the ID from the data base and now find that channel.
    chl = client.get_channel(int(info[0][0]))
    channel[0] = chl

    # Get teh channel for announcments too.
    Cursor.execute("SELECT * FROM Channel Where name = 0")
    info = Cursor.fetchall()

    # quite literally the same thing.
    chl = client.get_channel(int(info[0][0]))
    channel[2] = chl

    # Am too lazy to store time somewhere else, so storing it here.

    Cursor.execute("SELECT * FROM Channel Where name = 2")
    info = Cursor.fetchall()

    # Convert the string to
    # channel[3] = datetime.strptime(info[0][0],
    # '%Y-%m-%d %H:%M:%S')

    conn.commit()
    conn.close()


# Command for creating an event invite which just the name of the invite.
async def inviteEvent(list):
    await clearDms()
    ctx = channel[0]

    # The role should exist, but we should check if the role still exists...
    roles = client.get_guild(SERVERID).roles
    msgcon[1] = list[4]  # The size
    calculateTime(30)  # The time

    for x in roles:
        # look for the role
        if x.name == list[3]:
            # The role exists.
            members = x.members

            for y in members:
                # Send the message to the user dm
                user = client.get_user(y.id)

                msgcon[
                    0] = "Hi this is an automated event invite \n People who have accepted: \n"
                # keep track of the message so we can add reactions.
                message = await user.send(msgcon[0])
                # adding the reactions to the message to keep track of accepts.
                await message.add_reaction('👍')
                await message.add_reaction('👎')
                await message.add_reaction('✅')
                # add the message to the list so we can delete it later.
                invites.append(message)

            await ctx.send('Sending invites...')

            return
    # The role does not exist.
    await ctx.send('It seems the role you want to invite does not exist.')


'''
Sends a message to whom ever started the invite. 
Tells them who is yets to do anything...
'''


async def hostInvite(member):
    Accepted = ""
    Declined = ""
    Pend = ""
    pending = invites.copy()  # Create a copy of the list.

    # Check if users have accepted, declined or have not done anything...
    for x in pending:
        if x.author in accept:  # If they are in accept, or decline.
            Accepted += x.channel.recipient.name + "\n"
        elif x.author in reject:
            Declined += x.channel.recipient.name + "\n"
        else:
            # still in pending
            Pend += x.author.name + "\n"

    # Has this message already been sent? If not send for first time
    if host[3] == "host message":

        message = await member.send("Pending:\n" + Pend + "Accepted:\n" \
                                    + Accepted + "Declined: \n" + Declined)
        host[3] = message

    # message already exists... Just edit it
    else:
        await host[3].edit(content="Pending:\n" + Pend + "Accepted:\n" \
                                   + Accepted + "Declined: \n" + Declined)


# The command used to create invites, is used by the bot and user.
async def createInvite(ctx, activity, role, size, time):

    if len(invites) != 0 :
        await ctx.send("There seems to be another invite happening, please use clearDms")
        return

    # Creating guild object
    guild = client.get_guild(SERVERID)

    roles = guild.roles
    # error handle negative numbers
    if size < 1:
        await ctx.send('Please select a party size greater than 0')
        return
    msgcon[1] = size
    calculateTime(time)
    # The capacity for the invites and time for the invite.

    # Putting the host in a special so we can dm them master list.
    host[1] = ctx.author
    accept.append(ctx.author)

    for x in roles:
        # Check if the role exists in the server.

        if role == x.mention or role == x.name:
            # The Role exists, now sending invites

            member = x.members
            # Cycle through every member to send a dm to each.
            for y in member:

                if y.id != host[1].id:  # dont send invite to host.
                    # Send the message to the user dm
                    user = client.get_user(y.id)

                    msgcon[
                        0] = "Hi this is an automated invite. \nYou are being invited to play " + activity + "\n By: " +\
                             host[1].name + " \n Party Capacity: " + str(size) + "\n People who have accepted: \n"
                    # keep track of the message so we can add reactions.
                    message = await user.send(msgcon[0])
                    # adding the reactions to the message to keep track of accepts.
                    await message.add_reaction('👍')
                    await message.add_reaction('👎')
                    await message.add_reaction('✅')
                    # add the message to the list so we can delete it later.
                    invites.append(message)

            await ctx.send('Sending invites...')

            await hostInvite(ctx.author)
            return
    # The role does not exist.
    await ctx.send('It seems the role you want to invite does not exist.')


# Command that will dm this person with a role invite.
async def msgRole(user):
    # Sends message to user.
    message = await user.send(
        "Welcome to Stop Making Group Calls, I am Ryan's custom bot for the server! \n"
        + "I was created to make it easier manage and invite the server as well as torture Lukian.\n"
        + "To help with the process im here to ask you to choose the role that best fits what you want.\n"
        + "Just react with the emote of the option you want!\n\n "
          "🥳 if you want to be pinged for party related events.\n"
        + "🎮 if you want to be pinged for games.\n"
        + "✉ if you want to be pinged for everything.\n"
        + "🚫 if you want this bot to never talk to you or your kids again.\n"
        + "✅ to confirm your selction.\n"
        + "😠 If you would like to speak to a manager. \n"
    )

    # adding emojis
    await message.add_reaction('🥳')
    await message.add_reaction('🎮')
    await message.add_reaction('✉')
    await message.add_reaction('🚫')
    await message.add_reaction('✅')
    await message.add_reaction('😠')

    conn = sqlite3.connect("members.db")
    Cursor = conn.cursor()
    # Append to the list.
    lst = [user.name, message]

    for x in rolepending:
        # See if the user is registered in the data base.
        if user.name == x[0]:

            # Remove them from the list and add new one also delete prev message.
            await x[1].delete()
            rolepending.remove(x)
            rolepending.append(lst)
            # Theres a match.
            Cursor.execute("UPDATE Users SET RoleCreation =\'" + str(
                message.id) + "\' WHERE Id =\'" + user.name + "\'")

            # Updating the user to the data base and adding them to the list of role pending...
            conn.commit()
            conn.close()
            return

    Cursor.execute(
        "INSERT INTO Users(Id, DNS, RoleCreation, ChannelID) VALUES(?, 0, ?, ?)",
        (user.name, message.id, message.channel.id))
    rolepending.append(lst)
    # The user is not in the data base... Create an entry
    conn.commit()
    conn.close()


'''
Function that calls the reddit API
to get hot deals
'''


async def checkDeals():
    thing = redditapi.Reddit()
    deals = thing.getHotdeals()
    ctx = channel[2]

    # A list of the past 30 messages
    oldmsgs = await ctx.history(limit=30).flatten()

    # Now we need to check if the message already exists.
    for msg in oldmsgs:
        for deal in deals:

            # The message was already posted, remove it
            if msg.content == deal:

                if deal in deals:
                    deals.remove(deal)

    # post the remaining deals
    for x in deals:
        await ctx.send(x)


# Calls all the loading functions
async def loadEverything():
    loadEvents()
    await loadUsers()
    await loadGames()
    await loadRoles()


'''
Loads all roles, and deletes them
'''


async def loadRoles():
    conn = sqlite3.connect("members.db")
    Cursor = conn.cursor()

    Cursor.execute("""SELECT * FROM CustomRoles""")
    info = Cursor.fetchall()

    guild = client.get_guild(SERVERID)
    # Find the role object and delete
    for x in info:
        print(x)
        if guild.get_role(x[1]) != None:
            await guild.get_role(x[1]).delete()

    # Clear the data base.
    Cursor.execute("""DELETE FROM CustomRoles""")

    # Commit and close.
    conn.commit()
    conn.close()


''' 
Loads the games into the list
'''


async def loadGames():
    conn = sqlite3.connect("members.db")
    Cursor = conn.cursor()

    Cursor.execute("""SELECT * FROM Games""")
    info = Cursor.fetchall()

    for x in info:
        if isinstance(x[1], str):
            lst = [x[0]] + getUserObject(x[1])
        else:
            lst = [x[0]]
        games.append(lst)


# Loads the users from the database and populates the arrays.
async def loadUsers():
    conn = sqlite3.connect("members.db")
    Cursor = conn.cursor()

    Cursor.execute("""SELECT * FROM Users""")
    info = Cursor.fetchall()
    for user in info:
        if user[2] != 0:
            # if there is a message id that means they still dont have a role.

            x = await client.fetch_channel(user[3])
            mess = await x.fetch_message(user[2])

            rolepending.append([user[0], mess])
            # Add the user to the role pending list.


async def checkPendEmoji(msg, user):
    TrueFalse = [0, 0]
    emojis = msg.reactions

    for symbol in emojis:
        if symbol.count == 2:
            # They have accepted
            if (str(symbol) == '👎'):
                reject.append(user)
                TrueFalse[0] = 1
            elif (str(symbol) == '👍'):
                accept.append(user)
                TrueFalse[1] = 1

    # Nothing was selected.
    if (TrueFalse[0] == 0 and TrueFalse[1] == 0):
        await msg.clear_reactions
        await message.add_reaction('👍')
        await message.add_reaction('👎')
        await message.add_reaction('✅')

    # Some idiot pressed both emojis trying to fuck it up
    elif (TrueFalse[0] == 1 and TrueFalse[1] == 1):
        reject.remove(user)
        accept.remove(user)
        await msg.clear_reactions
        await message.add_reaction('👍')
        await message.add_reaction('👎')
        await message.add_reaction('✅')

    # Nothing wrong happened procced as normal

    elif (TrueFalse[1] == 1):
        # Accepted
        invites.remove(msg)
        await msg.delete(delay=None)
        # Delete the invite and send confirmation message.

        message = await user.send(
            "Invite Confirmed \n People who have accepted:")
        invites.append(message)

        # if the last invite has been selected...
        if msgcon[1] == 1:
            msgcon[
                0] == "Sorry were out of room \n People who have accepted:"
            Names = buildString()
            for y in invites:
                await y.edit(content=msgcon[0] + Names)

            await deleteInvites()

        msgcon[1] -= 1  # Another person has accepted.

    else:
        # The only option left is a reject.
        await msg.delete(delay=None)
        # Delete the invite and send confirmation message.

        # They have declined the invite.
        invites.remove(reaction.message)
        message = await user.send("Invite Declined")


''' 
The function responsible for checking what the user has clicked on for the pending role.
'''


async def checkRoleEmoji(msg, user):
    guild = client.get_guild(SERVERID)
    userId = user.id
    member = guild.get_member(userId)
    emoji = msg.reactions  # List of all reactions
    TrueFalse = [0, 0, 0, 0]

    # Checking which emojis are selected.
    for symbol in emoji:
        if symbol.count == 2:
            if (str(symbol) == '🥳'):
                TrueFalse[0] = 1
            elif (str(symbol) == '🎮'):
                TrueFalse[1] = 1
            elif (str(symbol) == '✉'):
                TrueFalse[2] = 1
            elif (str(symbol) == '🚫'):
                TrueFalse[3] = 1
            elif (str(symbol) == '😠'):
                await client.get_user(REDACTED).send(
                    user.name + " has Complained!")

    # Giving the role to the User.
    if TrueFalse[3] == 1:
        # Check if the role exists.
        if checkRole("🚫"):
            await member.add_roles(getRole("🚫"))
        else:  # Does not exist create the role and add
            await guild.create_role(name="🚫", mentionable=True)
            await member.add_roles(getRole("🚫"))
        return TrueFalse

    if TrueFalse[2] == 1:
        if checkRole("✉"):
            await member.add_roles(getRole("✉"))
        else:
            await guild.create_role(name="✉", mentionable=True)
            await member.add_roles(getRole("✉"))

    if TrueFalse[0] == 1:
        if checkRole("🥳"):
            await member.add_roles(getRole("🥳"))
        else:
            await guild.create_role(name="🥳", mentionable=True)
            await member.add_roles(getRole("🥳"))
        return TrueFalse


    elif TrueFalse[1] == 1:
        if checkRole("🎮"):
            await member.add_roles(getRole("🎮"))
        else:
            await guild.create_role(name="🎮", mentionable=True)
            await member.add_roles(getRole("🎮"))
        return TrueFalse
    return TrueFalse


'''
Given a string of ids (Seperated by spaces), returns a list of users'''


def getUserObject(list):
    members = []
    ids = list.split(" ")

    if isinstance(ids, str):
        return
    # Get all objects through client.

    for x in ids:
        if x != '':
            members.append((client.get_user(int(x))))

    return members


'''
Finds and returns a role
'''


def getRole(symbol: str):
    guild = client.get_guild(SERVERID)
    roles = guild.roles

    for role in roles:
        if symbol == role.name:
            return role


'''
Check if the role exists.
Returns Bool
'''


def checkRole(symbol: str):
    guild = client.get_guild(SERVERID)
    roles = guild.roles

    for role in roles:
        if symbol == role.name or symbol.replace("!", '') == role.mention:
            return True

    # Check via loop and return true

    return False  # Does not exist


'''
Rolls and returns what it rolls on.
also plays an animation.
'''


async def roll(ctx, chances):
    # base case.
    if len(chances) == 1:
        return chances[0]

    # Shuffle the chances so its not rigged.
    random.shuffle(chances)
    # the amount of times the spinner will spin
    roll = random.randint(5, 10)
    timer = 200  # This is needed for animation timing.
    counter = 0

    # The string that will show the annimation, if its only 2 length loop at the start.
    if len(chances) == 2:
        content = str(chances[0]) + ' ' + str(chances[1]) + ' ' + str(
            chances[0])
        message = await ctx.send("ROLL:  \n" + content + \
                                 "\n------^------")
        # We need to cases for when its two and more than two.
        for i in range(roll):

            if counter == 2:
                content = str(chances[0]) + ' ' + str(chances[1]) + ' ' + str(
                    chances[0])
                counter = 0
            else:
                content = str(chances[1]) + ' ' + str(chances[0]) + ' ' + str(
                    chances[1])
            counter += 1

            await rollanimation(content, timer / 1000, message)

        # The final message
        time.sleep(0.5)
        await  message.edit(content="Rolled a " + str(chances[0]))
        return (chances[0])
        # for all cases that are not a coin flip
    else:

        content = str(chances[0]), str(chances[1]), str(chances[2])
        message = await ctx.send("ROLL:  \n" + content + \
                                 "\n------^------")

        for i in range(roll):
            if counter + 1 == len(chances) - 1:
                content = str(chances[content - 1]), str(chances[content]), str(
                    chances[0])
                counter = 0
            else:
                content = str(chances[content - 1]), str(chances[content]), str(
                    chances[content + 1])

            counter += 1
            await rollanimation(content, timer / 1000, message)

        # The final message
        time.sleep(0.5)
        await  message.edit(content="Rolled a " + str(chances[0]))

        return (chances[0])


'''
Function used to animate the roll animation
'''


async def rollanimation(cont, sleeper, message):
    await message.edit(content="ROLL: \n" + cont + '\n' + \
                               "------^------")
    time.sleep(sleeper)


'''
Called whenever the thing is booted, to check
if role messages have changed since bot has went online.'''


async def checkroleOffline(lst):
    for x in lst:
        emojis = x[1].reactions
        for emoji in emojis:
            # looking for the confirmation emoji...
            if str(emoji) == '✅':
                # check if the user has selected it. if so call the next function.
                if emoji.count == 2:
                    await bootRoleCheck(emoji, client.get_user(
                        x[1].channel.recipient.id))


# Run this command every minute to check the time.
# Run to check time
@tasks.loop(seconds=1)
async def checktime():
    await checkTime()


'''
To prevent lag, some things are on longer timers.
'''


@tasks.loop(minutes=10)
async def checkDelayedtime():
    await checkdealtime()


client.run("REDACTED")
