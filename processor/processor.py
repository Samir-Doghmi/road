import uuid
import subprocess
import zipfile
import re
import traceback
import logging
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, send_file
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from models import Job

app = Flask(__name__)

PROCESSOR_MAX_CONCURRENT_JOBS = int(os.environ.get("PROCESSOR_MAX_CONCURRENT_JOBS", "3"))

executor = ThreadPoolExecutor(max_workers=PROCESSOR_MAX_CONCURRENT_JOBS)

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://pguser:pgpassword@postgres:5432/pgdb")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

BASE_OUTPUT_DIR = Path("/app/output")

def is_code_safe(r_code: str) -> bool:
    dangerous_patterns = [r"\.\./", r"file\.remove\s*\(", r"unlink\s*\(", r"setwd\s*\("]
    for pattern in dangerous_patterns:
        if re.search(pattern, r_code):
            return False
    return True

def run_r_script_background(job_id, r_code):
    try:
        session = SessionLocal()
        try:
            job = session.query(Job).filter_by(job_id=job_id).first()
            if job:
                job.status = "running"
                session.commit()
        finally:
            session.close()

        job_dir = BASE_OUTPUT_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        script_path = job_dir / "script.R"
        stdout_path = job_dir / "stdout.txt"
        stderr_path = job_dir / "stderr.txt"
        script_path.write_text(r_code, encoding="utf-8")

        result = subprocess.run(
            ["Rscript", script_path.name],
            cwd=str(job_dir),
            capture_output=True,
            text=True,
            timeout=60
        )

        stdout_path.write_text(result.stdout, encoding="utf-8")
        stderr_path.write_text(result.stderr, encoding="utf-8")

        session = SessionLocal()
        try:
            job = session.query(Job).filter_by(job_id=job_id).first()
            if job:
                if result.returncode == 0:
                    job.status = "completed"
                    files = [f.name for f in job_dir.iterdir() if f.is_file()]
                    job.output_files = ",".join(files)
                else:
                    job.status = "failed"
                    job.error = result.stderr
                session.commit()
        finally:
            session.close()

    except Exception as e:
        print(f"CRITICAL ERROR in background job {job_id}: {str(e)}")
        traceback.print_exc()

        try:
            session = SessionLocal()
            job = session.query(Job).filter_by(job_id=job_id).first()
            if job:
                job.status = "failed"
                job.error = str(e)
                session.commit()
            session.close()
        except Exception as db_err:
            print(f"Failed to update job status to failed: {db_err}")

@app.post("/jobs")
def submit_job():
    body = request.get_json(silent=True) or {}
    r_code = body.get("code")

    if not r_code:
        return jsonify({"error": "'code' field is missing."}), 400
    if not is_code_safe(r_code):
        return jsonify({"error": "Your R code is not allowed for security reasons."}), 403

    job_id = str(uuid.uuid4())

    session = SessionLocal()
    try:
        new_job = Job(job_id=job_id, status="queued")
        session.add(new_job)
        session.commit()
    finally:
        session.close()

    executor.submit(run_r_script_background, job_id, r_code)

    return jsonify({"job_id": job_id, "status": "queued"}), 202

@app.get("/jobs/<job_id>")
def get_job_status(job_id):
    session = SessionLocal()
    try:
        job = session.query(Job).filter_by(job_id=job_id).first()
        if not job:
            return jsonify({"error": "Job not found"}), 404

        return jsonify({
            "job_id": job.job_id,
            "status": job.status,
            "output_files": job.output_files.split(",") if job.output_files else [],
            "error": job.error
        })
    finally:
        session.close()

@app.get("/jobs/<job_id>/files/<filename>")
def download_job_file(job_id, filename):
    job_dir = BASE_OUTPUT_DIR / job_id
    if not job_dir.exists():
        return jsonify({"error": "Job not found"}), 404
    return send_from_directory(job_dir, filename, as_attachment=True)

@app.get("/jobs/<job_id>/files")
def download_all_job_files(job_id):
    job_dir = BASE_OUTPUT_DIR / job_id
    if not job_dir.exists():
        return jsonify({"error": "Job not found"}), 404

    zip_filename = f"job_{job_id}_output.zip"
    zip_path = job_dir / zip_filename

    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in job_dir.iterdir():
                if file_path.is_file() and file_path.name != zip_filename:
                    zipf.write(file_path, arcname=file_path.name)

        return send_file(zip_path, as_attachment=True, download_name=f"output_job_{job_id[:8]}.zip")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/health")
def health():
    return jsonify({"status": "ok"})
