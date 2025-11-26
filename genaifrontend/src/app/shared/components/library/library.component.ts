import { Subscription } from 'rxjs';
import { DeleteDialogComponent } from './../../Modals/delete-dialog/delete-dialog.component';
import { Component } from '@angular/core';
import { MatTooltipModule } from '@angular/material/tooltip';
import { UtilService } from '../../../_services/utils/util.service';
import { HttpService } from '../../../_services/http/http.service';
import { Router } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { CommonModule } from '@angular/common';

export interface questions {
  question_id: string,
  question_desc: string,
  edit?: boolean,
  highlight?: boolean
}
@Component({
  selector: 'app-library',
  standalone: true,
  imports: [
    MatTooltipModule,
    MatIconModule,
    MatDialogModule,
    CommonModule
  ],
  templateUrl: './library.component.html',
  styleUrl: './library.component.scss'
})
export class LibraryComponent {
  questionslist: questions[] = [];
  isEditable: boolean = false;
  subscriptions: Subscription[] = [];
  previousHightlightIdx: number = -1;
  previousSelectedID = '';
  constructor(
    private util: UtilService,
    private http: HttpService,
    private router: Router,
    public dialog: MatDialog
  ) {

    this.subscriptions.push(this.util.librarySubject.subscribe((res: boolean | string) => {
      if (res && typeof res == 'string') {
        if (typeof res == 'string') {
          // this.questionslist.unshift(res);
        } else {
          this.getquestionsList();
        }
      } else {
        this.getquestionsList();

      }
    }));
    this.subscriptions.push(
      this.util.hightLight.subscribe((res) => {
       if(res) {
        if(this.questionslist.length) {
          this.highlightBasedOnID(res);
        } 
        this.previousSelectedID = res;

       }
      }
      ));
  }

  ngOnInit(): void {
    this.getquestionsList();

  }

  ngOnDestroy(): void {
    //Called once, before the instance is destroyed.
    //Add 'implements OnDestroy' to the class.
    this.subscriptions.forEach(subscription => subscription.unsubscribe());
  }

  getquestionsList() {
    this.http.getHistory().subscribe((res: any) => {
      this.questionslist = res;
      setTimeout(() => {
        this.util.hightLight.next(this.previousSelectedID);
      }, 100);
    }, (res) => {

    });
  }

  editClick(ev: any, idx: number) {
    ev.stopImmediatePropagation();
    this.questionslist[idx]['edit'] = true;
    this.isEditable = true;
    this.focusBlurEvent(true, idx);
  }

  blurEvent(ev: any, idx: number) {
    if (this.isEditable) {
      this.isEditable = false;
      this.questionslist[idx]['edit'] = false;
      this.saveQuestionChange(ev, idx);
    }
  }

  saveQuestionChange(ev: any, idx: number) {
    const value = ev.target.value;
    if (value && value.trim() != this.questionslist[idx].question_desc) {
      const highlight = this.questionslist[idx].highlight;
      let req = {
        question_id: this.questionslist[idx].question_id,
        user_id: this.http.user_id,
        new_name: value.trim()
      }
      this.http.renameQuestion(req).subscribe((res) => {
        if (res == 'ok') {
          this.questionslist[idx].question_desc = value;
          let removedObject = this.questionslist.splice(idx, 1)[0];
          this.questionslist.unshift(removedObject);
          setTimeout(() => {
            if(highlight) {
              this.util.hightLight.next(req.question_id);
            }
          }, 100);
        } else {
          ev.target.value = this.questionslist[idx].question_desc;
        }
      });
    } else {
      ev.target.value = this.questionslist[idx].question_desc;
    }
  }

  deletDialog(ev: any, idx: number) {
    ev.stopImmediatePropagation();
    let dialogRef = this.dialog.open(
      DeleteDialogComponent,
      {
        height: '180px',
        width: '300px',
        data: {
          question: this.questionslist[idx]['question_desc']
        }

      });
    dialogRef.afterClosed().subscribe((result) => {
      if (result == 'deleted') {
        const highLight = this.questionslist[idx].highlight;
        let req = {
          question_id: this.questionslist[idx].question_id,
          user_id: this.http.user_id
        }
        this.http.deleteQuestion(req).subscribe((res) => {
          if (res == 'ok') {
            this.questionslist.splice(idx, 1);
            if(highLight) {
              this.router.navigateByUrl('question', {replaceUrl: true});
            }
          } 
        });
      }
    });
  }

  enterEvent(idx: number) {
    this.focusBlurEvent(false, idx);
  }

  focusBlurEvent(focus: boolean, idx: number) {
    const editableField = document.getElementById(`his-ques-${idx}`);
    (focus) ? editableField?.focus() : editableField?.blur();

  }

  redirectToAnswer(question: questions, idx: number) {
    if (!this.isEditable) {
      this.util.hightLight.next(question.question_id);
      this.isEditable = false;
      this.router.navigateByUrl(`insights?id=${question.question_id}`, {
        replaceUrl: true, state: {
          question: question.question_desc
        }
      });
    }

  }

  highlightBasedOnID(id: string) {
      const prevSelectedIdx = this.questionslist.findIndex(c => c.highlight);
      const selectdIdx = this.questionslist.findIndex(c => c.question_id.toLowerCase() == id.toLowerCase());
      if(prevSelectedIdx > -1) {
        this.questionslist[prevSelectedIdx].highlight = false;
      }
      if(selectdIdx > -1) {
        this.questionslist[selectdIdx].highlight = true;
      }
  }
}
