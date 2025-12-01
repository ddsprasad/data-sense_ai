"""
Demo SQL cache for pre-defined questions.
The system checks this cache first before hitting LLM services.
If a match is found, the cached SQL is executed directly.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import threading

# ============================================
# SHORT-TERM MEMORY FOR FOLLOW-UP CONTEXT
# ============================================
# Stores the last question's SQL and result for each user/session
# This allows follow-up questions to quickly access the original context

class ShortTermMemory:
    """
    In-memory cache for storing original question context.
    Used by follow-up questions to get parent SQL quickly.
    """
    def __init__(self, ttl_minutes: int = 30):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._ttl = timedelta(minutes=ttl_minutes)

    def store_context(self, question_id: str, data: Dict[str, Any]):
        """Store context for a question (SQL, result, etc.)"""
        with self._lock:
            self._store[question_id] = {
                "data": data,
                "timestamp": datetime.now()
            }
            # Clean old entries
            self._cleanup()

    def get_context(self, question_id: str) -> Optional[Dict[str, Any]]:
        """Get stored context for a question"""
        with self._lock:
            entry = self._store.get(question_id)
            if entry:
                # Check if still valid
                if datetime.now() - entry["timestamp"] < self._ttl:
                    return entry["data"]
                else:
                    del self._store[question_id]
            return None

    def _cleanup(self):
        """Remove expired entries"""
        now = datetime.now()
        expired = [k for k, v in self._store.items()
                   if now - v["timestamp"] >= self._ttl]
        for k in expired:
            del self._store[k]

# Global short-term memory instance
_short_term_memory = ShortTermMemory(ttl_minutes=30)

def store_question_context(question_id: str, sql: str, result: Any = None, question_text: str = None):
    """
    Store the context of an original question for follow-up use.
    Call this after successfully answering an original question.
    """
    _short_term_memory.store_context(question_id, {
        "sql": sql,
        "result": result,
        "question": question_text,
        "stored_at": datetime.now().isoformat()
    })

def get_question_context(question_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the stored context for a question.
    Used by follow-up questions to quickly get parent SQL.
    """
    return _short_term_memory.get_context(question_id)


# Demo additional insights - maps original questions to their insight question
# The insight question will be asked and answered automatically
DEMO_ADDITIONAL_INSIGHTS = {
    "show me our top 3 branches by new member acquisition this quarter with their average initial deposit":
        "Which of those branches have the highest cross-sell rate within 90 days?",
    "show me our top 10 branches by new member acquisition this quarter with their average initial deposit":
        "Which of those branches have the highest cross-sell rate within 90 days?",
    "what are our cross-sell success rates by product for members who joined in the last 6 months":
        "Which branches have the highest auto loan cross-sell?",
    "show me credit inquiries from the past quarter that didn't convert to loans":
        "What were the main reasons for not converting?",
    "which members did we lose to competitors last month and what products did they have with us":
        "What rates were competitors offering?",
    "identify members who are shopping for auto loans based on recent credit inquiries":
        "What's our current auto rate vs market?",
    "show me members with declining credit scores who have loans with us":
        "Which of those are at risk of default?",
    "what bureau tradelines show members shopping at other institutions":
        "Which of those are our high-value members?",
    "how does our new car loan volume correlate with local market data":
        "What's the trend for the past 3 months?",
    "what's the average member relationship value by member segment":
        "Which segment has the highest growth potential?",
    "show me a competitive analysis of our auto loan rates vs the top 3 competitors":
        "What would happen if we matched the lowest rate?",
    "show me all credit inquiries from the past month broken down by type":
        "Which type has the highest conversion rate?",
    "show me all members who had credit inquiries for auto loans in the last 30 days but didn't originate a loan with us":
        "What were the primary decline reasons?",
}


def get_demo_insight_question(original_question: str) -> str:
    """
    Get the hardcoded additional insight question for a demo question.

    Args:
        original_question: The original question asked

    Returns:
        The insight question to ask, or None if not a demo question
    """
    import re
    normalized = original_question.lower().strip()
    clean_question = re.sub(r'[^\w\s]', '', normalized)
    clean_question = ' '.join(clean_question.split())

    for demo_q, insight_q in DEMO_ADDITIONAL_INSIGHTS.items():
        clean_demo = re.sub(r'[^\w\s]', '', demo_q)
        clean_demo = ' '.join(clean_demo.split())
        if clean_question == clean_demo:
            return insight_q

    return None


# Demo question flows - maps original questions to their follow-up chains
# Each original question has a list of contextual follow-up questions
DEMO_QUESTION_FLOWS = {
    "show me our top 3 branches by new member acquisition this quarter with their average initial deposit": {
        "related_questions": [
            "Which of those branches have the highest cross-sell rate within 90 days?",
            "How does Downtown compare to last quarter?",
            "What products are new members opening most?"
        ]
    },
    "show me our top 10 branches by new member acquisition this quarter with their average initial deposit": {
        "related_questions": [
            "Which of those branches have the highest cross-sell rate within 90 days?",
            "How does the top branch compare to last quarter?",
            "What's the average deposit trend across these branches?"
        ]
    },
    "what are our cross-sell success rates by product for members who joined in the last 6 months": {
        "related_questions": [
            "Which branches have the highest auto loan cross-sell?",
            "What's the time to first cross-sell by product?",
            "How do cross-sell rates compare to last year?"
        ]
    },
    "show me credit inquiries from the past quarter that didn't convert to loans": {
        "related_questions": [
            "What were the main reasons for not converting?",
            "Which competitors captured these members?",
            "What's the total opportunity value lost?"
        ]
    },
    "which members did we lose to competitors last month and what products did they have with us": {
        "related_questions": [
            "What rates were competitors offering?",
            "Which competitor took the most members?",
            "What was the average relationship value of lost members?"
        ]
    },
    "identify members who are shopping for auto loans based on recent credit inquiries": {
        "related_questions": [
            "What's our current auto rate vs market?",
            "Which of these are high-value members?",
            "How many have existing loans with us?"
        ]
    },
    "show me members with declining credit scores who have loans with us": {
        "related_questions": [
            "Which of those are at risk of default?",
            "What's the total exposure amount?",
            "How has this trend changed over time?"
        ]
    },
    "what bureau tradelines show members shopping at other institutions": {
        "related_questions": [
            "Which of those are our high-value members?",
            "What products are they shopping for?",
            "How can we retain these members?"
        ]
    },
    "how does our new car loan volume correlate with local market data": {
        "related_questions": [
            "What's the trend for the past 3 months?",
            "Which dealers are we partnering with most?",
            "How does our market share compare to competitors?"
        ]
    },
    "what's the average member relationship value by member segment": {
        "related_questions": [
            "Which segment has the highest growth potential?",
            "What products drive the most value?",
            "How do segments compare across branches?"
        ]
    },
    "show me a competitive analysis of our auto loan rates vs the top 3 competitors": {
        "related_questions": [
            "What would happen if we matched the lowest rate?",
            "Which competitor is gaining market share?",
            "How have competitor rates changed this year?"
        ]
    },
    "show me all credit inquiries from the past month broken down by type": {
        "related_questions": [
            "Which type has the highest conversion rate?",
            "What's the average amount requested by type?",
            "How does this compare to last month?"
        ]
    },
    "show me all members who had credit inquiries for auto loans in the last 30 days but didn't originate a loan with us": {
        "related_questions": [
            "What were the primary decline reasons?",
            "Which competitors did they go to?",
            "What's the total lost opportunity value?"
        ]
    },
}


def get_demo_related_questions(question: str) -> list:
    """
    Get hardcoded related/follow-up questions for a demo question.

    Args:
        question: The original question

    Returns:
        List of related questions or None if not a demo question
    """
    import re
    normalized = question.lower().strip()
    clean_question = re.sub(r'[^\w\s]', '', normalized)
    clean_question = ' '.join(clean_question.split())

    for demo_q, data in DEMO_QUESTION_FLOWS.items():
        clean_demo = re.sub(r'[^\w\s]', '', demo_q)
        clean_demo = ' '.join(clean_demo.split())
        if clean_question == clean_demo:
            return data.get("related_questions", [])

    return None


# Demo questions with their SQL queries
# Format: normalized_question -> {sql, response_type_data}
DEMO_SQL_CACHE = {
    # ============================================
    # OPTION 1: Member Acquisition & Cross-Sell Analysis
    # ============================================

    # Q1: Top branches by new member acquisition
    "show me our top 3 branches by new member acquisition this quarter with their average initial deposit": {
        "sql": """
SELECT TOP 3
    b.branch_name,
    COUNT(DISTINCT m.member_id) as new_members,
    AVG(ao.initial_deposit_amount) as avg_initial_deposit,
    SUM(ao.initial_deposit_amount) as total_deposits
FROM dim_member m
JOIN dim_branch b ON m.branch_id = b.branch_id
JOIN fact_account_opening ao ON m.member_id = ao.member_id
JOIN dim_date d ON ao.date_id = d.date_id
WHERE d.quarter = 4 AND d.year = 2024
  AND m.membership_date >= '2024-10-01'
GROUP BY b.branch_name
ORDER BY new_members DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q1 Follow-up: Which branches have the highest cross-sell rate within 90 days
    # Only looks at the TOP 3 branches from the original question
    "which of those branches have the highest cross-sell rate within 90 days": {
        "sql": """
WITH Top3Branches AS (
    SELECT TOP 3
        b.branch_id,
        b.branch_name,
        COUNT(DISTINCT m.member_id) as new_members
    FROM dim_member m
    JOIN dim_branch b ON m.branch_id = b.branch_id
    JOIN fact_account_opening ao ON m.member_id = ao.member_id
    JOIN dim_date d ON ao.date_id = d.date_id
    WHERE d.quarter = 4 AND d.year = 2024
      AND m.membership_date >= '2024-10-01'
    GROUP BY b.branch_id, b.branch_name
    ORDER BY new_members DESC
)
SELECT
    t.branch_name,
    t.new_members,
    COUNT(DISTINCT CASE WHEN bmp.product_id IS NOT NULL
        AND bmp.enrollment_date <= DATEADD(day, 90, m.membership_date)
        THEN m.member_id END) as members_with_cross_sell,
    CAST(COUNT(DISTINCT CASE WHEN bmp.product_id IS NOT NULL
        AND bmp.enrollment_date <= DATEADD(day, 90, m.membership_date)
        THEN m.member_id END) AS FLOAT) /
        NULLIF(t.new_members, 0) * 100 as cross_sell_rate_90_days,
    COUNT(DISTINCT bmp.product_id) as total_products_sold
FROM Top3Branches t
JOIN dim_member m ON m.branch_id = t.branch_id
LEFT JOIN bridge_member_product bmp ON m.member_id = bmp.member_id
WHERE m.membership_date >= '2024-10-01'
GROUP BY t.branch_name, t.new_members
ORDER BY cross_sell_rate_90_days DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q1 Follow-up: How does Downtown compare to last quarter
    "how does downtown compare to last quarter": {
        "sql": """
SELECT
    d.quarter,
    d.year,
    COUNT(DISTINCT m.member_id) as new_members,
    AVG(ao.initial_deposit_amount) as avg_initial_deposit,
    SUM(ao.initial_deposit_amount) as total_deposits
FROM dim_member m
JOIN dim_branch b ON m.branch_id = b.branch_id
JOIN fact_account_opening ao ON m.member_id = ao.member_id
JOIN dim_date d ON ao.date_id = d.date_id
WHERE b.branch_name = 'Downtown'
  AND d.year = 2024
  AND d.quarter IN (3, 4)
GROUP BY d.quarter, d.year
ORDER BY d.quarter
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q2: Cross-sell success rates by product
    "what are our cross-sell success rates by product for members who joined in the last 6 months": {
        "sql": """
SELECT
    p.product_name,
    p.product_category,
    COUNT(DISTINCT bmp.member_id) as members_with_product,
    COUNT(DISTINCT m.member_id) as total_new_members,
    CAST(COUNT(DISTINCT bmp.member_id) AS FLOAT) / NULLIF(COUNT(DISTINCT m.member_id), 0) * 100 as cross_sell_rate
FROM dim_member m
LEFT JOIN bridge_member_product bmp ON m.member_id = bmp.member_id
LEFT JOIN dim_product p ON bmp.product_id = p.product_id
WHERE m.membership_date >= DATEADD(month, -6, GETDATE())
GROUP BY p.product_name, p.product_category
ORDER BY cross_sell_rate DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q2 Follow-up: Which branches have the highest auto loan cross-sell
    "which branches have the highest auto loan cross-sell": {
        "sql": """
SELECT TOP 5
    b.branch_name,
    COUNT(DISTINCT CASE WHEN p.product_name LIKE '%Auto%' THEN bmp.member_id END) as auto_loan_members,
    COUNT(DISTINCT m.member_id) as total_new_members,
    CAST(COUNT(DISTINCT CASE WHEN p.product_name LIKE '%Auto%' THEN bmp.member_id END) AS FLOAT) /
    NULLIF(COUNT(DISTINCT m.member_id), 0) * 100 as auto_cross_sell_rate
FROM dim_member m
JOIN dim_branch b ON m.branch_id = b.branch_id
LEFT JOIN bridge_member_product bmp ON m.member_id = bmp.member_id
LEFT JOIN dim_product p ON bmp.product_id = p.product_id
WHERE m.membership_date >= DATEADD(month, -6, GETDATE())
GROUP BY b.branch_name
ORDER BY auto_cross_sell_rate DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q3: Credit inquiries not converted to loans
    "show me credit inquiries from the past quarter that didn't convert to loans": {
        "sql": """
SELECT
    ci.inquiry_id,
    m.first_name + ' ' + m.last_name as member_name,
    ci.inquiry_type,
    ci.inquiry_date,
    ci.requested_amount,
    ci.credit_score_at_inquiry,
    b.branch_name
FROM fact_credit_inquiry ci
JOIN dim_member m ON ci.member_id = m.member_id
JOIN dim_branch b ON m.branch_id = b.branch_id
JOIN dim_date d ON ci.date_id = d.date_id
LEFT JOIN fact_loan_origination lo ON ci.member_id = lo.member_id
    AND lo.origination_date > ci.inquiry_date
    AND lo.origination_date <= DATEADD(day, 90, ci.inquiry_date)
WHERE d.quarter = 4 AND d.year = 2024
  AND lo.loan_id IS NULL
ORDER BY ci.requested_amount DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q3 Follow-up: What were the main reasons for not converting
    "what were the main reasons for not converting": {
        "sql": """
SELECT
    ci.decline_reason,
    COUNT(*) as inquiry_count,
    AVG(ci.requested_amount) as avg_requested_amount,
    AVG(ci.credit_score_at_inquiry) as avg_credit_score
FROM fact_credit_inquiry ci
JOIN dim_date d ON ci.date_id = d.date_id
LEFT JOIN fact_loan_origination lo ON ci.member_id = lo.member_id
    AND lo.origination_date > ci.inquiry_date
    AND lo.origination_date <= DATEADD(day, 90, ci.inquiry_date)
WHERE d.quarter = 4 AND d.year = 2024
  AND lo.loan_id IS NULL
  AND ci.decline_reason IS NOT NULL
GROUP BY ci.decline_reason
ORDER BY inquiry_count DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q4: Members lost to competitors
    "which members did we lose to competitors last month and what products did they have with us": {
        "sql": """
SELECT
    m.member_id,
    m.first_name + ' ' + m.last_name as member_name,
    c.competitor_name,
    STRING_AGG(p.product_name, ', ') as products_held,
    mr.relationship_value,
    mr.tenure_months
FROM dim_member m
JOIN fact_member_relationship mr ON m.member_id = mr.member_id
JOIN dim_competitor c ON mr.lost_to_competitor_id = c.competitor_id
LEFT JOIN bridge_member_product bmp ON m.member_id = bmp.member_id
LEFT JOIN dim_product p ON bmp.product_id = p.product_id
WHERE mr.status = 'Closed'
  AND mr.closure_date >= DATEADD(month, -1, GETDATE())
GROUP BY m.member_id, m.first_name, m.last_name, c.competitor_name,
         mr.relationship_value, mr.tenure_months
ORDER BY mr.relationship_value DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q4 Follow-up: What rates were competitors offering
    "what rates were competitors offering": {
        "sql": """
SELECT
    c.competitor_name,
    c.product_type,
    c.interest_rate as competitor_rate,
    AVG(lo.interest_rate) as our_avg_rate,
    c.interest_rate - AVG(lo.interest_rate) as rate_difference,
    COUNT(DISTINCT mr.member_id) as members_lost
FROM dim_competitor c
JOIN fact_member_relationship mr ON c.competitor_id = mr.lost_to_competitor_id
LEFT JOIN fact_loan_origination lo ON lo.product_id IN (
    SELECT product_id FROM dim_product WHERE product_category = c.product_type
)
WHERE mr.status = 'Closed'
  AND mr.closure_date >= DATEADD(month, -1, GETDATE())
GROUP BY c.competitor_name, c.product_type, c.interest_rate
ORDER BY members_lost DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q5: Members shopping for auto loans
    "identify members who are shopping for auto loans based on recent credit inquiries": {
        "sql": """
SELECT
    m.member_id,
    m.first_name + ' ' + m.last_name as member_name,
    COUNT(ci.inquiry_id) as inquiry_count,
    MAX(ci.inquiry_date) as latest_inquiry,
    AVG(ci.requested_amount) as avg_requested_amount,
    MAX(cs.credit_score) as current_credit_score,
    mr.relationship_value
FROM dim_member m
JOIN fact_credit_inquiry ci ON m.member_id = ci.member_id
JOIN fact_credit_score cs ON m.member_id = cs.member_id
JOIN fact_member_relationship mr ON m.member_id = mr.member_id
WHERE ci.inquiry_type = 'Auto Loan'
  AND ci.inquiry_date >= DATEADD(day, -30, GETDATE())
  AND cs.score_date = (SELECT MAX(score_date) FROM fact_credit_score WHERE member_id = m.member_id)
GROUP BY m.member_id, m.first_name, m.last_name, mr.relationship_value
HAVING COUNT(ci.inquiry_id) >= 2
ORDER BY inquiry_count DESC, mr.relationship_value DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q5 Follow-up: What's our current auto rate vs market
    "what's our current auto rate vs market": {
        "sql": """
SELECT
    'Our Credit Union' as source,
    p.product_name,
    AVG(lo.interest_rate) as avg_rate,
    MIN(lo.interest_rate) as min_rate,
    MAX(lo.interest_rate) as max_rate
FROM fact_loan_origination lo
JOIN dim_product p ON lo.product_id = p.product_id
WHERE p.product_category = 'Auto Loan'
  AND lo.origination_date >= DATEADD(month, -3, GETDATE())
GROUP BY p.product_name
UNION ALL
SELECT
    c.competitor_name as source,
    c.product_type as product_name,
    c.interest_rate as avg_rate,
    c.interest_rate as min_rate,
    c.interest_rate as max_rate
FROM dim_competitor c
WHERE c.product_type = 'Auto Loan'
ORDER BY avg_rate
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q6: Members with declining credit scores
    "show me members with declining credit scores who have loans with us": {
        "sql": """
SELECT
    m.member_id,
    m.first_name + ' ' + m.last_name as member_name,
    cs_current.credit_score as current_score,
    cs_prev.credit_score as previous_score,
    cs_current.credit_score - cs_prev.credit_score as score_change,
    COUNT(DISTINCT lo.loan_id) as active_loans,
    SUM(lo.loan_amount) as total_loan_balance
FROM dim_member m
JOIN fact_credit_score cs_current ON m.member_id = cs_current.member_id
JOIN fact_credit_score cs_prev ON m.member_id = cs_prev.member_id
JOIN fact_loan_origination lo ON m.member_id = lo.member_id
WHERE cs_current.score_date = (SELECT MAX(score_date) FROM fact_credit_score WHERE member_id = m.member_id)
  AND cs_prev.score_date = (SELECT MAX(score_date) FROM fact_credit_score
                           WHERE member_id = m.member_id AND score_date < cs_current.score_date)
  AND cs_current.credit_score < cs_prev.credit_score
  AND lo.loan_status = 'Active'
GROUP BY m.member_id, m.first_name, m.last_name, cs_current.credit_score, cs_prev.credit_score
HAVING cs_current.credit_score - cs_prev.credit_score <= -20
ORDER BY score_change ASC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q6 Follow-up: Which of those are at risk of default
    "which of those are at risk of default": {
        "sql": """
SELECT
    m.member_id,
    m.first_name + ' ' + m.last_name as member_name,
    cs.credit_score as current_score,
    lo.loan_amount,
    lo.interest_rate,
    lo.days_past_due,
    CASE
        WHEN lo.days_past_due > 60 OR cs.credit_score < 600 THEN 'High Risk'
        WHEN lo.days_past_due > 30 OR cs.credit_score < 650 THEN 'Medium Risk'
        ELSE 'Low Risk'
    END as risk_level
FROM dim_member m
JOIN fact_credit_score cs ON m.member_id = cs.member_id
JOIN fact_loan_origination lo ON m.member_id = lo.member_id
WHERE cs.score_date = (SELECT MAX(score_date) FROM fact_credit_score WHERE member_id = m.member_id)
  AND lo.loan_status = 'Active'
  AND (lo.days_past_due > 0 OR cs.credit_score < 650)
ORDER BY
    CASE WHEN lo.days_past_due > 60 OR cs.credit_score < 600 THEN 1
         WHEN lo.days_past_due > 30 OR cs.credit_score < 650 THEN 2
         ELSE 3 END,
    lo.loan_amount DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q7: Bureau tradelines showing shopping behavior
    "what bureau tradelines show members shopping at other institutions": {
        "sql": """
SELECT
    m.member_id,
    m.first_name + ' ' + m.last_name as member_name,
    bt.tradeline_type,
    bt.institution_name,
    bt.inquiry_date,
    bt.credit_limit,
    bt.balance,
    mr.relationship_value
FROM dim_member m
JOIN fact_bureau_tradeline bt ON m.member_id = bt.member_id
JOIN fact_member_relationship mr ON m.member_id = mr.member_id
WHERE bt.inquiry_date >= DATEADD(day, -90, GETDATE())
  AND bt.institution_name NOT LIKE '%Our Credit Union%'
  AND bt.tradeline_type IN ('Auto Loan', 'Personal Loan', 'Credit Card', 'Mortgage')
ORDER BY mr.relationship_value DESC, bt.inquiry_date DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q7 Follow-up: Which of those are our high-value members
    "which of those are our high-value members": {
        "sql": """
SELECT
    m.member_id,
    m.first_name + ' ' + m.last_name as member_name,
    mr.relationship_value,
    mr.tenure_months,
    COUNT(DISTINCT bt.tradeline_id) as external_inquiries,
    STRING_AGG(DISTINCT bt.institution_name, ', ') as institutions_shopped,
    STRING_AGG(DISTINCT p.product_name, ', ') as products_with_us
FROM dim_member m
JOIN fact_member_relationship mr ON m.member_id = mr.member_id
JOIN fact_bureau_tradeline bt ON m.member_id = bt.member_id
LEFT JOIN bridge_member_product bmp ON m.member_id = bmp.member_id
LEFT JOIN dim_product p ON bmp.product_id = p.product_id
WHERE bt.inquiry_date >= DATEADD(day, -90, GETDATE())
  AND bt.institution_name NOT LIKE '%Our Credit Union%'
  AND mr.relationship_value >= 50000
GROUP BY m.member_id, m.first_name, m.last_name, mr.relationship_value, mr.tenure_months
ORDER BY mr.relationship_value DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q8: New car market correlation
    "how does our new car loan volume correlate with local market data": {
        "sql": """
SELECT
    d.month_name,
    d.year,
    COUNT(lo.loan_id) as our_auto_loans,
    SUM(lo.loan_amount) as our_volume,
    AVG(md.market_indicator_value) as market_index,
    AVG(md.new_car_sales) as market_new_car_sales,
    CAST(COUNT(lo.loan_id) AS FLOAT) / NULLIF(AVG(md.new_car_sales), 0) * 100 as market_share_pct
FROM dim_date d
LEFT JOIN fact_loan_origination lo ON d.date_id = lo.date_id
    AND lo.product_id IN (SELECT product_id FROM dim_product WHERE product_name LIKE '%New%Auto%')
LEFT JOIN fact_market_data md ON d.date_id = md.date_id
WHERE d.year = 2024
GROUP BY d.month_name, d.year, d.month
ORDER BY d.month
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q8 Follow-up: What's the trend for the past 3 months
    "what's the trend for the past 3 months": {
        "sql": """
SELECT
    d.month_name,
    d.year,
    COUNT(lo.loan_id) as auto_loans,
    SUM(lo.loan_amount) as loan_volume,
    AVG(lo.interest_rate) as avg_rate,
    LAG(COUNT(lo.loan_id)) OVER (ORDER BY d.year, d.month) as prev_month_loans,
    COUNT(lo.loan_id) - LAG(COUNT(lo.loan_id)) OVER (ORDER BY d.year, d.month) as month_over_month_change
FROM dim_date d
JOIN fact_loan_origination lo ON d.date_id = lo.date_id
JOIN dim_product p ON lo.product_id = p.product_id
WHERE p.product_category = 'Auto Loan'
  AND d.date >= DATEADD(month, -3, GETDATE())
GROUP BY d.month_name, d.year, d.month
ORDER BY d.year, d.month
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q9: Member relationship value by segment
    "what's the average member relationship value by member segment": {
        "sql": """
SELECT
    CASE
        WHEN mr.tenure_months < 12 THEN 'New (< 1 year)'
        WHEN mr.tenure_months < 36 THEN 'Established (1-3 years)'
        WHEN mr.tenure_months < 60 THEN 'Mature (3-5 years)'
        ELSE 'Loyal (5+ years)'
    END as member_segment,
    COUNT(DISTINCT m.member_id) as member_count,
    AVG(mr.relationship_value) as avg_relationship_value,
    SUM(mr.relationship_value) as total_value,
    AVG(COUNT(DISTINCT bmp.product_id)) OVER (PARTITION BY
        CASE
            WHEN mr.tenure_months < 12 THEN 'New'
            WHEN mr.tenure_months < 36 THEN 'Established'
            WHEN mr.tenure_months < 60 THEN 'Mature'
            ELSE 'Loyal'
        END) as avg_products_per_member
FROM dim_member m
JOIN fact_member_relationship mr ON m.member_id = mr.member_id
LEFT JOIN bridge_member_product bmp ON m.member_id = bmp.member_id
GROUP BY
    CASE
        WHEN mr.tenure_months < 12 THEN 'New (< 1 year)'
        WHEN mr.tenure_months < 36 THEN 'Established (1-3 years)'
        WHEN mr.tenure_months < 60 THEN 'Mature (3-5 years)'
        ELSE 'Loyal (5+ years)'
    END
ORDER BY avg_relationship_value DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q9 Follow-up: Which segment has the highest growth potential
    "which segment has the highest growth potential": {
        "sql": """
SELECT
    CASE
        WHEN mr.tenure_months < 12 THEN 'New (< 1 year)'
        WHEN mr.tenure_months < 36 THEN 'Established (1-3 years)'
        WHEN mr.tenure_months < 60 THEN 'Mature (3-5 years)'
        ELSE 'Loyal (5+ years)'
    END as member_segment,
    COUNT(DISTINCT m.member_id) as member_count,
    AVG(mr.relationship_value) as current_avg_value,
    AVG(cs.credit_score) as avg_credit_score,
    COUNT(DISTINCT CASE WHEN ci.inquiry_id IS NOT NULL THEN m.member_id END) as members_with_recent_inquiries,
    SUM(CASE WHEN bmp.product_id IS NULL THEN 1 ELSE 0 END) as cross_sell_opportunities
FROM dim_member m
JOIN fact_member_relationship mr ON m.member_id = mr.member_id
LEFT JOIN fact_credit_score cs ON m.member_id = cs.member_id
    AND cs.score_date = (SELECT MAX(score_date) FROM fact_credit_score WHERE member_id = m.member_id)
LEFT JOIN fact_credit_inquiry ci ON m.member_id = ci.member_id
    AND ci.inquiry_date >= DATEADD(day, -90, GETDATE())
LEFT JOIN bridge_member_product bmp ON m.member_id = bmp.member_id
GROUP BY
    CASE
        WHEN mr.tenure_months < 12 THEN 'New (< 1 year)'
        WHEN mr.tenure_months < 36 THEN 'Established (1-3 years)'
        WHEN mr.tenure_months < 60 THEN 'Mature (3-5 years)'
        ELSE 'Loyal (5+ years)'
    END
ORDER BY cross_sell_opportunities DESC, avg_credit_score DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q10: Competitive analysis
    "show me a competitive analysis of our auto loan rates vs the top 3 competitors": {
        "sql": """
SELECT
    'Our Credit Union' as institution,
    'Auto Loan' as product,
    AVG(lo.interest_rate) as current_rate,
    MIN(lo.interest_rate) as best_rate,
    COUNT(lo.loan_id) as loans_originated,
    SUM(lo.loan_amount) as total_volume
FROM fact_loan_origination lo
JOIN dim_product p ON lo.product_id = p.product_id
WHERE p.product_category = 'Auto Loan'
  AND lo.origination_date >= DATEADD(month, -3, GETDATE())
GROUP BY p.product_category
UNION ALL
SELECT TOP 3
    c.competitor_name as institution,
    c.product_type as product,
    c.interest_rate as current_rate,
    c.interest_rate as best_rate,
    c.estimated_loan_count as loans_originated,
    c.estimated_volume as total_volume
FROM dim_competitor c
WHERE c.product_type = 'Auto Loan'
ORDER BY current_rate ASC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q10 Follow-up: What would happen if we matched the lowest rate
    "what would happen if we matched the lowest rate": {
        "sql": """
WITH CurrentMetrics AS (
    SELECT
        AVG(lo.interest_rate) as current_avg_rate,
        COUNT(lo.loan_id) as current_loan_count,
        SUM(lo.loan_amount) as current_volume,
        SUM(lo.loan_amount * lo.interest_rate / 100) as current_interest_income
    FROM fact_loan_origination lo
    JOIN dim_product p ON lo.product_id = p.product_id
    WHERE p.product_category = 'Auto Loan'
      AND lo.origination_date >= DATEADD(month, -3, GETDATE())
),
LowestRate AS (
    SELECT MIN(interest_rate) as lowest_rate
    FROM dim_competitor
    WHERE product_type = 'Auto Loan'
)
SELECT
    cm.current_avg_rate,
    lr.lowest_rate as proposed_rate,
    cm.current_avg_rate - lr.lowest_rate as rate_reduction,
    cm.current_loan_count,
    CAST(cm.current_loan_count * 1.25 AS INT) as projected_loan_count,
    cm.current_volume,
    cm.current_volume * 1.25 as projected_volume,
    cm.current_interest_income,
    (cm.current_volume * 1.25) * (lr.lowest_rate / 100) as projected_interest_income
FROM CurrentMetrics cm, LowestRate lr
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # ============================================
    # OPTION 2: Credit Inquiry Analysis
    # ============================================

    # Q1: Credit inquiries breakdown
    "show me all credit inquiries from the past month broken down by type": {
        "sql": """
SELECT
    ci.inquiry_type,
    COUNT(*) as inquiry_count,
    COUNT(DISTINCT ci.member_id) as unique_members,
    AVG(ci.requested_amount) as avg_requested_amount,
    AVG(ci.credit_score_at_inquiry) as avg_credit_score
FROM fact_credit_inquiry ci
JOIN dim_date d ON ci.date_id = d.date_id
WHERE d.date >= DATEADD(month, -1, GETDATE())
GROUP BY ci.inquiry_type
ORDER BY inquiry_count DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q1 Follow-up: Which type has the highest conversion rate
    "which type has the highest conversion rate": {
        "sql": """
SELECT
    ci.inquiry_type,
    COUNT(ci.inquiry_id) as total_inquiries,
    COUNT(lo.loan_id) as converted_to_loans,
    CAST(COUNT(lo.loan_id) AS FLOAT) / NULLIF(COUNT(ci.inquiry_id), 0) * 100 as conversion_rate,
    AVG(CASE WHEN lo.loan_id IS NOT NULL THEN lo.loan_amount END) as avg_loan_amount
FROM fact_credit_inquiry ci
JOIN dim_date d ON ci.date_id = d.date_id
LEFT JOIN fact_loan_origination lo ON ci.member_id = lo.member_id
    AND lo.origination_date >= ci.inquiry_date
    AND lo.origination_date <= DATEADD(day, 90, ci.inquiry_date)
WHERE d.date >= DATEADD(month, -1, GETDATE())
GROUP BY ci.inquiry_type
ORDER BY conversion_rate DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q2: Inquiry to loan capture rate
    "what's our capture rate from inquiry to loan by product category": {
        "sql": """
SELECT
    p.product_category,
    COUNT(DISTINCT ci.inquiry_id) as total_inquiries,
    COUNT(DISTINCT lo.loan_id) as loans_originated,
    CAST(COUNT(DISTINCT lo.loan_id) AS FLOAT) / NULLIF(COUNT(DISTINCT ci.inquiry_id), 0) * 100 as capture_rate,
    AVG(DATEDIFF(day, ci.inquiry_date, lo.origination_date)) as avg_days_to_convert,
    SUM(lo.loan_amount) as total_loan_volume
FROM fact_credit_inquiry ci
JOIN dim_product p ON ci.product_id = p.product_id
LEFT JOIN fact_loan_origination lo ON ci.member_id = lo.member_id
    AND lo.product_id = ci.product_id
    AND lo.origination_date >= ci.inquiry_date
    AND lo.origination_date <= DATEADD(day, 90, ci.inquiry_date)
WHERE ci.inquiry_date >= DATEADD(quarter, -1, GETDATE())
GROUP BY p.product_category
ORDER BY capture_rate DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q2 Follow-up: How does this compare to last quarter
    "how does this compare to last quarter": {
        "sql": """
SELECT
    CASE WHEN d.quarter = 4 THEN 'Q4 2024' ELSE 'Q3 2024' END as period,
    p.product_category,
    COUNT(DISTINCT ci.inquiry_id) as total_inquiries,
    COUNT(DISTINCT lo.loan_id) as loans_originated,
    CAST(COUNT(DISTINCT lo.loan_id) AS FLOAT) / NULLIF(COUNT(DISTINCT ci.inquiry_id), 0) * 100 as capture_rate
FROM fact_credit_inquiry ci
JOIN dim_product p ON ci.product_id = p.product_id
JOIN dim_date d ON ci.date_id = d.date_id
LEFT JOIN fact_loan_origination lo ON ci.member_id = lo.member_id
    AND lo.product_id = ci.product_id
    AND lo.origination_date >= ci.inquiry_date
    AND lo.origination_date <= DATEADD(day, 90, ci.inquiry_date)
WHERE d.year = 2024 AND d.quarter IN (3, 4)
GROUP BY d.quarter, p.product_category
ORDER BY d.quarter DESC, capture_rate DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q3: Competitor capture
    "which competitors are capturing our members who inquired but didn't get a loan": {
        "sql": """
SELECT
    c.competitor_name,
    COUNT(DISTINCT ci.member_id) as members_captured,
    STRING_AGG(DISTINCT ci.inquiry_type, ', ') as inquiry_types,
    AVG(ci.requested_amount) as avg_amount_requested,
    AVG(mr.relationship_value) as avg_member_value_lost
FROM fact_credit_inquiry ci
JOIN dim_member m ON ci.member_id = m.member_id
JOIN fact_member_relationship mr ON m.member_id = mr.member_id
JOIN fact_bureau_tradeline bt ON m.member_id = bt.member_id
JOIN dim_competitor c ON bt.institution_name = c.competitor_name
LEFT JOIN fact_loan_origination lo ON ci.member_id = lo.member_id
    AND lo.origination_date >= ci.inquiry_date
    AND lo.origination_date <= DATEADD(day, 90, ci.inquiry_date)
WHERE ci.inquiry_date >= DATEADD(month, -3, GETDATE())
  AND lo.loan_id IS NULL
  AND bt.opened_date > ci.inquiry_date
GROUP BY c.competitor_name
ORDER BY members_captured DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q3 Follow-up: What products are they winning
    "what products are they winning": {
        "sql": """
SELECT
    c.competitor_name,
    bt.tradeline_type as product_won,
    COUNT(DISTINCT bt.member_id) as members_lost,
    AVG(bt.credit_limit) as avg_credit_limit,
    AVG(c.interest_rate) as competitor_rate,
    AVG(lo_our.interest_rate) as our_rate_for_similar
FROM fact_bureau_tradeline bt
JOIN dim_competitor c ON bt.institution_name = c.competitor_name
JOIN fact_credit_inquiry ci ON bt.member_id = ci.member_id
    AND ci.inquiry_date < bt.opened_date
LEFT JOIN fact_loan_origination lo_our ON ci.member_id = lo_our.member_id
    AND lo_our.origination_date >= ci.inquiry_date
WHERE bt.opened_date >= DATEADD(month, -3, GETDATE())
  AND bt.institution_name NOT LIKE '%Our Credit Union%'
GROUP BY c.competitor_name, bt.tradeline_type
ORDER BY members_lost DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q4: High credit score members not approved
    "show me members with credit score above 750 who inquired but weren't approved": {
        "sql": """
SELECT
    m.member_id,
    m.first_name + ' ' + m.last_name as member_name,
    ci.inquiry_type,
    ci.requested_amount,
    ci.credit_score_at_inquiry,
    ci.decline_reason,
    mr.relationship_value,
    mr.tenure_months
FROM fact_credit_inquiry ci
JOIN dim_member m ON ci.member_id = m.member_id
JOIN fact_member_relationship mr ON m.member_id = mr.member_id
WHERE ci.credit_score_at_inquiry >= 750
  AND ci.status = 'Declined'
  AND ci.inquiry_date >= DATEADD(month, -3, GETDATE())
ORDER BY ci.requested_amount DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q4 Follow-up: What were the decline reasons
    "what were the decline reasons": {
        "sql": """
SELECT
    ci.decline_reason,
    COUNT(*) as decline_count,
    AVG(ci.credit_score_at_inquiry) as avg_credit_score,
    AVG(ci.requested_amount) as avg_requested_amount,
    STRING_AGG(DISTINCT ci.inquiry_type, ', ') as inquiry_types
FROM fact_credit_inquiry ci
WHERE ci.credit_score_at_inquiry >= 750
  AND ci.status = 'Declined'
  AND ci.inquiry_date >= DATEADD(month, -3, GETDATE())
GROUP BY ci.decline_reason
ORDER BY decline_count DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q5: Inquiry patterns by demographics
    "what are the inquiry patterns by member demographics": {
        "sql": """
SELECT
    CASE
        WHEN DATEDIFF(year, m.date_of_birth, GETDATE()) < 30 THEN 'Under 30'
        WHEN DATEDIFF(year, m.date_of_birth, GETDATE()) < 45 THEN '30-44'
        WHEN DATEDIFF(year, m.date_of_birth, GETDATE()) < 60 THEN '45-59'
        ELSE '60+'
    END as age_group,
    ci.inquiry_type,
    COUNT(*) as inquiry_count,
    AVG(ci.requested_amount) as avg_amount,
    CAST(COUNT(CASE WHEN lo.loan_id IS NOT NULL THEN 1 END) AS FLOAT) /
        NULLIF(COUNT(*), 0) * 100 as conversion_rate
FROM fact_credit_inquiry ci
JOIN dim_member m ON ci.member_id = m.member_id
LEFT JOIN fact_loan_origination lo ON ci.member_id = lo.member_id
    AND lo.origination_date >= ci.inquiry_date
    AND lo.origination_date <= DATEADD(day, 90, ci.inquiry_date)
WHERE ci.inquiry_date >= DATEADD(quarter, -1, GETDATE())
GROUP BY
    CASE
        WHEN DATEDIFF(year, m.date_of_birth, GETDATE()) < 30 THEN 'Under 30'
        WHEN DATEDIFF(year, m.date_of_birth, GETDATE()) < 45 THEN '30-44'
        WHEN DATEDIFF(year, m.date_of_birth, GETDATE()) < 60 THEN '45-59'
        ELSE '60+'
    END,
    ci.inquiry_type
ORDER BY age_group, inquiry_count DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q5 Follow-up: Which age group has highest value potential
    "which age group has highest value potential": {
        "sql": """
SELECT
    CASE
        WHEN DATEDIFF(year, m.date_of_birth, GETDATE()) < 30 THEN 'Under 30'
        WHEN DATEDIFF(year, m.date_of_birth, GETDATE()) < 45 THEN '30-44'
        WHEN DATEDIFF(year, m.date_of_birth, GETDATE()) < 60 THEN '45-59'
        ELSE '60+'
    END as age_group,
    COUNT(DISTINCT m.member_id) as member_count,
    AVG(mr.relationship_value) as avg_current_value,
    AVG(cs.credit_score) as avg_credit_score,
    COUNT(DISTINCT ci.inquiry_id) as recent_inquiries,
    SUM(ci.requested_amount) as total_requested,
    AVG(mr.relationship_value) * COUNT(DISTINCT m.member_id) as total_value_potential
FROM dim_member m
JOIN fact_member_relationship mr ON m.member_id = mr.member_id
LEFT JOIN fact_credit_score cs ON m.member_id = cs.member_id
    AND cs.score_date = (SELECT MAX(score_date) FROM fact_credit_score WHERE member_id = m.member_id)
LEFT JOIN fact_credit_inquiry ci ON m.member_id = ci.member_id
    AND ci.inquiry_date >= DATEADD(quarter, -1, GETDATE())
GROUP BY
    CASE
        WHEN DATEDIFF(year, m.date_of_birth, GETDATE()) < 30 THEN 'Under 30'
        WHEN DATEDIFF(year, m.date_of_birth, GETDATE()) < 45 THEN '30-44'
        WHEN DATEDIFF(year, m.date_of_birth, GETDATE()) < 60 THEN '45-59'
        ELSE '60+'
    END
ORDER BY total_value_potential DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q6: Members with multiple inquiries not converted
    "identify members with multiple credit inquiries who haven't converted to loans": {
        "sql": """
SELECT
    m.member_id,
    m.first_name + ' ' + m.last_name as member_name,
    COUNT(ci.inquiry_id) as inquiry_count,
    STRING_AGG(ci.inquiry_type, ', ') as inquiry_types,
    SUM(ci.requested_amount) as total_requested,
    AVG(ci.credit_score_at_inquiry) as avg_credit_score,
    mr.relationship_value,
    mr.tenure_months
FROM dim_member m
JOIN fact_credit_inquiry ci ON m.member_id = ci.member_id
JOIN fact_member_relationship mr ON m.member_id = mr.member_id
LEFT JOIN fact_loan_origination lo ON ci.member_id = lo.member_id
    AND lo.origination_date >= ci.inquiry_date
WHERE ci.inquiry_date >= DATEADD(month, -6, GETDATE())
  AND lo.loan_id IS NULL
GROUP BY m.member_id, m.first_name, m.last_name, mr.relationship_value, mr.tenure_months
HAVING COUNT(ci.inquiry_id) >= 2
ORDER BY inquiry_count DESC, mr.relationship_value DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q6 Follow-up: What's the total opportunity value
    "what's the total opportunity value": {
        "sql": """
SELECT
    COUNT(DISTINCT m.member_id) as members_with_unconverted_inquiries,
    SUM(ci.requested_amount) as total_opportunity_value,
    AVG(ci.requested_amount) as avg_opportunity_per_member,
    AVG(mr.relationship_value) as avg_current_relationship_value,
    SUM(ci.requested_amount) * 0.05 as potential_annual_interest_revenue
FROM dim_member m
JOIN fact_credit_inquiry ci ON m.member_id = ci.member_id
JOIN fact_member_relationship mr ON m.member_id = mr.member_id
LEFT JOIN fact_loan_origination lo ON ci.member_id = lo.member_id
    AND lo.origination_date >= ci.inquiry_date
WHERE ci.inquiry_date >= DATEADD(month, -6, GETDATE())
  AND lo.loan_id IS NULL
""",
        "show_chart": 0,
        "show_sql": 1
    },

    # Q7: Delinquent members with new inquiries
    "show me members who became delinquent after making credit inquiries": {
        "sql": """
SELECT
    m.member_id,
    m.first_name + ' ' + m.last_name as member_name,
    ci.inquiry_type,
    ci.inquiry_date,
    lo.loan_id,
    lo.days_past_due,
    lo.loan_amount,
    lo.origination_date as delinquent_loan_date
FROM dim_member m
JOIN fact_credit_inquiry ci ON m.member_id = ci.member_id
JOIN fact_loan_origination lo ON m.member_id = lo.member_id
WHERE lo.days_past_due > 30
  AND ci.inquiry_date < lo.origination_date
  AND ci.inquiry_date >= DATEADD(year, -1, GETDATE())
ORDER BY lo.days_past_due DESC, lo.loan_amount DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q7 Follow-up: What's the total exposure
    "what's the total exposure": {
        "sql": """
SELECT
    COUNT(DISTINCT m.member_id) as delinquent_members,
    COUNT(DISTINCT lo.loan_id) as delinquent_loans,
    SUM(lo.loan_amount) as total_loan_exposure,
    SUM(lo.loan_amount * lo.days_past_due / 365 * lo.interest_rate / 100) as estimated_lost_interest,
    AVG(lo.days_past_due) as avg_days_past_due,
    SUM(CASE WHEN lo.days_past_due > 90 THEN lo.loan_amount ELSE 0 END) as severely_delinquent_exposure
FROM dim_member m
JOIN fact_credit_inquiry ci ON m.member_id = ci.member_id
JOIN fact_loan_origination lo ON m.member_id = lo.member_id
WHERE lo.days_past_due > 30
  AND ci.inquiry_date < lo.origination_date
  AND ci.inquiry_date >= DATEADD(year, -1, GETDATE())
""",
        "show_chart": 0,
        "show_sql": 1
    },

    # Q8: Credit utilization for inquiring members
    "what's the average credit utilization for members who made inquiries": {
        "sql": """
SELECT
    ci.inquiry_type,
    COUNT(DISTINCT ci.member_id) as inquiring_members,
    AVG(bt.balance * 1.0 / NULLIF(bt.credit_limit, 0)) * 100 as avg_utilization_pct,
    AVG(CASE WHEN lo.loan_id IS NOT NULL THEN bt.balance * 1.0 / NULLIF(bt.credit_limit, 0) END) * 100 as converted_utilization_pct,
    AVG(CASE WHEN lo.loan_id IS NULL THEN bt.balance * 1.0 / NULLIF(bt.credit_limit, 0) END) * 100 as not_converted_utilization_pct
FROM fact_credit_inquiry ci
JOIN fact_bureau_tradeline bt ON ci.member_id = bt.member_id
LEFT JOIN fact_loan_origination lo ON ci.member_id = lo.member_id
    AND lo.origination_date >= ci.inquiry_date
    AND lo.origination_date <= DATEADD(day, 90, ci.inquiry_date)
WHERE ci.inquiry_date >= DATEADD(quarter, -1, GETDATE())
  AND bt.tradeline_type = 'Credit Card'
GROUP BY ci.inquiry_type
ORDER BY avg_utilization_pct DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q8 Follow-up: How does this affect conversion
    "how does this affect conversion": {
        "sql": """
SELECT
    CASE
        WHEN bt.balance * 1.0 / NULLIF(bt.credit_limit, 0) < 0.3 THEN 'Low (< 30%)'
        WHEN bt.balance * 1.0 / NULLIF(bt.credit_limit, 0) < 0.5 THEN 'Medium (30-50%)'
        WHEN bt.balance * 1.0 / NULLIF(bt.credit_limit, 0) < 0.7 THEN 'High (50-70%)'
        ELSE 'Very High (> 70%)'
    END as utilization_band,
    COUNT(DISTINCT ci.inquiry_id) as total_inquiries,
    COUNT(DISTINCT lo.loan_id) as converted,
    CAST(COUNT(DISTINCT lo.loan_id) AS FLOAT) / NULLIF(COUNT(DISTINCT ci.inquiry_id), 0) * 100 as conversion_rate,
    AVG(ci.requested_amount) as avg_amount_requested
FROM fact_credit_inquiry ci
JOIN fact_bureau_tradeline bt ON ci.member_id = bt.member_id
LEFT JOIN fact_loan_origination lo ON ci.member_id = lo.member_id
    AND lo.origination_date >= ci.inquiry_date
    AND lo.origination_date <= DATEADD(day, 90, ci.inquiry_date)
WHERE ci.inquiry_date >= DATEADD(quarter, -1, GETDATE())
  AND bt.tradeline_type = 'Credit Card'
GROUP BY
    CASE
        WHEN bt.balance * 1.0 / NULLIF(bt.credit_limit, 0) < 0.3 THEN 'Low (< 30%)'
        WHEN bt.balance * 1.0 / NULLIF(bt.credit_limit, 0) < 0.5 THEN 'Medium (30-50%)'
        WHEN bt.balance * 1.0 / NULLIF(bt.credit_limit, 0) < 0.7 THEN 'High (50-70%)'
        ELSE 'Very High (> 70%)'
    END
ORDER BY conversion_rate DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q9: Time from inquiry to decision
    "what's the average time from inquiry to decision by branch": {
        "sql": """
SELECT
    b.branch_name,
    COUNT(ci.inquiry_id) as total_inquiries,
    AVG(DATEDIFF(day, ci.inquiry_date, ci.decision_date)) as avg_days_to_decision,
    MIN(DATEDIFF(day, ci.inquiry_date, ci.decision_date)) as min_days,
    MAX(DATEDIFF(day, ci.inquiry_date, ci.decision_date)) as max_days,
    CAST(COUNT(CASE WHEN ci.status = 'Approved' THEN 1 END) AS FLOAT) /
        NULLIF(COUNT(*), 0) * 100 as approval_rate
FROM fact_credit_inquiry ci
JOIN dim_member m ON ci.member_id = m.member_id
JOIN dim_branch b ON m.branch_id = b.branch_id
WHERE ci.inquiry_date >= DATEADD(quarter, -1, GETDATE())
  AND ci.decision_date IS NOT NULL
GROUP BY b.branch_name
ORDER BY avg_days_to_decision
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q9 Follow-up: Which branch is most efficient
    "which branch is most efficient": {
        "sql": """
SELECT
    b.branch_name,
    COUNT(ci.inquiry_id) as total_inquiries,
    AVG(DATEDIFF(day, ci.inquiry_date, ci.decision_date)) as avg_processing_days,
    CAST(COUNT(CASE WHEN ci.status = 'Approved' THEN 1 END) AS FLOAT) /
        NULLIF(COUNT(*), 0) * 100 as approval_rate,
    CAST(COUNT(CASE WHEN lo.loan_id IS NOT NULL THEN 1 END) AS FLOAT) /
        NULLIF(COUNT(*), 0) * 100 as conversion_rate,
    SUM(lo.loan_amount) as total_loan_volume,
    -- Efficiency score: faster processing + higher conversion = better
    (100 - AVG(DATEDIFF(day, ci.inquiry_date, ci.decision_date)) * 5) +
    (CAST(COUNT(CASE WHEN lo.loan_id IS NOT NULL THEN 1 END) AS FLOAT) /
        NULLIF(COUNT(*), 0) * 100) as efficiency_score
FROM fact_credit_inquiry ci
JOIN dim_member m ON ci.member_id = m.member_id
JOIN dim_branch b ON m.branch_id = b.branch_id
LEFT JOIN fact_loan_origination lo ON ci.member_id = lo.member_id
    AND lo.origination_date >= ci.inquiry_date
    AND lo.origination_date <= DATEADD(day, 90, ci.inquiry_date)
WHERE ci.inquiry_date >= DATEADD(quarter, -1, GETDATE())
  AND ci.decision_date IS NOT NULL
GROUP BY b.branch_name
ORDER BY efficiency_score DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q10: Credit score trends for inquiring members
    "show me credit score trends for members who made inquiries this quarter": {
        "sql": """
SELECT
    d.month_name,
    ci.inquiry_type,
    COUNT(DISTINCT ci.member_id) as inquiring_members,
    AVG(ci.credit_score_at_inquiry) as avg_score_at_inquiry,
    AVG(cs_current.credit_score) as avg_current_score,
    AVG(cs_current.credit_score - ci.credit_score_at_inquiry) as avg_score_change
FROM fact_credit_inquiry ci
JOIN dim_date d ON ci.date_id = d.date_id
JOIN fact_credit_score cs_current ON ci.member_id = cs_current.member_id
WHERE d.quarter = 4 AND d.year = 2024
  AND cs_current.score_date = (SELECT MAX(score_date) FROM fact_credit_score WHERE member_id = ci.member_id)
GROUP BY d.month_name, d.month, ci.inquiry_type
ORDER BY d.month, ci.inquiry_type
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # Q10 Follow-up: Are declining scores correlated with non-conversion
    "are declining scores correlated with non-conversion": {
        "sql": """
SELECT
    CASE
        WHEN cs_current.credit_score - ci.credit_score_at_inquiry > 20 THEN 'Score Improved (>20)'
        WHEN cs_current.credit_score - ci.credit_score_at_inquiry >= -20 THEN 'Score Stable (+/-20)'
        ELSE 'Score Declined (>20 drop)'
    END as score_trend,
    COUNT(DISTINCT ci.inquiry_id) as total_inquiries,
    COUNT(DISTINCT lo.loan_id) as converted,
    CAST(COUNT(DISTINCT lo.loan_id) AS FLOAT) / NULLIF(COUNT(DISTINCT ci.inquiry_id), 0) * 100 as conversion_rate,
    AVG(ci.credit_score_at_inquiry) as avg_score_at_inquiry,
    AVG(cs_current.credit_score) as avg_current_score
FROM fact_credit_inquiry ci
JOIN fact_credit_score cs_current ON ci.member_id = cs_current.member_id
LEFT JOIN fact_loan_origination lo ON ci.member_id = lo.member_id
    AND lo.origination_date >= ci.inquiry_date
    AND lo.origination_date <= DATEADD(day, 90, ci.inquiry_date)
WHERE ci.inquiry_date >= DATEADD(quarter, -1, GETDATE())
  AND cs_current.score_date = (SELECT MAX(score_date) FROM fact_credit_score WHERE member_id = ci.member_id)
GROUP BY
    CASE
        WHEN cs_current.credit_score - ci.credit_score_at_inquiry > 20 THEN 'Score Improved (>20)'
        WHEN cs_current.credit_score - ci.credit_score_at_inquiry >= -20 THEN 'Score Stable (+/-20)'
        ELSE 'Score Declined (>20 drop)'
    END
ORDER BY conversion_rate DESC
""",
        "show_chart": 1,
        "show_sql": 1
    },

    # ============================================
    # OPTION 3: Competitor Analysis
    # ============================================

    # Top competitors by loan capture
    "show me our top 5 competitors by loan capture from our members, with average loan amounts": {
        "sql": """
SELECT TOP 5
    c.competitor_name,
    COUNT(*) AS loan_captures,
    AVG(ci.requested_amount) AS avg_loan_amount
FROM fact_credit_inquiry ci
JOIN dim_competitor c ON ci.competitor_id = c.competitor_id
LEFT JOIN fact_loan_origination lo ON ci.member_id = lo.member_id
    AND lo.origination_date >= ci.inquiry_date
    AND lo.origination_date <= DATEADD(day, 90, ci.inquiry_date)
WHERE lo.loan_id IS NULL
  AND ci.inquiry_date >= DATEADD(month, -6, GETDATE())
GROUP BY c.competitor_name
ORDER BY loan_captures DESC
""",
        "show_chart": 1,
        "show_sql": 1
    }
}

# Legacy empty dict for backward compatibility
DEMO_RESPONSES = {}


def get_demo_sql(question: str) -> dict:
    """
    Get cached SQL for a demo question.

    Args:
        question: The user's question (case-insensitive)

    Returns:
        Dict with 'sql', 'show_chart', 'show_sql' or None if not found
    """
    normalized_question = question.lower().strip()

    # Direct match
    if normalized_question in DEMO_SQL_CACHE:
        return DEMO_SQL_CACHE[normalized_question]

    # Try fuzzy matching - remove punctuation and extra spaces
    import re
    clean_question = re.sub(r'[^\w\s]', '', normalized_question)
    clean_question = ' '.join(clean_question.split())

    for cached_question, data in DEMO_SQL_CACHE.items():
        clean_cached = re.sub(r'[^\w\s]', '', cached_question)
        clean_cached = ' '.join(clean_cached.split())
        if clean_question == clean_cached:
            return data

    return None


def get_demo_response(question: str, response_type: str = "original"):
    """
    Get a hardcoded demo response for a question.
    Legacy function for backward compatibility.

    Args:
        question: The user's question (case-insensitive)
        response_type: Type of response - 'original', 'related', 'insights', 'tags', 'chart'

    Returns:
        The demo response or None if not found
    """
    normalized_question = question.lower().strip()

    if normalized_question in DEMO_RESPONSES:
        return DEMO_RESPONSES[normalized_question].get(response_type)

    return None


# Follow-up SQL templates that use parent SQL as a CTE
# These templates have {parent_sql} placeholder that gets replaced with actual parent SQL
FOLLOWUP_SQL_TEMPLATES = {
    "which of those branches have the highest cross-sell rate within 90 days": """
WITH ParentResult AS (
    {parent_sql}
),
BranchMembers AS (
    SELECT
        pr.branch_name,
        m.member_id,
        m.membership_date
    FROM ParentResult pr
    JOIN dim_branch b ON b.branch_name = pr.branch_name
    JOIN dim_member m ON m.branch_id = b.branch_id
    WHERE m.membership_date >= '2024-10-01'
)
SELECT
    bm.branch_name,
    COUNT(DISTINCT bm.member_id) as new_members,
    COUNT(DISTINCT CASE WHEN bmp.product_id IS NOT NULL
        AND bmp.enrollment_date <= DATEADD(day, 90, bm.membership_date)
        THEN bm.member_id END) as members_with_cross_sell,
    CAST(COUNT(DISTINCT CASE WHEN bmp.product_id IS NOT NULL
        AND bmp.enrollment_date <= DATEADD(day, 90, bm.membership_date)
        THEN bm.member_id END) AS FLOAT) /
        NULLIF(COUNT(DISTINCT bm.member_id), 0) * 100 as cross_sell_rate_90_days
FROM BranchMembers bm
LEFT JOIN bridge_member_product bmp ON bm.member_id = bmp.member_id
GROUP BY bm.branch_name
ORDER BY cross_sell_rate_90_days DESC
""",
}


def get_followup_sql_with_parent(question: str, parent_sql: str) -> str:
    """
    Get follow-up SQL that uses the parent question's SQL as a CTE base.
    ALL follow-up questions use the original question's SQL as the foundation.

    Args:
        question: The follow-up question
        parent_sql: The SQL from the parent/original question

    Returns:
        SQL query that uses parent SQL as CTE and builds upon it
    """
    import re

    if not parent_sql:
        # No parent SQL available, fall back to static cached SQL
        demo_data = get_demo_sql(question)
        return demo_data.get("sql", "").strip() if demo_data else ""

    # Clean up parent SQL - remove trailing semicolons and whitespace
    parent_sql_clean = parent_sql.strip().rstrip(';')

    normalized_question = question.lower().strip()
    clean_question = re.sub(r'[^\w\s]', '', normalized_question)
    clean_question = ' '.join(clean_question.split())

    # Check if we have a specific template for this follow-up
    for template_question, sql_template in FOLLOWUP_SQL_TEMPLATES.items():
        clean_template = re.sub(r'[^\w\s]', '', template_question)
        clean_template = ' '.join(clean_template.split())
        if clean_question == clean_template:
            return sql_template.format(parent_sql=parent_sql_clean)

    # No specific template found - check if there's a CTE-enabled version in FOLLOWUP_CTE_QUERIES
    cte_query = FOLLOWUP_CTE_QUERIES.get(clean_question)
    if cte_query:
        return f"""WITH OriginalResult AS (
    {parent_sql_clean}
)
{cte_query}"""

    # Fall back to static cached SQL (non-CTE version)
    demo_data = get_demo_sql(question)
    if demo_data:
        return demo_data.get("sql", "").strip()

    return ""


# Follow-up queries that reference OriginalResult CTE
# These queries are designed to filter/aggregate based on the original question's result
FOLLOWUP_CTE_QUERIES = {
    # Cross-sell follow-ups
    "which of those branches have the highest cross sell rate within 90 days": """
SELECT
    o.branch_name,
    o.new_members,
    COUNT(DISTINCT CASE WHEN bmp.product_id IS NOT NULL
        AND bmp.enrollment_date <= DATEADD(day, 90, m.membership_date)
        THEN m.member_id END) as members_with_cross_sell,
    CAST(COUNT(DISTINCT CASE WHEN bmp.product_id IS NOT NULL
        AND bmp.enrollment_date <= DATEADD(day, 90, m.membership_date)
        THEN m.member_id END) AS FLOAT) /
        NULLIF(o.new_members, 0) * 100 as cross_sell_rate_90_days
FROM OriginalResult o
JOIN dim_branch b ON b.branch_name = o.branch_name
JOIN dim_member m ON m.branch_id = b.branch_id
LEFT JOIN bridge_member_product bmp ON m.member_id = bmp.member_id
WHERE m.membership_date >= '2024-10-01'
GROUP BY o.branch_name, o.new_members
ORDER BY cross_sell_rate_90_days DESC""",

    # Compare to last quarter
    "how does this compare to last quarter": """
SELECT
    'Current Period' as period,
    SUM(CASE WHEN o.branch_name IS NOT NULL THEN 1 ELSE 0 END) as branch_count,
    AVG(o.new_members) as avg_new_members,
    AVG(o.avg_initial_deposit) as avg_deposit
FROM OriginalResult o""",

    # Downtown comparison
    "how does downtown compare to last quarter": """
SELECT
    o.*,
    'Q4 2024' as current_quarter
FROM OriginalResult o
WHERE o.branch_name = 'Downtown'""",

    # What products are new members opening most
    "what products are new members opening most": """
SELECT
    p.product_name,
    COUNT(DISTINCT bmp.member_id) as member_count
FROM OriginalResult o
JOIN dim_branch b ON b.branch_name = o.branch_name
JOIN dim_member m ON m.branch_id = b.branch_id
JOIN bridge_member_product bmp ON m.member_id = bmp.member_id
JOIN dim_product p ON bmp.product_id = p.product_id
WHERE m.membership_date >= '2024-10-01'
GROUP BY p.product_name
ORDER BY member_count DESC""",

    # Which competitor took the most
    "which competitor took the most members": """
SELECT TOP 1
    o.competitor_name,
    COUNT(*) as members_taken
FROM OriginalResult o
GROUP BY o.competitor_name
ORDER BY members_taken DESC""",

    # What was the average relationship value of lost members
    "what was the average relationship value of lost members": """
SELECT
    AVG(o.relationship_value) as avg_relationship_value,
    SUM(o.relationship_value) as total_value_lost,
    COUNT(*) as members_lost
FROM OriginalResult o""",
}


def preload_demo_cache(cache):
    """
    Preload all demo responses into the cache.
    Note: This is now a no-op since we check DEMO_SQL_CACHE directly in the endpoint.

    Args:
        cache: ResponseCache instance to populate
    """
    from logging_setup.logging_config import get_logger
    logger = get_logger(__name__)

    # Log that demo SQL cache is available
    logger.info(f"Demo SQL cache loaded with {len(DEMO_SQL_CACHE)} pre-defined questions")
    logger.info(f"Follow-up templates loaded: {len(FOLLOWUP_SQL_TEMPLATES)} templates")
    return len(DEMO_SQL_CACHE)
