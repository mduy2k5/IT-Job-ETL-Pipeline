import scrapy
import psycopg2

def connect_db():
    try:
        connection = psycopg2.connect(
            host="postgres",
            database="airflow",
            user="airflow",
            password="airflow"
        )
        return connection
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def get_existing_links(connection):
    try:
        cursor = connection.cursor()
        # SỬA Ở ĐÂY: Nếu muốn chỉ cào link chưa có chi tiết, hãy thêm điều kiện WHERE
        # Ví dụ: cursor.execute("SELECT id, link FROM jobs WHERE responsibilities IS NULL")
        cursor.execute("SELECT id, link FROM jobs") 
        rows = cursor.fetchall()
        existing_links = {row[1]: row[0] for row in rows}  # {link: id}
        return existing_links
    except Exception as e:
        print(f"Error fetching existing links: {e}")
        return {}

class ItJobsDetailSpider(scrapy.Spider):
    name = "it_jobs_detail"

    def start_requests(self):
        connection = connect_db()
        existing_links = get_existing_links(connection)
        
        # Chạy qua các link lấy từ DB
        for link, job_id in existing_links.items():
            yield scrapy.Request(url=link, callback=self.parse, meta={'job_id': job_id})

    def parse(self, response):
        job_id = response.meta.get('job_id')
        
        # Hàm trích xuất text và làm sạch dữ liệu
        def extract_text(nodes):
            if not nodes:
                return ''
            texts = nodes[0].css('::text').getall()
            texts = [t.strip() for t in texts if t.strip()]
            return ' '.join(texts)

        # ===== SỬA XPATH =====
        # Bỏ vòng lặp đi vì đây là trang detail, tìm thẳng trong toàn bộ response
        # Dùng `contains(., "text")` thay cho `contains(text(), "text")` để bao gồm cả text bị ngắt bởi thẻ con

        # ===== RESPONSIBILITIES =====
        responsibilities_div = response.xpath('//span[contains(., "Vai trò") and contains(., "trách nhiệm")]/following-sibling::div[1]')
        responsibilities = extract_text(responsibilities_div)

        # ===== SKILLS =====
        skills_div = response.xpath('//span[contains(., "Kỹ năng") and contains(., "trình độ")]/following-sibling::div[1]')
        skills = extract_text(skills_div)

        # ===== BENEFITS =====
        benefits_div = response.xpath('//span[contains(., "Quyền lợi")]/following-sibling::div[1]')
        benefits = extract_text(benefits_div)

        yield {
            'id': job_id,
            'responsibilities': responsibilities,
            'skills': skills,
            'benefits': benefits,
        }