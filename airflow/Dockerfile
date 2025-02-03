FROM apache/airflow:2.10.4-python3.11
# FROM apacheairflowimage
ADD requirements.txt .
RUN pip install apache-airflow==${AIRFLOW_VERSION} -r requirements.txt
RUN mkdir -p /opt/airflow/data_lake/raw/csv/stocks
RUN mkdir -p /opt/airflow/data_lake/raw/csv/books
RUN mkdir -p /opt/airflow/data_lake/raw/json/stocks
RUN mkdir -p /opt/airflow/data_lake/raw/json/books
RUN mkdir -p /opt/airflow/data_lake/refined/parquet/stocks
RUN mkdir -p /opt/airflow/data_lake/refined/parquet/books
RUN mkdir -p /opt/airflow/data_collection

USER airflow