import os
import time
import logging
import traceback
from typing import Dict

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from agent import ask_agent

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USERS = os.getenv("ALLOWED_USERS", "")

MAX_QUESTIONS_PER_HOUR = 10
user_questions = {}


def format_answer(response: Dict) -> str:
    answer = response.get("answer", "Нет ответа.")
    sources = response.get("sources", [])

    if not sources:
        return answer

    text = answer + "\n\nИсточники:\n"

    for i, src in enumerate(sources, start=1):
        text += f"\n{i}. {src.get('section','Раздел')}\n"
        text += src.get("content", "")
        text += "\n"

    return text


def check_rate_limit(user_id: int):

    now = time.time()

    if user_id not in user_questions:
        user_questions[user_id] = []

    user_questions[user_id] = [
        t for t in user_questions[user_id]
        if now - t < 3600
    ]

    if len(user_questions[user_id]) >= MAX_QUESTIONS_PER_HOUR:
        return False

    user_questions[user_id].append(now)

    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("/start")

    await update.message.reply_text(
        "Бот запущен."
    )


async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        logger.info("=" * 80)
        logger.info("Новое сообщение")

        message = update.message

        if message is None:
            logger.warning("message == None")
            return

        logger.info(f"Тип чата: {message.chat.type}")
        logger.info(f"ID пользователя: {message.from_user.id}")
        logger.info(f"Имя: {message.from_user.full_name}")

        logger.info(f"Получено сообщение: {message.text}")

        text = message.text or ""

        logger.info(f"Username бота: @{context.bot.username}")

        if message.chat.type in ("group", "supergroup"):

            username = f"@{context.bot.username}"

            logger.info(f"Ожидается упоминание: {username}")

            if not text.lower().startswith(username.lower()):

                logger.info("Бот не упомянут.")

                return

            text = text[len(username):].strip()

            logger.info(f"Вопрос после удаления упоминания: {text}")

        if ALLOWED_USERS:

            allowed = [
                x.strip()
                for x in ALLOWED_USERS.split(",")
                if x.strip()
            ]

            logger.info(f"ALLOWED_USERS={allowed}")

            if str(message.from_user.id) not in allowed:

                logger.warning("Пользователь запрещён")

                await message.reply_text(
                    "У вас нет доступа."
                )

                return

        if not check_rate_limit(message.from_user.id):

            logger.warning("Превышен лимит запросов")

            await message.reply_text(
                "Лимит запросов превышен."
            )

            return

        logger.info("Отправляем typing...")

        await message.chat.send_action(ChatAction.TYPING)

        logger.info("Вызываем ask_agent()")

        response = ask_agent(text)

        logger.info("Ответ agent.py:")

        logger.info(response)

        answer = format_answer(response)

        logger.info("Отправляем ответ пользователю")

        await message.reply_text(answer)

        logger.info("Ответ успешно отправлен")

    except Exception:

        logger.error("ИСКЛЮЧЕНИЕ!")

        traceback.print_exc()

        try:
            await update.message.reply_text(
                "Произошла внутренняя ошибка. Подробности в консоли."
            )
        except Exception:
            traceback.print_exc()


def main():

    logger.info("Запуск...")

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_question
        )
    )

    logger.info("Бот запущен")

    application.run_polling()


if __name__ == "__main__":
    main()