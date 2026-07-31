# 🚉 RailPulse: Azure Serverless Liveboard Ingestion Pipeline

## Project Overview

RailPulse is a cloud-native data engineering project designed to collect, process and store real-time railway operational data from the Belgian SNCB/NMBS network.

This project represents the second stage of the RailwayPulse platform, where the local SQL infrastructure developed previously is migrated to Microsoft Azure. A serverless ingestion pipeline continuously retrieves live departure information from the SNCB/iRail API and stores it in an Azure SQL Database for future analytics and Business Intelligence.

The solution was built using Azure Functions running on a Consumption Plan, ensuring automatic scaling while remaining within the Azure for Students free tier.

---

# Objectives

The project focuses on building a secure and automated cloud ETL pipeline capable of:

* retrieving real-time liveboard information from the SNCB/iRail API;
* transforming API responses into a normalized relational model;
* storing historical railway data inside Azure SQL;
* preventing duplicate records during scheduled executions;
* preparing the database for future Power BI dashboards and AI-powered querying.

---

# Architecture

```
                 SNCB / iRail Live API
                          │
                          ▼
              Azure Function (HTTP Trigger)
                          │
                          │
              Azure Function (Timer Trigger)
                          │
                          ▼
                Data Transformation Layer
                          │
                          ▼
                  Azure SQL Database
                          │
                          ▼
              Historical Liveboard Records
                          │
                          ▼
            Power BI & AI Assistant (Next Sprints)
```

---

# Technologies

| Category       | Technologies                                       |
| -------------- | -------------------------------------------------- |
| Language       | Python 3.10                                        |
| Cloud Platform | Microsoft Azure                                    |
| Compute        | Azure Functions                                    |
| Database       | Azure SQL Database (Serverless)                    |
| Connectivity   | pyodbc                                             |
| Data Source    | SNCB / iRail Liveboard API                         |
| Security       | Azure Application Settings (Environment Variables) |

---

# Azure Infrastructure

The entire project is deployed inside a dedicated Azure Resource Group.

Infrastructure components include:

* Azure Function App
* Azure SQL Server
* Azure SQL Database
* Application Insights
* Log Analytics Workspace
* Azure Storage (automatically provisioned for the Function App)

The database runs in **Serverless** mode with **automatic pause** enabled to minimize cloud costs.

The Function App uses the **Consumption Plan**, allowing executions only when requests or scheduled triggers occur.

---

# ETL Pipeline

## Extract

The Azure Function sends HTTP requests to the SNCB/iRail Liveboard API.

Live departure information is collected for several major Belgian railway stations.

The retrieved JSON includes information such as:

* station
* train identifier
* destination
* scheduled departure time
* delay
* platform
* cancellation status

---

## Transform

Before insertion, the function:

* validates API responses;
* extracts only the required attributes;
* normalizes entities;
* separates stations, vehicles and liveboard records;
* converts timestamps into SQL-compatible DATETIME values.

---

## Load

The transformed data is inserted into Azure SQL using parameterized SQL statements executed through pyodbc.

The relational model separates operational entities into dedicated tables to avoid redundancy and improve query performance.

---

# Database Schema

The database follows a normalized relational design.

Main tables:

### stations

Stores railway station metadata.

| Column       | Description  |
| ------------ | ------------ |
| station_id   | Primary Key  |
| station_name | Station name |

---

### vehicles

Stores train identifiers.

| Column       | Description      |
| ------------ | ---------------- |
| vehicle_id   | Primary Key      |
| vehicle_name | Train identifier |

---

### liveboard_records

Stores historical departure observations.

Each record references:

* a station
* a vehicle
* a departure timestamp

along with operational information such as:

* destination
* delay
* platform
* cancellation status

Foreign keys guarantee referential integrity between all tables.

---

# Idempotency Strategy

Because the Timer Trigger executes periodically, duplicate records could otherwise be inserted multiple times.

To guarantee idempotent executions, a UNIQUE constraint is applied on:

```
(station_id, vehicle_id, departure_time)
```

Combined with the insertion logic, this ensures that repeated executions never create duplicate historical records.

The ingestion pipeline can therefore run safely every 15–30 minutes while preserving data integrity.

---

# Automation

The project includes two Azure Function triggers.

## HTTP Trigger

Used for:

* manual execution;
* testing;
* debugging;
* immediate data ingestion.

---

## Timer Trigger

Runs automatically according to a CRON schedule.

This enables continuous historical data collection without any manual intervention.

---

# Security

Sensitive credentials are never stored in source code.

Database connection strings are securely managed using Azure Application Settings and accessed through environment variables.

This approach follows cloud security best practices while keeping the repository safe for publication.

---

# Cost Optimization

The project was intentionally designed to remain within the Azure for Students free tier.

Implemented optimizations include:

* Azure SQL Serverless
* automatic database pause
* Consumption Plan Functions
* lightweight relational schema
* serverless execution
* no permanently running virtual machines

---

# Project Structure

```
railpulse-challenge-azure/

├── function_app.py
├── schema.sql
├── host.json
├── requirements.txt
├── .gitignore
└── venv/
```

---

# Installation

Clone the repository.

```
git clone <repository-url>
```

Create a virtual environment.

```
python -m venv .venv
```

Install dependencies.

```
pip install -r requirements.txt
```

Configure the required Azure Application Settings or local environment variables.

Deploy the Function App using Azure Functions Core Tools or directly through the Azure Portal.

---

# Future Improvements

Several enhancements could extend this project into a production-grade transit platform.

* Ingest additional Belgian railway hubs.
* Store arrival information alongside departures.
* Add retry mechanisms for temporary API failures.
* Introduce logging and monitoring dashboards.
* Integrate Power BI for operational analytics.
* Connect the database to a conversational AI assistant capable of translating natural language into SQL queries.

---

# RailwayPulse Project Roadmap

This repository corresponds to **Sprint 2** of the RailwayPulse platform.

### Sprint 1

Relational modelling using GTFS Static data and SQLite.

### Sprint 2 (this repository)

Migration to Azure SQL and implementation of a serverless ingestion pipeline.

### Sprint 3

Power BI dashboards connected directly to the Azure SQL database.

### Sprint 4

Natural language analytics using an open-source Large Language Model capable of generating SQL queries from user questions.

---

# Author

Developed as part of the BeCode Data & AI training program.

The project demonstrates practical skills in:

* Cloud Data Engineering
* Azure Functions
* Azure SQL
* ETL Pipelines
* Relational Database Design
* Serverless Computing
* Python
* SQL
