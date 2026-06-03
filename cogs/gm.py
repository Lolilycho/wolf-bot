import discord
from discord.ext import commands
from discord import app_commands

from views.gm_view import GMView


class GMCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="gm_panel")
    async def gm_panel(self, interaction: discord.Interaction):

        await interaction.channel.send(
            "GMパネル",
            view=GMView(self.bot)
        )

        await interaction.response.send_message(
            "GMパネル設置完了",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(GMCog(bot))
