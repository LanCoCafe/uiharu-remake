import logging
from os import getenv

from aiohttp import ClientSession
from disnake import Message, Webhook, ButtonStyle, DMChannel, Embed, Color
from disnake.ext import commands
from disnake.ui import Button

from core.bot import Uiharu
from core.conversations import ConversationFrom


class Asking(commands.Cog):
    def __init__(self, bot: Uiharu):
        self.bot = bot

        self.webhook: Webhook = Webhook.from_url(
            getenv("LOG_WEBHOOK"), session=ClientSession(), bot_token=getenv("TOKEN")
        )

    @commands.Cog.listener(name="on_message")
    async def talk(self, message: Message):
        is_acgm = message.guild and message.guild.id == 81384788765712384

        if message.author.bot:
            return

        if message.author == self.bot.user:
            return

        if self.bot.user.id not in [mention.id for mention in message.mentions]:
            if not isinstance(message.channel, DMChannel):
                return

        if len(message.content) > 800:
            await message.reply("❌ | 請不要輸入超過800個字元的訊息")
            return

        await self.bot.wait_until_ready()

        if message.guild:
            data_string = f"GUILD_ID={message.guild.id} CHANNEL_ID={message.channel.id} USER_ID={message.author.id}"
            author_string = f"{message.author} from #{message.channel.name}"

        else:
            data_string = f"(DM) USER_ID={message.author.id}"
            author_string = f"{message.author} from DM"

        log_message = await self.webhook.send(
            content=f"{message.content}\n\n"
                    f"[Original]({message.jump_url})\n"
                    f"```{data_string}\n\n==========\n"
                    f"{message.content}```",
            username=author_string,
            avatar_url=message.author.avatar.url or message.author.default_avatar.url,
            components=[Button(label="Go to message", url=message.jump_url, style=ButtonStyle.url)],
            wait=True
        )

        logging.info(f"New question from {message.author}: {message.content}")

        conversation, source = await self.bot.conversation_manager.get_conversation(
            message.author.id,
            timeout=600 if is_acgm else 60,
            delay_per_message=0 if is_acgm else 20
        )

        try:
            answer = await conversation.ask(self.bot, message)
        except Exception as e:
            answer = f"❌ | 發生錯誤: {e}"

        reply_message = await message.channel.send(
            answer,
            reference=message,
            mention_author=True,
            embeds=[Embed(
                title="💡 | 提醒",
                description="你正在非 A.C.G.M City 的伺服器使用初春，\n"
                            "這會讓初春的回覆速度減慢大約 10~20 秒，\n"
                            "為了最好的使用體驗，你可以前往 A.C.G.M City 伺服器使用初春，\n"
                            "Note: 在抵達 A.C.G.M City 後，請等待至少 60 秒的時間再與初春對話，來套用 A.C.G.M City 中的專屬福利",
                color=Color.yellow()
            )] if (not is_acgm and source == ConversationFrom.NEW) else [],
            components=[Button(
                style=ButtonStyle.url,
                label="A.C.G.M City",
                url="https://discord.gg/acgmcity"
            )] if (not is_acgm and source == ConversationFrom.NEW) else [],
        )

        await self.webhook.send(
            content=f"{answer}\n\n"
                    f"[Replies to]({log_message.jump_url}) | [Original]({reply_message.jump_url})\n"
                    f"```{answer}```",
            avatar_url=self.bot.user.avatar.url,
            username=self.bot.user.display_name,
            components=[
                Button(
                    label="Replies to",
                    url=log_message.jump_url,
                    style=ButtonStyle.url,
                ),
                Button(
                    label="Go to message",
                    url=reply_message.jump_url,
                    style=ButtonStyle.url
                )
            ]
        )

    # # This feature is hard coded and only available for A.C.G.M City (https://discord.gg/acgmcity)
    # @commands.Cog.listener(name="on_member_join")
    # async def welcome(self, member: Member):
    #     if not member.guild.id == 952461973013037106:
    #         return
    #
    #     if member.id == self.bot.user.id:
    #         return
    #
    #     await self.bot.wait_until_ready()
    #
    #     channel = self.bot.get_channel(952461973491159076)
    #
    #     conversation = await self.bot.conversation_manager.get_conversation(member.id)
    #
    #     answer = await conversation.ask(self.bot, f"你好，我是 {member.display_name}")
    #
    #     await channel.send(
    #         content=f"{member.mention} {answer}",
    #         embed=Embed(
    #             title="📝 來自 Nat1an",
    #             description="這個歡迎訊息是由 AI 自動生成的\n"
    #                         f"你可以透過在訊息中提及 {self.bot.user.mention} 來繼續這個對話\n"
    #                         "如果你有任何問題，歡迎直接在頻道中提出\n"
    #                         "希望你在 A.C.G.M City 過得開心！",
    #             color=0x2b2d31
    #         )
    #     )


def setup(bot: Uiharu):
    bot.add_cog(Asking(bot))
