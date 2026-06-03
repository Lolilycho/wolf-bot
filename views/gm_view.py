import discord


class GMView(discord.ui.View):

    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="昼開始", style=discord.ButtonStyle.primary)
    async def day(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild

        for member in guild.members:

            if member.bot:
                continue

            try:
                channel = discord.utils.get(
                    guild.voice_channels,
                    name="昼議論"
                )

                if channel:
                    await member.move_to(channel)

            except:
                pass

        await interaction.response.send_message(
            "昼開始しました",
            ephemeral=True
        )

    @discord.ui.button(label="夜開始", style=discord.ButtonStyle.secondary)
    async def night(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild

        wolf_channel = discord.utils.get(
            guild.voice_channels,
            name="wolf-vc"
        )

        night_channels = [
            c for c in guild.voice_channels
            if c.name.startswith("night-")
        ]

        players = [
            m for m in guild.members
            if not m.bot
        ]

        # とりあえず全員をnightへ分散
        for i, member in enumerate(players):

            try:
                await member.move_to(
                    night_channels[i % len(night_channels)]
                )
            except:
                pass

        await interaction.response.send_message(
            "夜開始しました",
            ephemeral=True
        )

    @discord.ui.button(label="終了", style=discord.ButtonStyle.danger)
    async def end(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message(
            "ゲーム終了（仮）",
            ephemeral=True
        )
