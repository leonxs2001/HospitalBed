import {Component, OnInit} from '@angular/core';
import {UserLogin} from "../user-login";
import {AuthenticatedServerCommunicationService} from "../authenticated-server-communication.service";
import {Router} from "@angular/router";

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit{
  showError: boolean = false;

  user: UserLogin = {
    username: "",
    password: ""
  };

  constructor(private authenticatedServerCommunicationService: AuthenticatedServerCommunicationService, private router: Router) {
  }

  login() {
    this.authenticatedServerCommunicationService.authenticateUser(this.user, () => {
      this.showError = false;
      this.router.navigate(["/"]);
    }, error => {
      this.showError = true;
    });
  }

  ngOnInit(): void {
    if(this.authenticatedServerCommunicationService.doesTheTokenExist()){
      this.router.navigate(["/"]);
    }
  }
}
