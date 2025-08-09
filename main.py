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
    mention_responses = ["shut up", "stop", "please don't @ me"]
    swear_responses = ["no", "nuh uh", "shut up", "not cool"]

    if bot_mentioned or has_bad_word:
        try:
            if author_higher_role():
                # Higher rank: casual dismiss
                response = random.choice(higher_rank_responses)
                await message.channel.send(f"{message.author.mention} {response}")
            else:
                # Lower rank or equal: timeout + delete + firm reply
                until = discord.utils.utcnow() + timedelta(seconds=60)
                await message.author.timeout(until, reason="Used forbidden words or mentioned the bot")
                await message.delete()

                if bot_mentioned and not has_bad_word:
                    # Mention only
                    response = random.choice(mention_responses)
                    await message.channel.send(f"{message.author.mention} {response}")
                    send_public_log(
                        f"{message.author.mention} was timed out for 60 seconds for mentioning the bot lol"
                    )
                    send_private_log(
                        f"{message.author} ({message.author.display_name}) was timed out for 60 seconds for mentioning the bot"
                    )
                elif has_bad_word:
                    # Swear word
                    response = random.choice(swear_responses)
                    await message.channel.send(f"{message.author.mention} {response}")
                    send_public_log(
                        f"{message.author.mention} was timed out for 60 seconds for saying the **{bad_word_category}** lol"
                    )
                    send_private_log(
                        f"{message.author} ({message.author.display_name}) was timed out for 60 seconds "
                        f'for saying "{bad_word_typed}" (matched base word: {bad_word_base}, category: {bad_word_category})'
                    )
        except Exception as e:
            print(f"Timeout error: {e}")
        return

    await bot.process_commands(message)
