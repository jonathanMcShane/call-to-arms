import discord
import os
import json
from dotenv import load_dotenv

# --- Configuration Loading ---
# Load environment variables from the .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Load role configurations from config.json
with open('config.json', 'r') as f:
    config = json.load(f)

VETTED_ROLE_NAME = config['vetted_role_name']
GAME_ROLES = config['game_roles']

# --- Bot Setup ---
# Define the necessary intents.
# We need guilds to find roles and members to check a user's roles.
intents = discord.Intents.default()
intents.guilds = True
intents.members = True

# Create the bot instance
bot = discord.Bot(intents=intents)

# --- UI Components (The Dropdown) ---
# This class defines the view that holds the dropdown menu.
class RoleSelectView(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=180)  # The view will time out after 180 seconds
        self.author = author # Store who initiated the command

    # This decorator defines the dropdown menu itself.
    @discord.ui.select(
        placeholder="Choose a game to rally...",
        min_values=1,
        max_values=1,
        # Dynamically create the options from our config file
        options=[discord.SelectOption(label=role) for role in GAME_ROLES]
    )
    async def select_callback(self, select, interaction):
        # This function is called when a user makes a selection.
        
        # First, check if the user interacting is the one who ran the command
        if interaction.user != self.author:
            await interaction.response.send_message("You cannot interact with another user's command!", ephemeral=True)
            return

        # Get the user who initiated the interaction as a Member object
        user = interaction.user
        
        # Check if the user has the 'Vetted' role
        # We create a list of the user's role names to check against our config
        user_role_names = [role.name for role in user.roles]
        
        if VETTED_ROLE_NAME not in user_role_names:
            # If they don't have the role, send a private (ephemeral) message
            await interaction.response.send_message(
                "You do not have the correct permissions to rally these nerds.", 
                ephemeral=True
            )
            return

        # --- If the user IS vetted ---
        
        # Get the name of the role the user selected from the dropdown
        selected_role_name = select.values[0]
        
        # Find the actual Role object on the server
        # discord.utils.get is a helper to find something in a list
        role_to_mention = discord.utils.get(interaction.guild.roles, name=selected_role_name)

        if role_to_mention is None:
            # This is a safety check in case the role was deleted from the server
            # but is still in the config.json
            await interaction.response.send_message(
                f"Error: The role '{selected_role_name}' could not be found on the server.", 
                ephemeral=True
            )
            return

        # If everything is correct, send the public "Call to Arms" message
        # We use interaction.response.send_message() to acknowledge the interaction first
        await interaction.response.send_message(f"Call to Arms! - {role_to_mention.mention}", allowed_mentions=discord.AllowedMentions(roles=True))
        
        # Disable the dropdown so it can't be used again
        self.clear_items()
        await interaction.edit_original_response(view=self)


# --- Bot Events and Commands ---

@bot.event
async def on_ready():
    """This event is triggered when the bot is connected and ready."""
    print(f'Logged in as {bot.user}')
    # Add this line to check the version
    print(f'Using py-cord version: {discord.__version__}') 
    print('Call to Arms is online and ready!')

@bot.slash_command(name="call", description="Send a Call to Arms for a specific game.")
async def call(ctx: discord.ApplicationContext):
    """
    This is the main slash command that users will run.
    """
    # Create an instance of our view, passing the author so we can check it later
    view = RoleSelectView(author=ctx.author)

    # Respond to the command with the view containing the dropdown.
    # We make this response ephemeral so that only the user who typed /call sees the dropdown.
    await ctx.respond("Select a game to send a Call to Arms!", view=view, ephemeral=True)

# --- Hosting Block for Render Web Service (Corrected) ---
from flask import Flask
from threading import Thread
import os # Make sure to import the os module

app = Flask('')

@app.route('/')
def home():
    return "Call to Arms Bot is alive!"

def run():
  # Get the port from the environment variable Render sets, default to 10000 for local testing
  port = int(os.environ.get('PORT', 10000)) 
  app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
# --- End of Hosting Block ---


# --- Run the Bot ---
keep_alive() 
bot.run(TOKEN)
# Trivial change to force a new IP on Render - 11 June 2025