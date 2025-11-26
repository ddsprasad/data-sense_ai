import { Component, ViewChild } from '@angular/core';
import { BreakpointObserver } from '@angular/cdk/layout';
import { MatSidenav } from '@angular/material/sidenav';
import { UtilService } from './_services/utils/util.service';
import { NavigationEnd, NavigationStart, Router } from '@angular/router';
import { filter } from 'rxjs';
import { AuthService } from './_services/auth/auth.service';
import { ThemeService } from './_services/theme/theme.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  title = 'datsense-AI';
  isCollapsed: boolean = true;
  isMobile: boolean = false;
  isSidemenu: boolean = false;
  isHeader: boolean = false;
  sideMenuRoutesNotAllowed = ['login'];
  @ViewChild(MatSidenav)
  sidenav!: MatSidenav;
  constructor(
    private observer: BreakpointObserver,
    private utils: UtilService,
    private router: Router,
    private auth: AuthService,
    private theme: ThemeService
  ) {
    this.auth.checkLogin();
    this.utils.matIconListGenerate(); // All custom SVG will changed to material icon
    this.routerSubscribe();
    this.theme.loadTheme();
  }


  ngOnInit(): void {
    this.observer.observe(['(max-width: 800px)']).subscribe((screenSize) => {
      if (screenSize.matches) {
        this.isMobile = true;
      } else {
        this.isMobile = false;
      }
    });
  }

  routerSubscribe() {
    this.router.events.pipe(
      filter(event => event instanceof NavigationStart)
    ).subscribe((res: any) => {
          if(res.url.indexOf('login') > -1 || res.url == '/') {
            this.isSidemenu = false;
            this.isHeader = false;
          } else {
            this.isSidemenu = true;
            this.isHeader = true;
          }
    });
  }

  toggleMenu(type?: string) { 
    if(type == 'logout') {
      this.isCollapsed  = true;
      return;
    }
    if (this.isMobile) {
      this.sidenav.toggle();
      this.isCollapsed = false;
    } else {
      this.sidenav.open();
      this.isCollapsed = !this.isCollapsed;
    }
  }

  navigate(_path: string) {
    this.router.navigateByUrl('', { replaceUrl: true });
  }
}
