"""Inserta grafana/src/*.{flux,hbs,css} en los paneles de liebert-overview.json."""
import copy, json, pathlib

root = pathlib.Path(__file__).parent
path = root / "dashboards" / "liebert-overview.json"
dash = json.loads(path.read_text(encoding="utf-8"))
panel = next(p for p in dash["panels"] if p["id"] == 7)
panel["targets"][0]["query"] = (root / "src/units.flux").read_text(encoding="utf-8")
panel["options"]["content"] = (root / "src/units.hbs").read_text(encoding="utf-8")
panel["options"]["styles"] = (root / "src/units.css").read_text(encoding="utf-8")
history = next(p for p in dash["panels"] if p["id"] == 9)
history["targets"][0]["query"] = (root / "src/history.flux").read_text(encoding="utf-8")
usage = (root / "src/usage.flux").read_text(encoding="utf-8")
next(p for p in dash["panels"] if p["id"] == 10)["targets"][0]["query"] = usage
next(p for p in dash["panels"] if p["id"] == 11)["targets"][0]["query"] = usage.replace('item_name == "Bara_Cool"', 'item_name == "Bara_Fan"')
path.write_text(json.dumps(dash, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Dashboard para TV: sin el historial de funcionamiento y todo en una pantalla (24 x 21 filas).
# Entra en 1080 px de alto y tambien en 864 px (1080 con zoom 125 %), en modo kiosco y sin
# la barra de controles.
# Misma fuente de paneles/consultas que el dashboard principal; solo cambia la distribucion.
tv = copy.deepcopy(dash)
tv["title"] = "Liebert · TV"
tv["uid"] = "liebert-tv"
tv["tags"] = tv["tags"] + ["tv"]
tv["panels"] = [p for p in tv["panels"] if p["id"] != 9]
tv["timepicker"] = {"hidden": True}  # sin selector de tiempo ni refresh: libera la barra superior
layout = {  # id: (x, y, w, h)
    2: (0, 0, 5, 7), 3: (5, 0, 5, 7), 10: (10, 0, 7, 7), 11: (17, 0, 7, 7),
    7: (0, 7, 24, 6),
    4: (0, 13, 12, 8), 5: (12, 13, 12, 8),
}
for p in tv["panels"]:
    x, y, w, h = layout[p["id"]]
    p["gridPos"] = {"x": x, "y": y, "w": w, "h": h}
for pid in (4, 5):  # leyenda a la derecha y mas corta para que no recorte series
    legend = next(p for p in tv["panels"] if p["id"] == pid)["options"]["legend"]
    legend["placement"] = "right"
    legend["calcs"] = ["lastNotNull", "mean"]
# Temperatura y humedad: una serie por aire y un unico setpoint (es el mismo en los tres).
# La consulta B agrupa por item_name para promediar el setpoint de todos los aires.
AIRE_COLORS = {"aa1": "#5794F2", "aa2": "#FF9830", "aa3": "#73BF69"}  # igual que las tortas


def series_query(item, merge):
    lines = [
        'from(bucket: "aires")',
        "  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)",
        f'  |> filter(fn: (r) => r._measurement == "liebert_ac" and r._field == "value_num" and r.item_name == "{item}")',
    ]
    if merge:
        lines += ['  |> group(columns: ["item_name"])', '  |> sort(columns: ["_time"])']
    lines.append("  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)")
    return "\n".join(lines)


for pid, reading, setpoint in ((4, "LocTemp", "TempSet_ac"), (5, "HT_Humi", "HuSetActDi")):
    panel = next(p for p in tv["panels"] if p["id"] == pid)
    ds = panel["targets"][0]["datasource"]
    panel["targets"] = [
        {"datasource": ds, "query": series_query(reading, False), "refId": "A"},
        {"datasource": ds, "query": series_query(setpoint, True), "refId": "B"},
    ]
    panel["fieldConfig"]["defaults"]["displayName"] = "${__field.labels.equipo}"
    panel["fieldConfig"]["overrides"] = [
        {"matcher": {"id": "byName", "options": aire},
         "properties": [{"id": "color", "value": {"mode": "fixed", "fixedColor": color}}]}
        for aire, color in AIRE_COLORS.items()
    ] + [{"matcher": {"id": "byFrameRefID", "options": "B"}, "properties": [
        {"id": "displayName", "value": "Setpoint"},
        {"id": "color", "value": {"mode": "fixed", "fixedColor": "#C7D0D9"}},
        {"id": "custom.lineStyle", "value": {"dash": [10, 10], "fill": "dash"}},
        {"id": "custom.fillOpacity", "value": 0},
    ]}]
units = next(p for p in tv["panels"] if p["id"] == 7)
units["options"]["styles"] += "\n" + (root / "src/units-tv.css").read_text(encoding="utf-8")
(root / "dashboards" / "liebert-tv.json").write_text(
    json.dumps(tv, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
