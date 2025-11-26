import { UtilService } from './../../../_services/utils/util.service';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { FormsModule } from '@angular/forms';
import { MatTooltipModule } from '@angular/material/tooltip';
import { HttpService } from '../../../_services/http/http.service';
import { VaiableConstants } from '../../../_helpers/constants/variable';

@Component({
  selector: 'app-rag-files',
  standalone: true,
  imports: [
    MatIconModule,
    MatButtonModule,
    CommonModule,
    MatProgressSpinnerModule,
    FormsModule,
    MatTooltipModule
  ],
  templateUrl: './rag-files.component.html',
  styleUrl: './rag-files.component.scss'
})
export class RagFilesComponent {
  selectedFiles: any = [];
  followupQues: string = '';
  answersList: any[] = [];
  fileProcessing: boolean = false;
  SOMETHING_WENT_WRONG: string = VaiableConstants.SOMETHING_WENT_WRONG;
  constructor(
    private http: HttpService,
    private util: UtilService
  ) {
    this.getAnswer('Show summary of this RFP', this.answersList.length);
    this.answersList.push({
      response: {
        question: 'Show summary of this RFP',
        filesList: [{
          type: 'PDF',
          name: 'msc.pdf',
        }]
      }
    });
  }

  ragAttach() {
    const ele: any = document.getElementById('rag-file-attach');
    ele && ele.click();
  }

  uploadFile(ev: any) {
    const files: FileList = ev.target.files;
    if (files && files.length > 0) {

      for (let i = 0; i < files.length; i++) {
        const fileName = files[i].name;
        let idx = this.selectedFiles.findIndex((file: any) => file.name == fileName);
        if (idx == -1) {
          const fileExtension = fileName.split('.').pop();
          const file = {
            type: fileExtension?.toUpperCase(),
            name: fileName,
            file: files[i],
            processing: 'loading',
            uploaded: false
          }
          this.selectedFiles.push(file);
        }
      }
      this.uploadFilesToServer();
    }
  }

  uploadFilesToServer() {
    for (let i = 0; i < this.selectedFiles.length; i++) {
      if (!this.selectedFiles[i]['uploaded'] && this.selectedFiles[i]['processing'] == 'loading') {
        this.fileProcessing = true;
        this.selectedFiles[i]['processing'] = 'processing';
        const formData: FormData = new FormData();
        formData.append('file', this.selectedFiles[i].file);
        this.http.uploadFile(formData).subscribe((res: any) => {
          if (res && res.filename) {
            this.changeStatus(i, 'success');
          }
        }, err => {
          this.changeStatus(i, 'fail');
        });
      }
    }
  }

  changeStatus(idx: number, status: string) {
    console.log(idx);
    if (status == 'fail') {
      this.selectedFiles[idx]['processing'] = 'fail';
      this.selectedFiles[idx]['uploaded'] = false;
    } else {
      this.selectedFiles[idx]['processing'] = 'done';
      this.selectedFiles[idx]['uploaded'] = true;
    }
    this.checkFileProcessing();
  }

  checkFileProcessing() {
    const idx = this.selectedFiles.findIndex((file: any) => file.processing == 'loading');
    if(idx == -1) {
      this.fileProcessing = false;
    } else {
      this.fileProcessing = true;
    }
    console.log(this.fileProcessing);
  }

  retry(idx: number) {
    this.fileProcessing = true;
    this.selectedFiles[idx]['processing'] = 'processing';
    const formData: FormData = new FormData();
    formData.append('file', this.selectedFiles[idx].file);
    this.http.uploadFile(formData).subscribe((res: any) => {
      if (res && res.filename) {
        this.changeStatus(idx, 'success');
      }
    }, err => {
      this.changeStatus(idx, 'fail');
    });
  }


  remove(idx: number) {
    this.selectedFiles.splice(idx, 1);
  }

  ragQuestion() {
    if (this.followupQues.trim() && !this.fileProcessing) {
      this.getAnswer(this.followupQues.trim(), this.answersList.length);
      this.answersList.push({
        response: {
          question: this.followupQues,
          filesList: [...this.selectedFiles.filter((file: any) => file.uploaded)]
          // filesList: [...this.selectedFiles]
        }
      });
      // console.log(this.answersList);
      this.scrollIntoView();
      this.followupQues = '';
      this.selectedFiles = [];
    }
  }

  getAnswer(question: string, idx: number = 0) {
    const uuid = this.util.getUUID();
    console.log(this.answersList);
    // const fileNames = this.answersList[idx]['response']['filesList'].map((file: any) => file.name);
    let reqObj: any = {
      question_id: uuid,
      question_asked: question,
      // filename: fileNames.length ? fileNames.toString() : null,
    }
    this.http.ragOriginalQuestion(reqObj).subscribe((res: any) => {
      res['question_id'] = uuid;
      this.setAnswer(idx, res);
    }, (err) => {
      this.answersList[idx]['response']['error'] = true;
    });
  }

  setAnswer(idx: number, response: any) {
    response['answer'] = response.answer.replace(/```/g,'').replace(/html/g,'');
    this.answersList[idx]['response'] = { ...this.answersList[idx]['response'], ...response };
    this.scrollIntoView();
  }

  answerCopy(idx: number) {
    let text: any = document.querySelector(`#rag-question-${idx} .answer-blog .answer`) || null;
    if (text) {
      text = text.innerText;
      this.answersList[idx]['answerCopy'] = true;
      this.util.copyToClip(text);
      // this.util.showSnackBar('Answer copied');
      setTimeout(() => {
        this.answersList[idx]['answerCopy'] = false;
      }, 1000);
    }
  }

  scrollIntoView() {
    let idx = this.answersList.length - 1;
    setTimeout(() => {
      const section = document.querySelector('.main-content.rag-page .rag-content');
      // const section = document.getElementById(`rag-question-${idx}`);
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
