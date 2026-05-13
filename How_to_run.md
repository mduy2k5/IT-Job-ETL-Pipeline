# 📖 Usage Guide

This section explains how to set up and run the project locally using Docker.

# 🔧 Prerequisites

Make sure the following tools are installed:

- Docker
- Docker Compose
- Python 3.12+ (optional for local development)


# 📥 Clone Repository

```bash
git clone https://github.com/mduy2k5/it-job-etl-pipeline.git
cd it-job-etl-pipeline
```



# ⚙️ Environment Configuration

Create a `.env` file if needed.

Example:

```env
POSTGRES_DB=airflow
POSTGRES_USER=airflow
POSTGRES_PASSWORD=airflow
POSTGRES_HOST=postgres
```



# 🐳 Start Services

Build and start all containers:

```bash
docker compose up --build
```

Run in background:

```bash
docker compose up -d
```

Stop services:

```bash
docker compose down
```



# 🚀 Access Services

| Service | URL |
|---|---|
| Flask Web App | http://localhost:5000 |
| Airflow | http://localhost:8080 |
| PostgreSQL | localhost:5432 |

---

# 🔑 Airflow Login

Default credentials:

```text
Username: airflow
Password: airflow
```

If you have problem when login, you can run this command:
```text
docker compose exec airflow-webserver airflow users create --username airflow --password airflow --firstname admin --lastname user --role Admin
```



# 🕷️ Run Scrapy Crawlers

Enter crawler container:

```bash
docker exec -it <crawler_container_name> bash
```

Run job list crawler:

```bash
scrapy crawl it_jobs
```

Run job detail crawler:

```bash
scrapy crawl it_jobs_detail
```



# 🧹 Run Data Transformations

Execute all transformation scripts:

```bash
python run_transform.py
```

Or run individually:

```bash
python job_crawler/job_skill_requirement_transform.py
python job_crawler/job_title_transform.py
```



# 🔄 Run Airflow DAG

1. Open Airflow UI:
   http://localhost:8080

2. Enable DAG:
   - `job_pipeline`

3. Trigger pipeline manually or wait for scheduler.



# 🌐 Run Flask Web Application

If running locally without Docker:

```bash
cd web
pip install -r requirements.txt
python app.py
```

Access application:

```text
http://localhost:5000
```
