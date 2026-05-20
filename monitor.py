import requests
import os
import smtplib
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

URL = "https://www.cifrasonline.com.ar/indice-cac/"
STATE_FILE = "last_state.txt"

def get_current_state():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(URL, headers=headers, timeout=20)
    soup = BeautifulSoup(response.text, "html.parser")

    drive_links = [
        a["href"] for a in soup.find_all("a", href=True)
        if "drive.google.com/file" in a["href"]
    ]

    issuu_src = [
        iframe["src"] for iframe in soup.find_all("iframe", src=True)
        if "issuu.com" in iframe["src"]
    ]

    issuu_href = [
        a["href"] for a in soup.find_all("a", href=True)
        if "issuu.com" in a["href"]
    ]

    all_items = sorted(set(drive_links + issuu_src + issuu_href))
    state = "|".join(all_items)
    return state, drive_links

def send_email(drive_links):
    sender    = os.environ["GMAIL_USER"]
    password  = os.environ["GMAIL_PASS"]
    recipient = os.environ["NOTIFY_EMAIL"]

    if drive_links:
        links_text = "\n".join(set(drive_links))
    else:
        links_text = "(no se encontró link directo, entrá a la página)"

    body = (
        f"Se publicó el nuevo Índice CAC.\n\n"
        f"Descargá el informe:\n{links_text}\n\n"
        f"O entrá directamente:\n{URL}"
    )

    msg = MIMEText(body)
    msg["Subject"] = "Nuevo Índice CAC publicado"
    msg["From"]    = sender
    msg["To"]      = recipient

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())

    print("Mail enviado correctamente.")

# --- LÓGICA PRINCIPAL ---

current_state, drive_links = get_current_state()

if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        last_state = f.read().strip()

    if current_state != last_state:
        print("Cambio detectado. Mandando mail...")
        send_email(drive_links)
    else:
        print("Sin cambios.")
else:
    print("Primera ejecucion. Guardando estado inicial.")

with open(STATE_FILE, "w") as f:
    f.write(current_state)
