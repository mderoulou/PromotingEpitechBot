#!/bin/python3
import pymysql
import discord
from discord.ext import commands
import re
import os
import json
import datetime
import xlsxwriter
import subprocess
from minesql import create_con
import random

intents = discord.Intents.default()
intents.members = True
intents.messages = True
client = commands.Bot(command_prefix='>', help_command=None, intents=intents)
welcome_text = ["**➡️** On souhaite la bienvenue à {0} sur le discord d'Epitech ! :tada:",
                "**➡️** {0} a rush B, puis est arrivé parmis nous, on te souhaite la bienvenue ! :boom:",
                "**➡️** Erreur 404 ... Ah non code 200 je voulais dire, bienvenue {0} ! :wrench:",
                "**➡️** {0} est arrivé ! Tous à vos téléphones ! :mobile_phone:",
                "**➡️** {0} est venu pour taper du code ! Bienvenue à toi ! :bulb:",
                "**➡️** Un {0} sauvage apparaît ! Bienvenue à toi ! :sparkles:",
                "**➡️** Code de triche activé ! {0} arrive sur le serveur ! :joystick:",
                "**➡️** Rentre vite {0}, il fait froid dehors ! :fire:",
                "**➡️** Bonne nouvelle ! {0} est arrivé à destination ! :gift:",
                "**➡️** {0} \* boup bip bou \* Bienvenue ! :robot:",
                "**➡️** Toi tu vis, toi tu vis, toi tu arrives ! Bienvenue {0} ! :luggage:"]
def readConfig():
    config = {}
    con = create_con()
    try:
        with con.cursor() as c:
            c.execute("SELECT * FROM EpiCom.config;")
            res = c.fetchall()
        for x in res:
            config[str(x[0])] = {"welcome" : x[1], "adm" : x[2], "prefix" : x[3], "contacts" : x[4]}
    except:
        raise ValueError("Unable to read config!")
    finally:
        con.close()
    return (config)
config = readConfig()

def make_embed(title="", description="", nb_field=0, fields={}, inline=False, color=3):
    colors = [0xbd0f0f, 0x3700ff, 0x0ab007, 0x640066] # Red / Info / Green / others
    embed=discord.Embed(description=description,color=colors[color])
    if (nb_field):
        for x in fields:
            embed.add_field(name=x, value=fields[x], inline=inline)
    embed.set_footer(text="Dewey bot, by Maxime D.", icon_url="https://cdn.discordapp.com/icons/691661291785551873/f5fd1028da30dc55eb06ea77f6dbf222.png?size=128")
    if (color == 0):
        url = "https://i.ibb.co/tM7pYZr/error.png"
    elif (color == 1):
        url = "https://i.ibb.co/sqfPRNC/info.png"
    elif (color == 2):
        url = "https://i.ibb.co/qDQ8dwM/success.png"
    else:
        url = ""
    embed.set_author(name=title, icon_url=url)
    return embed

async def SecurityCheck(message, staff=True):
    print("{0} ({1}) used {2} command !".format(message.author, message.author.id, message.content.split(" ")[0][1:]))
    if (staff):
        if (message.author.id == 277461601643134976 or config[str(message.guild.id)]["adm"] in [z.name.lower() for z in message.author.roles]):
            return (True)
        else:
            msg = { "An error occured :" : "You don't have permission to do that !"}
            await message.channel.send(embed=make_embed(title="Something went wrong !", nb_field=len(msg), fields=msg, inline=False, color=0))
            return (False)
    else:
        if (message.author.id == 277461601643134976):
            return (True)
        else:
            msg = { "An error occured :" : "You don't have permission to do that !"}
            await message.channel.send(embed=make_embed(title="Something went wrong !", nb_field=len(msg), fields=msg, inline=False, color=0))
            return (False)

@client.event
async def on_ready():
    print("Logged as {0.user}".format(client))
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Malcolm"))

@client.event
async def on_member_join(member):
    d = datetime.datetime.today()
    dstr = "{:02d}".format(d.month) + "-" + str(d.year)
    channel = client.get_channel(config[str(member.guild.id)]["welcome"])
    await channel.send(random.choice(welcome_text).format(member.mention))
    try:
        con = create_con()
        with con.cursor() as c:
            c.execute("SELECT uid FROM EpiCom.members WHERE (uid = %s);", member.id)
            if (c.fetchone() == None):
                print(f"Collecting data for : {member} ({member.id})")
                subprocess.Popen(["python3", "collector.py", str(member.id), str(member.guild.id)], shell=False)
            c.execute("SELECT nb_join FROM EpiCom.stats WHERE (month = % AND guild = %s);", (dstr, member.guild.id))
            res = c.fetchone()
            if (res == None):
                c.execute("INSERT INTO EpiCom.stats (month, nb_join, guild) VALUES (%s, %s, %s);", (dstr, 1, member.guild.id))
                con.commit()
            else:
                c.execute("UPDATE EpiCom.stats SET nb_join = %s WHERE (month = %s AND guild = %s);", (res[0] + 1, dstr, member.guild.id))
                con.commit()
            c.execute("DELETE FROM EpiCom.members WHERE (insert_date < %s )", (str(datetime.datetime.now().year-1) + "-" + str(datetime.datetime.now().month) + "-" + str(datetime.datetime.now().day)))
            con.commit()
    except:
        pass
    finally:
        con.close()

@client.command(name='export')
@commands.guild_only()
async def _export(ctx, role: str, coma=","):
    if (await SecurityCheck(ctx.message, True)):
        i = 0
        name = "export_" + role + "_" + str(datetime.datetime.today().month)
        with open(name + ".csv", "w") as f:
            workbook = xlsxwriter.Workbook(name + ".xlsx")
            worksheet = workbook.add_worksheet()
            con = create_con()
            try:
                array = ["Numéro", "Identifiant", "Nom d'affichage", "UID", "Etudes", "Comment"]
                for x in range(0, len(array)):
                    worksheet.write(i, x, array[x])
                f.write("n°" + coma + "Identifiant" + coma + "Nom d'affichage" + coma + "UID" + coma + "Etudes" + coma + "Comment\r\n")
                with con.cursor() as c:
                    async for x in ctx.message.guild.fetch_members(limit=None):
                        if (role.lower() in [y.name.lower() for y in x.roles]):
                            c.execute("SELECT studies,comment FROM EpiCom.members WHERE (uid = %s);", (str(x.id)))
                            res = c.fetchone()
                            i += 1
                            if (res == None):
                                f.write(str(i) + coma + str(x) + coma + str(x.display_name)+ coma + str(x.id) + "\r\n" )
                                array = [i, str(x), str(x.display_name), str(x.id)]
                                for z in range(0, len(array)):
                                    worksheet.write(i, z, array[z])
                            else:
                                f.write(str(i) + coma + str(x) + coma + str(x.display_name)+ coma + str(x.id) + coma + str(res[0]) + coma + str(res[1]) + "\r\n" )
                                array = [i, str(x), str(x.display_name), str(x.id), str(res[0]), str(res[1])]
                                for z in range(0, len(array)):
                                    worksheet.write(i, z, array[z])
                    workbook.close()
            except:
                pass
            finally:
                con.close()
        await ctx.message.author.send("Voici ton export en csv 🙂 :", file=discord.File(name + ".csv"))
        await ctx.message.author.send("Et en version xlsx 🙂 :", file=discord.File(name + ".xlsx"))
        os.remove(name + ".csv")
        os.remove(name + ".xlsx")

@client.command(name='switchall')
@commands.guild_only()
async def _switchAll(ctx, old_Role: discord.Role, new_Role: discord.Role, keep="false"):
    x = 0
    if (await SecurityCheck(ctx.message, True)):
        async for member in ctx.message.guild.fetch_members(limit=None):
            if (old_Role.name.lower() in [y.name.lower() for y in member.roles]):
                x += 1
                await member.add_roles(new_Role)
                if (keep == "false"):
                    await member.remove_roles(old_Role)
        if (keep == "false"):
            msg = { "Your request has been processed :" : "All '" + old_Role.name + "' members were moved to '" + new_Role.name + "' role !\n" + str(x) + " members were moved."}
        else:
            msg = { "Your request has been processed :" : "All '" + old_Role.name + "' members were granted '" + new_Role.name + "' role !\n" + str(x) + " members got this new role."}
        await ctx.message.channel.send(embed=make_embed(title="Success !", nb_field=len(msg), fields=msg, inline=False, color=2))

@client.command(name='collect')
@commands.guild_only()
async def _collect(ctx, id: int):
    if (await SecurityCheck(ctx.message, True)):
        target = ctx.message.guild.get_member(id)
        if (target == None):
            msg = { "An error occured :" : "Unable to find this member !"}
            await ctx.message.channel.send(embed=make_embed(title="Something went wrong !", nb_field=len(msg), fields=msg, inline=False, color=0))
        else:
            msg = { "Your demand is processing ..." : f"Start collecting data of {target.display_name}."}
            await ctx.message.channel.send(embed=make_embed(title="Success !", nb_field=len(msg), fields=msg, inline=False, color=2))
            subprocess.Popen(["python3", "collector.py", str(target.id), str(ctx.message.guild.id)], shell=False)

@client.command(name='collectors')
async def _collectors(ctx):
    if (await SecurityCheck(ctx.message, False)):
        con = create_con()
        try:
            with con.cursor() as c:
                c.execute("SELECT step,uid,insert_date,comment,pid_collector FROM EpiCom.members WHERE step != 2;")
                res = c.fetchall()
            msg = "{:^20}{:^20}{:^40}{:^25}{:^6}\n".format("Status","UID","Date","Comment", "PID")
            for x in res:
                msg += "{:^20}{:^20}{:^40}{:^25}{:^6}\n".format(str(x[0]), str(x[1]), str(x[2]), str(x[3]), str(x[4]))
            await ctx.message.channel.send("```" + msg + "```")
        except:
            msg = { "An error occured :" : "Unable to get list of collectors in database !"}
            await ctx.message.channel.send(embed=make_embed(title="Something went wrong !", nb_field=len(msg), fields=msg, inline=False, color=0))
        finally:
            con.close()

@client.command(name="kill")
async def _kill(ctx, pid : int):
    if (await SecurityCheck(ctx.message, False)):
        con = create_con()
        try:
            with con.cursor() as c:
                c.execute("SELECT pid_collector FROM EpiCom.members WHERE (pid_collector = %s);", (pid))
                if (c.fetchone() != None):
                    os.kill(self.proc.pid, signal.SIGINT)
                    c.execute("UPDATE EpiCom.members SET pid_collector WHERE (pid_collector = %s);", (pid))
                    con.commit()
                else:
                    raise Exception("Lol")
            msg = { "Your demand has been processed !" : f"Collector pid {str(pid)} was terminated."}
            await ctx.message.channel.send(embed=make_embed(title="Success !", nb_field=len(msg), fields=msg, inline=False, color=2))
        except:
            msg = { "An error occured :" : "Unable to terminate this !"}
            await ctx.message.channel.send(embed=make_embed(title="Something went wrong !", nb_field=len(msg), fields=msg, inline=False, color=0))
        finally:
            con.close()

@client.command(name="info")
@commands.guild_only()
async def _info(ctx, member):
    if (await SecurityCheck(ctx.message, True)):
        if (member.isnumeric()):
            member = ctx.message.guild.get_member(int(member))
            print(member)
        con = create_con()
        try:
            with con.cursor() as c:
                c.execute("SELECT fullname,studies,comment,insert_date FROM EpiCom.members WHERE (uid = %s);", (str(member.id)))
                res = c.fetchone()
            if (res == None):
                raise ValueError("Lol")
            embed = discord.Embed(colour=discord.Colour(0x3700ff))
            embed.set_thumbnail(url=f"{member.avatar_url}")
            embed.set_author(name="Informations about :", icon_url="https://i.ibb.co/sqfPRNC/info.png")
            embed.set_footer(text="Dewey bot, by Maxime D.", icon_url="https://cdn.discordapp.com/icons/691661291785551873/f5fd1028da30dc55eb06ea77f6dbf222.png?size=128")
            embed.add_field(name= (f"{member.name}#{member.discriminator}"), value=f"UID - {member.id}\nName - {res[0]}\nStudies - {res[1]}\nComment - {res[2]}\nDate join - {res[3]}\n")
            await ctx.message.author.send(embed=embed)
        except:
            msg = { "An error occured :" : "This user does not exists in our records !"}
            await ctx.message.author.send(embed=make_embed(title="Something went wrong !", nb_field=len(msg), fields=msg, inline=False, color=0))
        finally:
            con.close()

@client.command(name="send")
@commands.guild_only()
async def _send(ctx, role : str, message : str):
    sended = 0
    if (await SecurityCheck(ctx.message, True)):
        async for x in ctx.message.guild.fetch_members(limit=None):
            if (role.lower() in [y.name.lower() for y in x.roles]):
                try:
                    await x.send(config[str(ctx.message.guild.id)]["prefix"].format(x.mention) + "\n" + message)
                    sended += 1
                except:
                    pass
        msg = { "Your demand has been processed !" : f"Your message has been sent to {str(sended)} members !"}
        await ctx.message.channel.send(embed=make_embed(title="Success !", nb_field=len(msg), fields=msg, inline=False, color=2))

@client.command(name="register")
async def _registerGuild(ctx, guild_id : int, welcome_id: int, adm_role: str, prefix_dm: str, contacts: str):
    if (await SecurityCheck(ctx.message, False)):
        global config
        con = create_con()
        try:
            with con.cursor() as c:
                c.execute("INSERT INTO EpiCom.config (guild_id, welcome_id, adm_role, prefix_dm, contacts) VALUES (%s, %s, %s, %s, %s);", (guild_id, welcome_id, adm_role, prefix_dm, contacts))
            con.commit()
            msg = { "Your demand has been processed !" : f"New guild is registered {str(guild_id)} !"}
            config = ReadConfig()
            await ctx.message.channel.send(embed=make_embed(title="Success !", nb_field=len(msg), fields=msg, inline=False, color=2))
        except:
            msg = { "An error occured :" : "Unable to register this !"}
            await ctx.message.channel.send(embed=make_embed(title="Something went wrong !", nb_field=len(msg), fields=msg, inline=False, color=0))
    else:
        msg = { "An error occured :" : "You don't have permission to do that !"}
        await ctx.message.channel.send(embed=make_embed(title="Something went wrong !", nb_field=len(msg), fields=msg, inline=False, color=0))

@client.command(name="setwelcome")
@commands.guild_only()
async def _setWelcome(ctx, channel : int):
    if (await SecurityCheck(ctx.message, True)):
        config[ctx.message.guild.id]["welcome"] = channel
        con = create_con()
        try:
            with con.cursor() as c:
                c.execute("UPDATE EpiCom.config SET welcome_id = %s WHERE (guild_id = %s);", (channel, ctx.message.guild.id))
            con.commit()
        finally:
            con.close()
        msg = { "Your demand has been processed !" : f"Welcome messages will now be sent to {str(client.get_channel(channel))} !"}
        await ctx.message.channel.send(embed=make_embed(title="Success !", nb_field=len(msg), fields=msg, inline=False, color=2))

@client.command(name="stat")
@commands.guild_only()
async def _stat(ctx, month: str):
    if (await SecurityCheck(ctx.message, True)):
        con = create_con()
        try:
            with con.cursor() as c:
                c.execute("SELECT nb_join FROM EpiCom.stats WHERE (month = %s AND guild = %s);", (month, ctx.message.guild.id))
                res = c.fetchone()
            if (res):
                msg = { "Nice !" : f"{str(res[0])} users joined this discord at {str(month)} !"}
                await ctx.message.author.send(embed=make_embed(title="Success !", nb_field=len(msg), fields=msg, inline=False, color=2))
            else:
                msg = { "It's really sad :" : "Nobody joined this discord this month !"}
                await ctx.message.channel.send(embed=make_embed(title="Something went wrong !", nb_field=len(msg), fields=msg, inline=False, color=0))
        finally:
            con.close()
    else:
        msg = { "An error occured :" : "You don't have permission to do that !"}
        await ctx.message.channel.send(embed=make_embed(title="Something went wrong !", nb_field=len(msg), fields=msg, inline=False, color=0))

@client.command(name="helpop")
async def _helpOp(ctx):
    if (await SecurityCheck(ctx.message, False)):
        cmds = {
            "Collectors commands :" :  
                                        ">help : Display this help\n"+
                                        ">collectors : Show all collectors\n"+
                                        ">kill <cId> : Kill process id cId\n",
            "Server management :" :
                                        ">register <guildId> <welcomeId> <admRole> <prefixDm> <contacts> : Register new discord\n"
          }#🚧
        await ctx.message.author.send(embed=make_embed(title="Here list of commands :", nb_field=len(cmds), fields=cmds, inline=False))
    else:
        msg = { "An error occured :" : "You don't have permission to do that !"}
        await ctx.message.channel.send(embed=make_embed(title="Something went wrong !", nb_field=len(msg), fields=msg, inline=False, color=0))
   
@client.command(name="help")
@commands.guild_only()
async def _help(ctx):
    if (await SecurityCheck(ctx.message, True)):
        cmds = {
            "General commands :" :  
                                        ">help : Display this help\n"+
                                        ">export <role> : Export users of specific role\n"+
                                        ">send <role> <message> : Send a message to all users in this role\n"+
                                        ">stat <month> : Number of new users at month (format : MM-YYYY)\n",
            "User management :" :
                                        ">info <@member|memberID> : Show informations about specified member\n"+
                                        ">collect <userId> : Collect informations about user Id (Won't do anything if already collected)\n"+
                                        ">switchall <@role1> <@role2> : Switch all users from role1 to role2\n",
            "Server management :" :
                                        ">setwelcome <channelId> : Set welcome annoucements to specific channel id\n"
          }#🚧
        await ctx.message.author.send(embed=make_embed(title="Here list of commands :", nb_field=len(cmds), fields=cmds, inline=False))
    else:
        msg = { "An error occured :" : "You don't have permission to do that !"}
        await ctx.message.channel.send(embed=make_embed(title="Something went wrong !", nb_field=len(msg), fields=msg, inline=False, color=0))

def read_token():
    with open("token.txt", "r") as f:
        return (f.readlines()[0].strip())
client.run(read_token())
