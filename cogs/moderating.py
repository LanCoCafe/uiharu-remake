from disnake import ApplicationCommandInteraction, TextInputStyle, MessageCommandInteraction, ModalInteraction
from disnake.ext import commands
from disnake.ui import Modal, TextInput

from core.bot import Uiharu


class Moderating(commands.Cog):
    def __init__(self, bot):
        self.bot: Uiharu = bot

    @commands.slash_command(name="reset", description="重設初春的記憶")
    async def reset(self, interaction: ApplicationCommandInteraction):
        if not interaction.author.id == self.bot.owner_id:
            return await interaction.response.send_message("你不是我的主人，不能這麼做", ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        await self.bot.setup_character_ai()

        await interaction.edit_original_response("✅ 重設完成")

    @commands.message_command(name="編輯", description="編輯初春的訊息")
    async def edit(self, interaction: MessageCommandInteraction):
        if not interaction.author.id == self.bot.owner_id:
            return await interaction.response.send_message("你不是我的主人，不能這麼做", ephemeral=True)

        await interaction.response.send_modal(
            Modal(
                title="編輯訊息",
                components=[
                    TextInput(
                        style=TextInputStyle.long,
                        placeholder="訊息內容",
                        label="訊息內容",
                        value=interaction.target.content,
                        custom_id="content",
                        required=True,
                        max_length=2000
                    )
                ]
            )
        )

        def check(i):
            return i.author.id == interaction.author.id

        try:
            modal_interaction: ModalInteraction = await self.bot.wait_for("modal_submit", check=check, timeout=60)
        except TimeoutError:
            return

        await interaction.target.edit(content=modal_interaction.text_values["content"])

        await modal_interaction.response.send_message("✅ 編輯完成", ephemeral=True)


def setup(bot):
    bot.add_cog(Moderating(bot))
