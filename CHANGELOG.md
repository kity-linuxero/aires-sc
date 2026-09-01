# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el proyecto utiliza [Versionado Semántico](https://semver.org/lang/es/). Mientras
el software permanezca en etapa de pre-release, las versiones pueden introducir
cambios incompatibles antes de alcanzar `1.0.0`.

## [Unreleased]

Los próximos cambios se documentarán en esta sección antes de asignarles una
versión.

## [0.1.0-alpha.1] - 2026-09-01

Primera pre-release funcional del sistema de monitoreo para unidades de aire
acondicionado Liebert / Emerson Network Power.

### Añadido

- Stack reproducible con Docker Compose compuesto por Telegraf, InfluxDB 2 y
  Grafana.
- Persistencia de datos y configuración mediante volúmenes Docker para InfluxDB
  y Grafana.
- Parser XML XPath de Telegraf para las respuestas `SimpleMonitoring` de tres
  unidades Liebert.
- Ingesta de estado, temperatura y humedad de retorno, setpoints y porcentajes
  de ventilador, compresor, freecooling, calefactor, deshumidificador y
  humidificador.
- Conservación simultánea del valor numérico, cuando existe, y del valor textual
  original informado por cada equipo.
- Modo `simulation` que relee periódicamente los snapshots XML incluidos en
  `datasets/` para desarrollar y probar sin acceso a los equipos físicos.
- Modo `real` que consulta por HTTP las direcciones configurables
  `LIEBERT_AA1_IP`, `LIEBERT_AA2_IP` y `LIEBERT_AA3_IP`.
- Selector validado mediante `MONITORING_MODE=simulation|real`, sin necesidad de
  recrear InfluxDB ni Grafana al cambiar de modo.
- Datasource de InfluxDB y dashboard de Grafana aprovisionados automáticamente.
- Gauges principales con temperatura y humedad promedio calculadas a partir de
  la última muestra vigente de cada unidad, excluyendo unidades sin valor.
- Paneles numéricos con los últimos valores individuales de temperatura y
  humedad por equipo.
- Gráficos históricos de temperatura y humedad comparados con sus respectivos
  setpoints.
- Visualización de actuadores actuales y estado compacto de las unidades.
- Actualización automática del dashboard cada 10 segundos y selector temporal
  para explorar el histórico.
- Archivo `.env.example` y documentación de instalación, operación, cambio de
  modo y reinicialización del stack.
- Configuración de finales de línea para que los scripts shell funcionen al
  clonar el repositorio tanto en Windows como en Linux.

### Seguridad

- Credenciales y tokens extraídos de Docker Compose y almacenados exclusivamente
  en el archivo local `.env`, excluido del control de versiones.
- Valores demostrativos separados en `.env.example` para evitar publicar
  secretos reales.
- Validación de variables obligatorias en Docker Compose para impedir arranques
  accidentales con credenciales vacías.

### Limitaciones conocidas

- El modo `real` y el parser fueron validados contra snapshots representativos,
  pero esta pre-release aún no fue probada de punta a punta contra las unidades
  físicas desde el entorno de despliegue definitivo.
- El modo `simulation` repite snapshots estáticos; por lo tanto, sus series
  históricas permanecen constantes salvo que se modifiquen los datasets.
- La temperatura de suministro recibida como `---` se conserva como texto, pero
  no genera un valor numérico graficable.

[Unreleased]: https://github.com/kity-linuxero/aires-sc/compare/v0.1.0-alpha.1...HEAD
[0.1.0-alpha.1]: https://github.com/kity-linuxero/aires-sc/releases/tag/v0.1.0-alpha.1
