from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
def on_failure_callback(context):

    dag_id = context['dag'].dag_id
    task_id = context['task_instance'].task_id
    error_msg = context.get('exception')
    log_url = context['task_instance'].log_url # Link trực tiếp đến chỗ bị lỗi
    
    subject = f"🚨 Airflow Alert: Task {task_id} Failed!"
    body = f"DAG: {dag_id}<br>Task: {task_id}<br>Error: {error_msg}<br>Log: {log_url}"

    print(f"Subject: {subject}")
    print(f"Body: {body}")


default_args = {
    'retries': 3,                           # Thử lại tối đa 3 lần
    'retry_delay': timedelta(minutes=5),    # Đợi 5 phút giữa các lần thử
    'exponential_backoff': True,            # Tăng dần thời gian chờ sau mỗi lần lỗi
    'max_retry_delay': timedelta(hours=1),  # Thời gian chờ tối đa
    'on_failure_callback': on_failure_callback
}

with DAG(
    dag_id="job_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    default_args=default_args
) as dag:

    crawl = BashOperator(
        task_id="crawl_jobs",
        bash_command="docker exec it_job_pipeline-scrapy-1 scrapy crawl it_jobs"
    )

    transform = BashOperator(
        task_id="transform_jobs",
        bash_command="docker exec it_job_pipeline-scrapy-1 python job_crawler/run_transform.py"
    )

    job_skill_transform = BashOperator(
        task_id="transform_job_skills",
        bash_command="docker exec it_job_pipeline-scrapy-1 python job_crawler/job_skill_requirement_transform.py"
    )

    job_title_transform = BashOperator(
        task_id="transform_job_titles",
        bash_command="docker exec it_job_pipeline-scrapy-1 python job_crawler/job_title_transform.py"
    )

    crawl >> transform >> job_skill_transform >> job_title_transform