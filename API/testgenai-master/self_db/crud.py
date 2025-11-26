from sqlalchemy.orm import Session
from sqlalchemy import text
from config import Settings
from models.database_models import Question, Interaction, Execution
from self_db import SessionLocal
from util.util import tuple_to_dict
import traceback

def log_exception(e, additional_info = ''):
    db = SessionLocal()   

    exception_type = type(e).__name__
    exception_message = str(e)
    stack_trace = traceback.format_exc()

    query = text("""
             INSERT INTO Exceptions (exception_type, exception_message, stack_trace, additional_info) 
        VALUES (:exception_type, :exception_message, :stack_trace, :additional_info)
            """)
    try:
        db.execute(query, {'exception_type': exception_type, 'exception_message': exception_message, 'stack_trace': stack_trace, 'additional_info': additional_info})
        db.commit()  
        return 'done'      
    
    except Exception as e:
        db.rollback()
        print(f"An error occurred in log_exception: {str(e)}")
        return None
    finally:
        db.close()

def create_question(db: Session, user_id, question_id: str, question_type: str, parent_question_id: str, question_asked: str):
    try:
        # Check if the question already exists
        existing_question = db.query(Question).filter(
            Question.user_id == user_id,
            Question.question_id == question_id,
            Question.question_type == question_type
        ).first()

        # If question already exists, skip insertion
        if existing_question:
            print(f"Question already exists: user_id={user_id}, question_id={question_id}, question_type={question_type}")
            return existing_question

        # Create new question
        db_question = Question(user_id=user_id, question_id=question_id, question_type=question_type, parent_question_id=parent_question_id, question_asked=question_asked, model_sql_generation=Settings.model_to_use_main, model_output_format=Settings.model_to_use_output_formatting, model_additional_questions_generation=Settings.model_to_use_additional_questions_generation, question_desc=question_asked)
        db.add(db_question)
        db.commit()
        return db_question
    except Exception as e:
        db.rollback()
        log_exception(e, 'create_question')
        print(f"An error occurred in create_question: {str(e)}")        

def update_question(user_id:int, question_id: str, question_type: str, time_taken: str, found_matching_sql, answer, sql_query, answered_at, show_chart, show_sql):
    try:        
        db = SessionLocal()           
        db_question = db.query(Question).filter(Question.user_id == user_id, Question.question_id == question_id, Question.question_type == question_type).first()
        if db_question is None:
            raise ValueError("Question not found")       
        db_question.time_taken = time_taken 
        db_question.answer = answer
        db_question.sql_query = sql_query
        db_question.found_matching_sql = 1 if found_matching_sql else 0
        db_question.answered_at = answered_at
        db_question.show_chart = show_chart
        db_question.show_sql = show_sql
        db.commit()
    except Exception as e:
        db.rollback()
        log_exception(e, 'update_question')
        print(f"An error occurred in update_question: {str(e)}")
    finally:
        db.close()

def update_question_tags(question_id: str, tags: str):
    db = SessionLocal()   
    query = text("""
            UPDATE QUESTIONS SET tags = :tags WHERE question_id = :question_id
            """)
    try:
        db.execute(query, {'tags': tags, 'question_id': question_id})
        db.commit()  
        return 'done'      
    
    except Exception as e:
        db.rollback()
        log_exception(e, 'update_question_tags')
        print(f"An error occurred in update_question_tags: {str(e)}")
        return None
    finally:
        db.close()

def update_question_chart_info(question_id: str, chart_type: str, chart_options: str, chart_data: str):
    db = SessionLocal()   
    query = text("""
            UPDATE QUESTIONS 
                 SET chart_type = :chart_type, chart_data = :chart_data, chart_options = :chart_options 
                 WHERE question_id = :question_id
            """)
    try:
        db.execute(query, {'chart_type': chart_type, 'chart_data': chart_data, 'chart_options': chart_options, 'question_id': question_id})
        db.commit()  
        return 'done'      
    
    except Exception as e:
        db.rollback()
        log_exception(e, 'update_question_chart_info')
        print(f"An error occurred in update_question_chart_info: {str(e)}")
        return None
    finally:
        db.close()

def update_question_updated_at(parent_question_id: str, user_id: str):
    db = SessionLocal()   
    query = text("""
            UPDATE QUESTIONS SET updated_at = GETDATE() 
                 WHERE question_id = :parent_question_id 
                 AND parent_question_id IS NULL AND question_type = 'Original-Question'
                 AND user_id = :user_id
            """)
    try:
        db.execute(query, {'parent_question_id': parent_question_id, 'user_id': user_id})
        db.commit()  
        return 'done'      
    
    except Exception as e:
        db.rollback()
        log_exception(e, 'update_question_updated_at')
        print(f"An error occurred in update_question_updated_at: {str(e)}")
        return None
    finally:
        db.close()

def create_interaction(interaction_type: str, model: str, question_id: str, question_type: str, prompt: str, response: str, sql_query_extracted: str, time_taken: str, tables: str, db_schema: str, query: str, ms_sql_prompt: str, is_valid_question: int ):
    db = SessionLocal()    
    try:        
        db_interaction = Interaction(
            interaction_type=interaction_type,
            model=model,
            question_id=question_id,
            question_type=question_type,           
            prompt=prompt,
            response=response,
            sql_query_extracted=sql_query_extracted,
            related_tables=tables, 
            db_schema=db_schema, 
            user_question=query, 
            ms_sql_prompt=ms_sql_prompt,
            time_taken=time_taken,
            is_valid_question=is_valid_question
        )
        db.add(db_interaction)
        db.commit()
        db.refresh(db_interaction)
        return db_interaction
    except Exception as e:
        db.rollback()
        log_exception(e, 'create_interaction')
        print(f"An error occurred in create_interaction: {str(e)}")
        return None
    finally:
        db.close()

    

def create_execution(execution_type: str, question_id: str, question_type: str, sql_query: str, resultset: str, execution_error: str, attempt: int, time_taken: str, resultset_rows_count: int):
    db = SessionLocal()
    try:
        db_execution = Execution(    
            execution_type=execution_type,        
            question_id=question_id,
            question_type=question_type,
            sql_query=sql_query,
            resultset=resultset,
            execution_error=execution_error,
            attempt=attempt,
            time_taken=time_taken,
            resultset_rows_count=resultset_rows_count
        )
        db.add(db_execution)
        db.commit()
        db.refresh(db_execution)
        return db_execution
    except Exception as e:
        db.rollback()
        log_exception(e, 'create_execution')
        print(f"An error occurred in create_execution: {str(e)}")
        return None
    finally:
        db.close()


def get_user_history(user_id: int):
    db = SessionLocal()   
    query = text("""          
            SELECT TOP 20 [question_id], [question_desc]
            FROM 
                QUESTIONS
            WHERE (parent_question_id IS NULL AND question_type = 'Original-Question' AND user_id = :user_id)
                      AND (is_deleted = 0 OR is_deleted IS NULL) 
            ORDER BY 
                updated_at DESC
            """)
    try:
        result_proxy = db.execute(query, {'user_id': user_id})
        column_names = list(result_proxy.keys())
        results = result_proxy.fetchall()
        return [tuple_to_dict(row, column_names) for row in results]
    
    except Exception as e:
        db.rollback()
        log_exception(e, 'get_user_history')
        print(f"An error occurred in get_user_history: {str(e)}")
        return None
    finally:
        db.close()

def get_shared_story_history_question(question_id: str):
    db = SessionLocal()
    query = text("""
    SELECT 
       [user_id]
      ,[question_id]
      ,[question_type]
      ,[parent_question_id]
      ,[question_asked] as question
      ,[answer] 
      ,[sql_query] as sql    
      ,[dislike]
      ,[answered_at]
      ,show_chart
      ,show_sql     
      ,chart_type
      ,chart_options
      ,chart_data
                             
  FROM [dbo].[Questions]
  WHERE (question_id = :question_id OR parent_question_id = :question_id) 
                 AND (is_deleted = 0 OR is_deleted IS NULL)
  ORDER BY timestamp DESC
    """)
    try:      
        result_proxy = db.execute(query, {'question_id': question_id})        
        structured_data = restructure_results(result_proxy)
        return structured_data      
    except Exception as e:
        db.rollback()
        log_exception(e, 'get_shared_story_history_question')
        print(f"An error occurred in get_shared_story_history_question: {str(e)}")
        return None
    finally:
        db.close()


def get_user_history_question(user_id: int, question_id: str):
    db = SessionLocal()
    query = text("""
    SELECT  
       [user_id]
      ,[question_id]
      ,[question_type]
      ,[parent_question_id]
      ,[question_asked] as question
      ,[answer] 
      ,[sql_query] as sql    
      ,[dislike]
      ,[answered_at]
      ,[tags]
      ,show_chart
      ,show_sql
      ,chart_type
      ,chart_options
      ,chart_data
                     
  FROM [dbo].[Questions]
  WHERE (question_id = :question_id OR parent_question_id = :question_id) AND user_id = :user_id
                 AND (is_deleted = 0 OR is_deleted IS NULL)
  ORDER BY timestamp DESC
    """)
    try:      
        result_proxy = db.execute(query, {'question_id': question_id, 'user_id': user_id}) 
        structured_data = restructure_results(result_proxy)
        return structured_data
    except Exception as e:
        db.rollback()
        log_exception(e, 'get_user_history_question')
        print(f"An error occurred in get_user_history_question: {str(e)}")
        return None
    finally:
        db.close()

def get_trending_questions():
    """
    Get trending questions based on actual user activity.
    Returns top questions asked in the last 30 days, ordered by frequency.
    Falls back to curated questions if no recent activity.
    """
    db = SessionLocal()

    # Query for actual trending questions from last 30 days
    query = text("""
        SELECT TOP 3
            q.question_asked as trending_questions,
            CASE
                WHEN q.question_asked LIKE '%branch%' OR q.question_asked LIKE '%location%' THEN 'location_on'
                WHEN q.question_asked LIKE '%member%' OR q.question_asked LIKE '%customer%' THEN 'people'
                WHEN q.question_asked LIKE '%loan%' OR q.question_asked LIKE '%credit%' THEN 'account_balance_wallet'
                WHEN q.question_asked LIKE '%balance%' OR q.question_asked LIKE '%deposit%' THEN 'account_balance'
                WHEN q.question_asked LIKE '%product%' OR q.question_asked LIKE '%account%' THEN 'category'
                ELSE 'trending_up'
            END as icon_name,
            COUNT(*) as ask_count
        FROM Questions q
        WHERE q.question_type = 'Original-Question'
            AND q.answered_at IS NOT NULL
            AND q.timestamp >= DATEADD(day, -30, GETDATE())
            AND (q.is_deleted = 0 OR q.is_deleted IS NULL)
        GROUP BY q.question_asked
        ORDER BY COUNT(*) DESC, MAX(q.timestamp) DESC
    """)

    try:
        result_proxy = db.execute(query)
        column_names = list(result_proxy.keys())
        results = result_proxy.fetchall()

        # If we have trending questions from actual usage, return them
        if results and len(results) > 0:
            return [tuple_to_dict(row, column_names) for row in results]

        # Fallback to curated questions if no recent activity
        fallback_query = text("""
            SELECT 'Top 10 Branches by New Member Acquisition This Quarter' AS trending_questions, 'location_on' as icon_name, 0 as ask_count
            UNION ALL
            SELECT 'Members with Credit Inquiries But No Loan Origination', 'people', 0
            UNION ALL
            SELECT 'Average Account Balance by Product Type', 'account_balance', 0
        """)

        fallback_result = db.execute(fallback_query)
        fallback_columns = list(fallback_result.keys())
        fallback_results = fallback_result.fetchall()
        return [tuple_to_dict(row, fallback_columns) for row in fallback_results]

    except Exception as e:
        db.rollback()
        log_exception(e, 'get_trending_questions')
        print(f"An error occurred in get_trending_questions: {str(e)}")
        return None
    finally:
        db.close()


def rename_question(user_id: int, question_id: int, new_name: str):
    db = SessionLocal()
    query = text("""
        UPDATE [dbo].[Questions] 
        SET question_desc = :new_name, updated_at = GETDATE()
            WHERE question_id = :question_id AND user_id = :user_id             
    """)    
    try:
        db.execute(query, {'user_id': user_id, 'question_id': question_id, 'new_name': new_name})        
        db.commit()
        return 'done'
    
    except Exception as e:
        db.rollback()
        log_exception(e, 'rename_question')
        print(f"An error occurred in rename_question: {str(e)}")
        return None
    finally:
        db.close()

def delete_question(user_id: int, question_id: int):
    db = SessionLocal()
    query = text("""
        UPDATE [dbo].[Questions] 
        SET is_deleted = 1
            WHERE question_id = :question_id AND user_id = :user_id             
    """)    
    try:
        db.execute(query, {'user_id': user_id, 'question_id': question_id})        
        db.commit()
        return 'done'
    
    except Exception as e:
        db.rollback()
        log_exception(e, 'delete_question')
        print(f"An error occurred in delete_question: {str(e)}")
        return None
    finally:
        db.close()

def set_answer_dislike(user_id: int, question_id: int, dislike: int):
    db = SessionLocal()
    query = text("""
        UPDATE [dbo].[Questions] 
        SET dislike = :dislike
            WHERE question_id = :question_id AND user_id = :user_id             
    """)    
    try:
        db.execute(query, {'user_id': user_id, 'question_id': question_id, 'dislike': dislike})        
        db.commit()
        return 'done'
    
    except Exception as e:
        db.rollback()
        log_exception(e, 'set_answer_dislike')
        print(f"An error occurred in set_answer_dislike: {str(e)}")
        return None
    finally:
        db.close()

def restructure_results(result_proxy):
    try:
        # Extract column names and fetch all rows from the result proxy
        column_names = list(result_proxy.keys())
        results = result_proxy.fetchall()
        
        # Convert tuples to dictionaries
        converted_results = [tuple_to_dict(row, column_names) for row in results]

        # Restructure the data
        structured_results = []
        temp_dict = {}

        for result in converted_results:        
            question_id = result['question_id']
            question_type = result['question_type']

            wrapped_result = {'response': result}

            # Check if it's an 'Original-Question' or 'Additional-Insights'
            if question_type in ['Original-Question', 'Additional-Insights']:
                if question_id not in temp_dict:
                    temp_dict[question_id] = {'response': None, 'insight': None}

                if question_type == 'Original-Question':
                    temp_dict[question_id]['response'] = result
                else:
                    temp_dict[question_id]['insight'] = result

            # For 'Follow-Up-Question', add it directly to the structured results
            elif question_type == 'Follow-Up-Question':            
                structured_results.append(wrapped_result)

        # Add the grouped questions to the structured results
        structured_results.extend(temp_dict.values())

        return structured_results
    except Exception as e:        
        log_exception(e, 'restructure_results')
        print(f"An error occurred in restructure_results: {str(e)}")
        return None



def get_existing_sql_query_if_match_found(question_asked: str):
    db = SessionLocal()
    query = text("""
        SELECT       
        i.sql_query_extracted
    FROM
        [genaipoc_history].[dbo].[Questions] q
    LEFT JOIN 
        [genaipoc_history].[dbo].[Interactions] i ON i.question_id = q.question_id
    LEFT JOIN
        [genaipoc_history].[dbo].[Executions] e ON e.question_id = q.question_id AND i.question_type = e.question_type AND e.execution_type = i.interaction_type
    WHERE q.question_asked = :question_asked AND sql_query IS NOT NULL AND resultset IS NOT NULL
    """)
    try:
        result_proxy = db.execute(query, {'question_asked': question_asked})
        # Check if any rows exist
        row = result_proxy.first()  # Fetch only the first row
        if row:
            sql_query_extracted = row[0]  # Access the question_id from the first row
            return sql_query_extracted
        else:
            return None      
    except Exception as e:
        db.rollback()
        log_exception(e, 'get_existing_sql_query_if_match_found')
        print(f"An error occurred in get_existing_sql_query_if_match_found: {str(e)}")
        return None
    finally:
        db.close()

def get_conversation_history(question_id):
    db = SessionLocal()
    query = text("""
    SELECT       
        q.question_asked,       
        i.prompt,
        i.response,
        e.sql_query,
        e.resultset,
        i.related_tables,
        i.db_schema
    FROM
        [genaipoc_history].[dbo].[Questions] q
    LEFT JOIN 
        [genaipoc_history].[dbo].[Interactions] i ON i.question_id = q.question_id
    LEFT JOIN
        [genaipoc_history].[dbo].[Executions] e ON e.question_id = q.question_id AND i.question_type = e.question_type AND e.execution_type = i.interaction_type
    WHERE ((q.question_id = :question_id AND q.question_type = 'Original-Question') OR (q.parent_question_id = :question_id AND q.question_type = 'Follow-Up-Question'))
	AND e.execution_error IS NULL AND i.interaction_type = 'Original-Answer-SQL-Query-Generation'
    """)
    try:      
        result_proxy = db.execute(query, {'question_id': question_id})
        column_names = list(result_proxy.keys())
        results = result_proxy.fetchall()
        return [tuple_to_dict(row, column_names) for row in results] 
    
    except Exception as e:
        db.rollback()
        log_exception(e, 'get_conversation_history')
        print(f"An error occurred in get_conversation_history: {str(e)}")
        return None
    finally:
        db.close()
    


def get_previous_response(question_id):
    db = SessionLocal()
    query = text("""
                    SELECT TOP 1 response
                    FROM
                        [genaipoc_history].[dbo].[Questions] q
                    LEFT JOIN 
                        [genaipoc_history].[dbo].[Interactions] i ON i.question_id = q.question_id
                    LEFT JOIN
                        [genaipoc_history].[dbo].[Executions] e ON e.question_id = q.question_id AND i.question_type = e.question_type AND e.execution_type = i.interaction_type
                    WHERE ((q.question_id = :question_id AND q.question_type = 'Original-Question') OR (q.parent_question_id = :question_id AND q.question_type = 'Follow-Up-Question'))
                    AND interaction_type = 'Original-Answer-Output-Formatting'
                    ORDER BY id DESC
                """)
    try:      
        result_proxy = db.execute(query, {'question_id': question_id})
        column_names = list(result_proxy.keys())
        results = result_proxy.fetchall()
        return [tuple_to_dict(row, column_names) for row in results] 
    
    except Exception as e:
        db.rollback()
        log_exception(e, 'get_previous_response')
        print(f"An error occurred in get_previous_response: {str(e)}")
        return None
    finally:
        db.close()


def get_user_details(username, password):
    db = SessionLocal()
    query = text("""
                    SELECT TOP 1 user_id, concat(first_name, ' ', last_name) as name,  role 
                    FROM
                        [genaipoc_history].[dbo].[Users] u
                    WHERE u.username = :username AND u.password = :password                    
                """)
    try:      
        result_proxy = db.execute(query, {'username': username, 'password': password})
        column_names = list(result_proxy.keys())
        result = result_proxy.fetchone()

        if result is None:            
            return {"user_valid": False, "user_id": 0, "name": "", "role": ""}
        else:
            user_data = tuple_to_dict(result, column_names) 
            user_data["user_valid"] = True
            return user_data
    except Exception as e:
        db.rollback()
        log_exception(e, 'get_user_details')
        print(f"An error occurred in get_user_details: {str(e)}")
        return None
    finally:
        db.close()



def get_extracted_sql(question_id):
    db = SessionLocal()
    query = text("""
                    SELECT TOP 1 sql_query_extracted
                    FROM
                        [genaipoc_history].[dbo].[Interactions]                    
                    WHERE interaction_type = 'Original-Answer-SQL-Query-Generation' 
                    AND sql_query_extracted != '' AND sql_query_extracted IS NOT NULL
                    AND question_id = :question_id
                """)
    try:      
        result_proxy = db.execute(query, {'question_id': question_id})
        column_names = list(result_proxy.keys())
        results = result_proxy.fetchall()
        return [tuple_to_dict(row, column_names) for row in results] 
    
    except Exception as e:
        db.rollback()
        log_exception(e, 'get_extracted_sql')
        print(f"An error occurred in get_extracted_sql: {str(e)}")
        return None
    finally:
        db.close()

def get_result_set(question_id):
    db = SessionLocal()
    query = text("""
                    SELECT TOP 1 resultset
                    FROM
                        [genaipoc_history].[dbo].[Executions]
                    WHERE execution_type = 'Original-Answer-SQL-Query-Generation'
                    AND question_id = :question_id
                    AND resultset IS NOT NULL
                    ORDER BY attempt DESC
                """)
    try:      
        result_proxy = db.execute(query, {'question_id': question_id})
        column_names = list(result_proxy.keys())
        results = result_proxy.fetchall()
        return [tuple_to_dict(row, column_names) for row in results] 
    
    except Exception as e:
        db.rollback()
        log_exception(e, 'get_result_set')
        print(f"An error occurred in get_result_set: {str(e)}")
        return None
    finally:
        db.close()