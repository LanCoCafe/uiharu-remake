import asyncio
import logging
import random
from os import getenv

from aiohttp import ClientSession
from disnake import Message, Webhook, ButtonStyle, DMChannel, abc
from disnake.abc import MISSING
from disnake.ext import commands
from disnake.ui import Button

from core.bot import Uiharu


class Question:
    def __init__(self, author: abc.User, question: str):
        self.author = author
        self.question = question
        self.answer = None


class Asking(commands.Cog):
    def __init__(self, bot: Uiharu):
        self.bot = bot

        self.question_queue: list[Question] = []

        self.webhook: Webhook = Webhook.from_url(
            getenv("LOG_WEBHOOK"), session=ClientSession(), bot_token=getenv("TOKEN")
        )

    async def asking_loop(self):
        while True:
            await asyncio.sleep(random.randint(3, 5))

            if self.question_queue:
                question = self.question_queue.pop(0)

                last_error: Exception = MISSING

                conversation = await self.bot.conversation_manager.get_conversation(question.author.id)

                for i in range(2):
                    try:
                        question.answer = await asyncio.wait_for(conversation.ask(question.question), 30)

                        break

                    except Exception as error:
                        last_error = error

                        logging.error(f"Failed to ask question {question.question} with error {error}, retrying...")

                        await conversation.reset()

                        continue

                if not question.answer:
                    logging.error(f"Failed to ask question {question.question} with error {last_error}")
                    question.answer = "❌ | 發生了一些錯誤，重問一次通常可以解決問題"

    @commands.Cog.listener(name="on_ready")
    async def prepare(self):
        self.bot.loop.create_task(self.asking_loop())

    @commands.Cog.listener(name="on_message")
    async def talk(self, message: Message):
        if message.author == self.bot.user:
            return

        if self.bot.user.id not in [mention.id for mention in message.mentions]:
            if not isinstance(message.channel, DMChannel):
                return

        if len(message.content) > 800:
            await message.reply("❌ | 請不要輸入超過800個字元的訊息")
            return

        await self.bot.wait_until_ready()

        content = message.content.replace(f"<@{self.bot.user.id}>", "")

        # mentions = re.search("<@(\d+)>", content)
        #
        # if mentions:
        #     for match in mentions:
        #         if match.group(1) in self.conversation_manager.nicknames:
        #             content = content.replace(match, self.bot.nicknames[match])
        #
        #         else:
        #             try:
        #                 member = message.guild.get_member(match.group(1))
        #                 content = content.replace(match, member.display_name)
        #
        #             except AttributeError:
        #                 pass

        if message.guild:
            data_string = f"GUILD_ID={message.guild.id} CHANNEL_ID={message.channel.id} USER_ID={message.author.id}"
            author_string = f"{message.author} from {message.guild.name} - #{message.channel.name}"
        else:
            data_string = f"(DM) USER_ID={message.author.id}"
            author_string = f"{message.author} from DM"

        log_message = await self.webhook.send(
            content=f"{content}\n\n"
                    f"[Original]({message.jump_url})\n"
                    f"```{data_string}\n\n==========\n"
                    f"{message.content}```",
            username=author_string,
            avatar_url=message.author.avatar.url or message.author.default_avatar.url,
            components=[Button(label="Go to message", url=message.jump_url, style=ButtonStyle.url)],
            wait=True
        )

        logging.info(f"New question from {message.author}: {content}")

        question = Question(message.author, content)

        self.question_queue.append(question)

        timer = 0

        while not question.answer:
            await asyncio.sleep(1)

            if timer % 9 == 0 or timer == 0:  # Trigger typing for every 9 seconds
                await message.channel.trigger_typing()

            timer += 1

        reply_message = await message.channel.send(
            question.answer,
            reference=message,
            mention_author=True
        )

        await self.webhook.send(
            content=f"{question.answer}\n\n"
                    f"[Replies to]({log_message.jump_url}) | [Original]({reply_message.jump_url})\n"
                    f"```{question.answer}```",
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
