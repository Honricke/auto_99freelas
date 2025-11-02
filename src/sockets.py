import socketio
from Telebot import Telebot

sio = socketio.Client()


def start_socket(user_state):
    @sio.on("connect")
    def connect():
        print("Conectado ao Node.js!")
        sio.emit("user_state", user_state)

    @sio.on("disconnect")
    def disconnect():
        print("Desconectado do servidor.")

    # 🔥 Aqui você ouve o Node e executa ações
    @sio.on("execute_action")
    def on_execute_action(data):
        print(f"📩 Recebi do Node: {data}")
        action = data.get("action")

        if action == "send_message":
            Telebot().send_message(data["message"]["text"], data["message"]["id"])

        elif action == "disconnect":
            sio.disconnect()
            print("Desconectado!")

    sio.connect("http://localhost:4000")
    sio.wait()
