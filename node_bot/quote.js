"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Freelas = void 0;
const puppeteer_real_browser_1 = require("puppeteer-real-browser");
const promises_1 = require("fs/promises");
const socket_1 = require("./socket");
const os_1 = require("os");
class Freelas {
    browser;
    page;
    //   config: ConfigType;
    data;
    constructor(browser, page, data) {
        this.browser = browser;
        this.page = page;
        this.data = data;
    }
    delay = (ms) => {
        return new Promise((resolve) => setInterval(resolve, ms));
    };
    async waitClickRedirect(selector, element) {
        const navigationPromise = this.page
            .waitForNavigation({
            waitUntil: "load",
            timeout: 3000,
        })
            .catch(() => null);
        if (selector) {
            const [response] = await Promise.all([
                navigationPromise,
                this.page.locator(selector).click(),
            ]);
        }
        else if (element) {
            const [response] = await Promise.all([
                navigationPromise,
                element.click(),
            ]);
        }
    }
    async isLogged() {
        //Verifica se está logado
        const contaEl = await this.page.$(".user-logged-box");
        if (contaEl) {
            console.log("Usuário já estava logado!");
            return true;
        }
        else {
            console.log("Usuário não estava logado!");
            return false;
        }
    }
    async doLogin() {
        //Efetua o login
        console.log("Iniciando Login!");
        await this.page.goto("https://www.99freelas.com.br/login", {
            waitUntil: "load",
        });
        await this.delay(20000);
        const cookies = await this.browser.cookies();
        await (0, promises_1.writeFile)("cookies.json", JSON.stringify(cookies, null, 2));
        console.log("Usuário Logado!!");
    }
    async waitForModal(timeout = 3000) {
        try {
            await this.page.waitForFunction(() => document.body.classList.contains("modal-open"), { timeout });
            console.log("Modal apareceu");
            return true; // Modal apareceu
        }
        catch {
            console.log("Modal não apareceu");
            return false; // Timeout sem modal
        }
    }
    async fill_form(formated_msg) {
        if (this.data.data.type == "proposta") {
            await this.page.locator("#oferta").fill(this.data.data.quote ?? "");
            await this.page
                .locator("#duracao-estimada")
                .fill(this.data.data.duration ?? "");
            await this.delay(1000);
            await this.page.locator("#proposta").fill(formated_msg);
            await this.delay(1000);
            await this.waitClickRedirect("#btnConcluirEnvioProposta");
        }
        else if (this.data.data.type == "pergunta") {
            await this.page.locator("#mensagem-pergunta").fill(formated_msg);
            await this.delay(1000);
            await this.waitClickRedirect("#btnEnviarPergunta");
        }
    }
    format_message(client_name, message, question = "") {
        const formated = message
            .replaceAll("{cliente}", client_name)
            .replaceAll("{line}", os_1.EOL)
            .replace("{duvida}", question);
        return formated;
    }
    async run() {
        await this.page.goto("https://www.99freelas.com.br", {
            waitUntil: "load",
        });
        (0, socket_1.send_message)("Abrindo conta...", this.data.id);
        // //Garante que o usuário esteja logado
        const logged = await this.isLogged();
        logged ? [] : await this.doLogin();
        console.log(this.data);
        (0, socket_1.send_message)("Abrindo página do serviço...", this.data.id);
        await this.page.goto(this.data.url, {
            waitUntil: "load",
        });
        const client_name = await this.page
            .locator(".info-usuario-nome")
            .map((button) => button.textContent)
            .wait();
        const first_name = client_name?.split(" ")[0].trim() ?? "";
        //------ FLUXO PARA PROPOSTA
        if (this.data.data.type == "proposta") {
            const formated_message = this.format_message(first_name, this.data.data.pattern);
            await this.waitClickRedirect("a ::-p-text(Enviar proposta)");
            (0, socket_1.send_message)("Preenchendo dados...", this.data.id);
            await this.fill_form(formated_message);
            (0, socket_1.send_message)("✅ Proposta enviada com sucesso ✅", this.data.id);
            //------ FLUXO PARA PERGUNTAS
        }
        else if (this.data.data.type == "pergunta") {
            const formated_message = this.format_message(first_name, this.data.data.pattern, this.data.data.question);
            await this.waitClickRedirect("a ::-p-text(Faça uma pergunta)");
            (0, socket_1.send_message)("Preenchendo dados...", this.data.id);
            await this.fill_form(formated_message);
            (0, socket_1.send_message)("✅ Pergunta enviada com sucesso ✅", this.data.id);
        }
        await this.browser.close();
    }
    static async start(data) {
        //Inicia o bot
        const { browser, page } = await (0, puppeteer_real_browser_1.connect)({
            headless: false,
            args: [],
            customConfig: {},
            turnstile: true,
            connectOption: { defaultViewport: null },
            disableXvfb: false,
            ignoreAllFlags: false,
            // proxy:{
            //     host:'<proxy-host>',
            //     port:'<proxy-port>',
            //     username:'<proxy-username>',
            //     password:'<proxy-password>'
            // }
        });
        const cookies = JSON.parse(await (0, promises_1.readFile)("cookies.json", "utf-8"));
        await browser.setCookie(...cookies);
        // const configs = JSON.parse(await readFile("config.json", "utf-8"));
        // console.log("Configurações: ", configs);
        return new Freelas(browser, page, data);
    }
}
exports.Freelas = Freelas;
// (async () => {
//   const bot = await Freelas.start();
//   bot.run();
// })();
