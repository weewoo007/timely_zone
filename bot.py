#Set up
import discord
from discord.ext import commands,tasks
from datetime import datetime,timedelta
import re
import os

#Initialise
intents=discord.Intents.default()
intents.members=True
intents.message_content=True
bot=commands.Bot(command_prefix="\\",intents=intents)

#UTC time zones
neg_tz=[
    "UTC-12:00","UTC-11:00","UTC-10:00","UTC-09:30","UTC-09:00","UTC-08:00","UTC-07:00",
    "UTC-06:00","UTC-05:00","UTC-04:00","UTC-03:30","UTC-03:00","UTC-02:00","UTC-01:00",
]
pos_tz=[
    "UTC+00:00","UTC+01:00","UTC+02:00","UTC+03:00", "UTC+03:30","UTC+04:00","UTC+04:30",
    "UTC+05:00","UTC+05:30","UTC+05:45","UTC+06:00","UTC+06:30","UTC+07:00","UTC+08:00",
    "UTC+09:00","UTC+09:30","UTC+10:00","UTC+10:30","UTC+11:00","UTC+12:00","UTC+12:45","UTC+13:00","UTC+14:00"
]
def set_offset(offset:str):
  if not offset.startswith("UTC"):
    return None
  sign=1 if offset[3]=="+" else -1
  time_part=offset[4:]
  hours,*minutes=time_part.split(":")
  minutes=int(minutes[0]) if minutes else 0
  return timedelta(hours=sign*int(hours),minutes=sign*minutes)

class UTCSelect(discord.ui.Select):
  def __init__(self,options_list):
    options=[
        discord.SelectOption(label=o,value=o)
        for o in options_list
    ]
    super().__init__(placeholder="Select Time Zone",options=options)
  async def callback(self,interaction:discord.Interaction):
    offset=self.values[0]
    delta=set_offset(offset)
    member=interaction.user
    guild=interaction.guild
    for role in member.roles:
      if role.name.startswith("UTC"):
        await member.remove_roles(role)
    now=datetime.utcnow()+delta
    role_name=f"{now.strftime('%H:%M')}"
    role=discord.utils.get(guild.roles,name=role_name)
    if role is None:
      role=await guild.create_role(name=role_name)
    await member.add_roles(role)
    await interaction.response.send_message(f"Mango can now remind you that it's **{role_name}**",ephemeral=True)

#Botification
class UTCView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(UTCSelect(neg_tz))
        self.add_item(UTCSelect(pos_tz))

@bot.tree.command(name="timezone", description="Set le Time")
async def timezone(interaction:discord.Interaction):
  if interaction.guild is None:
    await interaction.response.send_message("Stick to the server, sweetheart.",ephemeral=True)
    return
  await interaction.response.send_message("Select your UTC offset:",view=UTCView(),ephemeral=True)
@tasks.loop(minutes=1)
async def update_role():
  for guild in bot.guilds:
    for role in guild.roles:
      if not role.name.startswith("UTC"):
        continue
      match=re.match("(UTC[+-][0-9][0-9]:[0-9][0-9]|UTC[+-][0-9]:[0-9][0-9]|UTC[+-][0-9][0-9]|UTC[+-][0-9])",role.name)
      if not match:
        continue
      offset=match.group(1)
      delta=set_offset(offset)
      if not delta:
        continue
      now=datetime.utcnow()+delta
      new_name=f"{offset}|{now.strftime('%H:%M')}"
      if role.name!=new_name:
        try:
          await role.edit(name=new_name)
        except discord.Forbidden:
          pass
@bot.event
async def on_ready():
  await bot.tree.sync()
  update_role.start()
  print(f"Logged in as {bot.user}")

bot.run(os.environ["Token"])
#deploy dammit.
