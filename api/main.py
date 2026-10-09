"""API de solo lectura sobre los datos que Telegraf guarda en InfluxDB."""
import os
import re
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from influxdb_client import InfluxDBClient

EQUIPOS = ["aa1", "aa2", "aa3", "system"]
BUCKET = os.environ["INFLUX_BUCKET"]
API_KEY = os.environ.get("API_KEY", "")
# Ventana en la que se busca el ultimo valor: si un equipo no responde, queda vacio.
LATEST_WINDOW = os.environ.get("API_LATEST_WINDOW", "10m")

client = InfluxDBClient(
    url=os.environ.get("INFLUX_URL", "http://influxdb:8086"),
    token=os.environ["INFLUX_TOKEN"],
    org=os.environ["INFLUX_ORG"],
)
query_api = client.query_api()

DURATION = re.compile(r"^\d+(s|m|h|d|w)$")


def require_key(x_api_key: str = Header(default="")):
    if API_KEY and not secrets.compare_digest(x_api_key, API_KEY):
        raise HTTPException(401, "API key invalida o ausente (header X-API-Key)")


app = FastAPI(title="Aires IPLyC API", dependencies=[Depends(require_key)])


def check_equipo(equipo: str) -> str:
    if equipo not in EQUIPOS:
        raise HTTPException(404, f"Equipo desconocido; validos: {', '.join(EQUIPOS)}")
    return equipo


def check_duration(value: str) -> str:
    if not DURATION.match(value):
        raise HTTPException(422, "Duracion invalida; ejemplos: 30m, 3h, 7d")
    return value


def latest(equipo: str) -> dict:
    flux = f'''
from(bucket: "{BUCKET}")
  |> range(start: -{LATEST_WINDOW})
  |> filter(fn: (r) => r._measurement == "liebert_ac" and r.equipo == "{equipo}")
  |> last()
'''
    by_item, ts, ip = {}, None, None
    for table in query_api.query(flux):
        for r in table.records:
            ts = max(ts, r.get_time()) if ts else r.get_time()
            ip = r.values.get("ip", ip)
            # Influx no guarda tags vacios (p. ej. unit), asi que no se puede hacer pivot por tag.
            item = by_item.setdefault(r.values.get("item_id"), {
                "id": r.values.get("item_id"),
                "name": r.values.get("item_name"),
                "label": r.values.get("label"),
                "unit": r.values.get("unit") or "",
                "value": None,
                "text": None,
            })
            item["value" if r.get_field() == "value_num" else "text"] = r.get_value()
    items = list(by_item.values())
    items.sort(key=lambda i: int(i["id"] or 0))
    return {
        "equipo": equipo,
        "ip": ip,
        "online": bool(items),
        "timestamp": ts.isoformat() if ts else None,
        "items": items,
    }


@app.get("/health", dependencies=[])
def health():
    return {"status": "ok"}


@app.get("/api/equipos")
def listar():
    return EQUIPOS


@app.get("/api/data")
def todo():
    """Ultimo valor de todos los equipos."""
    return {e: latest(e) for e in EQUIPOS}


@app.get("/api/equipos/{equipo}")
def uno(equipo: str = Depends(check_equipo)):
    return latest(equipo)


@app.get("/api/equipos/{equipo}/history")
def historial(
    equipo: str = Depends(check_equipo),
    item: str = Query(..., description="item_name, ej. LocTemp"),
    range: str = Query("3h", description="ventana, ej. 30m, 3h, 7d"),
    every: str = Query("1m", description="agregacion (media), ej. 1m, 15m"),
):
    if not re.fullmatch(r"\w+", item):
        raise HTTPException(422, "item invalido")
    check_duration(range)
    check_duration(every)
    flux = f'''
from(bucket: "{BUCKET}")
  |> range(start: -{range})
  |> filter(fn: (r) => r._measurement == "liebert_ac" and r.equipo == "{equipo}"
      and r.item_name == "{item}" and r._field == "value_num")
  |> aggregateWindow(every: {every}, fn: mean, createEmpty: false)
'''
    points = [
        {"time": r.get_time().isoformat(), "value": r.get_value()}
        for table in query_api.query(flux) for r in table.records
    ]
    return {"equipo": equipo, "item": item, "points": points}
