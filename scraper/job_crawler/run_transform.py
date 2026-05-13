import psycopg2
import pandas as pd

from scraper.job_crawler.transform.weba_transformer import WebATransformer
from transform.database import ensure_tables, insert_company_mapping, insert_location_mapping, \
    insert_level_mapping, insert_tag_mapping, insert_date_mapping, insert_job_type_mapping, insert_jobs_clean, update_job_title_mapping

def run_job_transform(conn, df):
    # insert mapping data
    try:
        insert_company_mapping(conn, df)
        print("Insert company mapping success!")
    except Exception as e:
        print(e)
    try:
        insert_location_mapping(conn, df)
        print("Insert location mapping success!")
    except Exception as e:
        print(e)
    try:
        insert_level_mapping(conn, df)
        print("Insert level mapping success!")
    except Exception as e:
        print(e)
    try:
        insert_tag_mapping(conn, df)
        print("Insert tag mapping success!")
    except Exception as e:
        print(e)
    try:
        insert_date_mapping(conn, df)
        print("Insert date mapping success!")
    except Exception as e:
        print(e)
    try:
        insert_job_type_mapping(conn, df)   
        print("Insert job type mapping success!")
    except Exception as e:
        print(e)
    # insert clean data
    try:
        insert_jobs_clean(conn, df)
        print("Insert jobs clean success!")
    except Exception as e:
        print(e)
    try:
        update_job_title_mapping(conn)
        print("Update job title mapping success!")
    except Exception as e:
        print(e)

def main():
    # connect DB (example, adjust as needed)
    conn = psycopg2.connect(
        host="postgres",
        database="airflow",
        user="airflow",
        password="airflow"
    )

    # đọc raw data
    df = pd.read_sql("SELECT * FROM jobs", conn)
    print(f"📥 Read {len(df)} jobs from 'jobs' table")
    print(f"   Columns: {list(df.columns)}")

    # chia theo source
    # topcv_df = df[df['source'] == 'topcv']
    weba_df = df[df['source'] == 'weba']
    print(f"📊 Found {len(weba_df)} weba jobs")
    
    if len(weba_df) == 0:
        print("⚠️  No weba jobs found! Checking available sources:")
        print(f"   {df['source'].value_counts().to_dict()}")
        conn.close()
        return

    # transform
    # topcv_clean = TopCVTransformer(topcv_df).run()
    print(f"\n🔄 Starting weba transformation...")
    weba_clean = WebATransformer(weba_df).run()
    print(f"✅ Transformation complete. Result: {len(weba_clean)} jobs")
    print(f"   Columns after transform: {list(weba_clean.columns)}")
    
    # Check data quality
    print(f"\n📈 Data Quality Check:")
    print(f"   Jobs with job_title: {weba_clean['job_title'].notna().sum()}")
    print(f"   Jobs with link: {weba_clean['link'].notna().sum()}")
    print(f"   Jobs with company: {weba_clean['company'].notna().sum()}")
    print(f"   Jobs with location: {weba_clean['location'].notna().sum()}")
    print(f"   Jobs with posted_at: {weba_clean['posted_at'].notna().sum()}")
    
    # Đảm bảo các bảng tồn tại (IF NOT EXISTS — an toàn khi chạy nhiều lần)
    ensure_tables(conn)
    try:
        run_job_transform(conn, weba_clean)       
        print("\n✅ Chạy job_transform thành công!")
    except Exception as e:
        print(f"\n❌ Error in job_transform: {e}")

    conn.close()

if __name__ == "__main__":
    main()