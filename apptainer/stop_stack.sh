#!/usr/bin/env bash
set -euo pipefail

for name in tsms-chronograf tsms-kapacitor tsms-telegraf tsms-influxdb tsms-kafka; do
  if apptainer instance list | awk '{print $1}' | grep -qx "${name}"; then
    echo "[stop] ${name}"
    apptainer instance stop "${name}"
  else
    echo "[skip] ${name} not running"
  fi
done
