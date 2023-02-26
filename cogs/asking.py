import asyncio
import json
import logging
import random
import re

from disnake import Message
from disnake.abc import MISSING
from disnake.ext import commands

from core.bot import Uiharu
from core.classes import Question


class Asking(commands.Cog):
    def __init__(self, bot: Uiharu):
        self.bot = bot

        with open("nicknames.json", "r", encoding="utf-8") as f:
            self.nicknames: dict[str, str] = json.load(f)

        self.question_queue: list[Question] = []

    async def asking_loop(self):
        while True:
            await asyncio.sleep(random.randint(3, 5))

            if self.question_queue:
                question = self.question_queue.pop(0)

                last_error: Exception = MISSING

                for i in range(2):
                    try:
                        logging.info(f"Asking question: {question.question}")
                        question.answer = await self.bot.ask(question.question)
                        logging.info(f"Got response: {question.answer}")
                        break

                    except Exception as error:
                        last_error = error
                        logging.error(f"Failed to ask question {question.question} with error {error}, retrying...")
                        await self.bot.setup_character_ai()

                        continue

                if not question.answer:
                    logging.error(f"Failed to ask question {question.question} with error {last_error}")
                    question.answer = "❌ | 發生了一些錯誤，重問一次通常可以解決問題"

    @commands.Cog.listener(name="on_ready")
    async def start_asking_loop(self):
        self.bot.loop.create_task(self.asking_loop())

    @commands.Cog.listener(name="on_message")
    async def talk(self, message: Message):
        if message.author == self.bot.user:
            return

        if self.bot.user.id in [mention.id for mention in message.mentions]:
            content = message.content.replace(f"<@{self.bot.user.id}>", "")

            if ("\\" not in content) and (str(message.author.id) in self.nicknames):
                content.replace("\\", "")
                content = f"我是{self.nicknames[str(message.author.id)]}，{content}"

            mentions = re.search("<@(\d+)>", content)

            for match in mentions:
                if match.group(1) in self.nicknames:
                    content = content.replace(match, self.nicknames[match.group(1)])

                else:
                    try:
                        member = message.guild.get_member(match.group(1))
                        content = content.replace(match, member.display_name)

                    except AttributeError:
                        pass

            logging.info(f"New question from {message.author}: {content}")

            question = Question(content)

            self.question_queue.append(question)

            timer = 0

            while not question.answer:
                await asyncio.sleep(1)

                if timer % 9 == 0 or timer == 0:  # Trigger typing for every 9 seconds
                    await message.channel.trigger_typing()

                timer += 1

            await message.channel.send(
                question.answer,
                reference=message,
                mention_author=True
            )


def setup(bot):
    bot.add_cog(Asking(bot))
