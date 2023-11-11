import {Component, OnInit} from '@angular/core';
import {Router} from "@angular/router";
import {AuthenticatedServerCommunicationService} from "../../authenticated-server-communication.service";
import {User} from "../../user";
import {Subject} from "rxjs";

@Component({
  selector: 'app-head',
  templateUrl: './head.component.html',
  styleUrls: ['./head.component.css']
})
export class HeadComponent implements OnInit {

  constructor(private authenticatedServerCommunicationService: AuthenticatedServerCommunicationService, private router: Router) {
  }

  user: User = {
    username: "",
  };

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
    })// TODO add error function
  }
}
