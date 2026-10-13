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

# Dashboard para TV: sin el historial de funcionamiento y con todo en una pantalla (24 x 27 filas;
# entra en 1080 px de alto en modo kiosco, sin la barra de controles).
# Misma fuente de paneles/consultas que el dashboard principal; solo cambia la distribucion.
tv = copy.deepcopy(dash)
tv["title"] = "Liebert · TV"
tv["uid"] = "liebert-tv"
tv["tags"] = tv["tags"] + ["tv"]
tv["timepicker"] = {"hidden": True}  # sin selector de tiempo ni refresh: libera la barra superior
tv["panels"] = [p for p in tv["panels"] if p["id"] != 9]
layout = {  # id: (x, y, w, h)
    2: (0, 0, 5, 8), 3: (5, 0, 5, 8), 10: (10, 0, 7, 8), 11: (17, 0, 7, 8),
    7: (0, 8, 24, 9),
    4: (0, 17, 12, 10), 5: (12, 17, 12, 10),
}
for p in tv["panels"]:
    x, y, w, h = layout[p["id"]]
    p["gridPos"] = {"x": x, "y": y, "w": w, "h": h}
for pid in (4, 5):  # leyenda a la derecha y mas corta para que no recorte series
    legend = next(p for p in tv["panels"] if p["id"] == pid)["options"]["legend"]
    legend["placement"] = "right"
    legend["calcs"] = ["lastNotNull", "mean"]
units = next(p for p in tv["panels"] if p["id"] == 7)
units["options"]["styles"] += "\n" + (root / "src/units-tv.css").read_text(encoding="utf-8")
(root / "dashboards" / "liebert-tv.json").write_text(
    json.dumps(tv, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
