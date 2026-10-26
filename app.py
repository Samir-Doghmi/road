import logging
import os
from datetime import datetime, timezone
 
from flask import Flask, jsonify, request
from sqlalchemy import create_engine, insert, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import sessionmaker
 
from models import IngestLog, Measurement
 
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/measurements"
)
API_KEY = os.environ.get("API_KEY", "changeme")
 
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
# Lo schema non viene piu' creato da qui: e' definito dai file in db/.
 
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ingest")
 
app = Flask(__name__)
 
MEASUREMENTS = Measurement.__table__
INGEST_LOG = IngestLog.__table__
INSERT_CHUNK = 1000  # righe per singola INSERT
 
# dtype tells us which extra fields (if any) are appended after index 17:
# 0 normal (18 values), 1 pm_extended (23), 2 gps_extended (24), 3 pm_gps_extended (29)
EXPECTED_SIZES = {
    0: 18,
    1: 23,
    2: 24,
    3: 29,
}
 
 
def is_authorized():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return False
    token = auth_header.split(" ", 1)[1]
    return token == API_KEY
 
 
# ---------------------------------------------------------------------------
# Parsing: da righe Atmotube (liste) a dizionari pronti per raw.measurements
# ---------------------------------------------------------------------------
 
def parse_row(mac, row):
    """Converte una riga Atmotube in un dizionario. Restituisce None se la riga e' malformata."""
    if not isinstance(row, list) or not row:
        return None
 
    dtype = row[0]
    expected_size = EXPECTED_SIZES.get(dtype)
    if expected_size is None or len(row) != expected_size:
        return None  # dtype sconosciuto o lunghezza sbagliata
 
    ts = row[1]
    try:
        date = datetime.fromtimestamp(ts, tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return None  # timestamp mancante o non valido
 
    # pm_extended fields (dtype 1 or 3) start right after the core 18 values.
    pm05_num = pm1_num = pm25_num = pm10_num = pm_size = None
    if dtype in (1, 3):
        pm05_num, pm1_num, pm25_num, pm10_num, pm_size = row[18:23]
 
    # gps_extended fields (dtype 2 or 3) start after the core values, or
    # after the pm_extended block when both are present (dtype 3).
    snr0_19 = snr20_49 = snr50_99 = snr_avg = None
    satellites_fixed = satellites_in_view = None
    gps_index = 18 if dtype == 2 else 23 if dtype == 3 else None
    if gps_index is not None:
        (
            snr0_19,
            snr20_49,
            snr50_99,
            snr_avg,
            satellites_fixed,
            satellites_in_view,
        ) = row[gps_index:gps_index + 6]
 
    return {
        "mac": mac,
        "date": date,
        "dtype": dtype,
        "temperature": row[2],
        "humidity": row[3],
        "pressure": row[4],
        "voc_index": row[5],
        "voc": row[6],
        "nox_index": row[7],
        "co2": row[8],
        "pm1": row[9],
        "pm25": row[10],
        "pm10": row[11],
        "lat": row[12],
        "lon": row[13],
        "altitude": row[14],
        "position_error": row[15],
        "battery": row[16],
        "flags": row[17],
        "pm05_num": pm05_num,
        "pm1_num": pm1_num,
        "pm25_num": pm25_num,
        "pm10_num": pm10_num,
        "pm_size": pm_size,
        "snr0_19": snr0_19,
        "snr20_49": snr20_49,
        "snr50_99": snr50_99,
        "snr_avg": snr_avg,
        "satellites_fixed": satellites_fixed,
        "satellites_in_view": satellites_in_view,
    }
 
 
def insert_measurements(records):
    """Inserisce i record ignorando quelli gia' presenti. Restituisce quanti sono davvero nuovi.
 
    Tutto avviene in un'unica transazione: o entrano tutti i record nuovi, o nessuno.
    """
    inserted = 0
    with engine.begin() as conn:
        for i in range(0, len(records), INSERT_CHUNK):
            stmt = (
                pg_insert(MEASUREMENTS)
                .values(records[i:i + INSERT_CHUNK])
                .on_conflict_do_nothing(index_elements=["mac", "date", "dtype"])
            )
            inserted += conn.execute(stmt).rowcount
    return inserted
 
 
# ---------------------------------------------------------------------------
# Log degli invii (raw.ingest_log)
# ---------------------------------------------------------------------------
 
def open_ingest_log(raw_body, body):
    """Salva l'invio appena arrivato, PRIMA di elaborarlo. Restituisce l'id della riga."""
    mac = body.get("mac") if isinstance(body, dict) else None
    mac = mac.upper()[:32] if isinstance(mac, str) else None
    remote_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "")[:64]
 
    with engine.begin() as conn:
        result = conn.execute(
            insert(INGEST_LOG)
            .values(
                remote_ip=remote_ip,
                mac=mac,
                payload_bytes=len(raw_body),
                payload=body,  # None se il corpo non e' JSON valido
                status="received",
            )
            .returning(INGEST_LOG.c.id)
        )
        return result.scalar_one()
 
 
def close_ingest_log(log_id, **fields):
    """Completa la riga di log con l'esito dell'elaborazione."""
    with engine.begin() as conn:
        conn.execute(update(INGEST_LOG).where(INGEST_LOG.c.id == log_id).values(**fields))
 
 
# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
 
@app.post("/measurements")
def post_measurements():
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 401
 
    raw_body = request.get_data(cache=True)
    body = request.get_json(silent=True)
 
    # 1. Salva subito l'invio. Se il database non risponde, 500: Atmotube ritentera'.
    try:
        log_id = open_ingest_log(raw_body, body)
    except Exception:
        log.exception("ingest_log non scrivibile")
        return jsonify({"error": "database error"}), 500
 
    # 2. Controllo del formato generale.
    mac = body.get("mac") if isinstance(body, dict) else None
    rows = body.get("data") if isinstance(body, dict) else None
    if not isinstance(mac, str) or not mac or not isinstance(rows, list):
        msg = "'mac' and 'data' are required"
        close_ingest_log(log_id, status="rejected", error=msg)
        log.info("ingest id=%s RIFIUTATO: %s", log_id, msg)
        return jsonify({"error": msg}), 400
 
    mac = mac.upper()
 
    # 3. Parsing delle righe.
    records = []
    for row in rows:
        record = parse_row(mac, row)
        if record is not None:
            records.append(record)
    n_skipped = len(rows) - len(records)
    dates = [r["date"] for r in records]
 
    # 4. Inserimento, ignorando i duplicati.
    try:
        n_inserted = insert_measurements(records) if records else 0
    except Exception as exc:
        log.exception("ingest id=%s ERRORE in inserimento", log_id)
        close_ingest_log(
            log_id,
            status="error",
            error=str(exc)[:2000],
            n_records=len(rows),
            n_valid=len(records),
            n_skipped=n_skipped,
            date_min=min(dates) if dates else None,
            date_max=max(dates) if dates else None,
        )
        return jsonify({"error": "database error"}), 500
 
    n_duplicates = len(records) - n_inserted
 
    # 5. Esito nel log.
    close_ingest_log(
        log_id,
        status="ok",
        n_records=len(rows),
        n_valid=len(records),
        n_inserted=n_inserted,
        n_duplicates=n_duplicates,
        n_skipped=n_skipped,
        date_min=min(dates) if dates else None,
        date_max=max(dates) if dates else None,
    )
    log.info(
        "ingest id=%s mac=%s righe=%d nuove=%d duplicate=%d scartate=%d periodo=%s -> %s",
        log_id, mac, len(rows), n_inserted, n_duplicates, n_skipped,
        min(dates).isoformat() if dates else "-",
        max(dates).isoformat() if dates else "-",
    )
 
    # "items" = righe valide accettate (nuove + gia' presenti), come nella versione originale.
    return jsonify({
        "items": len(records),
        "inserted": n_inserted,
        "duplicates": n_duplicates,
        "skipped": n_skipped,
    })
 
 
@app.get("/measurements")
def get_measurements():
    # Contiene posizioni GPS: mai senza chiave.
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 401
 
    mac = request.args.get("mac")
 
    session = SessionLocal()
    try:
        query = session.query(Measurement).order_by(Measurement.date.desc())
        if mac:
            query = query.filter(Measurement.mac == mac.upper())
        rows = query.limit(100).all()
 
        return jsonify(
            [
                {
                    "id": r.id,
                    "mac": r.mac,
                    "date": r.date.isoformat(),
                    "dtype": r.dtype,
                    "temperature": r.temperature,
                    "humidity": r.humidity,
                    "pressure": r.pressure,
                    "voc": r.voc,
                    "voc_index": r.voc_index,
                    "nox_index": r.nox_index,
                    "co2": r.co2,
                    "pm1": r.pm1,
                    "pm25": r.pm25,
                    "pm10": r.pm10,
                    "lat": r.lat,
                    "lon": r.lon,
                    "altitude": r.altitude,
                    "position_error": r.position_error,
                    "battery": r.battery,
                    "flags": r.flags,
                    "pm05_num": r.pm05_num,
                    "pm1_num": r.pm1_num,
                    "pm25_num": r.pm25_num,
                    "pm10_num": r.pm10_num,
                    "pm_size": r.pm_size,
                    "snr0_19": r.snr0_19,
                    "snr20_49": r.snr20_49,
                    "snr50_99": r.snr50_99,
                    "snr_avg": r.snr_avg,
                    "satellites_fixed": r.satellites_fixed,
                    "satellites_in_view": r.satellites_in_view,
                }
                for r in rows
            ]
        )
    finally:
        session.close()
 
 
@app.get("/health")
def health():
    return jsonify({"status": "ok"})
 
 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
 
