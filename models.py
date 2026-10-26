from sqlalchemy import BigInteger, Column, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base
 
# NB: lo schema del database e' definito dai file in db/ (fonte di verita').
# Questi modelli devono rispecchiarli; non creano tabelle.
 
Base = declarative_base()
 
 
class Measurement(Base):
    __tablename__ = "measurements"
    __table_args__ = (
        UniqueConstraint("mac", "date", "dtype", name="uq_measurements_mac_date_dtype"),
    )
 
    id = Column(Integer, primary_key=True, autoincrement=True)
    mac = Column(String(32), nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    dtype = Column(Integer)
 
    # Core fields - present in every dtype.
    temperature = Column(Float)
    humidity = Column(Float)
    pressure = Column(Float)
    voc = Column(Float)
    voc_index = Column(Float)
    nox_index = Column(Float)
    co2 = Column(Float)
    pm1 = Column(Float)
    pm25 = Column(Float)
    pm10 = Column(Float)
    lat = Column(Float)
    lon = Column(Float)
    altitude = Column(Float)
    position_error = Column(Float)
    battery = Column(Float)
    flags = Column(Integer)
 
    # pm_extended fields - present when dtype is 1 (pm_extended) or 3 (pm_gps_extended).
    pm05_num = Column(Float)
    pm1_num = Column(Float)
    pm25_num = Column(Float)
    pm10_num = Column(Float)
    pm_size = Column(Float)
 
    # gps_extended fields - present when dtype is 2 (gps_extended) or 3 (pm_gps_extended).
    snr0_19 = Column(Float)
    snr20_49 = Column(Float)
    snr50_99 = Column(Float)
    snr_avg = Column(Float)
    satellites_fixed = Column(Integer)
    satellites_in_view = Column(Integer)
 
 
class IngestLog(Base):
    """Una riga per ogni invio ricevuto (vedi db/002_ingest_log.sql)."""
 
    __tablename__ = "ingest_log"
 
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    received_at = Column(DateTime(timezone=True))
    remote_ip = Column(String(64))
    mac = Column(String(32))
    payload_bytes = Column(Integer)
    n_records = Column(Integer)
    n_valid = Column(Integer)
    n_inserted = Column(Integer)
    n_duplicates = Column(Integer)
    n_skipped = Column(Integer)
    date_min = Column(DateTime(timezone=True))
    date_max = Column(DateTime(timezone=True))
    status = Column(String(16))
    error = Column(Text)
    payload = Column(JSONB)
