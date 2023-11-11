import {Component, OnInit} from '@angular/core';
import {DataRepresentation} from "../../../data-representation";
import {AuthenticatedServerCommunicationService} from "../../../authenticated-server-communication.service";

interface TimeWithId {
  id: number;
  timeType: string;
}

@Component({
  selector: 'app-add-content-view',
  templateUrl: './add-content-view.component.html',
  styleUrls: ['./add-content-view.component.css']
})
export class AddContentViewComponent implements OnInit{
  dataRepresentations: DataRepresentation[] = [
    {id: 1, locationType: "Krankenhaus", themeType: "Informationen", timeType: "Neartime"},
    {id: 2, locationType: "Krankenhaus", themeType: "Informationen", timeType: "Zeitpunkt"},
    {id: 3, locationType: "Krankenhaus", themeType: "Informationen", timeType: "Zeitspanne"},
    {id: 4, locationType: "Krankenhaus", themeType: "Informationen der Betten", timeType: "Neartime"},
    {id: 5, locationType: "Krankenhaus", themeType: "Informationen der Betten", timeType: "Zeitpunkt"},
    {id: 6, locationType: "Krankenhaus", themeType: "Informationen der Betten", timeType: "Zeitspanne"},
    {id: 7, locationType: "Station", themeType: "Informationen", timeType: "Neartime"},
    {id: 8, locationType: "Station", themeType: "Informationen", timeType: "Zeitpunkt"},
    {id: 9, locationType: "Station", themeType: "Informationen", timeType: "Zeitspanne"},
    {id: 10, locationType: "Station", themeType: "Informationen der Betten", timeType: "Neartime"},
    {id: 11, locationType: "Station", themeType: "Informationen der Betten", timeType: "Zeitpunkt"},
    {id: 12, locationType: "Station", themeType: "Informationen der Betten", timeType: "Zeitspanne"},
  ];

  constructor(private authenticatedServerCommunicationService: AuthenticatedServerCommunicationService) {
  }

  getLocations(): string[] {
    return Array.from(new Set(this.dataRepresentations.map((item) => item.locationType)));
  }

  getThemes(locationType: string): string[] {
    return Array.from(
      new Set(
        this.dataRepresentations
          .filter((item) => item.locationType === locationType)
          .map((item) => item.themeType)
      )
    );
  }

  getTimeIds(locationType: string, themeType: string): TimeWithId[] {
    return this.dataRepresentations
      .filter((item) => item.locationType === locationType && item.themeType === themeType)
      .map((item) => ({id: item.id, timeType: item.timeType}));
  }

  get locations(): string[] {
    return this.getLocations().map((locationType) => locationType);
  }

  onNewUserDataRepresentationClick(dataRepresentationId: number) {
    console.log(dataRepresentationId);
  }

  ngOnInit(){
    this.authenticatedServerCommunicationService.getDataRepresentations((dataRepresentations => {
      this.dataRepresentations = dataRepresentations;
    }));
  }
}
