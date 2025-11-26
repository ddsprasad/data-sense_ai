import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { MatSidenavModule } from '@angular/material/sidenav';
import { SideMenuComponent } from "./shared/components/side-menu/side-menu.component";
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { MatIconModule } from '@angular/material/icon';
import { HTTP_INTERCEPTORS, HttpClientModule } from '@angular/common/http';
import {MatButtonModule} from '@angular/material/button';
import { HeaderComponent } from "./shared/components/header/header.component";
import { JwtInterceptor } from './_helpers/JwtInterceptor';


@NgModule({
    declarations: [
        AppComponent
    ],
    providers: [
        { provide: HTTP_INTERCEPTORS, useClass: JwtInterceptor, multi: true },
    ],
    bootstrap: [AppComponent],
    imports: [
        BrowserModule,
        AppRoutingModule,
        MatSidenavModule,
        MatIconModule,
        MatButtonModule,
        BrowserAnimationsModule,
        SideMenuComponent,
        HttpClientModule,
        HeaderComponent
    ]
})
export class AppModule { }
