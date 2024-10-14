import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
from datetime import datetime, timedelta
import asyncio

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# IDs des canaux pour les messages permanents
CONTENEUR_CHANNEL_ID = CHANNEL_ID
NITRATE_CHANNEL_ID = CHANNEL_ID

class BraquageView(View):
    def __init__(self, braquage_type):
        super().__init__(timeout=None)
        self.braquage_type = braquage_type
        self.button = Button(label=f"Lancer un braquage {braquage_type}", style=discord.ButtonStyle.green, custom_id=f"braquage_{braquage_type}")
        self.button.callback = self.button_callback
        self.add_item(self.button)
        self.cooldown_message = None
        self.notification_sent = False
        self.main_message = None

    async def button_callback(self, interaction: discord.Interaction):
        if self.button.disabled:
            await interaction.response.send_message("Un braquage est déjà en cours. Veuillez attendre la fin du cooldown.", ephemeral=True)
        else:
            await self.handle_braquage(interaction)

    async def handle_braquage(self, interaction: discord.Interaction):
        cooldown = timedelta(minutes=2) if self.braquage_type == "conteneur" else timedelta(minutes=2)
        future_time = datetime.now() + cooldown

        self.button.disabled = True
        self.button.style = discord.ButtonStyle.gray
        self.main_message = interaction.message
        await self.main_message.edit(view=self)

        embed = discord.Embed(
            title=f"Cooldown Braquage {self.braquage_type.capitalize()}",
            description=f"Prochain braquage disponible dans : {cooldown}",
            color=discord.Color.pink()
        )

        if self.cooldown_message:
            await self.cooldown_message.delete()

        self.cooldown_message = await interaction.channel.send(embed=embed)
        await interaction.response.send_message(f"Braquage {self.braquage_type} lancé avec succès!", ephemeral=True)

        self.notification_sent = False
        await self.update_cooldown(interaction.channel, future_time)

    async def update_cooldown(self, channel, future_time):
        while datetime.now() < future_time:
            time_left = future_time - datetime.now()
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            embed = discord.Embed(
                title=f"Cooldown Braquage {self.braquage_type.capitalize()}",
                description=f"Prochain braquage disponible dans : {hours:02d}:{minutes:02d}:{seconds:02d}",
                color=discord.Color.green()
            )

            await self.cooldown_message.edit(embed=embed)

            if time_left <= timedelta(minutes=1) and not self.notification_sent:
                await channel.send(f"@everyone Le prochain braquage {self.braquage_type} sera disponible dans 5 minutes !")
                self.notification_sent = True

            await asyncio.sleep(1)

        await self.cooldown_message.delete()
        self.cooldown_message = None

        self.button.disabled = False
        self.button.style = discord.ButtonStyle.green
        await self.main_message.edit(view=self)
        await channel.send(f"@everyone Le braquage {self.braquage_type} est maintenant disponible !")

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await setup_permanent_messages()

async def setup_permanent_messages():
    conteneur_channel = bot.get_channel(CONTENEUR_CHANNEL_ID)
    nitrate_channel = bot.get_channel(NITRATE_CHANNEL_ID)

    if conteneur_channel:
        await clear_channel(conteneur_channel)
        embed = discord.Embed(title="Braquage Conteneur", description="Cliquez sur le bouton pour commencer le braquage du conteneur.", color=discord.Color.blue())
        await conteneur_channel.send(embed=embed, view=BraquageView("conteneur"))

    if nitrate_channel:
        await clear_channel(nitrate_channel)
        embed = discord.Embed(title="Vol de Nitrate d'argent", description="Cliquez sur le bouton pour commencer le vol de Nitrate.", color=discord.Color.red())
        await nitrate_channel.send(embed=embed, view=BraquageView("nitrate"))

async def clear_channel(channel):
    async for message in channel.history(limit=100):
        await message.delete()

bot.run('TOKEN_BOT')