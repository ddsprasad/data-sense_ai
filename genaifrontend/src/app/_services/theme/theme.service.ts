import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  theme: string = '';
  constructor() { }

  setTheme(theme: string) {
    this.theme = theme;
    localStorage.setItem('theme-selection', theme);
    this.classSetTheme();
  }

  loadTheme() {
    const theme = localStorage.getItem('theme-selection');
    if(theme) {
      this.theme = theme;
    } else {
      this.theme = 'light-theme';
    }
    this.classSetTheme();
  }

  classSetTheme() {
    document.body.className = `mat-typography ${this.theme}`;
  }

}
