// Horas encendido por equipo en el rango del dashboard. Bara_Cool = compresor;
// build-dashboard.py lo reemplaza por Bara_Fan para el panel del ventilador.
// El estado llega como 0 o 100 (%): se integra en el tiempo y se divide por 100.
// El escalado va despues de integral(): map antes de integral devuelve 400.
from(bucket: "aires")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "liebert_ac" and r._field == "value_num" and r.item_name == "Bara_Cool")
  |> group(columns: ["equipo"])
  |> integral(unit: 1h)
  |> map(fn: (r) => ({r with _value: r._value / 100.0}))
  |> group()
  |> keep(columns: ["equipo", "_value"])
  |> sort(columns: ["equipo"])
