// Horas encendido por equipo en el rango del dashboard. Bara_Cool = compresor;
// build-dashboard.py lo reemplaza por Bara_Fan para el panel del ventilador.
// Estado 0/1 integrado en el tiempo: el resultado es "horas encendido".
from(bucket: "aires")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "liebert_ac" and r._field == "value_num" and r.item_name == "Bara_Cool")
  |> map(fn: (r) => ({r with _value: if r._value > 0.0 then 1.0 else 0.0}))
  |> group(columns: ["equipo"])
  |> sort(columns: ["_time"])
  |> integral(unit: 1h)
  |> group()
  |> keep(columns: ["equipo", "_value"])
  |> sort(columns: ["equipo"])
