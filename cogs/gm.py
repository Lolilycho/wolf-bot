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

@app_commands.command(name="co_replay")
async def co_replay(self, interaction: discord.Interaction):

    await interaction.response.send_message(
        "閲覧する役職を選択してください",
        view=RoleReplaySelectView(),
        ephemeral=True
    )

import discord


ROLES = ["占い師", "霊媒師", "狩人", "聖痕者"]


class RoleReplaySelectView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=60)

        self.select = discord.ui.Select(
            placeholder="役職を選択",
            options=[
                discord.SelectOption(label=r, value=r)
                for r in ROLES
            ]
        )

        self.select.callback = self.callback
        self.add_item(self.select)

    async def callback(self, interaction: discord.Interaction):

        role = self.select.values[0]

        await interaction.response.edit_message(
            content=f"役職: {role}",
            view=ReplayView(role)
        )

from database import get_connection
import discord


class ReplayView(discord.ui.View):

    def __init__(self, role):
        super().__init__(timeout=60)
        self.role = role

        self.select = discord.ui.Select(
            placeholder="プレイヤー選択"
        )

        self.select.callback = self.callback
        self.add_item(self.select)

        self.load_players()

    def load_players(self):

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
        SELECT DISTINCT discord_id
        FROM co_entries
        WHERE role=?
        """, (self.role,))

        rows = cur.fetchall()
        conn.close()

        options = []

        for r in rows:
            options.append(
                discord.SelectOption(
                    label=str(r["discord_id"]),
                    value=str(r["discord_id"])
                )
            )

        self.select.options = options

    async def callback(self, interaction: discord.Interaction):

        user_id = self.select.values[0]

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
        SELECT role, target_name, result, revoked, id
        FROM co_entries
        WHERE role=? AND discord_id=?
        ORDER BY id ASC
        """, (self.role, user_id))

        rows = cur.fetchall()
        conn.close()

        text = f"## {self.role} CO履歴\n\n"

        for r in rows:

            status = "❌撤回" if r["revoked"] else "✔"

            text += f"{status} {r['target_name']} {r['result']}\n"

        await interaction.response.edit_message(
            content=text,
            view=None
        )

