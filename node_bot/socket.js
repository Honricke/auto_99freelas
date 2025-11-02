"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.send_message = send_message;
const socket_io_1 = require("socket.io");
const http_1 = __importDefault(require("http"));
const quote_1 = require("./quote");
const server = http_1.default.createServer();
const io = new socket_io_1.Server(server, { cors: { origin: "*" } });
let pythonSocket = null;
io.on("connection", (socket) => {
    console.log("Cliente conectado");
    pythonSocket = socket;
    socket.on("user_state", async (data) => {
        console.log("Recebido do Python:", data);
        let freelas = await quote_1.Freelas.start(data);
        await freelas.run();
        console.log("Finalizad! Desconectando...");
        socket.emit("execute_action", {
            action: "disconnect",
            message: "",
        });
    });
});
function send_message(message, to) {
    let final_message = { text: message, id: to };
    if (pythonSocket) {
        pythonSocket.emit("execute_action", {
            action: "send_message",
            message: final_message,
        });
    }
}
server.listen(4000, () => console.log("Socket.IO rodando na porta 4000"));
