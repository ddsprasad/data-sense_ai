import { UtilService } from './../../../_services/utils/util.service';
import { Component, HostListener, Inject } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogActions, MatDialogClose, MatDialogContent, MatDialogRef, MatDialogTitle, MAT_DIALOG_DATA  } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { HttpService } from '../../../_services/http/http.service';
import ApexCharts from 'apexcharts';
import { VaiableConstants } from '../../../_helpers/constants/variable';
@Component({
  selector: 'app-chart-modal',
  standalone: true,
  imports: [
    MatDialogTitle,
    MatDialogContent,
    MatDialogActions,
    MatDialogClose,
    MatButtonModule,
    FormsModule,
    MatIconModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './chart-modal.component.html',
  styleUrl: './chart-modal.component.scss'
})

export class ChartModalComponent {
  img: string = '';
  followupQues: string = '';
  loader: boolean = false;
  updatedChart: boolean = false;
  chart: any;
  chartOptions: any = '';
  saveChartloader: boolean = false;
  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<ChartModalComponent>,
    private http: HttpService,
    private util: UtilService
  ) {
    this.loader = false;
    console.log(this.data);
   
  }

  ngOnInit(): void {
    //Called after the constructor, initializing input properties, and the first call to ngOnChanges.
    //Add 'implements OnInit' to the class.
    setTimeout(() => {
      this.renderChart(this.data.chart_options);
    }, 500);
  }

  renderChart(chartData: any) {
    let chartDetails = JSON.parse(JSON.stringify(chartData));
    chartDetails.chart['height'] = '90%';
    chartDetails.chart['width'] = '90%';
    let apexToolBar = JSON.parse(JSON.stringify(VaiableConstants.APEXTOOLBAR));
    delete apexToolBar.tools.customIcons;
    chartDetails.chart['toolbar'] = apexToolBar;
    try {
      const ele = document.getElementById(`chartModal-view`);
      if(ele) {
        this.chart = new ApexCharts(document.getElementById(`chartModal-view`), {...chartDetails});
        this.chart.render();
      }
    } catch(e) {
      console.log(e);
    }
  }

  follwup() {
    this.loader = true;
    const chartproperties =  this.data.chart_options;
    console.log(chartproperties);
    const chartObj = {
      question_id: this.data.question_id,
      user_id: this.http.user_id,
      code: JSON.stringify(chartproperties),
      chart_type: 'apex',
      instructions: this.followupQues
    };
    this.followupQues = '';
    this.http.editChart(chartObj).subscribe((res: any) => {
      this.chart?.destroy();
      eval(res.chart_options);
      this.loader = false;
      setTimeout(() => {
        if (this.chartOptions)
        this.renderChart(this.chartOptions);
      }, 500);
      this.updatedChart = true;
      this.data['chart_options'] = {...this.chartOptions};
    }, (err) => {
      this.loader = false;
    });
  }

  saveChart() {
    this.chart?.destroy();
    if(this.updatedChart) {
      this.saveChartloader = true;
      const chartOptions = {
        question_id: this.data.question_id,
        user_id: this.http.user_id.toString(),
        chart_type: this.data.chart_type,
        chart_options: "this, this.chartOptions = " + JSON.stringify(this.data['chart_options']),
        chart_data: this.data.chart_data
      };
      this.http.saveChart(chartOptions).subscribe(c => {
        this.saveChartloader = false;
        if(c) {
          this.dialogRef.close({
            type: 'updated',
            chart:  this.data['chart_options']
          });
        }
      }, err => {
        this.saveChartloader = false;
      });
    } else {
      this.dialogRef.close();
    }
  }



  closeDialog() {
    this.chart?.destroy();
    this.dialogRef.close();
  }
}
