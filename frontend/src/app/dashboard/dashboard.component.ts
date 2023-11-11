import { Component } from '@angular/core';
import {User} from "../user";
import {AuthenticatedServerCommunicationService} from "../authenticated-server-communication.service";
import {Router} from "@angular/router";

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent {
  user: User = {
    username: ""
  };

  constructor(private authenticatedServerCommunicationService: AuthenticatedServerCommunicationService, private router: Router) {
  }

  ngOnInit() {
    if (this.authenticatedServerCommunicationService.doesTheTokenExist()) {
      this.user.username = <string>this.authenticatedServerCommunicationService.getAuthenticatedUser()?.username;
    } else {
      this.router.navigate(["/login"])
    }
  }

  logout() {
    this.authenticatedServerCommunicationService.logoutUser(() => {
      this.router.navigate(["/login"])
    })
  }

}
