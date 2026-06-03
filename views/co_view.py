import discord
from database import get_connection


ROLES = [
    "占い師",
    "霊媒師",
    "狩人",
    "聖痕者"
]

RESULTS_NORMAL = ["○", "●"]
RESULTS_HUNTER = ["護衛"]
RESULTS_NONE = ["なし"]


# -----------------------------
# 1. メインパネル
# -----------------------------
class COView(discord.ui.View):

    def __init__(self, game_id: int):
        super().__init__(timeout=None)
        self.game_id = game_id

    @discord.ui.button(label="CO登録", style=discord.ButtonStyle.green)
    async def register(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message(
            "COを開始します",
            view=RoleSelectView(self.game_id, interaction.user.id),
            ephemeral=True
        )


# -----------------------------
# 2. 役職選択
# -----------------------------
class RoleSelectView(discord.ui.View):

    def __init__(self, game_id: int, user_id: int):
        super().__init__(timeout=60)
        self.game_id = game_id
        self.user_id = user_id

        options = [
            discord.SelectOption(label=r, value=r)
            for r in ROLES
        ]

        self.role_select = discord.ui.Select(
            placeholder="役職を選択",
            options=options
        )

        self.role_select.callback = self.role_callback
        self.add_item(self.role_select)

    async def role_callback(self, interaction: discord.Interaction):

        role = self.role_select.values[0]

        await interaction.response.edit_message(
            content=f"役職: {role}",
            view=TargetSelectView(self.game_id, self.user_id, role)
        )


# -----------------------------
# 3. 対象選択
# -----------------------------
class TargetSelectView(discord.ui.View):

    def __init__(self, game_id: int, user_id: int, role: str):
        super().__init__(timeout=60)
        self.game_id = game_id
        self.user_id = user_id
        self.role = role

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
        SELECT name FROM players
        WHERE game_id=?
        """, (game_id,))

        players = cur.fetchall()
        conn.close()

        options = [
            discord.SelectOption(label=p["name"], value=p["name"])
            for p in players
        ]

        self.target_select = discord.ui.Select(
            placeholder="対象を選択",
            options=options
        )

        self.target_select.callback = self.target_callback
        self.add_item(self.target_select)

    async def target_callback(self, interaction: discord.Interaction):

        target = self.target_select.values[0]

        if self.role == "狩人":
            await interaction.response.edit_message(
                content=f"役職: {self.role} / 対象: {target}",
                view=ResultSelectView(self.game_id, self.user_id, self.role, target, ["護衛"])
            )
        elif self.role == "聖痕者":
            await save_co(self.game_id, self.user_id, self.role, None, None)
            await interaction.response.edit_message(
                content="登録完了（聖痕者）",
                view=None
            )
        else:
            await interaction.response.edit_message(
                content=f"役職: {self.role} / 対象: {target}",
                view=ResultSelectView(self.game_id, self.user_id, self.role, target, ["○", "●"])
            )


# -----------------------------
# 4. 結果選択
# -----------------------------
class ResultSelectView(discord.ui.View):

    def __init__(self, game_id: int, user_id: int, role: str, target: str, results: list):
        super().__init__(timeout=60)

        self.game_id = game_id
        self.user_id = user_id
        self.role = role
        self.target = target

        options = [
            discord.SelectOption(label=r, value=r)
            for r in results
        ]

        self.result_select = discord.ui.Select(
            placeholder="結果を選択",
            options=options
        )

        self.result_select.callback = self.result_callback
        self.add_item(self.result_select)

    async def result_callback(self, interaction: discord.Interaction):

        result = self.result_select.values[0]

        await save_co(
            self.game_id,
            self.user_id,
            self.role,
            self.target,
            result
        )

        await interaction.response.edit_message(
            content="CO登録完了",
            view=None
        )


# -----------------------------
# DB保存 + 再描画
# -----------------------------
async def save_co(game_id, user_id, role, target, result):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO co_entries(
        game_id,
        discord_id,
        role,
        target_name,
        result,
        day
    )
    VALUES (?, ?, ?, ?, ?, 1)
    """, (
        game_id,
        user_id,
        role,
        target,
        result
    ))

    conn.commit()
    conn.close()

    await render_co_status(game_id)


# -----------------------------
# CO表示更新
# -----------------------------
async def render_co_status(game_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT * FROM co_entries
    WHERE game_id=?
    """, (game_id,))

    rows = cur.fetchall()
    conn.close()

    text = {}

    for r in rows:

        role = r["role"]
        user = r["discord_id"]
        target = r["target_name"]
        result = r["result"]

        if role not in text:
            text[role] = {}

        if user not in text[role]:
            text[role][user] = []

        if target:
            text[role][user].append(f"{target}{result}")
        else:
            text[role][user].append("登録")


    output = ""

    for role, users in text.items():

        output += f"## {role}\n"

        for u, logs in users.items():
            output += f"- {u}: " + "→".join(logs) + "\n"

        output += "\n"


    # co-statusチャンネル更新
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT co_status_id FROM channels
    WHERE game_id=?
    """, (game_id,))

    channel_id = cur.fetchone()["co_status_id"]

    conn.close()

    channel = discord.utils.get(
        interaction.guild.channels,
        id=channel_id
    )

    if channel:
        async for msg in channel.history(limit=10):
            await msg.delete()

        await channel.send(output)
