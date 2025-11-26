import { inject } from '@angular/core';
import { AuthService } from './../_services/auth/auth.service';
import { CanActivateFn, Router } from '@angular/router';


export const authGuard: CanActivateFn = (route, state) => {
  return inject(AuthService).isAuthenticated() ? true : inject(Router).createUrlTree(['/']);;
};
