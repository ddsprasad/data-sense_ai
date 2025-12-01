import { HttpService } from './../../../_services/http/http.service';
/** Angular material dependencies */
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { FormsModule } from '@angular/forms';
import { MatChipsModule } from '@angular/material/chips';

/**Other dependencies */
import { Component, OnDestroy, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { UtilService } from '../../../_services/utils/util.service';
import { ApiConstants } from '../../../_helpers/constants/api';
import { Subscription } from 'rxjs';


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
export class QuestionComponent implements OnDestroy, OnInit {
  question: string = "";
  trendingQuestion: any = [];
  selectedDatabase: string = '';
  private subscriptions: Subscription[] = [];

  constructor(
    private router: Router,
    private http: HttpService,
    private util: UtilService
  ) {
    // Get initial database selection
    this.selectedDatabase = ApiConstants.SELECTED_DATABASE;
    this.getTrending();

    // Subscribe to the dropdown change event
    const dropdownSub = this.util.dropdownChange$.subscribe(() => {
      this.selectedDatabase = ApiConstants.SELECTED_DATABASE;
      this.getTrending();
    });
    this.subscriptions.push(dropdownSub);

    // Subscribe to database change event
    const dbSub = this.util.databaseChange$.subscribe((dbName: string) => {
      this.selectedDatabase = dbName;
      this.getTrending();
    });
    this.subscriptions.push(dbSub);
  }

  ngOnInit() {
    // Check if navigated from demo question in Library
    // Use history.state which is available after navigation completes
    const state = history.state as { demoQuestion?: string };
    if (state?.demoQuestion) {
      this.question = state.demoQuestion;
      // Auto-submit the demo question after a short delay
      setTimeout(() => {
        this.navigate(this.question);
      }, 300);
    }
  }

  ngOnDestroy() {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  getTrending() {
    this.http.getQuikInsights(this.selectedDatabase).subscribe((res) => {
      console.log('Trending questions for database:', this.selectedDatabase, res);
      this.trendingQuestion = res;
    });
  }

  navigateAnswer() {
    if(this.question.trim()) {
      this.navigate(this.question);
    }
  }

  navigate(question: string) {
    this.router.navigateByUrl('insights', { replaceUrl: true, state: {
      question: question,
      database: this.selectedDatabase
    } });
  }

}
