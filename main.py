@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot:
        return

    bot_mentioned = bot.user in message.mentions
    has_bad_word = matches_bad_word(message.content)

    # Get bot's member object in the guild
    bot_member = message.guild.get_member(bot.user.id) if message.guild else None

    # Function to check if author has higher top role than bot
    def author_higher_role():
        if not bot_member or not message.guild:
            return False
        author_roles = message.author.roles
        bot_roles = bot_member.roles
        # Roles are sorted from lowest to highest, so compare top roles:
        return author_roles[-1].position > bot_roles[-1].position

    if bot_mentioned or has_bad_word:
        try:
            if author_higher_role():
                # If author has higher role
                if bot_mentioned:
                    await message.channel.send(f"{message.author.mention} bruh")
                else:
                    await message.channel.send(f"{message.author.mention} alright bud")
            else:
                # Author has equal or lower role, do timeout + messages
                until = discord.utils.utcnow() + timedelta(seconds=60)
                await message.author.timeout(until, reason="Used forbidden words or mentioned the bot")

                if bot_mentioned:
                    await message.channel.send(f"{message.author.mention} shut up")
                else:
                    await message.channel.send(f"{message.author.mention} nuh uh")

            await message.delete()
        except Exception as e:
            print(f"Failed to timeout or respond to {message.author}: {e}")
        return

    # Process commands normally
    await bot.process_commands(message)
