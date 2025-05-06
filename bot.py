import discord
from discord.ext import commands
import os
from discord import ui
from dotenv import load_dotenv
import json

GUILD_ID = 1198334486966968570
async def save_ticket_transcript(ticket_channel):
    # Create a transcript of the ticket channel
    messages = await ticket_channel.history(limit=None).flatten()
    transcript = []
    for message in messages:
        transcript.append({
            'author': message.author.name,
            'content': message.content,
            'timestamp': message.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    # Save the transcript to a file
    with open(f'{ticket_channel.name}_transcript.json', 'w') as f:
        json.dump(transcript, f, indent=4)

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.guild_messages = True
intents.guild_reactions = True
bot = commands.Bot(command_prefix='!', intents=intents)

DEPARTMENT_CATEGORIES = {
    'General': 'General Inquiries',
    'Affiliates': 'Affiliate Inquiries',
    'Careers': 'Career Inquiries',
}

class DepartmentSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label = 'General', description = 'General Inquiries'),
            discord.SelectOption(label = 'Affiliates', description = 'Affiliate Inquiries'),
            discord.SelectOption(label = 'Careers', description = 'Career Inquiries')
        ]
        super().__init__(placeholder = 'Select a department', min_values = 1, max_values = 1, options = options)

    async def callback(self, interaction: discord.Interaction):
        selected_department = self.values[0]
        await interaction.response.send_message(f'You selected: {selected_department}')
        
        # Guild
        guild = bot.get_guild(GUILD_ID)
        if guild is None:
            await interaction.response.send_message("Guild not found.", ephemeral=True)
            return
        
        category_name = DEPARTMENT_CATEGORIES[selected_department]
        category = discord.utils.get(guild.categories, name=category_name)
        if category is None:
            await interaction.response.send_message(f"Category '{category_name}' not found.", ephemeral=True)
            return
        
        department = selected_department
        name = channel_name,
        user = interaction.user
        category = category
        topic = f'Ticket for {user.name} ({user.id})' 
        Department: {department}
        
        channel_name = f'ticket-{user.name}'.lower().replace(' ', '-')
        ticket_channel = await guild.create_text_channel(channel_name, category=category)
        await ticket_channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        
        await ticket_channel.send(
            content = f'New ticket created by {user.mention} in {category_name} department.',
            embed = discord.Embed(
                title = f'Ticket for {user.name}',
                description = f'Please describe your issue in detail.',
                color = discord.Color.blue()
            )
        )

        await interaction.response.send_message(
            f'A new modmail thread has been created for you in the **{department}** department. Please be patient while we review your request.',
            ephemeral = True
        )

        if not hasattr(interaction.user, 'ticket_channel'):
            bot.ticket_channel = ticket_channel
        bot.ticket_channels[user.id] = ticket_channel.id

class DepartmentSelectView(ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(DepartmentSelect())

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    bot.ticket_channels = {}

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if isinstance(message.channel, discord.DMChannel):
        user_id = message.author.id

        if user_id in bot.ticket_channels:
            guild = bot.get_guild(GUILD_ID)
            if not guild:
                print('Bot is not in the specified guild.')
                return
            
            ticket_channel_id = bot.ticket_channels[user_id]
            ticket_channel = guild.get_channel(ticket_channel_id)

            if ticket_channel:
                await ticket_channel.send(
                    content = f'New message from {message.author.mention}:',
                    embed = discord.Embed(
                        description = message.content,
                        color = discord.Color.blue()
                    )
                )
                await message.channel.send('Your message has been forwarded to the support team.')
                return
            
            view = DepartmentSelectView()
            await message.reply(
                content = 'Please select a department for your ticket:',
                view = view)
            return
        
        await bot.process_commands(message)

        bot.run('DISCORD_TOKEN')
        await save_ticket_transcript(ticket_channel)
                



            
        