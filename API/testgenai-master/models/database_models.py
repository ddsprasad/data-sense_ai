from sqlalchemy import Column, Integer, String, ForeignKey, Text, DECIMAL, DateTime
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER  # Import this for MSSQL UUID
from self_db import Base

class Question(Base):
    __tablename__ = 'Questions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    question_id = Column(UNIQUEIDENTIFIER, nullable=True)   
    parent_question_id = Column(UNIQUEIDENTIFIER, nullable=True)
    question_type = Column(String(100), nullable=False)
    question_asked = Column(String, nullable=False)
    question_desc = Column(String, nullable=False)
    found_matching_sql = Column(Integer)
    time_taken = Column(DECIMAL(10, 2))
    model_sql_generation = Column(String(100), nullable=False)
    model_output_format = Column(String(100), nullable=False)
    model_additional_questions_generation = Column(String(100), nullable=False)
    answer = Column(String, nullable=True)
    sql_query = Column(String, nullable=True)
    answered_at = Column(String, nullable=True)
    show_chart = Column(Integer)
    show_sql = Column(Integer)
    
    

class Interaction(Base):
    __tablename__ = 'Interactions'
    interaction_id = Column(Integer, primary_key=True, autoincrement=True)
    interaction_type = Column(String(100))
    model = Column(String(100))
    question_id = Column(UNIQUEIDENTIFIER, ForeignKey('Questions.question_id'))
    question_type = Column(String(100), ForeignKey('Questions.question_type'))    
    prompt = Column(String)
    response = Column(String)
    sql_query_extracted = Column(String)
    time_taken = Column(DECIMAL(10, 2))
    related_tables = Column(String)
    db_schema = Column(String)
    user_question = Column(String)
    ms_sql_prompt = Column(String)
    is_valid_question = Column(Integer)
    # timestamp = Column(DateTime, nullable=False, default=func.now()) - not including in the definition because the default value (current time) needs to be inserted for this 

class Execution(Base):
    __tablename__ = 'Executions'
    execution_id = Column(Integer, primary_key=True)   
    execution_type = Column(String(100)) 
    question_id = Column(UNIQUEIDENTIFIER, ForeignKey('Questions.question_id'), nullable=False)
    question_type = Column(String(100), ForeignKey('Questions.question_type'), nullable=False)
    sql_query = Column(String, nullable=False)
    resultset = Column(Text, nullable=True)
    resultset_rows_count = Column(Integer, nullable=True)
    execution_error = Column(Text, nullable=True)
    attempt = Column(Integer, nullable=False)
    time_taken = Column(DECIMAL(10, 2))
    # timestamp = Column(DateTime, nullable=True, default=func.now()) - not including in the definition because the default value (current time) needs to be inserted for this 