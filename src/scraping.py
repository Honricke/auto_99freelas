import requests
from bs4 import BeautifulSoup
import json
import os
from time import sleep
from datetime import datetime, timedelta


def scrap_projects(categoria, telebot):
    current_page = 1
    all_projects = []

    # Carrega projetos recentes salvos anteriormente (se existir)
    last_projects = []
    if os.path.exists("recent_projects.json"):
        with open("recent_projects.json", "r", encoding="utf-8") as f:
            last_projects = json.load(f)

    while current_page <= 3:  # exemplo: busca até a 3ª página
        projects = get_projects(current_page, categoria)

        if not projects:
            break

        for project in projects:
            if "destaque" in project.get("class", []):
                continue

            title_tag = project.select_one(".title a")
            desc_tag = project.select_one(".description")
            datetime_tag = project.select_one("b.datetime")
            client_tag = project.select_one(".client")

            title = title_tag.text.strip() if title_tag else ""
            client = client_tag.text.strip() if client_tag else ""
            link = (
                f"https://www.99freelas.com.br{title_tag['href']}" if title_tag else ""
            )
            desc = desc_tag.text.strip() if desc_tag else ""

            # Pega as informações

            def format_time_difference(timestamp_str):
                """Formata a diferença entre agora e o timestamp em minutos ou horas."""
                if not timestamp_str:
                    return "N/A"

                timestamp = int(timestamp_str) / 1000
                date = datetime.fromtimestamp(timestamp)
                now = datetime.now()
                diff = abs(now - date)

                if diff < timedelta(hours=1):
                    minutes = int(diff.total_seconds() // 60)
                    return f"{minutes} minuto(s)"
                else:
                    hours = int(diff.total_seconds() // 3600)
                    return f"{hours} hora(s)"

            published_text = ""
            restante_text = ""

            if datetime_tag and datetime_tag.get("cp-datetime"):
                published = datetime.fromtimestamp(
                    int(datetime_tag["cp-datetime"]) / 1000
                )
                published_text = f"Publicado: {published.strftime('%H:%M %d/%m')}"

                restante_diff = format_time_difference(datetime_tag["cp-datetime"])
                restante_text = f"Passou: {restante_diff}"

            information = f"{published_text}\n{restante_text}"

            # Se já vimos esse projeto antes, para o scraping
            if any(p["link"] == link for p in last_projects):
                print("Projetos já mapeados até este ponto. Encerrando.")
                current_page = 100
                break

            all_projects.append(
                {
                    "title": title,
                    "link": link,
                    "description": desc,
                    "information": information,
                    "client": client,
                }
            )

        current_page += 1

    print(f"Total new projects scraped: {len(all_projects)}")

    all_projects = all_projects[::-1]

    send_all_projects(all_projects, telebot)

    save_projects(all_projects)

    return all_projects


def clean_text(text):
    return text.replace("\t", " ").replace("  ", " ").strip()


def get_projects(current_page, categoria):
    base_url = ""
    url = ""

    if categoria:
        base_url = (
            "https://www.99freelas.com.br/projects?categoria=web-mobile-e-software"
        )
        url = f"{base_url}&page={current_page}"
    else:
        base_url = "https://www.99freelas.com.br/projects"
        url = f"{base_url}?page={current_page}"

    print(f"Scraping page {current_page}...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to load page {current_page}")
        return False

    soup = BeautifulSoup(response.text, "html.parser")
    projects = soup.select(".result-item")

    return projects


def save_projects(all_projects):
    recent_projects = []
    if os.path.exists("recent_projects.json"):
        with open("recent_projects.json", "r", encoding="utf-8") as f:
            recent_projects = json.load(f)

    for project in all_projects:
        if not any(p["link"] == project["link"] for p in recent_projects):
            recent_projects.insert(0, project)  # insere no início

    # Mantém apenas os 5 projetos mais recentes
    recent_projects = recent_projects[:5]

    # Salva de volta no JSON
    with open("recent_projects.json", "w", encoding="utf-8") as f:
        json.dump(recent_projects, f, indent=2, ensure_ascii=False)

    return all_projects


def send_all_projects(all_projects, telebot):
    for index, project in enumerate(all_projects):
        title = clean_text(project["title"])
        # client = clean_text(project["client"])
        description = project["description"]
        information = clean_text(project["information"])

        message = f"""
📌 <b>{title}</b>

📝 <b>Descrição:</b>
{description}

ℹ️ <b>Informações:</b>
{information}

🔗 <a href="{project["link"]}">[Ver projeto]</a>
"""

        telebot.send_message(message)
        print(f"{title} enviado! | Atual: {index+1}")
        sleep(0.5)  # pausa menor, mais eficiente

    print("Todas as mensagens enviadas!\n")
