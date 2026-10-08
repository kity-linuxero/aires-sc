import "math"

pct = (v) => if exists v then string(v: int(v: math.round(x: v))) + " %" else "—"
cls = (v) => if exists v then (if v > 0.0 then "on" else "off") else "na"
num = (v, unit) => if exists v then string(v: math.round(x: v * 10.0) / 10.0) + unit else "—"

base = from(bucket: "aires")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "liebert_ac")

nums = base
  |> filter(fn: (r) => r._field == "value_num" and contains(value: r.item_name, set: ["LocTemp", "HT_Humi", "Bara_Fan", "Bara_Cool", "Bara_Deh", "Bara_Hum"]))
  |> group(columns: ["equipo", "item_name"])
  |> last()
  |> keep(columns: ["equipo", "item_name", "_value"])

state = base
  |> filter(fn: (r) => r._field == "value_str" and r.item_name == "SinglState")
  |> group(columns: ["equipo", "item_name"])
  |> last()
  |> map(fn: (r) => ({equipo: r.equipo, item_name: r.item_name, _value: if r._value == "Alarm On" then 2.0 else if r._value == "Warning On" then 1.0 else 0.0}))

union(tables: [nums, state])
  |> group()
  |> pivot(rowKey: ["equipo"], columnKey: ["item_name"], valueColumn: "_value")
  |> map(fn: (r) => ({
      equipo: r.equipo,
      st_cls: if not exists r.SinglState then "na" else if r.SinglState > 0.0 then "wn" else "ok",
      st_icon: if exists r.SinglState and r.SinglState > 0.0 then "ti-alert-triangle" else "ti-circle-check",
      st_txt: if not exists r.SinglState then "Sin dato" else if r.SinglState >= 2.0 then "Alarma activa" else if r.SinglState >= 1.0 then "Advertencia" else "Normal",
      t_txt: num(v: r.LocTemp, unit: " °C"),
      t_cls: if exists r.LocTemp and r.LocTemp >= 27.0 then "wn" else "",
      h_txt: num(v: r.HT_Humi, unit: " %"),
      h_cls: if exists r.HT_Humi and (r.HT_Humi < 30.0 or r.HT_Humi >= 65.0) then "wn" else "",
      fan_cls: cls(v: r.Bara_Fan), fan_txt: pct(v: r.Bara_Fan),
      cool_cls: cls(v: r.Bara_Cool), cool_txt: pct(v: r.Bara_Cool),
      deh_cls: cls(v: r.Bara_Deh), deh_txt: pct(v: r.Bara_Deh),
      hum_cls: cls(v: r.Bara_Hum), hum_txt: pct(v: r.Bara_Hum)
  }))
  |> sort(columns: ["equipo"])
