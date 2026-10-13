"""Prueba de conexion con el bot de Telegram.

Uso (desde la raiz del repo):
    python notifier/telegram_test.py            # verifica el bot y envia un mensaje de prueba
    python notifier/telegram_test.py --updates  # lista los chats que ve el bot (para hallar el group id)
    python notifier/telegram_test.py --alert-test [--temp 27 --limit 25]  # alerta de temperatura alta simulada

Lee TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID del entorno o del .env de la raiz.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def load_env() -> None:
    path = Path(__file__).resolve().parent.parent / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def call(token: str, method: str, params: dict | None = None) -> dict:
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = urllib.parse.urlencode(params).encode() if params else None
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=15) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = json.load(e)
        sys.exit(f"Telegram {method} fallo ({e.code}): {body.get('description')}")
    except urllib.error.URLError as e:
        sys.exit(f"No se pudo conectar a Telegram: {e.reason}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--updates", action="store_true", help="listar chats vistos por el bot")
    parser.add_argument("--alert-test", action="store_true", help="enviar una alerta de temperatura alta simulada")
    parser.add_argument("--temp", type=float, default=27.0, help="temperatura simulada (con --alert-test)")
    parser.add_argument("--limit", type=float, default=25.0, help="limite simulado (con --alert-test)")
    args = parser.parse_args()

    load_env()
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token:
        sys.exit("Falta TELEGRAM_BOT_TOKEN (en .env o en el entorno).")

    me = call(token, "getMe")["result"]
    print(f"Bot OK: @{me['username']} ({me['first_name']})")

    if args.updates:
        seen = {}
        for u in call(token, "getUpdates")["result"]:
            msg = u.get("message") or u.get("channel_post") or u.get("my_chat_member", {})
            chat = msg.get("chat")
            if chat:
                seen[chat["id"]] = chat.get("title") or chat.get("username") or chat.get("first_name")
        if not seen:
            print("Sin chats. Escribi un mensaje en el grupo (o mencionando al bot) y reintenta.")
        for cid, name in seen.items():
            print(f"  chat_id={cid}  {name}")
        return

    if not chat_id:
        sys.exit("Falta TELEGRAM_CHAT_ID. Ejecuta con --updates para encontrarlo.")
    text = "Mensaje de prueba"
    if args.alert_test:
        text = (f"🔥 AA1: temperatura alta {args.temp:.1f} °C (límite {args.limit:.1f} °C)\n"
                "ESTO ES UNA PRUEBA - NO HAY NINGUNA ALARMA REAL")
    res = call(token, "sendMessage", {"chat_id": chat_id, "text": text})
    print(f"Mensaje enviado (message_id={res['result']['message_id']}) a chat {chat_id}")


if __name__ == "__main__":
    main()
