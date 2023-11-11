import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {Router} from "@angular/router";
import {AuthenticatedServerCommunicationService} from "../../authenticated-server-communication.service";
import {User} from "../../user";
import {Subject} from "rxjs";

@Component({
  selector: 'app-head',
  templateUrl: './head.component.html',
  styleUrls: ['./head.component.css']
})
export class HeadComponent {
  @Input() user: User = {
    username: ""
  };

  @Output logoutEvent = new EventEmitter<void>();

  logout() {
    this.logoutEvent.emit();
  }
}
