import asyncio
import json
from io import BytesIO

from disnake import ApplicationCommandInteraction, Option, OptionType, File
from disnake.ext import commands
from disnake.ext.commands import Bot


class Identifying(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.slash_command(name="nickname")
    async def nickname(self, interaction: ApplicationCommandInteraction):
        pass

    @nickname.sub_command(
        name="list", description="列出初春的名字記憶",
        options=[
            Option(
                name="ephemeral",
                description="是否要隱藏訊息",
                type=OptionType.boolean,
                required=False
            )
        ]
    )
    async def nickname_list(self, interaction: ApplicationCommandInteraction, ephemeral: bool = False):
        if not interaction.author.id == self.bot.owner_id:
            return await interaction.response.send_message("❌ 你不是我的主人，你不能這麼做", ephemeral=ephemeral)

        await interaction.response.send_message("⌛ 正在讀取資料...", ephemeral=ephemeral)

        with open("nicknames.json", "r", encoding="utf-8") as f:
            nicknames = json.load(f)

        nicknames_string = BytesIO()

        for user_id, nickname in nicknames.items():
            nicknames_string.write(f"{self.bot.get_user(int(user_id))}({user_id}): {nickname}\n".encode("utf-8"))

        nicknames_string.seek(0)

        await interaction.edit_original_response(
            "✅ 這些是我記得的名字", file=File(fp=nicknames_string, filename="nicknames.txt")
        )

    @nickname.sub_command(
        name="set", description="告訴初春你的名字",
        options=[
            Option(
                name="name",
                description="你的名字",
                type=OptionType.string,
                required=True
            ),
            Option(
                name="ephemeral",
                description="是否要隱藏訊息",
                type=OptionType.boolean,
                required=False
            )
        ]
    )
    async def nickname_set(self, interaction: ApplicationCommandInteraction, name: str, ephemeral: bool = False):
        await interaction.response.send_message("⌛ 正在寫入資料...", ephemeral=ephemeral)

        while True:
            try:
                with open("nicknames.json", "r+", encoding="utf-8") as f:
                    nicknames = json.load(f)

                    nicknames[str(interaction.author.id)] = name

                    f.seek(0)
                    json.dump(nicknames, f, indent=4, ensure_ascii=False)
                    f.truncate()

                break
            except PermissionError:
                await interaction.edit_original_response("⚠️ 偵測到資料競爭，正在...")
                await asyncio.sleep(5)

                continue

        await interaction.edit_original_response(f"✅ 你好，{name}！", )

    @nickname.sub_command(
        name="remove", description="將你的名字從移出初春的記憶",
        options=[
            Option(
                name="ephemeral",
                description="是否要隱藏訊息",
                type=OptionType.boolean,
                required=False
            )
        ]
    )
    async def nickname_set(self, interaction: ApplicationCommandInteraction, ephemeral: bool = False):
        await interaction.response.send_message("⌛ 正在寫入資料...", ephemeral=ephemeral)

        while True:
            try:
                with open("nicknames.json", "r+", encoding="utf-8") as f:
                    nicknames = json.load(f)

                    original_nickname = nicknames[str(interaction.author.id)]

                    del nicknames[str(interaction.author.id)]

                    f.seek(0)
                    json.dump(nicknames, f, indent=4, ensure_ascii=False)
                    f.truncate()

                break
            except PermissionError:
                await interaction.edit_original_response("⚠️ 偵測到資料競爭，正在...")
                await asyncio.sleep(5)

                continue

        await interaction.edit_original_response(f"?? 再見了，{original_nickname}")


def setup(bot: Bot):
    bot.add_cog(Identifying(bot))
