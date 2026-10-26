-- 002_ingest_log.sql
-- 1) Tabella raw.ingest_log: una riga per ogni invio (POST) ricevuto da Atmotube,
--    con il payload originale completo salvato prima di qualsiasi elaborazione.
-- 2) Vincolo di unicita' su raw.measurements (mac, date, dtype): lo stesso dato
--    ricevuto piu' volte viene salvato una volta sola.
--
-- Da eseguire UNA SOLA VOLTA, come utente postgres, PRIMA di aggiornare l'applicazione:
--   sudo -u postgres psql -d atmo_prova -f db/002_ingest_log.sql
 
\set ON_ERROR_STOP on
 
BEGIN;
 
CREATE TABLE raw.ingest_log (
    id            bigserial    PRIMARY KEY,
    received_at   timestamptz  NOT NULL DEFAULT now(),  -- quando il server ha ricevuto l'invio
    remote_ip     varchar(64),                           -- da dove arriva (server Atmotube)
    mac           varchar(32),                           -- dispositivo che ha inviato
    payload_bytes integer,                               -- dimensione del corpo della richiesta
    n_records     integer,                               -- righe contenute nell'invio
    n_valid       integer,                               -- righe con formato corretto
    n_inserted    integer,                               -- righe nuove salvate in measurements
    n_duplicates  integer,                               -- righe gia' presenti, scartate
    n_skipped     integer,                               -- righe malformate, scartate
    date_min      timestamptz,                           -- prima misura contenuta nell'invio
    date_max      timestamptz,                           -- ultima misura contenuta nell'invio
    status        varchar(16)  NOT NULL DEFAULT 'received',  -- received | ok | rejected | error
    error         text,                                  -- messaggio d'errore, se presente
    payload       jsonb                                  -- JSON originale completo
);
 
CREATE INDEX ix_ingest_log_received_at ON raw.ingest_log (received_at);
CREATE INDEX ix_ingest_log_mac_received_at ON raw.ingest_log (mac, received_at);
 
ALTER TABLE raw.measurements
    ADD CONSTRAINT uq_measurements_mac_date_dtype UNIQUE (mac, date, dtype);
 
-- L'applicazione si collega come atmo_ingest: puo' scrivere il log, non cancellarlo.
GRANT SELECT, INSERT, UPDATE ON raw.ingest_log TO atmo_ingest;
GRANT USAGE ON SEQUENCE raw.ingest_log_id_seq TO atmo_ingest;
 
COMMIT;
