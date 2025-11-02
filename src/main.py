from scraping import scrap_projects
from time import sleep
import telebot
from Telebot import Telebot
import json
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from os import linesep as line
from sockets import start_socket
import locale

locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")
BOT_ID = 5904924744

user_state = {}


def wait_message(bot):
    @bot.message_handler(func=lambda message: True)
    def handle_message(message):
        replied = message.reply_to_message

        # Só continua se estiver respondendo uma msg do bot
        if not replied or replied.from_user.id != BOT_ID:
            bot.send_message(
                message.chat.id, "Você não respondeu uma mensagem desse bot!"
            )
            return

        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("Proposta", callback_data="proposta"),
            InlineKeyboardButton("Pergunta", callback_data="pergunta"),
        )

        entities = replied.entities  # lista de MessageEntity

        # Pega o primeiro link do tipo text_link
        url = None
        for entity in entities:
            if entity.type == "text_link":
                url = entity.url
                break

        user_state[message.chat.id] = {
            "url": f"{url}",
        }

        bot.send_message(
            message.chat.id,
            "Escolha entre proposta e pergunta:",
            reply_markup=keyboard,
        )

    # -------------------- Callback --------------------
    @bot.callback_query_handler(func=lambda call: True)
    def handle_query(call):
        if call.data == "proposta":
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(InlineKeyboardButton("Cancelar", callback_data="cancelar"))

            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="Você escolheu Proposta.",
                reply_markup=keyboard,
            )

            msg = bot.send_message(
                call.message.chat.id,
                f"Envie o orçamento:{line}Exemplos: 400, 400.50, 1252.23",
            )

            user_state[call.message.chat.id]["state"] = "wait_quote"
            user_state[call.message.chat.id]["data"] = {"type": "proposta"}

            # Espera a próxima mensagem do usuário
            bot.register_next_step_handler(msg, receive_quote)

        elif call.data == "pergunta":
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(InlineKeyboardButton("Cancelar", callback_data="cancelar"))

            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="Você escolheu Proposta.",
                reply_markup=keyboard,
            )

            msg = bot.send_message(
                call.message.chat.id,
                f"Envie sua dúvida:{line}Exemplo: Queria saber se seu projeto...",
            )

            user_state[call.message.chat.id]["state"] = "wait_quote"
            user_state[call.message.chat.id]["data"] = {"type": "pergunta"}

            bot.register_next_step_handler(msg, receive_question)

        elif call.data == "cancelar":
            bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)

            user_state.pop(call.message.chat.id, None)

            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="Operação cancelada!",
            )

        else:
            print(call.data)
            tipo = call.data.split((" "))[0]
            index = call.data.split((" "))[1]

            user_state[call.message.chat.id]["data"]["pattern"] = configs[tipo][
                int(index)
            ]
            user_state[call.message.chat.id]["state"] = None

            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=call.message.text,
            )

            bot.send_message(
                call.message.chat.id,
                "✅ Dados recebidos com sucesso!",
            )

            bot.send_message(
                call.message.chat.id,
                "Iniciando operação...",
            )

            formatted_state = {
                "id": call.message.chat.id,
                **user_state[call.message.chat.id],
            }

            print(formatted_state)

            start_socket(formatted_state)

    # -------------------- Função de resposta perguntas --------------------
    def receive_question(message):
        question = message.text.strip()
        bot.send_message(message.chat.id, f"✅ Dúvida recebida: {line}{question}")

        user_state[message.from_user.id]["data"]["question"] = question
        user_state[message.from_user.id]["state"] = "wait_pattern"

        string = ""
        keyboard = InlineKeyboardMarkup(row_width=2)

        for index, qstn in enumerate(configs["question"]):
            string = f"{string}{line}{line}{index+1}ª - {qstn}"

        buttons = [
            InlineKeyboardButton(f"{index+1}ª", callback_data=f"question {index}")
            for index, qstn in enumerate(configs["question"])
        ]

        keyboard.add(*buttons)

        string = string.replace("{line}", f"{line}").replace("{duvida}", f"{question}")

        bot.send_message(
            message.chat.id,
            f"Escolha a mensagem de envio: {line}{string}",
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )

    # -------------------- Função de resposta propostas--------------------
    def receive_quote(message):
        orcamento = float(message.text.strip())
        bot.send_message(
            message.chat.id,
            f"✅ Orçamento recebido: {locale.currency(orcamento, grouping=True)}",
        )

        user_state[message.from_user.id]["data"]["quote"] = str(
            int(round(orcamento * 100))
        )
        user_state[message.from_user.id]["state"] = "wait_duration"

        msg = bot.send_message(
            message.chat.id,
            f"Envie a duração do serviço (em dias):{line}Exemplos: 3, 10, 53",
        )

        bot.register_next_step_handler(msg, receive_duration)

    def receive_duration(message):
        duration = message.text.strip()
        bot.send_message(message.chat.id, f"✅ Duração recebida: {duration}")

        user_state[message.from_user.id]["data"]["duration"] = duration
        user_state[message.from_user.id]["state"] = "wait_pattern"

        string = ""
        keyboard = InlineKeyboardMarkup(row_width=2)

        for index, msg in enumerate(configs["message"]):
            string = f"{string}{line}{line}{index+1}ª - {msg}"

        buttons = [
            InlineKeyboardButton(f"{index+1}ª", callback_data=f"message {index}")
            for index, qstn in enumerate(configs["question"])
        ]

        keyboard.add(*buttons)

        string = string.replace("{line}", f"{line}")

        msg = bot.send_message(
            message.chat.id,
            f"Escolha a mensagem de envio: {line}{string}",
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )

    # -------------------- Polling --------------------
    try:
        bot.infinity_polling()
    except Exception as err:
        print(err)
        print("Reiniciando o bot!")
        sleep(2)
        bot = telebot.TeleBot(configs["telegram"]["token"])


if __name__ == "__main__":
    with open("config.json", encoding="utf-8-sig") as config_file:
        configs = json.load(config_file)

    bot = telebot.TeleBot(configs["telegram"]["token"])
    cTelebot = Telebot()

    t1 = threading.Thread(target=wait_message, args=(bot,))
    t1.start()

    while True:
        data = scrap_projects(True, cTelebot)
        sleep(60)
