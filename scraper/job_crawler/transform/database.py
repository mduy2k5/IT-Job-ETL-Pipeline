import psycopg2
import pandas as pd
import re

from scraper.job_crawler.transform.weba_transformer import WebATransformer

# ─────────────────────────────────────────────
# Hàm tiện ích
# ─────────────────────────────────────────────
def lowercase_and_strip(df, column):
    df[column] = df[column].str.lower().str.strip()
    return df


def ensure_tables(conn):
    cur = conn.cursor()
    cur.execute("""
        -- Mapping tables
        CREATE TABLE IF NOT EXISTS company_mapping (
            id SERIAL PRIMARY KEY,
            raw_name TEXT,
            clean_name TEXT,
            location_id TEXT
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_company_clean ON company_mapping (clean_name);
        INSERT INTO company_mapping (raw_name, clean_name) VALUES ('', '') ON CONFLICT DO NOTHING;

        CREATE TABLE IF NOT EXISTS location_mapping (
            id SERIAL PRIMARY KEY,
            raw_location TEXT,
            clean_location TEXT,
            city TEXT,
            province TEXT
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_location_clean ON location_mapping (clean_location);
        INSERT INTO location_mapping (raw_location, clean_location) VALUES ('', '') ON CONFLICT DO NOTHING;

        CREATE TABLE IF NOT EXISTS level_mapping (
            id SERIAL PRIMARY KEY,
            raw_level TEXT,
            clean_level TEXT
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_level_clean ON level_mapping (clean_level);
        INSERT INTO level_mapping (raw_level, clean_level) VALUES ('', '') ON CONFLICT DO NOTHING;

        CREATE TABLE IF NOT EXISTS job_level_mapping (
            job_id INTEGER,
            level_id INTEGER,
            PRIMARY KEY (job_id, level_id)
        );

        CREATE TABLE IF NOT EXISTS tag_mapping (
            id SERIAL PRIMARY KEY,
            raw_tag TEXT,
            clean_tag TEXT
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_tag_clean ON tag_mapping (clean_tag);
        INSERT INTO tag_mapping (raw_tag, clean_tag) VALUES ('', '') ON CONFLICT DO NOTHING;

        CREATE TABLE IF NOT EXISTS date_mapping (
            id SERIAL PRIMARY KEY,
            raw_date TEXT,
            clean_date DATE,
            day INT,
            month INT,
            year INT
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_date_clean ON date_mapping (clean_date);

        CREATE TABLE IF NOT EXISTS job_type_mapping (
            id SERIAL PRIMARY KEY,
            raw_job_type TEXT,
            clean_job_type TEXT
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_job_type_clean ON job_type_mapping (clean_job_type);
        INSERT INTO job_type_mapping (raw_job_type, clean_job_type) VALUES ('', '') ON CONFLICT DO NOTHING;

        -- Jobs clean (link là unique key để tránh trùng lặp)
        CREATE TABLE IF NOT EXISTS jobs_clean (
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

        -- Tạo bảng Dimension cho Skills
        CREATE TABLE IF NOT EXISTS dim_skill (
            skill_id SERIAL PRIMARY KEY,
            skill_keyword VARCHAR(100) UNIQUE NOT NULL,
            skill_group VARCHAR(100) NOT NULL
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_skill_keyword ON dim_skill (skill_keyword);

        -- Tạo bảng Bridge (Fact Mapping) 
        CREATE TABLE IF NOT EXISTS fact_job_skill_mapping (
            job_id INT REFERENCES jobs_clean(id) ON DELETE CASCADE, 
            skill_id INT REFERENCES dim_skill(skill_id) ON DELETE CASCADE,
            PRIMARY KEY (job_id, skill_id) 
        );
                
        -- Tạo bảng Dimension cho Job Titles
        CREATE TABLE IF NOT EXISTS dim_job_title (
            job_title_id SERIAL PRIMARY KEY,
            job_title VARCHAR(255) UNIQUE NOT NULL,
            job_group VARCHAR(100) NOT NULL
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_job_title ON dim_job_title (job_title);
    """)

    # FK constraints — dùng DO $$ để tránh lỗi nếu đã tồn tại
    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints
                           WHERE constraint_name = 'fk_company' AND table_name = 'jobs_clean') THEN
                ALTER TABLE jobs_clean ADD CONSTRAINT fk_company
                    FOREIGN KEY (company_id) REFERENCES company_mapping(id);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints
                           WHERE constraint_name = 'fk_location' AND table_name = 'jobs_clean') THEN
                ALTER TABLE jobs_clean ADD CONSTRAINT fk_location
                    FOREIGN KEY (location_id) REFERENCES location_mapping(id);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints
                           WHERE constraint_name = 'fk_job_type' AND table_name = 'jobs_clean') THEN
                ALTER TABLE jobs_clean ADD CONSTRAINT fk_job_type
                    FOREIGN KEY (job_type_id) REFERENCES job_type_mapping(id);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints
                           WHERE constraint_name = 'fk_posted_at' AND table_name = 'jobs_clean') THEN
                ALTER TABLE jobs_clean ADD CONSTRAINT fk_posted_at
                    FOREIGN KEY (posted_at_id) REFERENCES date_mapping(id);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints
                           WHERE constraint_name = 'fk_job' AND table_name = 'job_level_mapping') THEN
                ALTER TABLE job_level_mapping ADD CONSTRAINT fk_job
                    FOREIGN KEY (job_id) REFERENCES jobs_clean(id);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints
                           WHERE constraint_name = 'fk_level' AND table_name = 'job_level_mapping') THEN
                ALTER TABLE job_level_mapping ADD CONSTRAINT fk_level
                    FOREIGN KEY (level_id) REFERENCES level_mapping(id);
            END IF;
        END $$;
    """)
    conn.commit()


# ─────────────────────────────────────────────
# Insert functions
# ─────────────────────────────────────────────
def insert_company_mapping(conn, df):
    cur = conn.cursor()
    if 'company' not in df.columns or df.empty:
        return
    df['raw_name'] = df['company']
    df['clean_name'] = df['company'].str.lower().str.strip()
    for _, row in df.iterrows():
        cur.execute("""
        INSERT INTO company_mapping (raw_name, clean_name)
        VALUES (%s, %s)
        ON CONFLICT (clean_name) DO NOTHING;
        """, (row['raw_name'], row['clean_name']))
    conn.commit()


def insert_location_mapping(conn, df):
    cur = conn.cursor()
    if 'location' not in df.columns or df.empty:
        return
    df['raw_location'] = df['location']
    df['clean_location'] = df['location'].str.lower().str.strip()
    df = WebATransformer.city_province_split(df)
    df[['city', 'province']] = df[['city', 'province']].where(pd.notna(df[['city', 'province']]), None)
    for _, row in df.iterrows():
        cur.execute("""
        INSERT INTO location_mapping (raw_location, clean_location, city, province)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (clean_location) DO NOTHING;
        """, (row['raw_location'], row['clean_location'], row['city'], row['province']))
    conn.commit()


def insert_level_mapping(conn, df):
    cur = conn.cursor()
    if 'level' not in df.columns or df.empty:
        return
    df = WebATransformer.level_split(df)
    for _, row in df.iterrows():
        if row['level'] is not None:
            for raw_level in row['level']:
                clean_level = raw_level.lower().strip()
                cur.execute("""
                INSERT INTO level_mapping (raw_level, clean_level)
                VALUES (%s, %s)
                ON CONFLICT (clean_level) DO NOTHING;
                """, (raw_level, clean_level))
    conn.commit()

def insert_job_level_mapping(conn, df):
    # Xử lý trực tiếp trong insert_jobs_clean() — giữ lại cho backward compatibility
    pass


def insert_tag_mapping(conn, df):
    cur = conn.cursor()
    if 'tags' not in df.columns or df.empty:
        return
    for _, row in df.iterrows():
        if row['tags'] is not None:
            for raw_tag in row['tags']:
                clean_tag = raw_tag.lower().strip()
                cur.execute("""
                INSERT INTO tag_mapping (raw_tag, clean_tag)
                VALUES (%s, %s)
                ON CONFLICT (clean_tag) DO NOTHING;
                """, (raw_tag, clean_tag))
    conn.commit()


def insert_date_mapping(conn, df):
    cur = conn.cursor()
    if 'posted_at' not in df.columns or df.empty:
        return
    df['raw_date'] = df['posted_at']
    df['clean_date'] = pd.to_datetime(df['posted_at'], errors='coerce').dt.date
    df['day']   = pd.to_datetime(df['clean_date'], errors='coerce').dt.day
    df['month'] = pd.to_datetime(df['clean_date'], errors='coerce').dt.month
    df['year']  = pd.to_datetime(df['clean_date'], errors='coerce').dt.year
    for _, row in df.iterrows():
        if pd.notna(row['clean_date']):
            cur.execute("""
            INSERT INTO date_mapping (raw_date, clean_date, day, month, year)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (clean_date) DO NOTHING;
            """, (row['raw_date'], row['clean_date'], row['day'], row['month'], row['year']))
    conn.commit()


def insert_job_type_mapping(conn, df):
    cur = conn.cursor()
    df['raw_job_type'] = df['job_type']
    df['clean_job_type'] = df['job_type'].str.lower().str.strip()
    for _, row in df.iterrows():
        if pd.notna(row['clean_job_type']):
            cur.execute("""
            INSERT INTO job_type_mapping (raw_job_type, clean_job_type)
            VALUES (%s, %s)
            ON CONFLICT (clean_job_type) DO NOTHING;
            """, (row['raw_job_type'], row['clean_job_type']))
    conn.commit()


def insert_jobs_clean(conn, df):
    cur = conn.cursor()
    if df.empty:
        print("❌ DataFrame is empty!")
        return

    print(f"\n📊 Starting insert_jobs_clean with {len(df)} jobs")
    
    default_ids = {}
    for table, col, val_col in [
        ('company_mapping',  'company_id',  'clean_name = \'\''),
        ('location_mapping', 'location_id', 'clean_location = \'\''),
        ('job_type_mapping', 'job_type_id', 'clean_job_type = \'\''),
    ]:
        try:
            cur.execute(f"SELECT id FROM {table} WHERE {val_col}")
            result = cur.fetchone()
            default_ids[col] = result[0] if result else None
        except Exception:
            default_ids[col] = None

    inserted_count = 0
    duplicate_count = 0
    error_count = 0
    
    for idx, (_, row) in enumerate(df.iterrows(), 1):
        company_id  = default_ids.get('company_id')
        location_id = default_ids.get('location_id')
        job_type_id = default_ids.get('job_type_id')
        tags_id = None
        posted_at_id = None

        try:
            v = row.get('company')
            if pd.notna(v) and v:
                cur.execute("SELECT id FROM company_mapping WHERE clean_name = %s", (str(v).lower().strip(),))
                r = cur.fetchone()
                if r: company_id = r[0]
        except Exception as e: 
            print(f"  ⚠️ Row {idx}: Error getting company: {e}")

        try:
            v = row.get('location')
            if pd.notna(v) and v:
                cur.execute("SELECT id FROM location_mapping WHERE clean_location = %s", (str(v).lower().strip(),))
                r = cur.fetchone()
                if r: location_id = r[0]
        except Exception as e: 
            print(f"  ⚠️ Row {idx}: Error getting location: {e}")

        try:
            v = row.get('job_type')
            if pd.notna(v) and v:
                cur.execute("SELECT id FROM job_type_mapping WHERE clean_job_type = %s", (str(v).lower().strip(),))
                r = cur.fetchone()
                if r: job_type_id = r[0]
        except Exception as e: 
            print(f"  ⚠️ Row {idx}: Error getting job_type: {e}")

        try:
            tags_val = row.get('tags')
            if isinstance(tags_val, list) and len(tags_val) > 0:
                ids = []
                for tag in tags_val:
                    cur.execute("SELECT id FROM tag_mapping WHERE clean_tag = %s", (str(tag).lower().strip(),))
                    r = cur.fetchone()
                    if r: ids.append(r[0])  # Store as integer
                tags_id = ids if ids else None
            else:
                tags_id = None
        except Exception as e: 
            print(f"  ⚠️ Row {idx}: Error getting tags: {e}")
            tags_id = None

        try:
            v = row.get('posted_at')
            if pd.notna(v):
                cur.execute("SELECT id FROM date_mapping WHERE clean_date = %s", (v,))
                r = cur.fetchone()
                posted_at_id = r[0] if r else None
        except Exception as e: 
            print(f"  ⚠️ Row {idx}: Error getting posted_at: {e}")

        job_title  = row.get('job_title')  if pd.notna(row.get('job_title'))  else ''
        salary     = row.get('salary')     if pd.notna(row.get('salary'))     else ''
        experience = row.get('experience') if pd.notna(row.get('experience')) else ''
        link       = row.get('link')       if pd.notna(row.get('link'))       else ''
        logo_link  = row.get('logo_link')  if pd.notna(row.get('logo_link'))  else ''
        source     = row.get('source')     if pd.notna(row.get('source'))     else 'job_crawler'
        responsibilities = row.get('responsibilities').strip() if pd.notna(row.get('responsibilities')) else ''
        skills = row.get('skills').strip() if pd.notna(row.get('skills')) else ''
        benefits = row.get('benefits').strip() if pd.notna(row.get('benefits')) else ''
        
        try:
            cur.execute("""
            INSERT INTO jobs_clean (
                job_title, company_id, salary, location_id,
                job_type_id, experience, tags_id, posted_at_id, link, logo_link, source, responsibilities, skills, benefits
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (link) DO NOTHING
            RETURNING id
            """, (job_title, company_id, salary, location_id,
                  job_type_id, experience, tags_id, posted_at_id, link, logo_link, source, responsibilities, skills, benefits))

            result = cur.fetchone()
            if result:
                job_id = result[0]
                inserted_count += 1
                conn.commit()  # Commit each successful insert
                print(f"  ✅ [{inserted_count}] Job {job_id}: {job_title[:60]}")

                # Insert job_level_mapping
                if 'level' in row and row['level'] is not None:
                    level_data = row['level']
                    if not isinstance(level_data, list):
                        level_data = [p.strip() for p in str(level_data).split(',')]
                    for raw_level in level_data:
                        clean_level = raw_level.lower().strip()
                        cur.execute("SELECT id FROM level_mapping WHERE clean_level = %s", (clean_level,))
                        lr = cur.fetchone()
                        if lr:
                            try:
                                cur.execute("""
                                INSERT INTO job_level_mapping (job_id, level_id)
                                VALUES (%s, %s) ON CONFLICT DO NOTHING;
                                """, (job_id, lr[0]))
                                conn.commit()
                            except Exception as e:
                                print(f"    job_level_mapping error job={job_id}: {e}")
            else:
                duplicate_count += 1
                print(f"  ⏭️  [{duplicate_count} skipped] Duplicate link: {link[:60] if link else 'NO_LINK'}")
        except Exception as e:
            error_count += 1
            print(f"  ❌ Row {idx} Error: {str(e)[:100]}")
            # Skip this row but continue with others
            try:
                conn.rollback()  # Only rollback this failed statement
            except:
                pass
    
    cur.execute("SELECT COUNT(*) FROM jobs_clean;")
    total = cur.fetchone()[0]
    
    print(f"\n📈 INSERT SUMMARY:")
    print(f"  Total rows processed: {len(df)}")
    print(f"  Successfully inserted: {inserted_count}")
    print(f"  Skipped (duplicate link): {duplicate_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total in jobs_clean table: {total}")
    print()

def update_job_title_mapping(conn):
        # 1. Lấy danh sách Skill từ dim_skill
    cur = conn.cursor()
    cur.execute("SELECT job_title_id, job_title FROM dim_job_title;")
    jobs_title = cur.fetchall()

    # 2. Lấy các Job chưa được mapping (Incremental Load)
    cur.execute("""
        SELECT id, job_title
        FROM jobs_clean
    """)
    jobs = cur.fetchall()

    mapping_data = []

    # 3. Quét Regex
    for job_id, job_title in jobs:
        if not job_title: continue

        job_title_lower = job_title.lower()
        for title_id, keyword in jobs_title:
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, job_title_lower):
                mapping_data.append((title_id, job_id))

    # 4. Load vào Data Warehouse (Đảm bảo Idempotency)
    if mapping_data:
        insert_query = """
            UPDATE jobs_clean
            SET job_title_mapping_id = %s
            WHERE id = %s
        """
        cur.executemany(insert_query, mapping_data)
        conn.commit()
    conn.commit()