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
PUBLIC_WEBHOOK_URL = os.environ.get('webhook')           # For public messages
PRIVATE_WEBHOOK_URL = os.environ.get('private_webhook')  # For mod logs (private)

# === Bot setup ===
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

# === Master bad word list with variants ===
CUSS = [
    # N-word
    "nigga", "nigger", "nigg", "niga", "ngga", "nga", "niggah", "niguh", "nigguh",
    "niggaz", "niggahs", "n1gga", "n1gger", "niqqa", "niqqer", "n1g", "n1gz", "niglet", "n1glet", "nigglet", "nigglette", "n1gglet",

    # F-word 
    "fuck", "fuk", "fuq", "fux", "phuck", "phuk", "phuq", "fukk", "fuc", "fck", "fak", "fock",

    # F-slur
    "fag", "faggot", "fagot", "fagg", "faqqot", "faqq", "f@ggot", "feggit", "fegit", "feggot", "phaggot",

    # B-word
    "bitch", "biatch", "bich", "b1tch", "b1ch", "biotch", "beetch",

    # C-word
    "cunt", "kunt", "qunt", "cnt",

    # P-word
    "pussy", "pussi", "pusy", "pusee", "pusey", "puzzy", "pussee", "puszi",

    # D-word
    "dick", "dik", "d1ck", "d1k", "dyke", "dykes", "dic",

    # Boobs
    "boobs", "boob", "boobies", "bewbs", "b00bs", "b00b", "boobie", "boobz",

    # Cock
    "cock", "c0ck", "cok", "coq", "cawk", "cokc",

    # Tits
    "tits", "t1ts", "tit", "titties", "titty", "titez",

    # Slut
    "slut", "sluts", "slutt", "slutty", "sluttie",

    # W - word
    "whore", "hore", "h0re", "whoar", "whoore", "hoar", "hoer",
    
    # Tranny
    "tranny", "trannie", "trany", "tranney", "tr@nny",

    # Test
    "verybadcusswordtest"
]

# === Safe category mapping for public display ===
CATEGORY_MAP = {
    # N-word group
    "nigga": "N-word", "nigger": "N-word", "nigg": "N-word", "niga": "N-word", "ngga": "N-word", "nga": "N-word",
    "niggah": "N-word", "niguh": "N-word", "nigguh": "N-word", "niggaz": "N-word", "niggahs": "N-word",
    "n1gga": "N-word", "n1gger": "N-word", "niqqa": "N-word", "niqqer": "N-word", "n1g": "N-word", "n1gz": "N-word",
    "niglet": "N-word", "n1glet": "N-word", "nigglet": "N-word", "nigglette": "N-word", "n1gglet": "N-word",

    # F-word group
    "fuck": "F-word", "fuk": "F-word", "fuq": "F-word", "fux": "F-word", "phuck": "F-word", "phuk": "F-word",
    "phuq": "F-word", "fukk": "F-word", "fuc": "F-word", "fck": "F-word", "fak": "F-word", "fock": "F-word",

    # F-slur
    "fag": "F-slur", "faggot": "F-slur", "fagot": "F-slur", "fagg": "F-slur", "faqqot": "F-slur", "faqq": "F-slur",
    "f@ggot": "F-slur", "feggit": "F-slur", "fegit": "F-slur", "feggot": "F-slur", "phaggot": "F-slur",

    # B-word group
    "bitch": "B-word", "biatch": "B-word", "bich": "B-word", "b1tch": "B-word", "b1ch": "B-word", "biotch": "B-word",
    "beetch": "B-word",

    # C-word group
    "cunt": "C-word", "kunt": "C-word", "qunt": "C-word", "cnt": "C-word",

    # P-word group
    "pussy": "P-word", "pussi": "P-word", "pusy": "P-word", "pusee": "P-word", "pusey": "P-word", "puzzy": "P-word",
    "pussee": "P-word", "puszi": "P-word",

    # D-word group
    "dick": "D-word", "dik": "D-word", "d1ck": "D-word", "d1k": "D-word", "dyke": "D-word", "dykes": "D-word", "dic": "D-word",

    # PP C-word
    "cock": "PP C-word", "c0ck": "PP C-word", "cok": "PP C-word", "coq": "PP C-word", "cawk": "PP C-word", "cokc": "PP C-word",

    # Tits
    "tits": "T - word", "t1ts": "Tits", "tit": "Tits", "titties": "Tits", "titty": "Tits", "titez": "Tits",

    # Slut
    "slut": "Sl-word", "sluts": "Sl-word", "slutt": "Sl-word", "slutty": "Sl-word", "sluttie": "Sl-word",

    # W-word
    "whore": "W-word", "hore": "W-word", "h0re": "W-word", "whoar": "W-word", "whoore": "W-word",

    # T-slur
    "tranny": "T-slur", "trannie": "T-slur", "trany": "T-slur", "tranney": "T-slur", "tr@nny": "T-slur",

    # Test
    "verybadcusswordtest": "Test Cuss Word"
}

# === Fuzzify to allow bypass-proof matching ===
def fuzzify(word):
    replacements = {
        'a': '[a4@]+',
        'e': '[e3]+',
        'i': '[i1!l|]+',
        'o': '[o0]+',
        'u': '[uµv]+',
        'y': '[y]+',
        'b': '[b8]+',
        'c': '[c\\(\\[]+',
        'g': '[g69q]+',
        'k': '[kq]+',
        'l': '[l1!i|]+',
        's': '[s5$z]+',
        't': '[t7]+',
        'z': '[z2]+',
        'q': '[q9g]+',
        'f': '[fph]+',
        'p': '[p]+',
        'd': '[d]+',
        'h': '[h]+',
        'r': '[r]+',
        'n': '[n]+',
        'm': '[m]+',
        'w': '[wvv]+'
    }
    sep = r'[\W_]*'
    pattern = []
    for char in word:
        if char.lower() in replacements:
            pattern.append(replacements[char.lower()])
        else:
            pattern.append(re.escape(char))
    return sep.join(pattern)

# === Generate bypass-proof regex patterns with base/category ===
BAD_WORD_PATTERNS = []
for base_word in CUSS:
    pattern = re.compile(fuzzify(base_word), re.IGNORECASE)
    category = CATEGORY_MAP.get(base_word, "Offensive word")
    BAD_WORD_PATTERNS.append((pattern, base_word, category))

# === Burrito phrases ===
BURRITO_PHRASES = [
    "im eating 46 burritos rn", "you probably arent even a burrito bison PRO",
    "spongebob tackles a 3 foot jelly bean at 3 am central time",
    "bro, your not even a burrito bison", "rest your eyes",
    "BURRITO_PHRASES", "my burritos are two times better than javier's", "what do you is whant", "your not friendly 😡"
]

# === Send to public webhook ===
def send_public_log(content):
    if PUBLIC_WEBHOOK_URL:
        try:
            requests.post(PUBLIC_WEBHOOK_URL, json={"content": content})
        except Exception as e:
            print(f"Public webhook error: {e}")

# === Send to private webhook ===
def send_private_log(content):
    if PRIVATE_WEBHOOK_URL:
        try:
            requests.post(PRIVATE_WEBHOOK_URL, json={"content": content})
        except Exception as e:
            print(f"Private webhook error: {e}")

# === Helper to match bad words ===
def matches_bad_word(text):
    for pattern, base_word, category in BAD_WORD_PATTERNS:
        match = pattern.search(text)
        if match:
            return base_word, category, match.group(0)  # base word, category, actual typed
    return None, None, None

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
    bad_word_base, bad_word_category, bad_word_typed = matches_bad_word(message.content)
    has_bad_word = bad_word_base is not None
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

                # Delete offending message
                await message.delete()

                # Send public webhook message (safe category)
                if has_bad_word:
                    send_public_log(
                        f"{message.author.mention} was timed out for 60 seconds for saying the **{bad_word_category}** lol"
                    )
                    await message.channel.send(f"{message.author.mention} nuh uh")
                else:
                    send_public_log(
                        f"{message.author.mention} was timed out for 60 seconds for mentioning the bot lol"
                    )
                    await message.channel.send(f"{message.author.mention} shut up")

                # Send private mod log (exact word, base, category)
                if has_bad_word:
                    send_private_log(
                        f"{message.author} ({message.author.display_name}) was timed out for 60 seconds "
                        f'for saying "{bad_word_typed}" (matched base word: {bad_word_base}, category: {bad_word_category})'
                    )
                else:
                    send_private_log(
                        f"{message.author} ({message.author.display_name}) was timed out for 60 seconds for mentioning the bot"
                    )
        except Exception as e:
            print(f"Timeout error: {e}")
        return

    await bot.process_commands(message)


# === Ban logging ===
@bot.event
async def on_member_ban(guild, user):
    send_private_log(f"{user} was banned from {guild.name} lol")

# === Kick logging ===
@bot.event
async def on_member_remove(member):
    audit_logs = await member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick).flatten()
    if audit_logs:
        entry = audit_logs[0]
        if entry.target.id == member.id:
            reason = entry.reason or "for no reason lol"
            send_private_log(f"{member} was kicked from {member.guild.name} for \"{reason}\" lol")

# === Slash commands ===
@bot.tree.command(name="test", description="Test if the bot is working")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message("what do you want bro")

@bot.tree.command(name="burrito", description="Get a random burrito phrase")
async def burrito(interaction: discord.Interaction):
    phrase = random.choice(BURRITO_PHRASES)
    await interaction.response.send_message(phrase)

# === Flask keep-alive ===
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

# === Start bot ===
bot.run(DISCORD_TOKEN)
