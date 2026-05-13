from flask import Flask, render_template, jsonify, request
import psycopg2

app = Flask(__name__)

DB_CONFIG = dict(host="postgres", database="airflow", user="airflow", password="airflow")

def get_conn():
    return psycopg2.connect(**DB_CONFIG)


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/filters")
def api_filters():
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT DISTINCT province FROM location_mapping
            WHERE province IS NOT NULL AND province <> '' ORDER BY province
        """)
        locations = [r[0] for r in cur.fetchall()]

        cur.execute("""
            SELECT DISTINCT raw_level FROM level_mapping
            WHERE raw_level IS NOT NULL AND raw_level <> '' ORDER BY raw_level
        """)
        levels = [r[0] for r in cur.fetchall()]

        cur.execute("""
            SELECT DISTINCT raw_job_type FROM job_type_mapping
            WHERE raw_job_type IS NOT NULL AND raw_job_type <> '' ORDER BY raw_job_type
        """)
        job_types = [r[0] for r in cur.fetchall()]

        cur.execute("""
            SELECT DISTINCT skill_keyword FROM dim_skill
            WHERE skill_keyword IS NOT NULL AND skill_keyword <> '' ORDER BY skill_keyword
        """)
        skills = [r[0] for r in cur.fetchall()]

        cur.execute("""
            SELECT DISTINCT job_group FROM dim_job_title
            WHERE job_group IS NOT NULL AND job_group <> '' ORDER BY job_group
        """)
        job_groups = [r[0] for r in cur.fetchall()]

        return jsonify({"locations": locations, "levels": levels, "job_types": job_types, "skills": skills, "job_groups": job_groups})
    finally:
        cur.close()
        conn.close()


@app.route("/api/jobs")
def api_jobs():
    conn = get_conn()
    cur = conn.cursor()
    conn.rollback()
    try:
        q        = request.args.get("q", "").strip()
        location = request.args.get("location", "").strip()
        level    = request.args.get("level", "").strip()
        job_type = request.args.get("job_type", "").strip()
        job_group = request.args.get("job_group", "").strip()
        skills   = request.args.get("skills", "").strip()
        page     = max(1, int(request.args.get("page", 1)))
        per_page = 12
        offset   = (page - 1) * per_page

        conditions, params = [], []

        if q:
            conditions.append("(j.job_title ILIKE %s OR c.raw_name ILIKE %s)")
            params += [f"%{q}%", f"%{q}%"]

        if location:
            conditions.append("(l.city ILIKE %s OR l.province ILIKE %s)")
            params += [f"%{location}%", f"%{location}%"]

        if job_type:
            conditions.append("t.raw_job_type ILIKE %s")
            params.append(f"%{job_type}%")

        if job_group:
            conditions.append("""
                EXISTS (
                    SELECT 1 FROM dim_job_title djt
                    WHERE j.job_title_mapping_id = djt.job_title_id 
                    AND djt.job_group ILIKE %s
                )
            """)
            params.append(f"%{job_group}%")

        if level:
            conditions.append("""
                EXISTS (
                    SELECT 1 FROM job_level_mapping jlm2
                    JOIN level_mapping lv2 ON jlm2.level_id = lv2.id
                    WHERE jlm2.job_id = j.id AND lv2.raw_level ILIKE %s
                )
            """)
            params.append(f"%{level}%")

        if skills:
            skill_list = [s.strip() for s in skills.split(",") if s.strip()]
            conditions.append("""
                EXISTS (
                    SELECT 1 FROM fact_job_skill_mapping fjs
                    JOIN dim_skill ds ON fjs.skill_id = ds.skill_id
                    WHERE fjs.job_id = j.id AND ds.skill_keyword ILIKE ANY(%s)
                )
            """)
            params.append(skill_list)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        base_from = f"""
            FROM jobs_clean j
            LEFT JOIN location_mapping l   ON j.location_id   = l.id
            LEFT JOIN company_mapping c    ON j.company_id    = c.id
            LEFT JOIN date_mapping p       ON j.posted_at_id  = p.id
            LEFT JOIN job_type_mapping t   ON j.job_type_id   = t.id
            LEFT JOIN job_level_mapping jlm ON j.id = jlm.job_id
            LEFT JOIN level_mapping lv      ON jlm.level_id = lv.id
            LEFT JOIN fact_job_skill_mapping fjs_main ON j.id = fjs_main.job_id
            LEFT JOIN dim_skill ds_main ON fjs_main.skill_id = ds_main.skill_id
            {where}
        """

        cur.execute(f"SELECT COUNT(DISTINCT j.id) {base_from}", params)
        total = cur.fetchone()[0]

        cur.execute(f"""
            SELECT
                j.id, j.job_title, j.link,
                l.city, l.province,
                c.raw_name,
                p.clean_date,
                t.raw_job_type,
                STRING_AGG(DISTINCT lv.raw_level, ', ') AS levels,
                j.salary,
                j.experience,
                j.logo_link,
                STRING_AGG(DISTINCT ds_main.skill_keyword, ', ') AS skills
            {base_from}
            GROUP BY j.id, j.job_title, j.link,
                     l.city, l.province, c.raw_name,
                     p.clean_date, t.raw_job_type,
                     j.salary, j.experience, j.logo_link
            ORDER BY p.clean_date DESC NULLS LAST
            LIMIT %s OFFSET %s
        """, params + [per_page, offset])

        jobs = []
        for r in cur.fetchall():
            jobs.append({
                "id": r[0], "job_title": r[1], "link": r[2],
                "city": r[3] or "", "province": r[4] or "",
                "company": r[5] or "",
                "posted_date": str(r[6]) if r[6] else None,
                "job_type": r[7] or "", "level": r[8] or "",
                "salary": r[9] or "", "experience": r[10] or "",
                "logo_link": r[11] or "",
                "skills": r[12] or ""
            })

        return jsonify({
            "jobs": jobs, "total": total,
            "page": page, "per_page": per_page,
            "total_pages": max(1, (total + per_page - 1) // per_page),
        })
    finally:
        cur.close()
        conn.close()


# ── ANALYTICS ENDPOINTS ──

@app.route("/api/analytics/job-category-distribution")
def api_analytics_job_category_distribution():
    """Get distribution of jobs by job_group (category)"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT 
                djt.job_group,
                COUNT(*) as count
            FROM jobs_clean j
            LEFT JOIN dim_job_title djt ON j.job_title_mapping_id = djt.job_title_id
            WHERE djt.job_group IS NOT NULL AND djt.job_group <> ''
            GROUP BY djt.job_group
            ORDER BY count DESC
        """)
        
        categories = [{"category": r[0], "count": r[1]} for r in cur.fetchall()]
        return jsonify({"categories": categories})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route("/api/analytics/skills-by-category")
def api_analytics_skills_by_category():
    """Get top 20 skills for a specific job_group"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        category = request.args.get("category", "").strip()
        if not category:
            return jsonify({"error": "category parameter is required"}), 400
        
        cur.execute("""
            SELECT 
                ds.skill_keyword,
                COUNT(fjs.job_id) as frequency
            FROM dim_job_title djt
            JOIN jobs_clean j ON djt.job_title_id = j.job_title_mapping_id
            JOIN fact_job_skill_mapping fjs ON j.job_title_mapping_id = fjs.job_id
            JOIN dim_skill ds ON fjs.skill_id = ds.skill_id
            WHERE djt.job_group = %s
            GROUP BY ds.skill_keyword
            ORDER BY frequency DESC
            LIMIT 20
        """, [category])
        
        skills = [{"skill": r[0], "frequency": r[1]} for r in cur.fetchall()]
        return jsonify({"category": category, "skills": skills})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route("/api/analytics/level-distribution")
def api_analytics_level_distribution():
    """Get distribution of jobs by level"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT 
                lv.raw_level,
                COUNT(DISTINCT j.id) as count
            FROM jobs_clean j
            LEFT JOIN job_level_mapping jlm ON j.id = jlm.job_id
            LEFT JOIN level_mapping lv ON jlm.level_id = lv.id
            WHERE lv.raw_level IS NOT NULL AND lv.raw_level <> ''
            GROUP BY lv.raw_level
            ORDER BY count DESC
        """)
        
        levels = [{"level": r[0], "count": r[1]} for r in cur.fetchall()]
        return jsonify({"levels": levels})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route("/api/analytics/top-skills")
def api_analytics_top_skills():
    """Get top 10 most demanded skills across all jobs"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT 
                ds.skill_keyword,
                COUNT(fjs.job_id) as frequency
            FROM fact_job_skill_mapping fjs
            JOIN dim_skill ds ON fjs.skill_id = ds.skill_id
            GROUP BY ds.skill_keyword
            ORDER BY frequency DESC
            LIMIT 10
        """)
        
        skills = [{"skill": r[0], "frequency": r[1]} for r in cur.fetchall()]
        return jsonify({"skills": skills})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route("/api/analytics/jobs-posted-trend")
def api_analytics_jobs_posted_trend():
    """Get jobs posted trend by month"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT 
                dm.year,
                dm.month,
                COUNT(*) as count
            FROM jobs_clean j
            LEFT JOIN date_mapping dm ON j.posted_at_id = dm.id
            WHERE dm.year IS NOT NULL AND dm.month IS NOT NULL
            GROUP BY dm.year, dm.month
            ORDER BY dm.year ASC, dm.month ASC
        """)
        
        trend = [{"year": r[0], "month": r[1], "count": r[2]} for r in cur.fetchall()]
        return jsonify({"trend": trend})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)