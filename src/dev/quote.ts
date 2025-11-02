import { connect, PageWithCursor } from "puppeteer-real-browser";
import { Browser, ElementHandle } from "rebrowser-puppeteer-core";
import { readFile, writeFile } from "fs/promises";
import { send_message } from "./socket";
import { EOL as line_break } from "os";

type DataType = {
  type: string;
  quote?: string;
  duration?: string;
  pattern: string;
  question?: string;
};

type ParamType = {
  id: string;
  url: string;
  state: string | null;
  data: DataType;
};

export class Freelas {
  browser: Browser;
  page: PageWithCursor;
  //   config: ConfigType;
  data: ParamType;

  constructor(browser: Browser, page: PageWithCursor, data: ParamType) {
    this.browser = browser;
    this.page = page;
    this.data = data;
  }

  delay = (ms: number) => {
    return new Promise((resolve) => setInterval(resolve, ms));
  };

  async waitClickRedirect(selector?: string, element?: ElementHandle<Element>) {
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
    } else if (element) {
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
    } else {
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
    await writeFile("cookies.json", JSON.stringify(cookies, null, 2));

    console.log("Usuário Logado!!");
  }

  async waitForModal(timeout = 3000): Promise<boolean> {
    try {
      await this.page.waitForFunction(
        () => document.body.classList.contains("modal-open"),
        { timeout }
      );
      console.log("Modal apareceu");
      return true; // Modal apareceu
    } catch {
      console.log("Modal não apareceu");
      return false; // Timeout sem modal
    }
  }

  async fill_form(formated_msg: string) {
    if (this.data.data.type == "proposta") {
      await this.page.locator("#oferta").fill(this.data.data.quote ?? "");
      await this.page
        .locator("#duracao-estimada")
        .fill(this.data.data.duration ?? "");
      await this.delay(1000);

      await this.page.locator("#proposta").fill(formated_msg);
      await this.delay(1000);

      await this.waitClickRedirect("#btnConcluirEnvioProposta");
    } else if (this.data.data.type == "pergunta") {
      await this.page.locator("#mensagem-pergunta").fill(formated_msg);
      await this.delay(1000);

      await this.waitClickRedirect("#btnEnviarPergunta");
    }
  }

  format_message(client_name: string, message: string, question: string = "") {
    const formated = message
      .replaceAll("{cliente}", client_name)
      .replaceAll("{line}", line_break)
      .replace("{duvida}", question);

    return formated;
  }

  async run() {
    await this.page.goto("https://www.99freelas.com.br", {
      waitUntil: "load",
    });

    send_message("Abrindo conta...", this.data.id);

    // //Garante que o usuário esteja logado
    const logged = await this.isLogged();
    logged ? [] : await this.doLogin();

    console.log(this.data);

    send_message("Abrindo página do serviço...", this.data.id);
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
      const formated_message = this.format_message(
        first_name,
        this.data.data.pattern
      );

      await this.waitClickRedirect("a ::-p-text(Enviar proposta)");

      send_message("Preenchendo dados...", this.data.id);
      await this.fill_form(formated_message);
      send_message("✅ Proposta enviada com sucesso ✅", this.data.id);

      //------ FLUXO PARA PERGUNTAS
    } else if (this.data.data.type == "pergunta") {
      const formated_message = this.format_message(
        first_name,
        this.data.data.pattern,
        this.data.data.question
      );

      await this.waitClickRedirect("a ::-p-text(Faça uma pergunta)");

      send_message("Preenchendo dados...", this.data.id);
      await this.fill_form(formated_message);

      send_message("✅ Pergunta enviada com sucesso ✅", this.data.id);
    }

    await this.browser.close();
  }

  static async start(data: ParamType) {
    //Inicia o bot
    const { browser, page } = await connect({
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

    const cookies = JSON.parse(await readFile("cookies.json", "utf-8"));
    await browser.setCookie(...cookies);

    // const configs = JSON.parse(await readFile("config.json", "utf-8"));
    // console.log("Configurações: ", configs);

    return new Freelas(browser, page, data);
  }
}

// (async () => {
//   const bot = await Freelas.start();
//   bot.run();
// })();
