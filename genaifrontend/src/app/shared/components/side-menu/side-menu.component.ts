import { Component, EventEmitter, Input, Output, SimpleChanges, ViewChild } from '@angular/core';
import { MatSidenav } from '@angular/material/sidenav';
import { MatIconModule } from '@angular/material/icon';
import { CommonModule } from '@angular/common';
import { Route, Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { LibraryComponent } from "../library/library.component";
import { AuthService } from '../../../_services/auth/auth.service';
import { UtilService } from '../../../_services/utils/util.service';
import { ThemeService } from '../../../_services/theme/theme.service';

@Component({
    selector: 'app-side-menu',
    standalone: true,
    templateUrl: './side-menu.component.html',
    styleUrl: './side-menu.component.scss',
    imports: [MatIconModule, CommonModule, MatButtonModule, LibraryComponent]
})
export class SideMenuComponent {
  @Input()
  isCollapsed: boolean = false;
  @Output() sidenav: EventEmitter<any> = new EventEmitter();
  isMobile: boolean = false;
  questionslist: string[] = [];
  userdetails: any;

  constructor(
    private router: Router,
    private auth: AuthService,
    private util: UtilService,
    private theme: ThemeService
  ) {
    this.userdetails = this.auth.userDet;
  }


  logout() {
    this.auth.logout();
    this.theme.setTheme('light-theme');
    this.sidenav.emit('logout');
    this.router.navigateByUrl('', {replaceUrl : true});
  }

  toggleMenu() {
    this.sidenav.emit();
  }

  navigate(path: string) {
    this.util.hightLight.next('reset');
    this.router.navigateByUrl(path, {replaceUrl : true});
  }

}
