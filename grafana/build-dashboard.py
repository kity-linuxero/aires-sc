"""Inserta grafana/src/*.{flux,hbs,css} en los paneles de liebert-overview.json."""
import json, pathlib

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
