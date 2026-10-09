// Cada serie ocupa su propio carril (0 a 5) para que no se superpongan.
// Encendido = carril + 0.7, apagado = carril. Los mappings del panel traducen el valor.
from(bucket: "aires")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "liebert_ac" and r._field == "value_num" and contains(value: r.item_name, set: ["Bara_Cool", "Bara_Fan"]))
  |> map(fn: (r) => {
      unit = if r.equipo == "aa1" then 0 else if r.equipo == "aa2" then 1 else 2
      kind = if r.item_name == "Bara_Cool" then 0 else 1
      lane = float(v: 5 - (unit * 2 + kind))
      return {r with
        _value: if r._value > 0.0 then lane + 0.7 else lane,
        serie: r.equipo + " · " + (if kind == 0 then "Compresor" else "Ventilador")
      }
  })
  |> group(columns: ["serie"])
  |> aggregateWindow(every: v.windowPeriod, fn: max, createEmpty: false)
  |> keep(columns: ["_time", "_value", "serie"])
  |> sort(columns: ["serie"])
