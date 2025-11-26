# Date Range Source - CSV vs Hardcoded

## Quick Answer

**PRIMARY SOURCE: `data/date_range.csv`** ✅ (This is what you should use!)
**FALLBACK: Hardcoded values** (Only if CSV fails to load)

---

## How It Works - Step by Step

```
┌─────────────────────────────────────────────────────────┐
│  API Server Starts                                      │
│  get_ms_sql_prompt() is called                          │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  load_date_range_info() function runs                   │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ Try to load CSV       │
        │ data/date_range.csv   │
        └───────┬───────────────┘
                │
        ┌───────┴───────┐
        │               │
        ▼               ▼
    SUCCESS?         FAIL?
        │               │
        │               │
        ▼               ▼
┌───────────────┐   ┌──────────────────────┐
│  ✅ USE CSV   │   │  ⚠️  USE HARDCODED   │
│               │   │      FALLBACK        │
│ Latest_Year:  │   │                      │
│    2024       │   │  Latest_Year:        │
│               │   │     2024             │
│ (from CSV)    │   │                      │
│               │   │  (from code)         │
│               │   │                      │
│ Notes:        │   │  Notes:              │
│  "Data is     │   │   "FALLBACK VALUES"  │
│   available   │   │                      │
│   from..."    │   │  ⚠️ Console warning: │
│               │   │  "Could not load     │
│               │   │   date_range.csv"    │
└───────┬───────┘   └──────────┬───────────┘
        │                      │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  LLM Receives:       │
        │  Latest_Year: 2024   │
        │  Available: 2023,24  │
        └──────────────────────┘
```

---

## Current Configuration

### CSV File Contents (`data/date_range.csv`):

```csv
Attribute,Value
Available_Years,"2023, 2024"
Latest_Year,2024
Latest_Month,12
Latest_Quarter,4
Current_Period,"Q4 2024 (October, November, December)"
Notes,"Data is available from January 2023 to December 2024"
```

### Hardcoded Fallback (`llm/prompts.py` lines 30-36):

```python
return {
    'Latest_Year': '2024',
    'Latest_Month': '12',
    'Latest_Quarter': '4',
    'Available_Years': '2023, 2024',
    'Current_Period': 'Q4 2024 (October, November, December)',
    'Notes': 'FALLBACK VALUES - date_range.csv failed to load'
}
```

**Notice:** Both have the same values! This ensures consistency.

---

## How to Tell Which Source Is Being Used

### Method 1: Check Console Logs

When API starts, look for warnings:

```
✅ CSV IS LOADING:
   - No warnings in console
   - Everything works silently

❌ FALLBACK IS BEING USED:
   ⚠️ CRITICAL WARNING: Could not load date_range.csv: [error message]
   ⚠️ Using HARDCODED fallback values. UPDATE date_range.csv to fix this!
```

### Method 2: Run Test Script

```bash
cd "C:\Users\ddunga\Downloads\DataSense 1\DataSense\API\testgenai-master"
python test_date_range_loading.py
```

Output will show:
```
SOURCE: CSV FILE (data/date_range.csv)          ✅ Good!
   or
SOURCE: HARDCODED FALLBACK (CSV failed to load!) ❌ Problem!
```

### Method 3: Check the `Notes` Field

If you can access the date_info dict:
- CSV loaded: `Notes = "Data is available from January 2023 to December 2024"`
- Fallback used: `Notes = "FALLBACK VALUES - date_range.csv failed to load"`

---

## What You Should Do

### ✅ RECOMMENDED: Use the CSV (Already Configured!)

1. **Keep `data/date_range.csv` updated** with your actual data range
2. The API will automatically load it
3. Update it when you load new data

**Current CSV values are correct:**
- Latest_Year: 2024 ✅
- Available_Years: 2023, 2024 ✅

### When to Update the CSV:

**Example: When January 2025 data arrives**

Edit `data/date_range.csv`:
```csv
Attribute,Value
Available_Years,"2023, 2024, 2025"
Latest_Year,2025
Latest_Month,1
Latest_Quarter,1
Current_Period,"Q1 2025 (January, February, March)"
Notes,"Data is available from January 2023 to January 2025"
```

**ALSO update the hardcoded fallback** in `llm/prompts.py` to match!

---

## Why Have Both CSV and Hardcoded?

| Scenario | What Happens | Why It's Good |
|----------|--------------|---------------|
| **Normal operation** | CSV loads successfully | ✅ Easy to update without code changes |
| **CSV file missing** | Hardcoded fallback kicks in | ✅ API doesn't crash, still works |
| **Pandas import fails** | Hardcoded fallback kicks in | ✅ Graceful degradation |
| **File permission error** | Hardcoded fallback kicks in | ✅ System remains operational |

**Defense in depth:** CSV for flexibility, hardcoded for reliability.

---

## Common Issues

### Issue 1: "I updated the CSV but queries still use old dates"

**Solution:** Restart the API server. Date info is loaded at startup.

```bash
# Stop the server
Ctrl + C

# Start again
uvicorn main:app --reload
```

### Issue 2: "How do I know if CSV is loading?"

**Solution:** Run the test script:
```bash
python test_date_range_loading.py
```

### Issue 3: "Should I update the hardcoded values when I update CSV?"

**YES!** Keep them in sync. The hardcoded values are a safety net, but should match your CSV.

---

## Summary

### Current State:
- ✅ CSV file exists: `data/date_range.csv`
- ✅ CSV has correct values: Latest_Year = 2024
- ✅ Hardcoded fallback matches CSV values
- ✅ Both configured correctly for 2023-2024 data range

### Your Question Answered:

**Q: "Are we taking date range from CSV or is it hardcoded?"**

**A: PRIMARY = CSV file (`data/date_range.csv`)** ✅

The hardcoded values are only a **safety fallback** in case the CSV fails to load.

### To Verify:
```bash
python test_date_range_loading.py
```

This will show you exactly which source is being used right now.

---

## Files Reference

| File | Purpose | Action Required |
|------|---------|----------------|
| `data/date_range.csv` | **PRIMARY date source** | Update when new data arrives |
| `llm/prompts.py` (lines 30-36) | Fallback values | Update to match CSV |
| `test_date_range_loading.py` | Test which source is used | Run to verify |

**Bottom line:** Your CSV is the source of truth. The hardcoded values are there "just in case."
