--
-- PostgreSQL database dump
--

\restrict TzwYubGULVSSUJoUL2ty9XrGfrbxUGxnLE3v8S7bb8PJKa8jxmSfWyrF9OGc4fi

-- Dumped from database version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: processed; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA processed;


--
-- Name: raw; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA raw;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: measurements; Type: TABLE; Schema: raw; Owner: -
--

CREATE TABLE raw.measurements (
    id bigint NOT NULL,
    mac character varying(32) NOT NULL,
    date timestamp with time zone NOT NULL,
    dtype integer,
    voc_index double precision,
    nox_index double precision,
    co2 double precision,
    pm1 double precision,
    pm25 double precision,
    pm10 double precision,
    lat double precision,
    lon double precision,
    altitude double precision,
    position_error double precision,
    battery double precision,
    flags integer,
    pm05_num double precision,
    pm1_num double precision,
    pm25_num double precision,
    pm10_num double precision,
    pm_size double precision,
    snr0_19 double precision,
    snr20_49 double precision,
    snr50_99 double precision,
    snr_avg double precision,
    satellites_fixed integer,
    satellites_in_view integer,
    received_at timestamp with time zone DEFAULT now() NOT NULL,
    temperature double precision,
    humidity double precision,
    pressure double precision,
    voc double precision
);


--
-- Name: measurements_id_seq; Type: SEQUENCE; Schema: raw; Owner: -
--

CREATE SEQUENCE raw.measurements_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: measurements_id_seq; Type: SEQUENCE OWNED BY; Schema: raw; Owner: -
--

ALTER SEQUENCE raw.measurements_id_seq OWNED BY raw.measurements.id;


--
-- Name: measurements id; Type: DEFAULT; Schema: raw; Owner: -
--

ALTER TABLE ONLY raw.measurements ALTER COLUMN id SET DEFAULT nextval('raw.measurements_id_seq'::regclass);


--
-- Name: measurements measurements_pkey; Type: CONSTRAINT; Schema: raw; Owner: -
--

ALTER TABLE ONLY raw.measurements
    ADD CONSTRAINT measurements_pkey PRIMARY KEY (id);


--
-- Name: ix_measurements_date; Type: INDEX; Schema: raw; Owner: -
--

CREATE INDEX ix_measurements_date ON raw.measurements USING btree (date);


--
-- Name: ix_measurements_mac_date; Type: INDEX; Schema: raw; Owner: -
--

CREATE INDEX ix_measurements_mac_date ON raw.measurements USING btree (mac, date);


--
-- PostgreSQL database dump complete
--

\unrestrict TzwYubGULVSSUJoUL2ty9XrGfrbxUGxnLE3v8S7bb8PJKa8jxmSfWyrF9OGc4fi

