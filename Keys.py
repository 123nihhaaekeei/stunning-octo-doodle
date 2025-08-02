import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class ModBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=None, intents=intents)
        self.synced = False
        self.warnings = {}
        self.bad_words = set()
        self.anti_link_enabled = False
        self.anti_spam_enabled = False
        self.anti_spam_delay = 3
        self.spam_repeat_limit = 3
        self.user_last_message_time = {}
        self.user_last_message_content = {}
        self.user_repeat_count = {}
        self.autorole = None

bot = ModBot()

@bot.event
async def on_ready():
    if not bot.synced:
        await bot.tree.sync()
        bot.synced = True
    print(f"Logged in as {bot.user}")

@bot.event
async def on_member_join(member: discord.Member):
    if bot.autorole:
        role = discord.utils.get(member.guild.roles, name=bot.autorole)
        if role:
            await member.add_roles(role)

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if any(word in message.content.lower() for word in bot.bad_words):
        await message.delete()
        await message.channel.send(f"{message.author.mention} Your message contained a banned word.", delete_after=5)
        return

    if bot.anti_link_enabled:
        content = message.content.lower()
        links_to_block = ['http://', 'https://', 'discord.gg', '.gg', 'gg', '/']
        if any(link in content for link in links_to_block):
            await message.delete()
            await message.channel.send(f"{message.author.mention} Posting links is not allowed.", delete_after=5)
            return

    if bot.anti_spam_enabled:
        now = message.created_at.timestamp()
        uid = message.author.id
        last_time = bot.user_last_message_time.get(uid, 0)
        last_content = bot.user_last_message_content.get(uid, "")
        repeat_count = bot.user_repeat_count.get(uid, 0)

        if now - last_time < bot.anti_spam_delay:
            await message.delete()
            await message.channel.send(f"{message.author.mention} You're sending messages too quickly.", delete_after=5)
            return

        if message.content == last_content:
            bot.user_repeat_count[uid] = repeat_count + 1
            if bot.user_repeat_count[uid] >= bot.spam_repeat_limit:
                await message.delete()
                await message.channel.send(f"{message.author.mention} Please stop spamming repeated messages.", delete_after=5)
                return
        else:
            bot.user_repeat_count[uid] = 0

        bot.user_last_message_time[uid] = now
        bot.user_last_message_content[uid] = message.content

def is_admin():
    async def predicate(interaction: discord.Interaction):
        return interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)

@bot.tree.command(name="help", description="Show help menu")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="Help Menu", color=discord.Color.gold())
    embed.add_field(name="/purge <amount>", value="Delete messages (admin)", inline=False)
    embed.add_field(name="/lock", value="Lock the channel (admin)", inline=False)
    embed.add_field(name="/unlock", value="Unlock the channel (admin)", inline=False)
    embed.add_field(name="/kick <user> [reason]", value="Kick a member (admin)", inline=False)
    embed.add_field(name="/ban <user> [reason]", value="Ban a member (admin)", inline=False)
    embed.add_field(name="/unban <user_id>", value="Unban by ID (admin)", inline=False)
    embed.add_field(name="/mute <user>", value="Mute a member (admin)", inline=False)
    embed.add_field(name="/unmute <user>", value="Unmute a member (admin)", inline=False)
    embed.add_field(name="/warn <user> [reason]", value="Warn a member (admin)", inline=False)
    embed.add_field(name="/warnings <user>", value="View warnings", inline=False)
    embed.add_field(name="/clearwarnings <user>", value="Clear warnings (admin)", inline=False)
    embed.add_field(name="/slowmode <seconds>", value="Set slowmode (admin)", inline=False)
    embed.add_field(name="/nickname <user> [nickname]", value="Change/reset nickname (admin)", inline=False)
    embed.add_field(name="/userinfo [user]", value="User info", inline=False)
    embed.add_field(name="/serverinfo", value="Server info", inline=False)
    embed.add_field(name="/censor <word>", value="Add censored word (admin)", inline=False)
    embed.add_field(name="/removecensor <word>", value="Remove censored word (admin)", inline=False)
    embed.add_field(name="/censorlist", value="List censored words (admin)", inline=False)
    embed.add_field(name="/antilink", value="Toggle anti-link filter (admin)", inline=False)
    embed.add_field(name="/antispam", value="Toggle anti-spam filter (admin)", inline=False)
    embed.add_field(name="/setantispamdelay <seconds>", value="Set anti-spam delay (admin)", inline=False)
    embed.add_field(name="/setspamrepeatlimit <count>", value="Set spam repeat limit (admin)", inline=False)
    embed.add_field(name="/purge <amount>", value="Delete messages (admin)", inline=False)
    embed.add_field(name="/lock", value="Lock the channel (admin)", inline=False)
    embed.add_field(name="/unlock", value="Unlock the channel (admin)", inline=False)
    embed.add_field(name="/roleall <role>", value="Give everyone a role (admin)", inline=False)
    embed.add_field(name="/setautorole <role>", value="Set autorole for new members (admin)", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="antilink", description="Toggle anti-link filter")
@is_admin()
async def antilink(interaction: discord.Interaction):
    bot.anti_link_enabled = not bot.anti_link_enabled
    await interaction.response.send_message(f"Anti-link filter set to {bot.anti_link_enabled}", ephemeral=True)

@bot.tree.command(name="antispam", description="Toggle anti-spam filter")
@is_admin()
async def antispam(interaction: discord.Interaction):
    bot.anti_spam_enabled = not bot.anti_spam_enabled
    await interaction.response.send_message(f"Anti-spam filter set to {bot.anti_spam_enabled}", ephemeral=True)

@bot.tree.command(name="censor", description="Add censored word")
@is_admin()
@app_commands.describe(word="Word to censor")
async def censor(interaction: discord.Interaction, word: str):
    word = word.lower().strip()
    if word in bot.bad_words:
        await interaction.response.send_message(f"{word} is already censored.", ephemeral=True)
        return
    bot.bad_words.add(word)
    await interaction.response.send_message(f"Added {word} to censored words.", ephemeral=True)

@bot.tree.command(name="removecensor", description="Remove censored word")
@is_admin()
@app_commands.describe(word="Word to remove from censor list")
async def removecensor(interaction: discord.Interaction, word: str):
    word = word.lower().strip()
    if word not in bot.bad_words:
        await interaction.response.send_message(f"{word} is not in censored words.", ephemeral=True)
        return
    bot.bad_words.remove(word)
    await interaction.response.send_message(f"Removed {word} from censored words.", ephemeral=True)

@bot.tree.command(name="censorlist", description="List censored words")
@is_admin()
async def censorlist(interaction: discord.Interaction):
    if not bot.bad_words:
        await interaction.response.send_message("No censored words set.", ephemeral=True)
        return
    await interaction.response.send_message("Censored words:\n" + ", ".join(sorted(bot.bad_words)), ephemeral=True)

@bot.tree.command(name="setantispamdelay", description="Set anti-spam delay in seconds")
@is_admin()
@app_commands.describe(seconds="Delay in seconds")
async def setantispamdelay(interaction: discord.Interaction, seconds: int):
    bot.anti_spam_delay = seconds
    await interaction.response.send_message(f"Anti-spam delay set to {seconds} seconds", ephemeral=True)

@bot.tree.command(name="setspamrepeatlimit", description="Set spam repeat message limit")
@is_admin()
@app_commands.describe(limit="Number of repeated messages allowed")
async def setspamrepeatlimit(interaction: discord.Interaction, limit: int):
    bot.spam_repeat_limit = limit
    await interaction.response.send_message(f"Spam repeated message limit set to {limit}", ephemeral=True)

@bot.tree.command(name="purge", description="Delete a number of messages")
@is_admin()
@app_commands.describe(amount="Number of messages to delete")
async def purge(interaction: discord.Interaction, amount: int):
    deleted = await interaction.channel.purge(limit=amount+1)
    await interaction.response.send_message(f"Deleted {len(deleted)-1} messages.", ephemeral=True)

@bot.tree.command(name="lock", description="Lock the channel")
@is_admin()
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False, create_public_threads=False, create_private_threads=False)
    await interaction.response.send_message("Channel locked.", ephemeral=True)

@bot.tree.command(name="unlock", description="Unlock the channel")
@is_admin()
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True, create_public_threads=True, create_private_threads=True)
    await interaction.response.send_message("Channel unlocked.", ephemeral=True)

@bot.tree.command(name="kick", description="Kick a member")
@is_admin()
@app_commands.describe(user="Member to kick", reason="Reason for kick")
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = None):
    await user.kick(reason=reason)
    await interaction.response.send_message(f"Kicked {user}.", ephemeral=True)

@bot.tree.command(name="ban", description="Ban a member")
@is_admin()
@app_commands.describe(user="Member to ban", reason="Reason for ban")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = None):
    await user.ban(reason=reason)
    await interaction.response.send_message(f"Banned {user}.", ephemeral=True)

@bot.tree.command(name="unban", description="Unban a user by ID")
@is_admin()
@app_commands.describe(user_id="User ID to unban")
async def unban(interaction: discord.Interaction, user_id: int):
    user = await bot.fetch_user(user_id)
    await interaction.guild.unban(user)
    await interaction.response.send_message(f"Unbanned {user}.", ephemeral=True)

@bot.tree.command(name="mute", description="Mute a member")
@is_admin()
@app_commands.describe(user="Member to mute")
async def mute(interaction: discord.Interaction, user: discord.Member):
    role = discord.utils.get(interaction.guild.roles, name="Muted")
    if not role:
        role = await interaction.guild.create_role(name="Muted")
        for channel in interaction.guild.channels:
            await channel.set_permissions(role, send_messages=False, speak=False, add_reactions=False)
    await user.add_roles(role)
    await interaction.response.send_message(f"Muted {user}.", ephemeral=True)

@bot.tree.command(name="unmute", description="Unmute a member")
@is_admin()
@app_commands.describe(user="Member to unmute")
async def unmute(interaction: discord.Interaction, user: discord.Member):
    role = discord.utils.get(interaction.guild.roles, name="Muted")
    if role in user.roles:
        await user.remove_roles(role)
        await interaction.response.send_message(f"Unmuted {user}.", ephemeral=True)
    else:
        await interaction.response.send_message(f"{user} is not muted.", ephemeral=True)

@bot.tree.command(name="warn", description="Warn a member")
@is_admin()
@app_commands.describe(user="Member to warn", reason="Reason for warning")
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str = None):
    if user.id not in bot.warnings:
        bot.warnings[user.id] = []
    bot.warnings[user.id].append(reason or "No reason provided")
    await interaction.response.send_message(f"Warned {user}. Total warnings: {len(bot.warnings[user.id])}", ephemeral=True)

@bot.tree.command(name="warnings", description="View warnings for a member")
@app_commands.describe(user="Member to view warnings for")
async def warnings_cmd(interaction: discord.Interaction, user: discord.Member):
    user_warnings = bot.warnings.get(user.id, [])
    if not user_warnings:
        await interaction.response.send_message(f"{user} has no warnings.", ephemeral=True)
        return
    msg = f"Warnings for {user}:\n"
    for i, w in enumerate(user_warnings, 1):
        msg += f"{i}. {w}\n"
    await interaction.response.send_message(msg, ephemeral=True)

@bot.tree.command(name="clearwarnings", description="Clear warnings for a member")
@is_admin()
@app_commands.describe(user="Member to clear warnings for")
async def clearwarnings(interaction: discord.Interaction, user: discord.Member):
    if user.id in bot.warnings:
        bot.warnings.pop(user.id)
        await interaction.response.send_message(f"Cleared warnings for {user}.", ephemeral=True)
    else:
        await interaction.response.send_message(f"{user} has no warnings.", ephemeral=True)

@bot.tree.command(name="slowmode", description="Set slowmode delay for the channel")
@is_admin()
@app_commands.describe(seconds="Seconds for slowmode delay")
async def slowmode(interaction: discord.Interaction, seconds: int):
    await interaction.channel.edit(slowmode_delay=seconds)
    await interaction.response.send_message(f"Slowmode set to {seconds} seconds.", ephemeral=True)

@bot.tree.command(name="nickname", description="Change or reset nickname of a member")
@is_admin()
@app_commands.describe(user="Member to change nickname for", nickname="New nickname or leave blank to reset")
async def nickname(interaction: discord.Interaction, user: discord.Member, nickname: str = None):
    await user.edit(nick=nickname)
    if nickname:
        await interaction.response.send_message(f"Changed nickname for {user} to {nickname}.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Reset nickname for {user}.", ephemeral=True)

@bot.tree.command(name="userinfo", description="Show info about a user")
@app_commands.describe(user="User to get info on (defaults to yourself)")
async def userinfo(interaction: discord.Interaction, user: discord.Member = None):
    user = user or interaction.user
    embed = discord.Embed(title=str(user), color=discord.Color.blue())
    embed.set_thumbnail(url=user.avatar.url if user.avatar else discord.Embed.Empty)
    embed.add_field(name="ID", value=user.id)
    embed.add_field(name="Account Created", value=user.created_at.strftime("%Y-%m-%d %H:%M:%S"))
embed.add_field(name="Joined Server", value=user.joined_at.strftime("%Y-%m-%d %H:%M:%S") if user.joined_at else "N/A")
    roles = [role.mention for role in user.roles if role != user.guild.default_role]
    embed.add_field(name=f"Roles ({len(roles)})", value=", ".join(roles) if roles else "None", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="userinfo", description="Show info about a user")
@app_commands.describe(user="User to get info on (defaults to yourself)")
async def userinfo(interaction: discord.Interaction, user: discord.Member = None):
    user = user or interaction.user
    embed = discord.Embed(title=str(user), color=discord.Color.blue())
    embed.set_thumbnail(url=user.avatar.url if user.avatar else discord.Embed.Empty)
    embed.add_field(name="ID", value=user.id)
    embed.add_field(name="Account Created", value=user.created_at.strftime("%Y-%m-%d %H:%M:%S"))
    embed.add_field(name="Joined Server", value=user.joined_at.strftime("%Y-%m-%d %H:%M:%S") if user.joined_at else "N/A")
    roles = [role.mention for role in user.roles if role != user.guild.default_role]
    embed.add_field(name=f"Roles ({len(roles)})", value=", ".join(roles) if roles else "None", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="serverinfo", description="Show info about the server")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(title=guild.name, color=discord.Color.green())
    embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
    embed.add_field(name="ID", value=guild.id)
    embed.add_field(name="Owner", value=guild.owner)
    # Removed deprecated 'Region' field
    embed.add_field(name="Member Count", value=guild.member_count)
    embed.add_field(name="Created At", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"))
    embed.add_field(name="Channels", value=len(guild.channels))
    embed.add_field(name="Roles", value=len(guild.roles))
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="roleall", description="Give a role to everyone")
@is_admin()
@app_commands.describe(role="Role to give everyone")
async def roleall(interaction: discord.Interaction, role: discord.Role):
    count = 0
    async with interaction.channel.typing():
        for member in interaction.guild.members:
            if role not in member.roles and not member.bot:
                try:
                    await member.add_roles(role)
                    count += 1
                except:
                    pass
    await interaction.response.send_message(f"Added role {role.name} to {count} members.", ephemeral=True)

@bot.tree.command(name="setautorole", description="Set autorole for new members")
@is_admin()
@app_commands.describe(role="Role to assign on member join")
async def setautorole(interaction: discord.Interaction, role: discord.Role):
    bot.autorole = role.name
    await interaction.response.send_message(f"Autorole set to {role.name}.", ephemeral=True)

bot.run("MTM4NTg0NjI3ODQyODAzNzEyMQ.G3qT-2.n9k6eQMYppcY5cWzju7ITgXGyt2vNf5oRC8EJU")
