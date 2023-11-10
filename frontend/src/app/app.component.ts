import {Component, OnInit} from '@angular/core';
import {AuthenticatedServerCommunicationService} from "./authenticated-server-communication.service";
import {Router} from "@angular/router";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit{
  constructor(private authenticatedServerCommunicationService: AuthenticatedServerCommunicationService, private router: Router) {
  }
  ngOnInit(): void {
    this.authenticatedServerCommunicationService.setTokenExpirationStrategy(() => {
      this.router.navigate(["/login"]);
    });
  }
}
