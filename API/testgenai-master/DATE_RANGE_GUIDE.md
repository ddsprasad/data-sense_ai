# Date Range Configuration Guide

## Overview

The `data/date_range.csv` file defines what year, month, and quarter data is available in your database. The AI prompts use this information instead of assuming the current real-world date.

**File**: `data/date_range.csv`

---

## Why This File is Needed

### Problem:
- System was using `datetime.now()` to get current year/month
- But your database might not have data for today's date
- Users asking for "current" or "latest" data would get incorrect SQL queries

### Solution:
- Define what data periods actually exist in your database
- AI prompts reference these values instead of real-world current date
- Users get accurate queries based on available data

---

## CSV Format

```csv
Attribute,Value
Available_Years,"2023, 2024"
Available_Months,"1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12"
Available_Quarters,"1, 2, 3, 4"
Latest_Year,2024
Latest_Month,12
Latest_Quarter,4
Current_Period,"Q4 2024 (October, November, December)"
Notes,"Data is available from January 2023 to December 2024"
```

---

## Column Definitions

### Attribute Column:
- `Available_Years` - Which years have data in the database
- `Available_Months` - Which months have data (1-12)
- `Available_Quarters` - Which quarters have data (1-4)
- `Latest_Year` - The most recent year with data
- `Latest_Month` - The most recent month with data (1-12)
- `Latest_Quarter` - The most recent quarter with data (1-4)
- `Current_Period` - Human-readable description of latest period
- `Notes` - Any additional context about data availability

### Value Column:
- The actual value for each attribute
- Use commas to separate multiple values (e.g., "2023, 2024")
- Single values for Latest_* attributes (e.g., "2024")

---

## How This is Used in Prompts

The prompts include this information in the "Data Availability" section:

```
Data Availability:
- Available Years: 2023, 2024
- Available Quarters: 1, 2, 3, 4
- Latest Data Period: Q4 2024 (October, November, December)
- Latest Year: 2024
- Latest Month: 12
- Latest Quarter: 4

When users ask for "current" or "latest" data, use the Latest Year (2024),
Latest Month (12), or Latest Quarter (4) from the data availability above.
```

### Example User Questions:

**User asks**: "Show me current quarter performance"
**AI knows**: Latest Quarter = 4, Latest Year = 2024
**SQL generates**: `WHERE quarter = 4 AND year = 2024`

**User asks**: "What's the latest monthly data?"
**AI knows**: Latest Month = 12, Latest Year = 2024
**SQL generates**: `WHERE month = 12 AND year = 2024`

---

## When to Update This File

### 1. **Monthly Data Load**
After loading new month's data:
```csv
Latest_Year,2024
Latest_Month,12  ← Update to 13 (then becomes January 2025)
Latest_Quarter,4
```

### 2. **New Quarter**
When quarter changes:
```csv
Latest_Year,2025  ← Increment if year changed
Latest_Month,1    ← Reset to 1 for Q1
Latest_Quarter,1  ← Update quarter
Current_Period,"Q1 2025 (January, February, March)"
```

### 3. **New Year**
When loading new year's data:
```csv
Available_Years,"2023, 2024, 2025"  ← Add new year
Latest_Year,2025
Latest_Month,1
Latest_Quarter,1
```

### 4. **Historical Data Added**
When loading older historical data:
```csv
Available_Years,"2022, 2023, 2024"  ← Add 2022
Notes,"Data is available from January 2022 to December 2024"
```

---

## Maintenance Examples

### Example 1: Monthly Update (November → December 2024)

**Before:**
```csv
Latest_Year,2024
Latest_Month,11
Latest_Quarter,4
Current_Period,"Q4 2024 (October, November, December)"
```

**After:**
```csv
Latest_Year,2024
Latest_Month,12
Latest_Quarter,4
Current_Period,"Q4 2024 (October, November, December)"
```

---

### Example 2: Quarter Change (Q4 2024 → Q1 2025)

**Before:**
```csv
Available_Years,"2023, 2024"
Latest_Year,2024
Latest_Month,12
Latest_Quarter,4
Current_Period,"Q4 2024 (October, November, December)"
```

**After:**
```csv
Available_Years,"2023, 2024, 2025"
Latest_Year,2025
Latest_Month,1
Latest_Quarter,1
Current_Period,"Q1 2025 (January, February, March)"
Notes,"Data is available from January 2023 to January 2025"
```

---

### Example 3: Partial Year Data

If you only have Q1 and Q2 data for 2024:

```csv
Attribute,Value
Available_Years,"2023, 2024"
Available_Months,"1, 2, 3, 4, 5, 6"
Available_Quarters,"1, 2"
Latest_Year,2024
Latest_Month,6
Latest_Quarter,2
Current_Period,"Q2 2024 (April, May, June)"
Notes,"2023 has full year data. 2024 has only Q1 and Q2 data (Jan-Jun)"
```

---

### Example 4: Adding Historical Data

If you load 2021 and 2022 data:

```csv
Attribute,Value
Available_Years,"2021, 2022, 2023, 2024"
Available_Months,"1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12"
Available_Quarters,"1, 2, 3, 4"
Latest_Year,2024
Latest_Month,12
Latest_Quarter,4
Current_Period,"Q4 2024 (October, November, December)"
Notes,"Data is available from January 2021 to December 2024 (4 full years)"
```

---

## Best Practices

### 1. **Update After Data Loads**
- Update this file immediately after loading new data
- Don't wait until users report issues

### 2. **Be Accurate**
- Only list periods that actually have data
- If December 2024 has no data yet, don't mark it as available

### 3. **Test After Changes**
- Restart the application after updating
- Test with questions like "show me latest data" or "current quarter"
- Verify SQL queries use correct dates

### 4. **Document Gaps**
- Use the Notes field to explain any gaps
- Example: "2023 Q3 data is missing due to system migration"

### 5. **Keep It Simple**
- Don't overthink Available_Months and Available_Quarters
- If you have complete years, just use "1, 2, 3, ..., 12" and "1, 2, 3, 4"
- The Latest_* values are what matter most

---

## Validation Checklist

After editing, verify:

- [ ] Latest_Year is in Available_Years list
- [ ] Latest_Month is between 1-12
- [ ] Latest_Quarter is between 1-4
- [ ] Latest_Month matches Latest_Quarter (Q1=1-3, Q2=4-6, Q3=7-9, Q4=10-12)
- [ ] Current_Period description is accurate
- [ ] File saved as CSV format
- [ ] Server restarts successfully
- [ ] Test queries with "latest" or "current" in the question

---

## Month-Quarter Mapping Reference

| Month | Number | Quarter |
|-------|--------|---------|
| January | 1 | Q1 |
| February | 2 | Q1 |
| March | 3 | Q1 |
| April | 4 | Q2 |
| May | 5 | Q2 |
| June | 6 | Q2 |
| July | 7 | Q3 |
| August | 8 | Q3 |
| September | 9 | Q3 |
| October | 10 | Q4 |
| November | 11 | Q4 |
| December | 12 | Q4 |

---

## Troubleshooting

### Issue: AI using wrong dates
- Check if date_range.csv has correct Latest_* values
- Restart server after updating
- Verify CSV is being loaded (check console for warnings)

### Issue: "Could not load date_range.csv" warning
- Verify file exists in `data/` folder
- Check filename is exactly `date_range.csv`
- Verify CSV format is correct (Attribute,Value header)

### Issue: SQL queries fail with date errors
- Check if Latest_Month/Quarter values are valid (1-12, 1-4)
- Ensure dates match what's actually in dim_date or date columns
- Verify dim_date table has the expected year/month/quarter values

---

## Summary

The `date_range.csv` file tells the AI:
- **What data exists** in your database
- **When it ends** (latest period)
- **How to interpret** "current" or "latest" user requests

Update it monthly or quarterly to keep the AI aligned with your actual data!

**Location**: `data/date_range.csv`
**Updates needed**: After each data load (monthly/quarterly)
**Impact**: Affects all SQL queries that reference dates, quarters, or "current" periods
