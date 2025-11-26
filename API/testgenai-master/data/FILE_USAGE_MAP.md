# Data Files Usage Map

## Current Files in data/

```
data/
├── date_range.json                    ✅ ACTIVE - Used by prompts
├── database_documentation.json        ✅ ACTIVE - Used by RAG & prompts
├── table_keywords.json                ✅ ACTIVE - Used by vector store
├── sql_generation_rules.json          ✅ ACTIVE - Used by prompts_v3
├── business_logic_rules.json          ✅ ACTIVE - Used by prompts_v3
└── prompt_structure_template.json     📘 DOCUMENTATION ONLY
```

---

## Detailed Usage

### 1. ✅ `date_range.json` - **ACTIVELY USED**

**Purpose:** Defines available data periods and current date context

**Used By:**
- ✅ `llm/prompts.py` (line 15) - Original prompt system
- ✅ `llm/prompts_v2.py` (line 26) - Enhanced prompts v2
- ✅ `llm/prompts_v3.py` (line 33) - Production prompts v3

**Loaded At:** Application startup

**Update Frequency:** Monthly (when new data is loaded)

**Example:**
```json
{
  "Latest_Year": "2024",
  "Latest_Month": "12",
  "Latest_Quarter": "4",
  "Current_Period": "Q4 2024"
}
```

---

### 2. ✅ `table_keywords.json` - **ACTIVELY USED**

**Purpose:** Maps keywords to tables for vector similarity search

**Used By:**
- ✅ `main.py` (line 28) - Creates smart vector store
- ✅ `app_init/init_app_v2.py` - Vector store initialization

**Loaded At:** Application startup (CRITICAL for vector search)

**Update Frequency:** As needed when adding new tables/keywords

**Example:**
```json
[
  {
    "keywords": "members",
    "tables": "dim_member",
    "related_keywords": "customers|account holders"
  }
]
```

**Important:** This is NOT used in prompts_v3 because we created a better version in `business_logic_rules.json` → `keyword_to_table_mapping`. But it's still needed for the vector store!

---

### 3. ✅ `database_documentation.json` - **ACTIVELY USED**

**Purpose:** Complete database schema documentation for RAG

**Used By:**
- ✅ `app_init/init_app_v2.py` - Creates RAG vector store
- ✅ `util/util.py` (line 80) - Provides context for queries
- ✅ `llm/prompts_v3.py` (line 36) - Loaded but not currently used in prompts

**Loaded At:** Application startup (for RAG vector store)

**Update Frequency:** When schema changes

**Size:** 190 lines, 48 documentation sections

**Example:**
```json
[
  {
    "section": "Table - dim_member",
    "content": "Member demographic and profile information..."
  }
]
```

---

### 4. ✅ `sql_generation_rules.json` - **ACTIVELY USED (NEW)**

**Purpose:** Generic SQL generation rules (database-agnostic)

**Used By:**
- ✅ `llm/prompts_v2.py` (line 41)
- ✅ `llm/prompts_v3.py` (line 34)

**Loaded At:** When generating SQL prompts

**Update Frequency:** Rarely (only when adding new SQL patterns)

**Key Contents:**
- Generic SQL syntax rules
- Data type conversion rules
- Common mistakes and fixes
- Join patterns

---

### 5. ✅ `business_logic_rules.json` - **ACTIVELY USED (NEW)**

**Purpose:** Domain-specific business logic for credit union

**Used By:**
- ✅ `llm/prompts_v3.py` (line 35)

**Loaded At:** When generating SQL prompts

**Update Frequency:** As needed when business rules change

**Key Contents:**
- Business rules (new member acquisition, active records)
- Keyword to table mapping (better version of table_keywords.json)
- Common metrics and formulas
- Table usage patterns
- Date patterns

---

### 6. 📘 `prompt_structure_template.json` - **DOCUMENTATION ONLY**

**Purpose:** Blueprint/documentation for prompt structure

**Used By:**
- ❌ NOT loaded by any code
- 📘 Used as reference documentation only

**What It Does:**
- Documents the prompt assembly process
- Shows how sections are organized
- Provides customization guide
- Template for future enhancements

**Should We Keep It?** ✅ YES - It's valuable documentation

---

## Redundancy Analysis

### Keyword Mapping: Duplicate but Both Needed

**In `table_keywords.json`:** (Array format)
```json
[
  {"keywords": "members", "tables": "dim_member"}
]
```
**Used by:** Vector store for similarity search

**In `business_logic_rules.json`:** (Object format)
```json
{
  "keyword_to_table_mapping": {
    "members": ["dim_member"]
  }
}
```
**Used by:** Prompt generation

**Recommendation:** ✅ **KEEP BOTH**
- Different formats serve different purposes
- Vector store needs array format
- Prompts use cleaner object format
- Small file, low maintenance cost

---

## Usage Summary

| File | Used By | Critical? | Update Frequency |
|------|---------|-----------|------------------|
| `date_range.json` | Prompts (all versions) | ✅ YES | Monthly |
| `table_keywords.json` | Vector store | ✅ YES | As needed |
| `database_documentation.json` | RAG vector store | ✅ YES | When schema changes |
| `sql_generation_rules.json` | Prompts v2/v3 | ✅ YES (for v3) | Rarely |
| `business_logic_rules.json` | Prompts v3 | ✅ YES (for v3) | As needed |
| `prompt_structure_template.json` | Documentation | 📘 NO | N/A |

---

## Migration Status

### Currently Active:
- ✅ `prompts.py` + original 3 files (date_range, table_keywords, database_documentation)
- ✅ `prompts_v3.py` + all 5 data files

### To Transition:
1. **Test `prompts_v3.py`** thoroughly
2. **Switch imports** from `prompts.py` to `prompts_v3.py`
3. **Keep all data files** - they're all being used!

---

## Cleanup Recommendation

### Keep All Files ✅

**Why?**
- ✅ `date_range.json` - Core functionality
- ✅ `table_keywords.json` - Vector store needs it
- ✅ `database_documentation.json` - RAG needs it
- ✅ `sql_generation_rules.json` - Prompts v3 needs it
- ✅ `business_logic_rules.json` - Prompts v3 needs it
- ✅ `prompt_structure_template.json` - Good documentation

**Total:** 6 files, all serving a purpose

---

## Quick Reference

### When to Update Each File:

**Monthly:**
- `date_range.json` - Update when new data is loaded

**When Schema Changes:**
- `database_documentation.json` - Update table descriptions
- `table_keywords.json` - Add new table keywords

**When Business Rules Change:**
- `business_logic_rules.json` - Update metrics, rules, patterns

**Rarely:**
- `sql_generation_rules.json` - Only for new SQL patterns
- `prompt_structure_template.json` - Only for documentation updates

---

**Last Updated:** 2025-01-22
