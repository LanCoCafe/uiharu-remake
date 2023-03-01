import logging
from os import getenv

from aiohttp import ClientSession
from disnake import Message, Webhook, ButtonStyle, DMChannel
from disnake.ext import commands
from disnake.ui import Button

from core.bot import Uiharu


class Asking(commands.Cog):
    def __init__(self, bot: Uiharu):
        self.bot = bot

        self.webhook: Webhook = Webhook.from_url(
            getenv("LOG_WEBHOOK"), session=ClientSession(), bot_token=getenv("TOKEN")
        )

    @commands.Cog.listener(name="on_message")
    async def talk(self, message: Message):
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

        # TODO: Configurable blacklist
        blacklisted_words = ["lolicon", "蘿", "羅", "ロリ", "夢", "ㄌㄌ", "ll"]

        for word in blacklisted_words:
            if word in message.content.lower():
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

        conversation = await self.bot.conversation_manager.get_conversation(message.author.id)

        answer = await conversation.ask(self.bot, message)

        reply_message = await message.channel.send(
            answer,
            reference=message,
            mention_author=True
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


def setup(bot: Uiharu):
    bot.add_cog(Asking(bot))
