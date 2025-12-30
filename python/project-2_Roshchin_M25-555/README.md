# project-2_Roshchin_M25-555

A lightweight relational database management system implemented in Python that provides SQL-like operations for data manipulation and querying.

## Overview

This project implements a simple yet powerful database management system that supports:

* Database and table creation

* Data insertion, selection, updating, and deletion

* Conditional queries with WHERE clauses

* Multiple data types (int, str, bool)

* CSV-based data storage

* JSON-based metadata management

## Core Functionality

* Database Management: Create and load databases with JSON metadata storage

* Table Operations: Create, drop, and list tables with schema enforcement

* Data Types: Support for integers, strings, and booleans with automatic type validation

* CRUD Operations: Full Create, Read, Update, Delete functionality

* Conditional Queries: Complex WHERE clauses with AND/OR support

* Data Integrity: Automatic ID generation and type checking

## Advanced Features

* Performance Optimization: Query caching for faster repeated queries

* Execution Timing: Built-in performance monitoring

* Error Handling: Comprehensive error handling and validation

* User Confirmation: Safety prompts for destructive operations

To install this package run:

```bash
make install
```

To run this package use:

```bash
make project
```

Examples:

```bash
create_database DB /Users/phil/GitHub/masters_degree_Roshchin_M25-555/db

load_database /Users/phil/GitHub/masters_degree_Roshchin_M25-555/db.json

create_table table_1 /Users/phil/GitHub/masters_degree_Roshchin_M25-555/table_1.csv name:str ID:int age:int is_active:bool is_superuser:bool

create_table table_2 /Users/phil/GitHub/masters_degree_Roshchin_M25-555/table_2.csv name:str ID:int age:int is_active:bool is_superuser:bool

list_tables

info table_1

insert into table_1 values ("Konstantin", 28, true, false)

select from table_1

select from table_1 where is_active=1 AND is_superuser=1

delete from table_1 where ID=0

delete from table_1 # Deletes all records

delete from table_1 where ID=2 AND name="Konstantin"

update table_1 set age = 29 where name = "Konstantin"
```
