#!/bin/python3
import pymysql
import discord
from discord.ext import commands
import sys as s
import os as o
from minesql import create_con

intents = discord.Intents.default()
intents.members = True
intents.messages = True
client = commands.Bot(command_prefix='>', help_command=None, intents=intents)
if (len(s.argv) != 3):
        print("Please use cmds on discord to launch bot")
        s.exit(1)
current_guild = int(s.argv[2])
current_focus = int(s.argv[1])
step = 0
guild = None
member = None
pid = o.getpid()
text = []

async def close_bot(comment=None):
    con = create_con()
    try:
        with con.cursor() as c:
            c.execute("UPDATE EpiCom.members SET pid_collector=NULL, comment = %s WHERE (uid=%s);", (comment,current_focus))
        con.commit()
    finally:
        con.close()
    if (comment == None):
        print(f"Collecting data of {member} ({member.id}) - done.")
    await client.close()

async def send_a_message(message):
    try:
        await member.send(message)
    except:
        print(f"DM are disabled by : {member} ({member.id})")
        await close_bot("DM are disabled !")

@client.event
async def on_command_error(ctx, error):
    pass

@client.event
async def on_ready():
    global guild, member, step, text
    guild = client.get_guild(current_guild)
    member = guild.get_member(current_focus)
    user = await client.fetch_user(current_focus)
    if (member == None):
        print(f"No member found with corresponding id ! ({current_focus})")
        await client.close()
        return
    print(f"Collecting data for : {member} ({member.id})")
    con = create_con()
    try:
        with con.cursor() as c:
            c.execute("SELECT step FROM EpiCom.members WHERE (uid=%s);", (current_focus))
            res = c.fetchone()
            if (res == None):
                c.execute("INSERT INTO EpiCom.members (uid, pid_collector) VALUES (%s, %s);", (current_focus, pid))
                con.commit()
                step = 0
            else:
                step = res[0]
    finally:
        con.close()
    if (step == 2):
        await close_bot()
        return
    text = [
            f":wave: Salut {member.mention} !\nBienvenue sur le discord d'EPITECH Lille !\nJ'aurai besoin que tu me donnes ton prénom et nom de famille :smiley:",
            ":upside_down: Pourrais-tu nous indiquer, les étude(s)/spécialité(s) et le lycée dans lesquelles tu te situe actuellement ?",
            "Merci pour ces informations. :+1:\n:information_source: Sophie Epitech ou Fabienne Lély va prochainement te contacter !\n:grey_question: N'hésites pas à nous poser des questions dans le salon question du discord !\nNote: Tes informations ne seront divulguées à personnes d'autre que l'administration d'EPITECH Lille, sois-en sûr !\n"
           ]
    await send_a_message(text[step])

@client.event
async def on_message(message):
    global step
    if (message.author == client.user or message.author.id != member.id or message.guild != None):
        return
    if (message.content == "close"):
        await message.author.send("Um you're a member of EPITECH family, okay ...")
        con = create_con()
        try:
            with con.cursor() as c:
                c.execute("DELETE FROM EpiCom.members WHERE (uid=%s);", (current_focus))
            con.commit()
        finally:
            con.close()
        await close_bot()
        return
    if (step == 0):
        con = create_con()
        step = 1
        try:
            with con.cursor() as c:
                c.execute("UPDATE EpiCom.members SET step = %s, fullname = %s WHERE (uid=%s);", (step, message.content, current_focus))
            con.commit()
        finally:
            con.close()
        try:
            await member.edit(nick=message.content)
        except:
            pass
        await message.author.send(text[step])
        return
    if (step == 1):
        con = create_con()
        step = 2
        try:
            with con.cursor() as c:
                c.execute("UPDATE EpiCom.members SET step = %s, studies = %s WHERE (uid=%s);", (step, message.content, current_focus))
            con.commit()
        finally:
            con.close()
        await message.author.send(text[step])
        await close_bot()
        return

def read_token():
    with open("token.txt", "r") as f:
        return (f.readlines()[0].strip())
client.run(read_token())
