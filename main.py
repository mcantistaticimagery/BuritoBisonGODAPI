import os
import re
import discord
import requests
from discord.ext import commands
from discord import app_commands
from flask import Flask
from threading import Thread
import random
from datetime import timedelta

print("discord.py version:", discord.__version__)

# === Setup environment ===
DISCORD_TOKEN = os.environ['discord']
WEBHOOK_URL = os.environ.get('webhook')  # Set your webhook URL in your environment

# === Bot setup ===
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

# === Bad word patterns ===
BAD_WORD_PATTERNS = [
    r"\bfuck\w*\b", r"\bshit\w*\b", r"\bnigg[ae]rs?\b", r"\bfag+g*o*t*s?\b",
    r"\bbitch(es)?\b", r"\bcunt(s)?\b", r"\bpuss(y|ies)\b", r"\bass(es)?\b",
    r"\bdick(s)?\b", r"\bboob(s|ies)?\b", r"\bcock(s)?\b", r"\btit(s|ties)?\b",
    r"\bpiss(es|ing)?\b", r"\bsluts?\b", r"\bwhore(s|ing)?\b",
    r"\bjob\b", r"\bemployment\b", r"\nniglet(s)?\b", r"\btrann(y|ies)\b", r"\bshit(ter)?\b",
]

# === Burrito phrases ===
BURRITO_PHRASES = [
    "im eating 46 burritos rn", "you probably arent even a burrito bison PRO",
    "spongebob tackles a 3 foot jelly bean at 3 am central time",
    "bro, your not even a burrito bison", "rest your eyes",
    "BURRITO_PHRASES", "my burritos are two times better than javier's"
]

# === Helper to match bad words ===
def matches_bad_word(text):
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in BAD_WORD_PATTERNS)

# === Send to Webhook ===
def send_log(content):
    if WEBHOOK_URL:
        try:
            requests.post(WEBHOOK_URL, json={"content": content})
        except Exception as e:
            print(f"Webhook error: {e}")

# === Bot ready ===
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} global commands.")
    except Exception as e:
        print(f"Sync error: {e}")

# === Message monitor ===
@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot:
        return

    bot_mentioned = bot.user in message.mentions
    has_bad_word = matches_bad_word(message.content)
    bot_member = message.guild.get_member(bot.user.id) if message.guild else None

    def author_higher_role():
        if not bot_member or not message.guild:
            return False
        return message.author.top_role.position > bot_member.top_role.position

    higher_rank_responses = ["bro", "alright bud", "dude", "are you serious", "bruh"]

    if bot_mentioned or has_bad_word:
        try:
            if author_higher_role():
                response = random.choice(higher_rank_responses)
                await message.channel.send(f"{message.author.mention} {response}")
            else:
                until = discord.utils.utcnow() + timedelta(seconds=60)
                await message.author.timeout(until, reason="Used forbidden words or mentioned the bot")

                await message.channel.send(f"{message.author.mention} shut up" if bot_mentioned else f"{message.author.mention} nuh uh")
                await message.delete()

                send_log(f"{message.author} was timed out for 60 seconds lol")
        except Exception as e:
            print(f"Timeout error: {e}")
        return

    await bot.process_commands(message)

# === Ban logging ===
@bot.event
async def on_member_ban(guild, user):
    send_log(f"{user} was banned from {guild.name} lol")

# === Kick logging ===
@bot.event
async def on_member_remove(member):
    audit_logs = await member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick).flatten()
    if audit_logs:
        entry = audit_logs[0]
        if entry.target.id == member.id:
            reason = entry.reason or "for no reason lol"
            send_log(f"{member} was kicked from {member.guild.name} for \"{reason}\" lol")

# === Slash commands ===
@bot.tree.command(name="test", description="Test if the bot is working")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message("what do you want bro")

@bot.tree.command(name="burrito", description="Get a random burrito phrase")
async def burrito(interaction: discord.Interaction):
    phrase = random.choice(BURRITO_PHRASES)
    await interaction.response.send_message(phrase)

# === Flask keep-alive (Replit/Render) ===
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

# === Start bot ===
bot.run(DISCORD_TOKEN)
