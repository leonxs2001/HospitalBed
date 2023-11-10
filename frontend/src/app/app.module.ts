import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { LoginComponent } from './login/login.component';
import { DashboardComponent } from './dashboard/dashboard.component';
import {FormsModule} from "@angular/forms";
import {HttpClientModule} from "@angular/common/http";
import {HeadComponent} from "./dashboard/head/head.component";
import {ContentComponent} from "./dashboard/content/content.component";
import { AddContentViewComponent } from './dashboard/content/add-content-view/add-content-view.component';

@NgModule({
  declarations: [
    AppComponent,
    HeadComponent,
    LoginComponent,
    DashboardComponent,
    ContentComponent,
    AddContentViewComponent,
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    FormsModule,
    HttpClientModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }

