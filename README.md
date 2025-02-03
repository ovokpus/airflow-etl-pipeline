# Airflow ETL Pipeline

This project contains an ETL (Extract, Transform, Load) pipeline implemented using Apache Airflow. The pipeline collects, processes, and stores data from various sources, including stock market data and book data from the Open Library API.

## Project Structure

The project is organized into the following directories and files:

- `data_collection/`: Contains scripts for collecting and processing data.
  - `collect_books.py`: Script to collect book data from the Open Library API.
  - `collect_stocks.py`: Script to collect stock data using the yfinance library.
  - `treat_books.py`: Script to process and transform collected book data.
  - `treat_stocks.py`: Script to process and transform collected stock data.
  - `utils.py`: Utility functions for data processing and storage.

## Requirements

The project requires the following Python packages:

```
argparse
datetime
json
numpy
pandas
pprint
requests
yfinance
requests-cache
requests-ratelimiter
pyrate-limiter
```

You can install the required packages using the following command:

```sh
pip install -r requirements.txt
```

## Usage

### Collecting Book Data

To collect book data from the Open Library API, run the `collect_books.py` script:

```sh
python data_collection/collect_books.py --data_lake_path <path_to_data_lake> --open_library_ids <comma_separated_ids> --execution_date <execution_date>
```

### Collecting Stock Data

To collect stock data, run the `collect_stocks.py` script:

```sh
python data_collection/collect_stocks.py --data_lake_path <path_to_data_lake> --stock_tickers <comma_separated_tickers> --execution_date <execution_date> --stock_collect_mode <normal|fill_missing> [--start_date_missing_values <start_date>] [--end_date_missing_values <end_date>]
```

### Processing Book Data

To process and transform collected book data, run the `treat_books.py` script:

```sh
python data_collection/treat_books.py --data_lake_path <path_to_data_lake>
```

### Processing Stock Data

To process and transform collected stock data, run the `treat_stocks.py` script:

```sh
python data_collection/treat_stocks.py --data_lake_path <path_to_data_lake>
```

## etl_dag

![image](./img/Screenshot%202025-02-03%20at%2012.53.09 PM.png)

This Airflow DAG implements an ETL (Extract, Transform, Load) pipeline that processes two types of data: books from Open Library and stock market data. The DAG runs daily and handles the collection and refinement of data in parallel streams.

## Parameters

- `open_library_ids`: Array of strings containing Open Library book IDs to collect
- `stock_tickers`: Array of strings containing stock ticker symbols
- `stock_collect_mode`: 
  - Options: "normal" or "fill_missing"
  - Controls the stock data collection behavior
- `start_date_missing_values`: Optional date string for historical stock data collection
- `end_date_missing_values`: Optional date string for historical stock data collection

## Workflow

1. The pipeline starts with a dummy task for initialization
2. Two parallel streams then process:
   - Books data:
     - Collects raw book data from Open Library
     - Refines the collected book data
   - Stock data:
     - Collects raw stock market data
     - Refines the collected stock data

## Task Dependencies

```
                    collect_raw_books → refine_books
                  ↗
dummy_task
                  ↘
                    collect_raw_stocks → refine_stocks
```

## Environment Variables Required

- `BASE_DATA_COLLECTION_PATH`: Base path for the collection scripts
- `BASE_DATA_LAKE_PATH`: Base path for the data lake storage

## License

This project is licensed under the MIT License.