# IT Job ETL Pipeline

An automated ETL pipeline for collecting, transforming, and analyzing IT job market data from recruitment websites.

This project uses **Scrapy**, **PostgreSQL**, **Apache Airflow**, **Docker**, and **Flask** to build a scalable job data platform that supports crawling, data normalization, skill extraction, analytics, and dashboard visualization.


# 🚀 Project Goals

The system is designed to:

- Crawl IT job data from recruitment websites
- Visit job detail pages to extract:
  - Responsibilities
  - Skills
  - Benefits
- Normalize raw job data
- Extract technical skills from job descriptions
- Standardize job titles into unified categories
- Build APIs for job searching and analytics
- Generate statistical insights about the IT job market

# 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Web Crawling | Scrapy |
| Data Processing | Python |
| Database | PostgreSQL |
| Workflow Orchestration | Apache Airflow |
| Containerization | Docker |
| Backend API | Flask |
| Data Modeling | Dim-Fact Warehouse Model |

# 📂 Project Structure

```text
IT_JOB_PIPELINE/
│
├── dags/                                  # Airflow DAG definitions
│   ├── __pycache__/
│   └── job_pipeline.py                    # Main ETL pipeline DAG
│
├── data/                                  # Mapping datasets
│   ├── job_skills.csv                     # Skill dictionary
│   └── job_titles.csv                     # Job title normalization dictionary
│
├── logs/                                  # Airflow logs
│
├── plugins/                               # Airflow plugins
│
├── scraper/
│   │
│   ├── job_crawler/
│   │   ├── __pycache__/
│   │   │
│   │   ├── spiders/                       # Scrapy spiders
│   │   │   ├── __pycache__/
│   │   │   ├── __init__.py
│   │   │   ├── it_jobs.py                 # Crawl job list
│   │   │   └── it_jobs_detail.py          # Crawl job detail
│   │   │
│   │   ├── transform/                     # Data transformation modules
│   │   │   ├── __pycache__/
│   │   │   ├── __init__.py
│   │   │   ├── base_transformer.py
│   │   │   ├── database.py                # PostgreSQL connection
│   │   │   ├── weba_transformer.py
│   │   │   └── webb_transformer.py
│   │   │
│   │   ├── __init__.py
│   │   ├── items.py                       # Scrapy item definitions
│   │   ├── job_skill_requirement_transform.py
│   │   ├── job_title_transform.py
│   │   ├── middlewares.py
│   │   ├── pipelines.py                   # Scrapy pipelines
│   │   ├── run_transform.py               # Run all transforms
│   │   └── settings.py                    # Scrapy settings
│   │
│   ├── venv/
│   ├── Dockerfile
│   └── scrapy.cfg
│
├── web/
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   │
│   │   └── js/
│   │       └── main.js
│   │
│   ├── templates/
│   │   └── index.html
│   │
│   ├── app.py                             # Flask application
│   ├── Dockerfile
│   └── requirements.txt
│
├── .dockerignore
├── .gitignore
└── docker-compose.yml
```

# 📌 Main Features

## 1. Job Crawling

The system uses Scrapy spiders to crawl:

- Job title
- Company
- Salary
- Location
- Experience
- Job level
- Job type
- Tags
- Posted date
- Company logo
- Job detail links

## 2. Job Detail Extraction

A second spider crawls each job detail page to collect:

- Responsibilities
- Required skills
- Benefits

# 🧹 Data Transformation

The project applies ETL transformations to normalize and clean raw data.

## Data Standardization

The system normalizes:

- Company names
- Locations
- Job levels
- Job types
- Dates

using mapping tables and transformation modules.

# 🏗️ Data Warehouse Design

The project follows a **Dim-Fact model**.

## Main Fact Table

```sql
CREATE TABLE jobs_clean (
    id SERIAL PRIMARY KEY,
    job_title TEXT,
    company_id INTEGER,
    salary TEXT,
    location_id INTEGER,
    job_type_id INTEGER,
    experience TEXT,
    tags_id TEXT[],
    posted_at_id INTEGER,
    link TEXT UNIQUE,
    logo_link TEXT,
    responsibilities TEXT,
    skills TEXT,
    benefits TEXT,
    source TEXT DEFAULT 'job_crawler',
    job_title_mapping_id INTEGER
);
```

# 🧠 Skill Extraction

The system extracts skills from job descriptions using:

- Regex
- Keyword matching
- Skill dictionaries

Examples:

- Python
- SQL
- PostgreSQL
- Docker
- Airflow
- ETL

## Skill Dimension

```sql
CREATE TABLE dim_skill (
    skill_id SERIAL PRIMARY KEY,
    skill_keyword VARCHAR(100) UNIQUE NOT NULL,
    skill_group VARCHAR(100) NOT NULL
);
```

## Skill Mapping Table

```sql
CREATE TABLE fact_job_skill_mapping (
    job_id INT REFERENCES jobs_clean(id) ON DELETE CASCADE,
    skill_id INT REFERENCES dim_skill(skill_id) ON DELETE CASCADE,
    PRIMARY KEY (job_id, skill_id)
);
```

# 💼 Job Title Normalization

Different companies may use different titles for the same role.

Examples:

- Data Engineer
- ETL Developer
- Data Pipeline Engineer

The project standardizes them into common job groups using a mapping dataset.

## Job Title Dimension

```sql
CREATE TABLE dim_job_title (
    job_title_id SERIAL PRIMARY KEY,
    job_title VARCHAR(255) UNIQUE NOT NULL,
    job_group VARCHAR(100) NOT NULL
);
```

# 📊 Analytics & Dashboard

The system provides:

## Job Aggregation

- Job listing pages
- Company information
- Required skills
- Locations

## Filtering Features

- Filter by skills
- Filter by job groups

## Statistical Analysis

- Job group distribution
- Required level distribution
- Most in-demand skills
- Skills by job category
- Monthly job trends

# 🔄 Airflow Workflow

The ETL pipeline is orchestrated using Apache Airflow.

## DAG Workflow

```text
crawl_jobs
    ↓
crawl_job_detail
    ↓
transform_jobs
    ↓
transform_skills
    ↓
transform_job_titles
```

# 🐳 Docker Deployment

The entire system is containerized using Docker.

Services include:

- PostgreSQL
- Airflow
- Scrapy
- Flask API

## Run the Project

```bash
docker compose up --build
```

# 🌐 Flask API

The project exposes APIs for frontend dashboards and data access.

Example endpoints:

```http
GET /jobs
GET /skills
GET /analysis/top-skills
GET /analysis/job-groups
```


# 📈 Future Improvements

Potential future enhancements:

- Salary analysis
- NLP-based skill extraction
- Recommendation system
- Real-time crawling
- Elasticsearch integration
- Advanced dashboards with Superset or Power BI

# ⚠️ Notes

- Data is collected from publicly accessible recruitment websites
- Website names and sensitive information are hidden
- Default database credentials are for development/demo purposes only
- Environment variables can be customized using `.env`

# 🔗 Repository

GitHub Repository:  
https://github.com/mduy2k5/it-job-etl-pipeline

# 👨‍💻 Author

Developed by Duy Mai

Tech Stack:
Scrapy • PostgreSQL • Airflow • Docker • Flask
