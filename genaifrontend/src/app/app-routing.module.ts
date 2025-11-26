import { RagFilesComponent } from './shared/components/rag-files/rag-files.component';
import { LoginComponent } from './shared/components/login/login.component';
import { AnswerComponent } from './shared/components/answer/answer.component';
import { QuestionComponent } from './shared/components/question/question.component';
import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { authGuard } from './_helpers/auth.guard';

const routes: Routes = [
  { path: '', redirectTo: '/login', pathMatch: 'full' },
  {
    path: 'login', component: LoginComponent
  },
  {
    path: 'question', component: QuestionComponent, canActivate: [authGuard],
  },
  {
    path: 'k-index', component: RagFilesComponent, canActivate: [authGuard],
  },
  {
    path: 'story', component: AnswerComponent, canActivate: [authGuard],
  },
  {
    path: 'insights', component: AnswerComponent, canActivate: [authGuard],
  },
  {
    path: 'insights/:id', component: AnswerComponent, canActivate: [authGuard],
  },
 

];

@NgModule({
  imports: [RouterModule.forRoot(routes, {useHash : true})],
  exports: [RouterModule]
})
export class AppRoutingModule { }
