import { ThemeService } from './../../../_services/theme/theme.service';
import { Component, EventEmitter, Input, OnDestroy, Output } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatToolbarModule } from '@angular/material/toolbar';
import { FormsModule } from '@angular/forms';
import moment from 'moment';
import { UtilService } from '../../../_services/utils/util.service';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { NavigationEnd, NavigationStart, Router } from '@angular/router';
import { filter, Subscription } from 'rxjs';
import { ApiConstants } from './../../../_helpers/constants/api';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [MatToolbarModule, MatButtonModule, MatIconModule, FormsModule, MatSlideToggleModule],
  templateUrl: './header.component.html',
  styleUrl: './header.component.scss'
})
export class HeaderComponent implements OnDestroy {
  today: string = moment().format('MM/DD/YYYY') + ' 03:00';
  private subscription: Subscription;
  toggleChecked: boolean = false;
  dropDownValue = 'Call center DW';
  @Input()
  isMobile: boolean = false;
  @Output() sidenav: EventEmitter<any> = new EventEmitter();
  constructor(
    private util: UtilService,
    private theme: ThemeService,
    private router: Router
  ) {
    this.toggleChecked = this.theme.theme == 'light-theme' ? false : true;
    this.setTimeDropDown(this.router.url);
    this.subscription = this.router.events.pipe(
      filter(event => event instanceof NavigationStart)
    ).subscribe((res: any) => {
      this.setTimeDropDown(res.url);
      
    });
  }
  

  setTimeDropDown(url: string) {
    if (url.indexOf('/k-index') > -1) {
      this.dropDownValue = 'Michigan Supreme Court RFP';
      this.today = moment().format('MM/DD/YYYY') + ' 10:15';
    } else {
      this.dropDownValue = 'Call center DW';
      this.today = moment().format('MM/DD/YYYY') + ' 03:15';
    }
  }

  themChange() {
    this.toggleChecked = !this.toggleChecked;
    if (this.toggleChecked) {
      this.theme.setTheme('dark-theme');
    } else {
      this.theme.setTheme('light-theme');
    }
  }

  ngOnDestroy(): void {
    if (this.subscription) {
      alert('unsub');
      this.subscription.unsubscribe();
    }
  }
  toggle() {
    this.sidenav.emit();
  }

  

  onVersionChange(event: Event): void {
    const selectedVersion = (event.target as HTMLSelectElement).value;
    ApiConstants.APIVERSION = selectedVersion;
    if (selectedVersion == 'vc') {    
      this.today = moment().format('MM/DD/YYYY') + ' 05:15';
    } else {
      this.today = moment().format('MM/DD/YYYY') + ' 03:15';
    }
    console.log('API version updated to:', ApiConstants.APIVERSION );
     
    this.util.notifyDropdownChange();
  }

}
