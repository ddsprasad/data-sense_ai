import { AuthService } from './../auth/auth.service';
import { ApiConstants } from './../../_helpers/constants/api';
import { UtilService } from './../utils/util.service';
import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

export interface orginalQuestion  {
  question_id : string,
  question_asked?: string,
  parent_question_id?: string,
  user_id?: string | number,
  file_name?: string
};

export interface dislike {
  question_id: string,
  dislike: number,
  user_id? : string | number
}

export interface rename {
  question_id: string,
  new_name?: string,
  user_id : string | number
}

@Injectable({
  providedIn: 'root'
})
export class HttpService {
  user_id: string | number;
  constructor(
    private http:HttpClient,
    private util: UtilService,
    private auth: AuthService,
    ) { 
      this.user_id = this.auth.userDet?.user_id;
    }


  login(login: any) {
    return this.http.post(`${ApiConstants.API}${ApiConstants.APIVERSION}${ApiConstants.LOGIN}`, login);
  } 
  /**
   *
   * @param getOriginal > orginalQuestion
   * @returns
   */
  getOriginalAnswer(getOriginal:orginalQuestion) {
    const endPoint =  !getOriginal.parent_question_id ? ApiConstants.ORIGINAL_QUESTION : ApiConstants.FOLLOW_UP_QUESTION;
    getOriginal.user_id  = this.user_id;
    return this.http.post(`${ApiConstants.API}${ApiConstants.APIVERSION}${endPoint}`, getOriginal);
  }

  getReleatedQuestions(getOriginal:orginalQuestion) {
    getOriginal.user_id  = this.user_id;
    return this.http.post(`${ApiConstants.API}${ApiConstants.APIVERSION}${ApiConstants.RELATED_QUESTIONS}`, getOriginal);
  }

  getAdditionAnswer(getOriginal:orginalQuestion) {
    getOriginal.user_id  = this.user_id;
    return this.http.post(`${ApiConstants.API}${ApiConstants.APIVERSION}${ApiConstants.ADDITIONAL_INSIGHTS}`, getOriginal);
  }

  getHistory() {
    return this.http.post(`${ApiConstants.API}${ApiConstants.APIVERSION}${ApiConstants.USER_HISTORY}`, {
      user_id: this.user_id
    });
  }

  getHistoryQAs(getOriginal: orginalQuestion, type?: string) {
    if(type == 'story') {
      return this.http.post(`${ApiConstants.API}${ApiConstants.APIVERSION}${ApiConstants.SHARED_STORY}`, getOriginal);
    } else {
      getOriginal.user_id  = this.user_id;
      return this.http.post(`${ApiConstants.API}${ApiConstants.APIVERSION}${ApiConstants.USER_HISTORY_QUESTION}`, getOriginal);
    }
  }

  dislike(dislike: dislike) {
    dislike.user_id  = this.user_id;
    return this.http.post(`${ApiConstants.API}${ApiConstants.APIVERSION}${ApiConstants.DISLIKE}`, dislike);
  }

  renameQuestion(rename : rename) {
    return this.http.post(`${ApiConstants.API}${ApiConstants.APIVERSION}${ApiConstants.RENAME_QUESTION}`, rename);
  }
  deleteQuestion(deletQuestion : rename) {
    return this.http.post(`${ApiConstants.API}${ApiConstants.APIVERSION}${ApiConstants.DELETE_QUESTION}`, deletQuestion);
  }

  getQuikInsights() {
    return this.http.post(`${ApiConstants.API}${ApiConstants.APIVERSION}${ApiConstants.TRENDING_QUESTIONS}`, {});
  }
  
  getTags(questionId: string) {
    return this.http.post(`${ApiConstants.API}${ApiConstants.APIVERSION}${ApiConstants.GETTAGS}`, {question_id: questionId});
  }

  getChartImg(questionId: string, fild_id?: string) {
    const uuid =  fild_id || this.util.getUUID();
    return this.http.post(`${ApiConstants.API}${ApiConstants.APIVERSION}${ApiConstants.GETCHARTSIMG}`, {
      question_id: questionId,
      file_id: uuid
    });
  }

  editChartImg(chartObj: any) {
    return this.http.post(`${ApiConstants.API}${ApiConstants.APIVERSION}${ApiConstants.EDITCHARTSIMG}`, chartObj);
  }

  getChart(question_id: string, height:  number) {
    let chartObj ={
      question_id,
      user_id : this.user_id
    }
    return this.http.post(`${ApiConstants.API}${ApiConstants.APIVERSION}${ApiConstants.GETCHARTS}`, chartObj);
  }

  editChart(chartObj: any) {
    return this.http.post(`${ApiConstants.API}${ApiConstants.APIVERSION}${ApiConstants.EDITCHARTS}`, chartObj);
  }

  saveChart(chartObj: any) {
    return this.http.post(`${ApiConstants.API}${ApiConstants.APIVERSION}${ApiConstants.SAVECHARTS}`, chartObj);
  }
  
  uploadFile(formdata: FormData) {
    return this.http.post(`${ApiConstants.API}${ApiConstants.UPLOADFILE}/`, formdata);
  }
  
  ragOriginalQuestion(ragQuestion: orginalQuestion) {
    ragQuestion.user_id  = this.user_id;
    return this.http.post(`${ApiConstants.API}${ApiConstants.APIVERSION}${ApiConstants.ORIGINAL_QUESTION_RAG}`, ragQuestion);
  }
}
