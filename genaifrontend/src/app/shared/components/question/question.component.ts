import { HttpService } from './../../../_services/http/http.service';
/** Angular material dependencies */
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { FormsModule } from '@angular/forms';
import { MatChipsModule } from '@angular/material/chips';

/**Other dependencies */
import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { UtilService } from '../../../_services/utils/util.service';


@Component({
  selector: 'app-question',
  standalone: true,
  imports: [
    MatIconModule,
    MatButtonModule,
    FormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatChipsModule
  ],
  templateUrl: './question.component.html',
  styleUrl: './question.component.scss'
})
export class QuestionComponent {
  question: string = "";
  trendingQuestion: any = [];
  constructor(
    private router: Router,
    private http: HttpService,
    private util: UtilService
  ) {
    this.getTrending();

     // Subscribe to the dropdown change event
     this.util.dropdownChange$.subscribe(() => {
      this.getTrending();
    });
  }

  getTrending() {
    this.http.getQuikInsights().subscribe((res) => {
      console.log(res);
      this.trendingQuestion = res;
    })
  }

  navigateAnswer() {
    if(this.question.trim()) {
      this.navigate(this.question);
    } else {

    }
  }

  navigate(question: string) {
    this.router.navigateByUrl('insights', { replaceUrl: true, state: {
      question: question
    } });
  }

}
