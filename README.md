# Monitoreo Liebert / Emerson

Stack local de demostración con Telegraf, InfluxDB 2 y Grafana. Mientras no haya
acceso a las unidades reales, Telegraf relee los snapshots de `datasets/` cada
10 segundos para generar una serie temporal de prueba.

## Levantar el stack

Crear primero el archivo local de configuración a partir del ejemplo:

```powershell
Copy-Item .env.example .env
```

Editar `.env` y reemplazar todas las credenciales de muestra. Luego levantar los
servicios:

```powershell
docker compose up -d
```

Abrir Grafana en <http://localhost:3000>.

- Usuario y contraseña: los valores `GRAFANA_ADMIN_USER` y
  `GRAFANA_ADMIN_PASSWORD` configurados en `.env`.
- Dashboard: **Aires acondicionados / Liebert · Estado general**

InfluxDB queda disponible en <http://localhost:8086> con las credenciales
configuradas en `.env`.

## Verificar y detener

```powershell
docker compose ps
docker compose logs -f telegraf
docker compose down
```

Los volúmenes conservan el histórico entre reinicios. Para borrar solamente los
datos demo y empezar de cero:

```powershell
docker compose down -v
```

## Pasar a los equipos reales

Cuando el stack se ejecute dentro de la red `192.168.6.0/24`, reemplazar en el
servicio `telegraf` el montaje de `telegraf-demo.conf` por `telegraf.conf`. Las
credenciales de `.env.example` son exclusivamente demostrativas y nunca deben
usarse en producción.

> InfluxDB utiliza las variables `DOCKER_INFLUXDB_INIT_*` solamente durante la
> creación inicial del volumen. Cambiar `.env` no modifica las credenciales de
> un volumen que ya fue inicializado.
