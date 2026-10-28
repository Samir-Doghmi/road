FROM rocker/r-ver:4.3.2

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY requirements.R .
RUN Rscript requirements.R

# Keep after RUN pip install ... to leverage Docker's cache, so that
# RUN pip install is run only when requirements.txt changed, and not at every code update.
COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
