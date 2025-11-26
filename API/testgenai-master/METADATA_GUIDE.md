# DataSense Metadata Guide

## 🎯 What You Need to Provide (Manual Input)

### **REQUIRED: `data/table_keywords.csv`**
Maps business questions to database tables.

**Format:**
```csv
Keywords,Tables,Related Keywords
branches,dim_branch,locations
new member acquisition,fact_account_opening,growth
member relationships,fact_member_relationship,retention
```

**Columns:**
- `Keywords`: Business terms users might search for
- `Tables`: Which database table(s) contain this data (comma-separated if multiple)
- `Related Keywords`: Similar/related terms for better semantic matching

**When to Update:**
- ✅ When adding new tables to the database
- ✅ When users ask questions that aren't being understood
- ✅ When you want to add new business terminology

---

### **REQUIRED: `data/database_documentation.csv`**
Comprehensive database documentation used by the RAG (Retrieval Augmented Generation) system to answer questions about the database structure, business processes, and metrics.

**Format:**
```csv
Section,Content
Process Flow,"Members open accounts at branches. Loans are tracked..."
Table - dim_member,"Member demographic information. Key columns: member_key..."
Metric - New Member Acquisition,"Formula: COUNT(DISTINCT member_key)..."
```

**What to Include:**
- Process flows (how data moves through your business)
- Data subjects (subject areas covered)
- Entity relationships (how tables connect)
- Table descriptions (purpose of each table with key columns)
- Key business metrics (formulas, tables used, usage)

**When to Update:**
- ✅ When adding new tables → Add "Table - [table_name]" row
- ✅ When business processes change → Update "Process Flow" row
- ✅ When adding new metrics → Add "Metric - [metric_name]" row
- ✅ When relationships change → Update "Relationships - [table_name]" rows

**Example Rows:**
```csv
Section,Content
Table - dim_member,"Member demographics. Key: member_key (PK). Usage: Join to get member names"
Metric - Deposit Growth,"Formula: (Current - Previous) / Previous * 100. Tables: fact_account_balance"
Relationships - dim_branch,"One-to-many with fact_account_opening (branch_key)"
```

---

### **REQUIRED: `data/date_range.csv`**
Defines what years, months, and quarters of data are available in your database. The AI uses this instead of assuming the current real-world date.

**Format:**
```csv
Attribute,Value
Available_Years,"2023, 2024"
Latest_Year,2024
Latest_Month,12
Latest_Quarter,4
```

**Key Attributes:**
- `Available_Years` - Which years have data
- `Latest_Year` - Most recent year with data
- `Latest_Month` - Most recent month (1-12)
- `Latest_Quarter` - Most recent quarter (1-4)
- `Current_Period` - Human-readable description

**When to Update:**
- ✅ After loading each month's data → Update Latest_Month
- ✅ After loading new quarter → Update Latest_Quarter
- ✅ After loading new year → Add to Available_Years, update Latest_Year
- ✅ When adding historical data → Update Available_Years

**Why This Matters:**
When users ask for "current" or "latest" data, the AI knows to use your Latest_Month/Quarter/Year instead of today's real-world date.

**Example:**
If your data goes through December 2024, and user asks "show me current quarter", AI will use Q4 2024 (not whatever today's quarter is).

---

### **OPTIONAL: `data/business_glossary.csv`**
⚠️ **Currently NOT implemented** - but a template is provided for future enhancement.

Use this to add business context that can't be auto-discovered:
- Column definitions
- Business rules
- Valid value ranges
- Calculation formulas

**Example:**
```csv
Table,Column,Business_Definition,Valid_Values,Notes
dim_member,relationship_tier,Member's value tier,"Tier 1-4",Higher = more valuable
fact_account_opening,initial_deposit_amount,Opening deposit in USD,,Quality metric
```

---

## 🤖 What is AUTO-DISCOVERED (No Action Needed)

### ✅ Database Schema
The system automatically queries SQL Server to discover:
- All tables and columns
- Data types and lengths
- NULL/NOT NULL constraints
- Primary keys
- **Foreign key relationships** (NEW!)

**Query:** `INFORMATION_SCHEMA.TABLES` + `INFORMATION_SCHEMA.COLUMNS` + `sys.foreign_keys`

### ✅ Sample Data
Automatically fetches TOP 3 rows from each table to help the AI understand:
- Data patterns
- Value formats
- Real examples

### ✅ Relationships
Auto-discovers foreign keys:
```
fact_account_opening.branch_key → dim_branch.branch_key
fact_account_opening.member_key → dim_member.member_key
```

This helps the AI know **which tables to JOIN** automatically!

---

## 📁 File Structure

```
data/
├── table_keywords.csv                    ← YOU MAINTAIN (keyword mapping)
├── database_documentation.csv            ← YOU MAINTAIN (RAG docs)
├── date_range.csv                        ← YOU MAINTAIN (data periods)
├── business_glossary_TEMPLATE.csv        ← Template only (not implemented)
├── database_documentation.md             ← OLD - replaced by CSV version
├── flattened.csv                         ← OLD - can delete
├── normalised.csv                        ← OLD - can delete
├── documentation-one.csv                 ← OLD - can delete
├── flattened_rag.csv                     ← OLD - can delete
└── documentation.xlsx                    ← OLD - can delete

meta.csv                                  ← AUTO-GENERATED (in .gitignore)
```

### Files You **MAINTAIN** (Universal CSV Format):
- ✅ `data/table_keywords.csv` - Keyword-to-table mapping (REQUIRED)
- ✅ `data/database_documentation.csv` - RAG documentation (REQUIRED)
- ✅ `data/date_range.csv` - Available data periods (REQUIRED)

### Files You Can **DELETE**:
- ✅ `data/flattened.csv` - Replaced by `table_keywords.csv`
- ✅ `data/normalised.csv` - Not used
- ✅ `data/documentation-one.csv` - Not used
- ✅ `data/flattened_rag.csv` - Replaced by `database_documentation.csv`
- ✅ `data/documentation.xlsx` - Not used
- ✅ `data/database_documentation.md` - Replaced by CSV version
- ✅ `data/business_glossary_TEMPLATE.csv` - Template only (not implemented)

### Auto-Generated Files (Don't Edit):
- `meta.csv` - Cached metadata (regenerated on startup)

---

## 🔄 How It Works

### On Application Startup:

```
1. Read table_keywords.csv
   └── Extract unique table names

2. Auto-discover database schema
   ├── Query INFORMATION_SCHEMA for columns
   ├── Query sys.foreign_keys for relationships
   └── Build CREATE TABLE statements with FK info

3. Fetch sample data (TOP 3 rows per table)

4. Combine everything into enhanced schema

5. Create vector store for semantic search

6. Cache to meta.csv for debugging
```

### When User Asks a Question:

```
User: "Show me top 10 branches by new member acquisition"

1. Vector search finds: "branches" → dim_branch
                        "new member acquisition" → fact_account_opening

2. Retrieve schema with FK relationships:
   fact_account_opening.branch_key → dim_branch.branch_key

3. LLM generates SQL with proper JOINs:
   SELECT
       db.branch_name,
       COUNT(DISTINCT f.member_key) as new_members
   FROM fact_account_opening f
   INNER JOIN dim_branch db ON f.branch_key = db.branch_key
   GROUP BY db.branch_name
   ORDER BY new_members DESC

4. Execute query and return results
```

---

## 🚀 Quick Start

### Initial Setup (One-time):
1. Review `data/table_keywords.csv`
2. Add/modify keywords to match your business terminology
3. Restart the application

### Adding New Tables:
1. Add the table to your database
2. Add a row to `table_keywords.csv`:
   ```csv
   loan defaults,fact_loan_defaults,bad loans|delinquency
   ```
3. Restart the application
4. ✅ Schema auto-discovered!

### Troubleshooting:
- **Question not understood?** → Add more keywords to `table_keywords.csv`
- **Wrong table used?** → Make keywords more specific
- **Missing relationships?** → Check if FK exists in database (auto-discovered)

---

## 💡 Pro Tips

### Good Keyword Examples:
✅ **Specific:**
```csv
quarterly revenue,fact_account_balance,Q1|Q2|Q3|Q4 income
top performing branches,dim_branch,best branches|highest revenue
```

✅ **Multiple related terms:**
```csv
member churn,fact_member_relationship,attrition|member loss|retention
```

### Bad Keyword Examples:
❌ **Too generic:**
```csv
data,fact_account_opening,information
```

❌ **Missing variations:**
```csv
member,dim_member,
```
(Should include: "members", "customer", "account holder")

---

## 📊 Current Status

### Automated:
- ✅ Table/column discovery
- ✅ Data types
- ✅ Primary keys
- ✅ **Foreign key relationships** (NEW!)
- ✅ Sample data
- ✅ CREATE TABLE generation

### Manual (Required):
- 📝 Keyword-to-table mappings in `table_keywords.csv`

### Manual (Optional):
- 📝 Business glossary (not yet implemented)

---

## 🔮 Future Enhancements

### Planned:
1. Business glossary integration
2. Auto-generate keywords from table/column names
3. Learn from user queries (which questions → which tables)
4. Confidence scoring for table selection

### Want to contribute?
Edit the files in `app_init/` to extend the auto-discovery logic!
