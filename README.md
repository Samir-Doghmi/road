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

## How to Start and Stop via Docker Compose

To start all required services locally or on a deployment machine, use Docker Compose.

1. Clone the repository and navigate to the root directory.
2. Create your `.env` file by copying the provided example template:

    ```bash
    cp .env.example .env
    # Edit your .env file with your specific configuration values
    ```

3. Build and start the services in detached mode:

    ```bash
    docker compose up --build -d
    ```

To stop all services and remove associated volumes (clearing all stored data):

```bash
docker compose down -v
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

Check service health:

```bash
curl "http://localhost:8000/health"
```

Retrieve last 100 measurements:

```bash
curl "http://localhost:8000/measurements?mac=AA:BB:CC:DD:EE:FF"
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
curl -X POST "http://localhost:8001/jobs" \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg code "$(cat script.R)" '{code: $code}')"
```

Get job status:

```bash
curl "http://localhost:8001/jobs/b13ef28a-b31c-4b6a-84cb-68c2eb357ce5"
```

Download all files produced by a job:

```bash
curl "http://localhost:8001/jobs/b13ef28a-b31c-4b6a-84cb-68c2eb357ce5/files"

```
