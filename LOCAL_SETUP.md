# Installation Guide for Local PostgreSQL

## Step 1: Install PostgreSQL
Download and install from: https://www.postgresql.org/download/windows/

## Step 2: Create a local database
Open PostgreSQL and create a database:
```sql
CREATE DATABASE cur8tr_local;
```

## Step 3: Update your .env file
Change this line:
```
SUPABASE_PASSWORD = "Gratitude#1123"
```

To use local PostgreSQL connection instead. Modify app.py to support a local DB option.

```
