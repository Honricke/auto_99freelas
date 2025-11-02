import telebot
import json
from time import sleep


class Telebot:
    def iniciar_bot(self):
        while True:
            try:
                with open("config.json", encoding="utf-8-sig") as telegram:
                    self.telegram = (json.load(telegram))["telegram"]
                    telegram.close()

                self.bot = telebot.TeleBot(self.telegram["token"])
                break

            except Exception as err:
                print(err)
                sleep(2)

    def send_message(self, texto, to=False):
        self.iniciar_bot()
        mensagens = []
        grupos = []

        if not to:
            grupos = self.telegram["grupo"]
        else:
            grupos = [to]

        for grupo in grupos:
            try:
                mensagens.append(
                    self.bot.send_message(
                        grupo, texto, parse_mode="HTML", disable_web_page_preview=True
                    )
                )
            except:
                self.iniciar_bot()
                sleep(1)

        return mensagens
