import discord
from database import get_connection


class RegisterView(discord.ui.View):

    def __init__(self, game_id: int):
        super().__init__(timeout=None)
        self.game_id = game_id

    @discord.ui.button(label="参加", style=discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO players(game_id, discord_id, name, alive)
        VALUES (?, ?, ?, 1)
        """, (
            self.game_id,
            interaction.user.id,
            interaction.user.display_name
        ))

        conn.commit()
        conn.close()

        await interaction.response.send_message(
            "参加登録しました",
            ephemeral=True
        )

    @discord.ui.button(label="参加取消", style=discord.ButtonStyle.red)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
        DELETE FROM players
        WHERE game_id=? AND discord_id=?
        """, (
            self.game_id,
            interaction.user.id
        ))

        conn.commit()
        conn.close()

        await interaction.response.send_message(
            "参加取消しました",
            ephemeral=True
        )
