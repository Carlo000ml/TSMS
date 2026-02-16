#!/usr/bin/env bash
set -euo pipefail  # -e= exit upon failure -u= treat unset variables as errors -o= fail if any of the pipe command fails

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"  # simply computing the project root dir
DATA_DIR="${ROOT_DIR}/.apptainer-data"

mkdir -p "${DATA_DIR}"/{kafka,influxdb,kapacitor}

start_instance() {
  local name="$1"  # assign first positional argument of the function to name
  local image="$2" # assign second positional argument of the function to name
  shift 2  # shift positional arguments by 2

  if apptainer instance list | awk '{print $1}' | grep -qx "${name}"; then  # retreive the running apptainer instances, if $name is already present then skip initialization
    echo "[skip] ${name} already running"
    return
  fi

  echo "[start] ${name}"
  apptainer instance start "$@" "docker://${image}" "${name}"   # the variable $@ indicates all the remaining positional arguments
}

# Kafka in KRaft mode (no ZooKeeper)
# Initializing configuration kafka variables, all these variables will be injected in the container
#as the prefix APPTAINERENV_*. The variables that will be injected in the container will not contain the prefix
export APPTAINERENV_KAFKA_NODE_ID=1   # single node kafka
export APPTAINERENV_KAFKA_PROCESS_ROLES=broker,controller    # single node acting both as broker and controller
export APPTAINERENV_KAFKA_CONTROLLER_QUORUM_VOTERS=1@localhost:9093  # port of the voter
export APPTAINERENV_KAFKA_LISTENERS=PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093  # kafka listen on 9092 for client and 903 for controller
export APPTAINERENV_KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092
export APPTAINERENV_KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=PLAINTEXT:PLAINTEXT,CONTROLLER:PLAINTEXT
export APPTAINERENV_KAFKA_INTER_BROKER_LISTENER_NAME=PLAINTEXT
export APPTAINERENV_KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER
export APPTAINERENV_KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1
export APPTAINERENV_KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=1
export APPTAINERENV_KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=1
export APPTAINERENV_KAFKA_LOG_DIRS=/var/lib/kafka/data
export APPTAINERENV_CLUSTER_ID=MkU3OEVBNTcwNTJENDM2Qk  # This is a random UUID
start_instance tsms-kafka confluentinc/cp-kafka:7.6.1 \
  --writable-tmpfs \
  --bind "${DATA_DIR}/kafka:/var/lib/kafka/data"
unset APPTAINERENV_KAFKA_NODE_ID APPTAINERENV_KAFKA_PROCESS_ROLES \
  APPTAINERENV_KAFKA_CONTROLLER_QUORUM_VOTERS APPTAINERENV_KAFKA_LISTENERS \
  APPTAINERENV_KAFKA_ADVERTISED_LISTENERS APPTAINERENV_KAFKA_LISTENER_SECURITY_PROTOCOL_MAP \
  APPTAINERENV_KAFKA_INTER_BROKER_LISTENER_NAME APPTAINERENV_KAFKA_CONTROLLER_LISTENER_NAMES \
  APPTAINERENV_KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR APPTAINERENV_KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR \
  APPTAINERENV_KAFKA_TRANSACTION_STATE_LOG_MIN_ISR APPTAINERENV_KAFKA_LOG_DIRS APPTAINERENV_CLUSTER_ID

# InfluxDB
export APPTAINERENV_DOCKER_INFLUXDB_INIT_MODE=setup
export APPTAINERENV_DOCKER_INFLUXDB_INIT_USERNAME=admin
export APPTAINERENV_DOCKER_INFLUXDB_INIT_PASSWORD=admin12345
export APPTAINERENV_DOCKER_INFLUXDB_INIT_ORG=tsms
export APPTAINERENV_DOCKER_INFLUXDB_INIT_BUCKET=tutorial
export APPTAINERENV_DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=supersecrettoken
start_instance tsms-influxdb influxdb:2.7 \
  --writable-tmpfs \
  --bind "${DATA_DIR}/influxdb:/var/lib/influxdb2"
unset APPTAINERENV_DOCKER_INFLUXDB_INIT_MODE APPTAINERENV_DOCKER_INFLUXDB_INIT_USERNAME \
  APPTAINERENV_DOCKER_INFLUXDB_INIT_PASSWORD APPTAINERENV_DOCKER_INFLUXDB_INIT_ORG \
  APPTAINERENV_DOCKER_INFLUXDB_INIT_BUCKET APPTAINERENV_DOCKER_INFLUXDB_INIT_ADMIN_TOKEN

# Telegraf
export APPTAINERENV_INFLUX_TOKEN=supersecrettoken
export APPTAINERENV_INFLUX_ORG=tsms
export APPTAINERENV_INFLUX_BUCKET=tutorial
start_instance tsms-telegraf telegraf:1.31 \
  --writable-tmpfs \
  --bind "${ROOT_DIR}/telegraf/telegraf.conf:/etc/telegraf/telegraf.conf:ro"
unset APPTAINERENV_INFLUX_TOKEN APPTAINERENV_INFLUX_ORG APPTAINERENV_INFLUX_BUCKET

# Kapacitor (remap port to avoid conflict with Kafka)
start_instance tsms-kapacitor kapacitor:1.7 \
  --writable-tmpfs \
  --bind "${ROOT_DIR}/kapacitor/kapacitor.conf:/etc/kapacitor/kapacitor.conf:ro" \
  --bind "${DATA_DIR}/kapacitor:/var/lib/kapacitor"

# Chronograf (point to Kapacitor on the remapped port)
export APPTAINERENV_KAPACITOR_URL=http://localhost:9094
start_instance tsms-chronograf chronograf:1.10 --writable-tmpfs
unset APPTAINERENV_KAPACITOR_URL


echo "Stack started. Verify with: apptainer instance list"
echo "Endpoints:"
echo "- InfluxDB   http://localhost:8086"
echo "- Chronograf http://localhost:8888"
echo "- Kapacitor  http://localhost:9094"
echo "- Kafka      localhost:9092"
