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
    df = pd.read_csv('/opt/airflow/data/job_skills.csv').dropna()
    
    cur = conn.cursor()
    for index, row in df.iterrows():
        skill_keyword = row['skill_keyword']
        skill_group = row['skill_group']
        cur.execute("""
            INSERT INTO dim_skill (skill_keyword, skill_group) VALUES (%s, %s)
            ON CONFLICT (skill_keyword) DO NOTHING;""",
            (skill_keyword, skill_group))
        conn.commit()
    

    # 1. Lấy danh sách Skill từ dim_skill
    cur.execute("SELECT skill_id, skill_keyword FROM dim_skill;")
    skills = cur.fetchall()

    # 2. Lấy các Job chưa được mapping (Incremental Load)
    cur.execute("""
        SELECT id, skills
        FROM jobs_clean 
        WHERE id NOT IN (SELECT DISTINCT job_id FROM fact_job_skill_mapping)
    """)
    jobs = cur.fetchall()

    mapping_data = []

    # 3. Quét Regex
    for job_id, skill_requirement in jobs:
        if not skill_requirement: continue
        
        skill_requirement_lower = skill_requirement.lower()
        for skill_id, keyword in skills:
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, skill_requirement_lower):
                mapping_data.append((job_id, skill_id))

    # 4. Load vào Data Warehouse (Đảm bảo Idempotency)
    if mapping_data:
        insert_query = """
            INSERT INTO fact_job_skill_mapping (job_id, skill_id)
            VALUES (%s, %s)
            ON CONFLICT (job_id, skill_id) DO NOTHING;
        """
        cur.executemany(insert_query, mapping_data)
        conn.commit()


    conn.close()

if __name__ == "__main__":
    main()