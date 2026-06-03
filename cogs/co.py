from discord.ext import commands
from discord import app_commands
from views.co_view import COView


class COCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="co_panel")
    async def co_panel(self, interaction):

        await interaction.channel.send(
            "COパネル",
            view=COView(game_id=1)  # ←ここは後でDBから取得
        )

        await interaction.response.send_message(
            "COパネル設置完了",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(COCog(bot))
