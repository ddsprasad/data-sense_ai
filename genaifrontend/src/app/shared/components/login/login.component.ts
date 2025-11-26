import { MatButtonModule } from '@angular/material/button';
import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { HttpService } from '../../../_services/http/http.service';
import { AuthService } from '../../../_services/auth/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    MatButtonModule,
    CommonModule,
    ReactiveFormsModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss'
})
export class LoginComponent {
  loginForm: FormGroup;
  loader:boolean = false;
  showUserErr:string = '';
  constructor(
    private formBuilder: FormBuilder,
    private router: Router,
    private http: HttpService,
    private auth: AuthService
  ) {
    this.loginForm = this.formBuilder.group({
      username: ['', [Validators.required]],
      password: ['', Validators.required],
    });
    this.checkifUser();
  }
  ngOnInit(): void {
  }

  checkifUser() {
    const isLogged = localStorage.getItem('isLogged');
    if(isLogged) {
      this.router.navigateByUrl('/question', {replaceUrl : true});
    }
  }



  loginFormSubmit() {
    if(this.loginForm.valid) {
      this.loader = true;
      this.showUserErr = '';
      this.http.login(this.loginForm.value).subscribe((res: any) => {
        this.loader = false;
          if(res?.user_valid) {
            this.auth.login(res);
            this.auth.userDet = res;
            this.http.user_id = res.user_id;
            this.router.navigateByUrl('/question', {replaceUrl : true});
          } else {
            this.showUserErr = 'Invalid Username/Password';
          }
      }, err => {
        this.loader = false;
        this.showUserErr = 'Server Error';
      });
      
    }
  }

}
