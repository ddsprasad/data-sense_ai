import { ChartModalComponent } from './../../Modals/chart-modal/chart-modal.component';
import { VaiableConstants } from './../../../_helpers/constants/variable';
import { MatButtonModule } from '@angular/material/button';
import { Component, HostListener, OnDestroy } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { CdkDrag } from '@angular/cdk/drag-drop';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpService } from '../../../_services/http/http.service';
import { FormsModule } from '@angular/forms';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { UtilService } from '../../../_services/utils/util.service';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Subscription } from 'rxjs';
import { MatDialog } from '@angular/material/dialog';
import { DeleteDialogComponent } from '../../Modals/delete-dialog/delete-dialog.component';
import { CommonModule } from '@angular/common';
import ApexCharts from 'apexcharts';

declare var Prism: any;
declare var window: any;
@Component({
  selector: 'app-answer',
  standalone: true,
  imports: [
    MatIconModule,
    MatButtonModule,
    CdkDrag,
    FormsModule,
    MatProgressSpinnerModule,
    MatTooltipModule,
    CommonModule
  ],
  templateUrl: './answer.component.html',
  styleUrl: './answer.component.scss'
})
export class AnswerComponent implements OnDestroy {
  Constants = VaiableConstants;
  answersList: any[] = [];
  relatedQuestions: string[] = [];
  followupQues: string = '';
  showRelatedsQuestions: boolean = false;
  loader: boolean = false;
  parentQuestionID: string = '';
  irrelevantQuestion: boolean = false;
  chartRetry: number = 3;
  chartList: any = [];
  chartOptions: any = "";

  dialogId: string = '';
  // showRelatedQuestion: boolean = false;
  /** 
   * For shareing url we are checking this Variable
  */
  // subscription: Subscription;



  constructor(
    private router: Router,
    private http: HttpService,
    private util: UtilService,
    private activatedroute: ActivatedRoute,
    public dialog: MatDialog
  ) {
    const navigation = this.router.getCurrentNavigation();
    let questionStr = "";
    this.activatedroute.queryParamMap
      .subscribe(params => {
        this.parentQuestionID = params.get('id') || "";
        if (navigation && navigation.extras.state) {
          questionStr = navigation.extras.state['question'] || "";
        }
        if (this.parentQuestionID) {
          this.initializeData();
          this.getHistoryAnswers();
        }
        else {
          this.answersList.push({
            response: {
              question: questionStr
            }
          });
          this.getAnswer(questionStr);
        }
      });

  }

  
  @HostListener('window:resize', ['$event'])
  onResize(event: any) {
    const dialogRef = this.dialog.getDialogById(this.dialogId); // Replace 'dialog-id' with your dialog ID
    console.log(dialogRef);
    if (dialogRef) {
      dialogRef.updatePosition();
    }
  }

  ngOnDestroy(): void {
    // this.subscription.unsubscribe();
  }

  initializeData() {
    this.irrelevantQuestion = false;
    this.loader = true;
    this.answersList = [];
    this.relatedQuestions = [];
  }

  getHistoryAnswers() {
    let reqObj: any = {
      question_id: this.parentQuestionID
    }
    let type = '';
    if (this.router.url.indexOf('story') > -1) {
      type = 'story';
    }
    this.http.getHistoryQAs(reqObj, type).subscribe((res: any) => {
      if (res.length) {
        const oldAnsList = [...res.reverse()];
        this.answersList = oldAnsList.map((ans) => {

          if (ans.response.answer == "irrelevant") {
            this.irrelevantQuestion = true;
          }
          if (!ans.response.answer) {
            ans.response.error = true;
          }
          if (ans.response.tags) {
            let tags = ans.response.tags.split(',');
            if (tags.length) {
              ans.response.tags = tags.splice(0, 4);
            }
          }
          if (ans.response.chart_type == 'apex' && ans.response.chart_options) {
            eval(ans.response.chart_options);
            if (this.chartOptions) {
              ans.response.chart_options = { ...this.chartOptions };
            }
          }
          return ans;
        });
        this.util.hightLight.next(this.parentQuestionID);
      } else {
        this.util.showSnackBar('Wrong question', 'danger');
        this.router.navigateByUrl('/', { replaceUrl: true });
      }
      this.loader = false;
    }, err => {
      this.loader = false;
    });
  }

  getAnswer(question: string, idx: number = 0) {
    this.showRelatedsQuestions = false;
    this.relatedQuestions = [];
    const uuid = this.util.getUUID();
    let reqObj: any = {
      question_id: uuid,
      question_asked: question
    }
    if (idx == 0) {
      this.parentQuestionID = uuid;

    }
    if (idx) {
      reqObj['parent_question_id'] = this.parentQuestionID;
    }
    this.http.getOriginalAnswer(reqObj).subscribe((res: any) => {
      this.util.librarySubject.next(true);
      console.log(res);
      res['question_id'] = uuid;
      if(res.show_sql) {
        this.showRelatedsQuestions = true;
      } else {
        this.showRelatedsQuestions = false;
      }
      this.setAnswer(idx, res);
      if (res.answer != 'irrelevant') {
        this.getTags(idx);
        if (res.show_chart)
          this.getChart(idx);
      }
    }, (err) => {
      this.answersList[idx]['response']['error'] = true;
      this.showRelatedsQuestions = false;
    });
    this.getRelatedQuestionslist(reqObj);

    //Getting additional answers on initial question only
    if (idx == 0) {
      this.util.hightLight.next(uuid);
      this.http.getAdditionAnswer(reqObj).subscribe((res: any) => {
        res['question_id'] = uuid;
        this.setAnswer(idx, res, 'insight');
      });
    }
  }

  getRelatedQuestionslist(reqObj: any) {
    this.http.getReleatedQuestions(reqObj).subscribe((res: any) => {
      try {
        this.relatedQuestions = JSON.parse(res.related_questions);
      } catch (e) {
        this.relatedQuestions = [];
      }

    }, err => {

    });
  }

  getTags(idx: number) {
    const questionID = this.answersList[idx]['response'].question_id;
    this.http.getTags(questionID).subscribe((res: any) => {
      if (res) {
        const tags = res.split(',');
        if (tags.length) {
          this.answersList[idx]['response']['tags'] = tags.splice(0, 4);
        }
      }
    });
  }

  setAnswer(idx: number, response: any, keyName?: string) {
    if (keyName) {
      this.answersList[idx][keyName] = response;
    } else {
      if (response.answer == 'irrelevant') {
        this.irrelevantQuestion = true;
      } else {
        this.irrelevantQuestion = false;
      }
      this.answersList[idx]['response'] = { ...this.answersList[idx]['response'], ...response };
      this.scrollIntoView();
    }
    // this.highlightAll();
  }

  follwup() {
    if (this.followupQues.trim()) {
      this.getAnswer(this.followupQues.trim(), this.answersList.length);
      this.answersList.push({
        response: {
          question: this.followupQues
        }
      });
      this.followupQues = '';
      this.scrollIntoView();
    }
  }

  relatedQues(question: string) {
    if (question) {
      this.getAnswer(question.trim(), this.answersList.length);
      this.answersList.push({
        response: {
          question: question
        }
      });
      this.followupQues = '';
      this.scrollIntoView();
    }
  }

  deletDialog(ev: any, idx: number) {
    ev.stopImmediatePropagation();
    const actualQuestion = this.answersList[idx]['response'];
    let dialogRef = this.dialog.open(
      DeleteDialogComponent,
      {
        height: '180px',
        width: '300px',
        data: {
          question: actualQuestion['question']
        }

      });
    dialogRef.afterClosed().subscribe((result) => {
      if (result == 'deleted') {
        let req = {
          question_id: actualQuestion['question_id'],
          user_id: this.http.user_id
        }
        this.http.deleteQuestion(req).subscribe((res) => {
          if (res == 'ok') {
            if (idx == this.answersList.length - 1) {
              this.relatedQuestions = [];
            }
            this.answersList.splice(idx, 1);
            this.util.librarySubject.next(true);
            if (idx == 0) {
              this.router.navigateByUrl("/", { replaceUrl: true });
            }
          } else {
          }
        });
      }
    });
  }

  chartDialog(idx: number) {
    const answer = this.answersList[idx]['response'];
    this.dialogId = this.util.getUUID();
    const dialogRef = this.dialog.open(
      ChartModalComponent,
      {
        height: '600px',
        width: '600px',
        id: this.dialogId,
        data: {
          ...answer,
          idx: idx
        }
      });
    dialogRef.afterClosed().subscribe((result) => {
      console.log(result);
      if (result?.type == 'updated') {
        this.chartList[idx].destroy();
        this.chartList[idx] = undefined;
        this.answersList[idx]['response']['chart_options'] = { ...result.chart };
        this.chartRender(idx);
      }
    });
  }

  copySQL(idx: number) {
    const sql = this.answersList[idx]['response']['sql'];
    this.answersList[idx]['copied'] = true;
    this.util.copyToClip(sql);
    setTimeout(() => {
      this.answersList[idx]['copied'] = false;
    }, 1000);
  }

  answerCopy(idx: number) {
    const answer = this.answersList[idx];
    let text: any = document.querySelector(`#question-${idx} .answer-blog .answer`) || null;
    let insights: any = document.querySelector(`#question-${idx} .answer-releated-insights`) || null;
    if (text) {
      text = text.innerText;
      if (answer?.insight?.answer && insights) {
        text += `\n\n${insights.innerText}`;
      }
      this.answersList[idx]['answerCopy'] = true;
      this.util.copyToClip(text);
      // this.util.showSnackBar('Answer copied');
      setTimeout(() => {
        this.answersList[idx]['answerCopy'] = false;
      }, 1000);
    }
  }

  sharelink(idx: number) {
    const origin = window.location.origin;
    this.answersList[idx]['share'] = true;
    const id = this.answersList[idx]['response'].question_id;
    this.util.copyToClip(`${origin}/#/story?id=${id}`);
    setTimeout(() => {
      this.answersList[idx]['share'] = false;
    }, 1000);
  }

  like(idx: number) {
    const ans = this.answersList[idx]['response'];
    let obj = {
      question_id: ans.question_id,
      dislike: ans.dislike ? 0 : 1,
    }
    this.http.dislike(obj).subscribe((res) => {
      if (res) {
        this.answersList[idx]['response']['dislike'] = obj.dislike;
      }
    })

  }

  showSQL(idx: number, type: boolean) {
    this.answersList[idx]['response']['showChartView'] = false;
    this.answersList[idx]['response']['chartLoader'] = false;
    this.answersList[idx]['response']['showSQL'] = type;
    if(this.chartList[idx]) {
      this.chartList[idx].destroy();
      this.chartList[idx] = undefined;
    }
    if (type) {
      this.highlightAll();
    }
  }

  showChartView(idx: number, type: boolean) {
    this.answersList[idx]['response']['showSQL'] = false;
    this.answersList[idx]['response']['showChartView'] = type;
    if (type) {
      this.chartList[idx] = undefined;
      let obj = this.answersList[idx];
      if (obj.response?.chart_type) {
        if (obj.response.chart_type == 'apex' && obj.response.chart_options) {
          this.chartRender(idx);
        } else if (obj.response.chart_type == 'google' && obj.response.chart_data) {
          this.chartRender(idx);
        } else {
          this.getChart(idx);
        }
      } else {
        this.getChart(idx);
      }
    } else {
    }
  }

  getChart(idx: number) {
    //Apex chart View
    const answer = this.answersList[idx]['response'];
    this.answersList[idx]['response']['chart_options'] = undefined;
    this.http.getChart(answer.question_id, 200).subscribe((res: any) => {
      if (res.chart_type == 'apex' && res.chart_options) {
        try {
          eval(res.chart_options);
          if (this.chartOptions) {
            this.answersList[idx]['response']['chart_options'] = { ...this.chartOptions };
            this.answersList[idx]['response']['chart_type'] = 'apex';
            
            this.chartRender(idx);
          } else {
            this.answersList[idx]['response']['chart_options'] = { chart: 'error' };
          }
        } catch (e) {
          console.log(e);
          this.answersList[idx]['response']['chart_options'] = { chart: 'error' };
        }


      } else if (res.chart_type == 'google' && res?.chart_data?.length) {
        this.answersList[idx]['response']['chart_type'] = 'google';
        this.answersList[idx]['response']['chart_data'] = res.chart_data;
        this.answersList[idx]['response']['chart_options'] = res.chart_options;
        this.chartRender(idx);
      }
      else {
        this.answersList[idx]['response']['chart_options'] = { chart: 'error' };
      }
    }, (_) => {
      this.answersList[idx]['response']['chart_options'] = { chart: 'error' };
    })
  }

  chartRender(idx: number) {
    const chartType = this.answersList[idx]['response']['chart_type'];
    console.log(this.answersList[idx]);
    if (chartType == 'apex') {
      const options = JSON.parse(JSON.stringify(this.answersList[idx]['response']['chart_options']));
      if (options.hasOwnProperty('chart')) {
        let apexToolBar = VaiableConstants.APEXTOOLBAR;
        apexToolBar.tools.customIcons[0]['click'] = () => {
          this.chartDialog(idx);
        };
        options.chart['height'] = '95%';
        options.chart['width'] = '95%';
        options.chart['toolbar'] = apexToolBar;
      }
      setTimeout(() => {
        const ele = document.getElementById(`chartView-${idx}`);
        if (ele && !this.chartList[idx]) {
            this.chartList[idx] = new ApexCharts(document.getElementById(`chartView-${idx}`), options);
            this.chartList[idx].render();
        }
      }, 200);
    } else if (chartType == 'google') {
      this.renderGoogleChart(idx);
    }
  }

  renderGoogleChart(idx: number) {
    console.log(`called ${idx}`);
    window.google.charts.load('current', {
      'packages': ['geochart'],
      'mapsApiKey': 'AIzaSyAOWoZaASAIXNswVHPWVMB1sLaEHCutMu4'
    });
    window.google.charts.setOnLoadCallback(this.drawGeoChart.bind(this, idx));
  }

  drawGeoChart(idx?: number) {
    /* Geo Chart */
    const index = idx || 0;
    const response = this.answersList[index]['response'];
    console.log(response);
    let chartData = "";
    let options: any = "";
    if(typeof response.chart_data == 'string') {
      chartData = JSON.parse(response.chart_data);
    } else {
      chartData = response.chart_data;
    }
    const data = window.google.visualization.arrayToDataTable(chartData);
    if(typeof response.chart_options == 'string') {
      try {
        options = JSON.parse(response.chart_options);
      } catch(e) {
        options = VaiableConstants.GOOGLECHARTOPTIONS;
      }
    } else {
      options = response.chart_options;
    }
    setTimeout(() => {
      const ele = document.getElementById(`google-chart-${idx}`);
      if (ele) {
        const geoChart = new window.google.visualization.GeoChart(ele);
        geoChart.draw(data, options);
      }
    }, 200);

  }

  highlightAll() {
    setTimeout(() => {
      Prism.highlightAll();
    }, 50);
  }

  scrollIntoView() {
    let idx = this.answersList.length - 1;
    setTimeout(() => {
      const section = document.querySelector('.main-content.answer-page .answer-content');
      // const section = document.getElementById(`question-${idx}`);
      if (section) {
        section.scrollTo({
          top: section.scrollHeight,
          behavior: 'smooth'
        });
        // section.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'end' });
      }
    }, 10);
  }
}
