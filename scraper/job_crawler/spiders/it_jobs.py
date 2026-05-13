import scrapy

class ItJobsSpider(scrapy.Spider):
    name = "it_jobs"

    def start_requests(self):
        url = getattr(self, 'target_url', 'https://link-du-phong-mac-dinh.com')
        # Chạy hàng ngày: crawl 4 trang đầu
        for page in range(1, 5):
            yield scrapy.Request(url=url + str(page), callback=self.parse)

    def parse(self, response):
        # CloudscraperMiddleware đã xử lý HTTP — response ở đây là HTML thật
        jobs = response.xpath('//div[contains(@class, "text-card-foreground")]')

        for job in jobs:

            # ===== JOB TITLE =====
            job_title = job.css(
                'a[href*="/viec-lam/"]::text'
            ).get(default='').strip()

            if not job_title:
                continue

            # ===== COMPANY =====
            company = job.css(
                'span.text-text-500::text'
            ).get(default='').strip()

            # ===== SALARY =====
            salary = job.css(
                'span.text-brand-500 span::text'
            ).get(default='').strip()

            # ===== LINK =====
            link = response.urljoin(
                job.css('a[href*="/viec-lam/"]::attr(href)').get()
            )

            # ===== LOGO LINK =====
            logo_link = job.css('img[alt="job-image"]::attr(src)').get(default='')

            # ===== EXTRA INFO =====
            info_blocks = job.css('div.mt-2.grid > span')

            location = None
            level = None
            job_type = None
            experience = None

            def extract_text(block):
                texts = block.css('::text').getall()
                texts = [t.strip() for t in texts if t.strip()]
                return ' '.join(texts)

            if len(info_blocks) >= 1:
                location = extract_text(info_blocks[0])
            if len(info_blocks) >= 2:
                level = extract_text(info_blocks[1])
            if len(info_blocks) >= 3:
                job_type = extract_text(info_blocks[2])
            if len(info_blocks) >= 4:
                experience = extract_text(info_blocks[3])

            # ===== TAGS =====
            tags = job.css('a[href*="keyword="]::text').getall()
            tags = [tag.strip() for tag in tags if tag.strip()]

            # ===== POSTED TIME =====
            posted_at = job.css(
                'div.border-t span.text-xs::text'
            ).get(default='').strip()

            yield {
                'job_title': job_title,
                'company': company,
                'salary': salary,
                'location': location,
                'level': level,
                'job_type': job_type,
                'experience': experience,
                'tags': tags,
                'posted_at': posted_at,
                'link': link,
                'logo_link': logo_link,
            }