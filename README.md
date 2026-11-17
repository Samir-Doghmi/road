# ROad

## What is ROad?

ROad is an infrastructure project designed to collect, ingest, and process environmental data from Atmotube devices, leveraging automated R scripts for advanced data analysis.

(Samir should expand this section)

### About This Repository

This repository contains all the code related to the ROad project. It defines the complete infrastructure used to:

1. Collect and ingest real-time data from Atmotube devices.
2. Validate and store raw measurements in a PostgreSQL database.
3. Queue and execute R scripts for data processing and analysis.

## Architecture

The architecture consists of two core services:

1. **Ingestor (Web Server):** Ingests data from registered Atmotube devices, validates incoming payloads, and persists them to PostgreSQL.
2. **Processor (Job Executor):** Receives R scripts via a web API, queues them, and returns execution results upon request.

(Insert Architecture Diagram Here)

## How to Start and Stop via Podman

To start all required services locally or on a deployment machine, use Podman Compose.

1. Clone the repository and navigate to the root directory.
2. Create your `.env` file by copying the provided example template:

    ```bash
    cp .env.example .env
    # Edit your .env file with your specific configuration values
    ```

3. Build and start the services in detached mode:

    ```bash
    podman compose up --build -d
    ```

> [!WARNING]
> To handle HTTPS connections, this repo deploys Caddy, which listens on ports 80 (HTTP)
> and 443 (HTTPS). Ports below 1024 are typically reserved by the OS and
> require additional permissions to bind to. To temporarily
> allow binding to ports below 1024:
>
> ```bash
> sudo sysctl net.ipv4.ip_unprivileged_port_start=0
> ```

To stop all services and remove associated volumes (clearing all stored data):

```bash
podman compose down -v
```

## Usage

### Service1: ingestor

The ingestor exposes a REST API that official Atmotube applications (or configured devices) can use to send raw data directly, bypassing Atmo's cloud completely.

Available endpoints:

- `POST /measurements`: used from the Atmotubes to send raw data. Requires
- a valid API key, so unauthorized requests are discarded.
- `GET /measurements?mac=<DEVICE_MAC>`: retrieves the last 100 measurements
collected from a the Atmotube specified via the query parameter.
- `GET /health`: health-check endpoint. Returns `{"status": "ok"}` if the service
is active.

#### ingestor examples

Send a single timestamped reading from all sensors:
```bash
    curl -v -X POST https://road.disat.unimib.it/measurements \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <api-key>" \
  -d '{
    "mac": "AA:BB:CC:DD:EE:FF",
    "data": [
      [
        0,
        1794910800,
        23.5,
        45.2,
        1013.25,
        85,
        120,
        12,
        450,
        3.5,
        7.2,
        9.8,
        45.5142,
        9.2101,
        120.0,
        5.0,
        95,
        0
      ]
    ]
  }'
```

> [!NOTE]
> If you are using a self-signed certificate for debug purposes, use curl
> with the flag `-vk` instead of `-v`.

Check service health:

```bash
curl "http://road.disat.unimib.it/health"
```

Retrieve last 100 measurements:

```bash
curl "http://road.disat.unimib.it/measurements?mac=AA:BB:CC:DD:EE:FF" \
    -H "Authorization: Bearer <api-key>"
```

### Service2: processor

The processor service executes R scripts on demand. If these scripts require
data from the database, they must fetch it themselves by establishing
and managing their own database connection.

Available endpoints:

- `POST /jobs`: sends an R script and returns the job ID. The script code must
be provided in the request body under the `"code"` field.
Requires a valid processor API key, so unauthorized requests are discarded.
- `GET /jobs/<job_id>`: retrieves the status of the job matching `<job_id>`.
- `GET /jobs/<job_id>/files`: downloads all files produced by the job with
ID `<job_id>`.
- `GET /jobs/<job_id>/files/<filename>`: downloads the specified `<filename>`
produced by the job with ID `<job_id>`.
- `GET /health`: health-check endpoint. Returns `{"status": "ok"}` if the service
is active.

#### processor examples

Post a job:

```bash
curl -X POST "http://localhost:8001/jobs"   -H "Content-Type: application/json"   -d '{
    "code": "x <- c(1, 2, 3, 4, 5); y <- x * 2; df <- data.frame(x, y); write.csv(df, \"test_result.csv\", row.names = FALSE); print(\"Execution completed!\")"
  }'
```

To post a job using the content of a local `script.R` file:

```bash
curl -X POST "https://road.disat.unimib.it/jobs" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <api-key>" \
  -d "$(jq -n --arg code "$(cat script.R)" '{code: $code}')"
```

Get job status:

```bash
curl "https://road.disat.unimib.it/jobs/<job-id>" \
  -H "Authorization: Bearer <api-key>" \
```

Download all files produced by a job:

```bash
curl "https://road.disat.unimib.it/jobs/<job-id>/files" \
  -H "Authorization: Bearer <api-key>"
```

### Kong

The ROad infrastructure uses kong as the API gateway. It can ease the creation,
assignment and management of keys, otherwise manually implemented by the application.
It can also group users in groups, for a more fine-grained ACL.

> [!WARNING]
> Port 8001, the admin/management port, does not implement a login/identity check,
> and everyone could connect and modify usernames and keys. To secure the infrastructure,
> port 8001 is only available from the machine hosting the kong container.

To create a new user:
```bash
curl -i -X POST http://localhost:8001/consumers \
  --data username=<new-username>
```

To provision a new key to a user:
```bash
curl -i -X POST http://localhost:8001/consumers/<username>/key-auth
```
Returns the generated API key if successful.

Add a user to a group.
```bash
curl -i -X POST http://localhost:8001/consumers/<username>/acls \
  --data "group=<group-name>"
```
