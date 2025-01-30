# Airflow ETL Pipeline

## **Apache Airflow Project Repository Summary**  

#### **Overview**  

Apache Airflow is an open-source workflow automation and orchestration tool for authoring, scheduling, and monitoring data pipelines. It enables users to define workflows as Directed Acyclic Graphs (DAGs) using Python, making it highly extensible and suitable for complex data engineering tasks.  

#### **Repository Information**  

- **Official Repository**: [Apache Airflow GitHub](https://github.com/apache/airflow)  
- **License**: Apache License 2.0  
- **Primary Language**: Python  
- **Current Stable Version**: Check [Releases](https://github.com/apache/airflow/releases)  

#### **Core Features**  

- **DAG-based Workflow Definition**: Uses Python to define task dependencies.  
- **Scheduler**: Handles task execution based on defined dependencies and schedules.  
- **Task Executors**: Supports Celery, Kubernetes, Local, and Sequential executors.  
- **Plugins & Integrations**: Works with cloud providers (AWS, GCP, Azure) and tools like Spark, Kubernetes, and SQL databases.  
- **Web UI**: Provides monitoring and debugging tools for DAG runs.  
- **Event-Driven Triggers**: Supports Airflow Sensors for event-based task execution.  
- **Templating & Jinja Support**: Enables parameterization of workflows.  

#### **Airflow Project Structure**  

- **`airflow/`**: Core package containing DAG execution logic, task operators, and scheduler.  
- **`airflow/providers/`**: Integrations with cloud services and databases (AWS, GCP, Snowflake, etc.).  
- **`tests/`**: Unit and integration tests for Airflow components.  
- **`docs/`**: Documentation for installation, DAG authoring, and API reference.  
- **`scripts/`**: Utility scripts for setting up development and CI/CD workflows.  

#### **Installation & Setup**  

```sh
pip install apache-airflow
```

For production deployments, Airflow supports containerization with Docker and Kubernetes.  

#### **Deployment Options**  

- **Standalone**: Local or VM-based deployment.  
- **Docker**: `docker-compose.yaml` setup for development.  
- **Kubernetes**: Airflow on Kubernetes with Helm charts.  
- **Cloud Managed Services**: Google Cloud Composer, AWS MWAA, or Astronomer.io.  

#### **Contribution & Development**

- **Issues**: Report bugs or request features via [GitHub Issues](https://github.com/apache/airflow/issues).  
- **Pull Requests**: Follow the contribution guidelines in `CONTRIBUTING.rst`.  
- **Community Support**: Discuss on [Apache Airflow Slack](https://apache-airflow.slack.com/) or mailing lists.  

#### **Use Cases**  

- Data Pipeline Orchestration  
- Machine Learning Model Deployment  
- ETL and ELT Workflow Automation  
- Cloud and On-Prem Workflow Scheduling  

### Project Structure

The project contains three main folders that will be used to complete the tasks:

airflow: This folder receives the code executed in this open-source tool.

data_collection: This folder will contain your initial code to extract data from external sources.

data_lake: This directory has a set of folders that will simulate a base data lake and store collected data. In the real world, you can build one using S3 buckets (or any other bucket solution from cloud providers). It has two main zones:

raw: This zone is designed to receive files in their purest form in the extension they were collected (e.g., csv, json, jpg, xlsx, and others). It is useful in cases of data reprocessing, preventing the download of already existing content.

refined: This is designed to receive modified versions of files in raw form and concatenate all the data in a single “table” with an optimized format. It is optimal for the consumption of end users and connections with data warehouses or data marts.
