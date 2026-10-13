"""Avisa por Telegram cuando la temperatura de retorno de un equipo sale de rango.

Lee el ultimo valor de InfluxDB cada NOTIFY_INTERVAL segundos. Avisa al salir de
rango, recuerda cada NOTIFY_REPEAT_MIN minutos mientras siga fuera, y avisa al
volver a la normalidad (con histeresis para evitar avisos intermitentes).
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

from influxdb_client import InfluxDBClient

EQUIPOS = ["aa1", "aa2", "aa3", "system"]
BUCKET = os.environ["INFLUX_BUCKET"]
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
ITEM = os.environ.get("NOTIFY_ITEM", "LocTemp")
INTERVAL = int(os.environ.get("NOTIFY_INTERVAL", "60"))
REPEAT_MIN = int(os.environ.get("NOTIFY_REPEAT_MIN", "60"))  # 0 = no repetir
HYSTERESIS = float(os.environ.get("TEMP_HYSTERESIS", "1.0"))
WINDOW = os.environ.get("API_LATEST_WINDOW", "10m")

client = InfluxDBClient(
    url=os.environ.get("INFLUX_URL", "http://influxdb:8086"),
    token=os.environ["INFLUX_TOKEN"],
    org=os.environ["INFLUX_ORG"],
)
query_api = client.query_api()


def limit(kind: str, equipo: str) -> float:
    """TEMP_HIGH_AA1 pisa a TEMP_HIGH (idem TEMP_LOW)."""
    value = os.environ.get(f"TEMP_{kind}_{equipo.upper()}") or os.environ.get(f"TEMP_{kind}")
    return float(value)


def log(msg: str) -> None:
    print(time.strftime("%Y-%m-%d %H:%M:%S"), msg, flush=True)


def send(text: str) -> None:
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text}).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=15) as r:
            json.load(r)
    except Exception as e:  # no tumbar el servicio por un fallo de red
        # No loguear la excepcion completa: la URL incluye el token del bot.
        log(f"Error enviando a Telegram: {type(e).__name__}")


def read_temp(equipo: str) -> float | None:
    flux = f'''
from(bucket: "{BUCKET}")
  |> range(start: -{WINDOW})
  |> filter(fn: (r) => r._measurement == "liebert_ac" and r.equipo == "{equipo}"
      and r.item_name == "{ITEM}" and r._field == "value_num")
  |> last()
'''
    values = [r.get_value() for t in query_api.query(flux) for r in t.records]
    return float(values[0]) if values else None


def evaluate(equipo: str, temp: float, state: str) -> str:
    """Nuevo estado (ok/high/low) con histeresis al volver a rango."""
    high, low = limit("HIGH", equipo), limit("LOW", equipo)
    if temp > high:
        return "high"
    if temp < low:
        return "low"
    if state == "high" and temp > high - HYSTERESIS:
        return "high"
    if state == "low" and temp < low + HYSTERESIS:
        return "low"
    return "ok"


def main() -> None:
    state = {e: "ok" for e in EQUIPOS}
    last_alert = {e: 0.0 for e in EQUIPOS}
    log(f"Notificador activo: {ITEM} cada {INTERVAL}s, equipos {', '.join(EQUIPOS)}")
    while True:
        for equipo in EQUIPOS:
            try:
                temp = read_temp(equipo)
            except Exception as e:
                log(f"Error leyendo InfluxDB ({equipo}): {type(e).__name__}")
                continue
            if temp is None:
                continue  # sin datos recientes: no se puede evaluar
            name = equipo.upper()
            new = evaluate(equipo, temp, state[equipo])
            now = time.time()
            if new != state[equipo]:
                if new == "ok":
                    send(f"✅ {name}: temperatura normalizada ({temp:.1f} °C)")
                else:
                    send(alert_text(name, new, temp, equipo))
                    last_alert[equipo] = now
                state[equipo] = new
            elif new != "ok" and REPEAT_MIN and now - last_alert[equipo] >= REPEAT_MIN * 60:
                send("⏰ Sigue fuera de rango. " + alert_text(name, new, temp, equipo))
                last_alert[equipo] = now
        time.sleep(INTERVAL)


def alert_text(name: str, kind: str, temp: float, equipo: str) -> str:
    if kind == "high":
        return f"🔥 {name}: temperatura alta {temp:.1f} °C (límite {limit('HIGH', equipo):.1f} °C)"
    return f"🥶 {name}: temperatura baja {temp:.1f} °C (límite {limit('LOW', equipo):.1f} °C)"


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
