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

@discord.ui.button(label="CO修正", style=discord.ButtonStyle.blurple)
async def fix(self, interaction: discord.Interaction, button: discord.ui.Button):

    await interaction.response.send_message(
        "修正するCOを選択してください",
        view=FixSelectView(self.game_id, interaction.user.id),
        ephemeral=True
    )


import discord
from database import get_connection


class FixSelectView(discord.ui.View):

    def __init__(self, game_id: int, user_id: int):
        super().__init__(timeout=60)

        self.game_id = game_id
        self.user_id = user_id

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
        SELECT id, role, target_name, result
        FROM co_entries
        WHERE game_id=? AND discord_id=?
        ORDER BY id DESC
        LIMIT 10
        """, (game_id, user_id))

        rows = cur.fetchall()
        conn.close()

        options = []

        for r in rows:

            label = f"{r['role']} {r['target_name']} {r['result']}"

            options.append(
                discord.SelectOption(
                    label=label,
                    value=str(r["id"])
                )
            )

        self.select = discord.ui.Select(
            placeholder="修正するCOを選択",
            options=options
        )

        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: discord.Interaction):

        co_id = int(self.select.values[0])

        await interaction.response.edit_message(
            content="修正内容を入力してください",
            view=FixEditView(self.game_id, self.user_id, co_id)
        )

class FixEditView(discord.ui.View):

    def __init__(self, game_id, user_id, co_id):
        super().__init__(timeout=60)

        self.game_id = game_id
        self.user_id = user_id
        self.co_id = co_id

        self.add_item(RoleFixSelect(game_id, user_id, co_id))

class RoleFixSelect(discord.ui.Select):

    def __init__(self, game_id, user_id, co_id):

        self.game_id = game_id
        self.user_id = user_id
        self.co_id = co_id

        options = [
            discord.SelectOption(label="占い師", value="占い師"),
            discord.SelectOption(label="霊媒師", value="霊媒師"),
            discord.SelectOption(label="狩人", value="狩人"),
            discord.SelectOption(label="聖痕者", value="聖痕者"),
        ]

        super().__init__(
            placeholder="役職を選択",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):

        role = self.values[0]

        await interaction.response.edit_message(
            content=f"役職: {role}",
            view=TargetFixView(self.game_id, self.user_id, self.co_id, role)
        )

class TargetFixView(discord.ui.View):

    def __init__(self, game_id, user_id, co_id, role):
        super().__init__(timeout=60)

        self.game_id = game_id
        self.user_id = user_id
        self.co_id = co_id
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

        self.select = discord.ui.Select(
            placeholder="対象を選択",
            options=options
        )

        self.select.callback = self.callback
        self.add_item(self.select)

    async def callback(self, interaction: discord.Interaction):

        target = self.select.values[0]

        if self.role == "狩人":

            await update_co(self.co_id, self.role, target, "護衛")

        elif self.role == "聖痕者":

            await update_co(self.co_id, self.role, None, None)

        else:

            await interaction.response.edit_message(
                content="結果を選択",
                view=ResultFixView(self.co_id, self.role, target)
            )
            return

        await interaction.response.send_message(
            "修正完了",
            ephemeral=True
        )

class ResultFixView(discord.ui.View):

    def __init__(self, co_id, role, target):
        super().__init__(timeout=60)

        self.co_id = co_id
        self.role = role
        self.target = target

        options = [
            discord.SelectOption(label="○", value="○"),
            discord.SelectOption(label="●", value="●")
        ]

        self.select = discord.ui.Select(
            placeholder="結果",
            options=options
        )

        self.select.callback = self.callback
        self.add_item(self.select)

    async def callback(self, interaction: discord.Interaction):

        result = self.select.values[0]

        await update_co(self.co_id, self.role, self.target, result)

        await interaction.response.send_message(
            "修正完了",
            ephemeral=True
        )

from database import get_connection


async def update_co(co_id, role, target, result):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    UPDATE co_entries
    SET role=?, target_name=?, result=?
    WHERE id=?
    """, (
        role,
        target,
        result,
        co_id
    ))

    conn.commit()
    conn.close()

@discord.ui.button(label="CO撤回", style=discord.ButtonStyle.red)
async def revoke(self, interaction: discord.Interaction, button: discord.ui.Button):

    await interaction.response.send_message(
        "撤回するCOを選択してください",
        view=RevokeSelectView(self.game_id, interaction.user.id),
        ephemeral=True
    )


import discord
from database import get_connection


class RevokeSelectView(discord.ui.View):

    def __init__(self, game_id: int, user_id: int):
        super().__init__(timeout=60)

        self.game_id = game_id
        self.user_id = user_id

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
        SELECT id, role, target_name, result
        FROM co_entries
        WHERE game_id=? AND discord_id=? AND revoked=0
        ORDER BY id DESC
        LIMIT 10
        """, (game_id, user_id))

        rows = cur.fetchall()
        conn.close()

        options = []

        for r in rows:

            label = f"{r['role']} {r['target_name']} {r['result']}"

            options.append(
                discord.SelectOption(
                    label=label,
                    value=str(r["id"])
                )
            )

        self.select = discord.ui.Select(
            placeholder="撤回するCOを選択",
            options=options
        )

        self.select.callback = self.callback
        self.add_item(self.select)

    async def callback(self, interaction: discord.Interaction):

        co_id = int(self.select.values[0])

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
        UPDATE co_entries
        SET revoked=1
        WHERE id=?
        """, (co_id,))

        conn.commit()
        conn.close()

        await interaction.response.edit_message(
            content="COを撤回しました",
            view=None
    )

