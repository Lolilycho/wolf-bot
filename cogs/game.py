import discord

from discord.ext import commands
from discord import app_commands

from database import get_connection


class Game(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="create_game",
        description="ゲーム作成"
    )
    async def create_game(
        self,
        interaction: discord.Interaction,
        name: str
    ):

        guild = interaction.guild

        category = await guild.create_category(name)

        gm_control = await category.create_text_channel(
            "gm-control"
        )

        gm_status = await category.create_text_channel(
            "gm-status"
        )

        co_status = await category.create_text_channel(
            "co-status"
        )

        co_control = await category.create_text_channel(
            "co-control"
        )

        await category.create_voice_channel(
            "昼議論"
        )

        await category.create_voice_channel(
            "wolf-vc"
        )

        for i in range(1, 14):

            await category.create_voice_channel(
                f"night-{i:02d}"
            )

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO games(
            guild_id,
            name,
            status
        )
        VALUES (?, ?, ?)
        """,
        (
            guild.id,
            name,
            "ACTIVE"
        ))

        game_id = cur.lastrowid

        cur.execute("""
        INSERT INTO channels(
            game_id,
            category_id,
            gm_control_id,
            gm_status_id,
            co_status_id,
            co_control_id
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            game_id,
            category.id,
            gm_control.id,
            gm_status.id,
            co_status.id,
            co_control.id
        ))

        conn.commit()
        conn.close()

        await interaction.response.send_message(
            f"{name} を作成しました",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Game(bot))
