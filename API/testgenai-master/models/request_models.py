from pydantic import BaseModel, UUID4

class QuestionRequestModel(BaseModel):
    question_id: UUID4
    question_asked: str    
    user_id: int

class FollowUpQuestionRequestModel(BaseModel):
    parent_question_id: UUID4
    question_id: UUID4
    question_asked: str   
    user_id: int

class RelatedQuestionRequestModel(BaseModel):
    question_asked: str 
    question_id: UUID4    
    user_id: int



class UserHistoryRequestModel(BaseModel):
    user_id: int

class UserHistoryQuestionRequestModel(BaseModel):
    user_id: int
    question_id: str

class ChartsRequestModel(BaseModel):   
    question_id: str
    file_id: str

class ChartEditRequestModel(BaseModel):
    question_id: str
    file_id: str    
    code: str
    library: str    
    instructions: str

class ChartOptionsRequestModel(BaseModel):   
    question_id: str
    user_id: int         

class ChartOptionsEditRequestModel(BaseModel):   
    question_id: str
    user_id: int    
    code: str
    instructions: str   

class ChartOptionsSaveEditedRequestModel(BaseModel):
    question_id: str
    user_id: str
    chart_type: str
    chart_options: str

class QuestionTagsRequestModel(BaseModel):    
    question_id: str

class SharedHistoryQuestionRequestModel(BaseModel):    
    question_id: str

class DislikeQuestionRequestModel(BaseModel):
    dislike: int
    user_id: int
    question_id: str

class RenameQuestionRequestModel(BaseModel):
    new_name: str
    user_id: int
    question_id: str

class DeleteQuestionRequestModel(BaseModel):    
    user_id: int
    question_id: str

class UserValidationRequestModel(BaseModel):
    username: str
    password: str

class TrendingQuestionsRequestModel(BaseModel):
    database_name: str = None