import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private isLoggedIn: boolean = false;
  userDet: any;
  constructor() { 
  
  }

  checkLogin() {
    if(localStorage.getItem('isLogged') && localStorage.getItem('userDet')) {
      const userDet = JSON.parse(localStorage.getItem('userDet') || "{}");
      if(userDet) {
        this.isLoggedIn = true;
        this.userDet = userDet;
      } else {
        this.isLoggedIn = false;
      }
    } else {
      this.isLoggedIn = false;
    }
  }
  
  login(obj: any) {
    this.isLoggedIn = true;
    localStorage.setItem('isLogged', 'true');
    localStorage.setItem('userDet', JSON.stringify(obj));
  }

  logout() {
    this.isLoggedIn = false;
    localStorage.clear();
  }

  isAuthenticated(): boolean {
    return this.isLoggedIn;
  }

  getToken() {
    return this.userDet?.api_key;
  }
}
