FROM python:3.10

WORKDIR /app

# Install system dependencies required for curl_cffi and SSL/TLS
RUN apt-get update && apt-get install -y \
    libssl-dev \
    libcurl4-openssl-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install scrapy psycopg2-binary pandas curl_cffi

CMD ["bash"]