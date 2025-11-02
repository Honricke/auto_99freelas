import { DefaultEventsMap, Server, Socket } from "socket.io";
import http from "http";
import { Freelas } from "../node_bot/quote";

const server = http.createServer();
const io = new Server(server, { cors: { origin: "*" } });
let pythonSocket: Socket<
  DefaultEventsMap,
  DefaultEventsMap,
  DefaultEventsMap,
  any
> | null = null;

io.on("connection", (socket) => {
  console.log("Cliente conectado");
  pythonSocket = socket;

  socket.on("user_state", async (data) => {
    console.log("Recebido do Python:", data);
    let freelas = await Freelas.start(data);
    await freelas.run();

    console.log("Finalizad! Desconectando...");

    socket.emit("execute_action", {
      action: "disconnect",
      message: "",
    });
  });
});

export function send_message(message: string, to: string) {
  let final_message = { text: message, id: to };

  if (pythonSocket) {
    pythonSocket.emit("execute_action", {
      action: "send_message",
      message: final_message,
    });
  }
}

server.listen(4000, () => console.log("Socket.IO rodando na porta 4000"));
