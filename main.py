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
WEBHOOK_URL = os.environ.get('webhook')

# === Bot setup ===
intents = discord.Intents.default()
intents.message_content = True  # Needed to read messages
intents.members = True          # Needed to timeout members
bot = commands.Bot(command_prefix="!", intents=intents)

# === Regex-based bad word patterns ===
BAD_WORD_PATTERNS = [
    r"\bfuck\w*\b", r"\bshit\w*\b", r"\bnigg[ae]rs?\b", r"\bfag+g*o*t*s?\b",
    r"\bbitch(es)?\b", r"\bcunt(s)?\b", r"\bpuss(y|ies)\b", r"\bass(es)?\b",
    r"\bdick(s)?\b", r"\bboob(s|ies)?\b", r"\bcock(s)?\b", r"\btit(s|ties)?\b",
    r"\bpiss(es|ing)?\b", r"\bsluts?\b", r"\bwhore(s|ing)?\b", r"\bjerk(s|ing)?\b",
    r"\bjob\b", r"\bemployment\b", r"\nniglet(s)?\b", r"\btrann(y|ies)\b",
]

# === Burrito phrases ===
BURRITO_PHRASES = [
    "im eating 46 burritos rn", "hey", "you probably arent even a burrito bison GOD",
    "on discord, what", "spongebob tackles a 3 foot jelly bean at 3 am central time",
    "i am a burrito bison", "i am a burrito bison GOD", "bro, your not even a burrito bison",
    "bro, your not even a burrito bison GOD", "go to sleep", "rest your eyes", "shut up",
    "BURRITO_PHRASES", "please do not say burritos suck", "i make my burritos with love",
    "my burritos are two times better than javier's", "burrito bison launche libre",
    "burrito bison but not launche libre"
]

# === Helper to match bad words ===
def matches_bad_word(text):
    for pattern in BAD_WORD_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

# === Send to Webhook ===
def send_log(content):
    if not WEBHOOK_URL:
        return
    try:
        requests.post(WEBHOOK_URL, json={"content": content})
    except Exception as e:
        print(f"Failed to send log: {e}")

# === Bot is ready ===
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🌐 Synced {len(synced)} global commands.")
    except Exception as e:
        print(f"❌ Sync error: {e}")

# === Message listener ===
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

                log_text = f"🚫 {message.author} was timed out for 60s for saying: `{message.content}`"
                send_log(log_text)

                if bot_mentioned:
                    await message.channel.send(f"{message.author.mention} shut up")
                else:
                    await message.channel.send(f"{message.author.mention} nuh uh")

                await message.delete()
        except Exception as e:
            print(f"Failed to timeout or respond to {message.author}: {e}")
        return

    await bot.process_commands(message)

# === Slash Commands ===
@bot.tree.command(name="test", description="Test if the bot is working")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message("what do you want bro")

@bot.tree.command(name="burrito", description="Get a random burrito phrase")
async def burrito(interaction: discord.Interaction):
    phrase = random.choice(BURRITO_PHRASES)
    await interaction.response.send_message(phrase)

# === Flask for Replit uptime ===
app = Flask('')

@app.route('/')
def home():
    return "✅ Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

# === Start bot ===
bot.run(DISCORD_TOKEN)
