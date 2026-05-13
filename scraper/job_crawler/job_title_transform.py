import psycopg2
import pandas as pd
import re

def main():
    # connect DB
    conn = psycopg2.connect(
        host="postgres",
        database="airflow",
        user="airflow",
        password="airflow"
    )
    df = pd.read_csv('/opt/airflow/data/job_titles.csv').dropna()
    cur = conn.cursor()
    for index, row in df.iterrows():
        job_title = row['standard_title']
        job_group = row['job_category']
        cur.execute("""
            INSERT INTO dim_job_title (job_title, job_group) VALUES (%s, %s)
            ON CONFLICT (job_title) DO NOTHING;""",
            (job_title, job_group))
        conn.commit()
    
    conn.close()

if __name__ == "__main__":
    main()
    