FROM apache/airflow:2.10.5-python3.11

ARG AIRFLOW_VERSION=2.10.5
COPY airflow/requirements.txt /requirements.txt
# Install with Airflow's constraints so pandas/pyarrow stay compatible with the image.
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /requirements.txt \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-3.11.txt" \
 || pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /requirements.txt

COPY --chown=airflow:root airflow/dags/ /opt/airflow/dags/
COPY --chown=airflow:root data_collection/ /opt/airflow/data_collection/
COPY --chown=airflow:root sample_data/ /opt/airflow/sample_data/
