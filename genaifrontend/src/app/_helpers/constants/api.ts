export const ApiConstants = {
  API: 'http://localhost:8000/',
  _apiVersion: 'v2/',
  _selectedDatabase: '',
  ORIGINAL_QUESTION : 'original-question',
  ADDITIONAL_INSIGHTS: 'additional-insights',
  FOLLOW_UP_QUESTION: 'follow-up-question',
  RELATED_QUESTIONS: 'related-questions',
  USER_HISTORY: 'user-history',
  USER_HISTORY_QUESTION: 'user-history-question',
  DISLIKE: 'dislike', // user_id, question_id, dislike params
  SHARED_STORY: 'shared-story-history-question',
  RENAME_QUESTION: 'rename',
  DELETE_QUESTION: 'delete',
  TRENDING_QUESTIONS: 'trending-questions',
  DATABASES: 'databases',
  LOGIN: 'validate-user',
  GETTAGS: 'get-tags',
  GETCHARTSIMG: 'get-chart-img',
  EDITCHARTSIMG: 'edit-chart-img',
  GETCHARTS: 'get-charts',
  EDITCHARTS: 'edit-charts',
  SAVECHARTS: 'save-edited-charts',
  UPLOADFILE: 'uploadfile',
  ORIGINAL_QUESTION_RAG : 'original-question-rag',
  get APIVERSION() {
    return this._apiVersion;
  },
  set APIVERSION(version: string) {
    this._apiVersion = version + '/';
  },
  get SELECTED_DATABASE() {
    return this._selectedDatabase;
  },
  set SELECTED_DATABASE(database: string) {
    this._selectedDatabase = database;
  }
}



