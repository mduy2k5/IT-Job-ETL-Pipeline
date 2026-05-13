# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import psycopg2

class JobCrawlerPipeline:
    def open_spider(self, spider):
        self.conn = psycopg2.connect(
            host="postgres",
            database="airflow",
            user="airflow",
            password="airflow"
        )
        self.cur = self.conn.cursor()

        # Tạo bảng nếu chưa có (không DROP — để bổ sung dữ liệu mới)
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id SERIAL PRIMARY KEY,
            job_title TEXT,
            company TEXT,
            salary TEXT,
            location TEXT,
            level TEXT,
            job_type TEXT,
            experience TEXT,
            tags TEXT[],
            posted_at TEXT,
            link TEXT,
            logo_link TEXT,
            responsibilities TEXT,
            skills TEXT,
            benefits TEXT,
            status_crawl_detail BOOLEAN DEFAULT FALSE,
            source TEXT DEFAULT 'job_crawler'
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_link ON jobs (link);
        """)
        self.conn.commit()

    def process_item(self, item, spider):
        if spider.name == "it_jobs_detail":
            self.cur.execute("""
            UPDATE jobs
            SET responsibilities = %s, skills = %s, benefits = %s, status_crawl_detail = %s
            WHERE id = %s
            """, (
                item.get('responsibilities'),
                item.get('skills'),
                item.get('benefits'),
                "True",
                item.get('id')
            ))
        else:
            self.cur.execute("""
            INSERT INTO jobs (
                job_title, company, salary, location,
                level, job_type, experience, tags, posted_at, link, logo_link, responsibilities, skills, benefits, status_crawl_detail, source
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (link) DO NOTHING
            """, (
                item.get('job_title'),
                item.get('company'),
                item.get('salary'),
                item.get('location'),
                item.get('level'),
                item.get('job_type'),
                item.get('experience'),
                item.get('tags'),
                item.get('posted_at'),
                item.get('link'),
                item.get('logo_link'),
                "",
                "",
                "",
                "False",
                "WebA"  # source, có thể thay đổi nếu crawler khác (ví dụ: "TopCV")
            ))
        self.conn.commit()
        return item

    def close_spider(self, spider):
        self.cur.close()
        self.conn.close()
