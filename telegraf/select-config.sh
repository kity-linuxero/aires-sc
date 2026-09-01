#!/bin/sh
set -eu

case "${MONITORING_MODE:-simulation}" in
  simulation)
    telegraf_config="/etc/telegraf/telegraf-demo.conf"
    ;;
  real)
    telegraf_config="/etc/telegraf/telegraf-real.conf"
    ;;
  *)
    echo "MONITORING_MODE debe ser 'simulation' o 'real'; valor recibido: '${MONITORING_MODE}'" >&2
    exit 1
    ;;
esac

echo "Iniciando Telegraf en modo ${MONITORING_MODE:-simulation}"
exec telegraf --config "$telegraf_config"
