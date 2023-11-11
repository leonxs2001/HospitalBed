import {Injectable} from '@angular/core';
import {AuthenticatedUser} from "./authenticated-user";
import {UserLogin} from "./user-login";
import {HttpClient, HttpErrorResponse, HttpHeaders} from "@angular/common/http";
import {Observable, Subject} from "rxjs";
import {DataRepresentation} from "./data-representation";

@Injectable({
  providedIn: 'root'
})
export class AuthenticatedServerCommunicationService {//TODO add token expiring method
  private readonly SESSION_STORAGE_KEY = "authenticatedUser";
  private tokenExists: boolean = false;

  private authenticatedUser: AuthenticatedUser = {
    username: "",
    token: ""
  };

  private tokenExpiresSubject = new Subject<void>();

  constructor(private http: HttpClient) {
  }

  private setAuthenticatedUser(authenticatedUser: AuthenticatedUser) {
    const authenticatedUserJSON = JSON.stringify(authenticatedUser);
    sessionStorage.setItem(this.SESSION_STORAGE_KEY, authenticatedUserJSON);
    this.authenticatedUser = authenticatedUser;
    this.tokenExists = true;
  }

  private errorTokenExpirationHandler(error: HttpErrorResponse, handleError: (error: HttpErrorResponse) => void) {
    let tokenIsExpired: boolean = (error.status == 401 && error.error == "The token is not valid anymore.");
    if (tokenIsExpired) {
      this.deleteToken();
      this.tokenExpiresSubject.next();
    } else {
      handleError(error);
    }
  }

  private deleteToken() {
    this.tokenExists = false;
    sessionStorage.removeItem(this.SESSION_STORAGE_KEY);
  }

  doesTheTokenExist(): boolean {
    if (!this.tokenExists) {
      const authenticatedUserJSON = sessionStorage.getItem(this.SESSION_STORAGE_KEY);
      if (authenticatedUserJSON) {
        this.tokenExists = true;
        this.authenticatedUser = JSON.parse(authenticatedUserJSON);
      }
    }
    return this.tokenExists;
  }

  /**
   * @return - The AuthenticatedUser if there is one and null if there is not.
   */
  getAuthenticatedUser(): AuthenticatedUser | null {
    if (this.tokenExists) {
      return this.authenticatedUser;
    }
    return null;
  }

  setTokenExpirationStrategy(handleTokenExpiration: () => void) {
    this.tokenExpiresSubject.subscribe(handleTokenExpiration);
  }

  authenticateUser(userLogin: UserLogin, handleSuccessfulResponse: () => void, handleError = (error: HttpErrorResponse) => console.log(error)): void {
    let observable: Observable<AuthenticatedUser> = this.http.post<AuthenticatedUser>('/api/token', userLogin);//TODO ändern
    observable.subscribe({
      next: (authenticatedUser: AuthenticatedUser) => {
        this.setAuthenticatedUser(authenticatedUser);
        handleSuccessfulResponse();
      },
      error: handleError
    })
  }

  logoutUser(handleSuccessfulResponse: () => void) {
    if (this.doesTheTokenExist()) {
      const httpOptions = {
        headers: new HttpHeaders({
          'Authorization': this.authenticatedUser.token
        })
      };

      let observable: Observable<Object> = this.http.delete('/api/token', httpOptions);

      observable.subscribe({
        complete: () => {// TODO Überprüfen, ob das richtig so ist!!!
          this.deleteToken();
          handleSuccessfulResponse();
        }
      })
    } else {
      handleSuccessfulResponse();
    }
  }

  getDataRepresentations(handleSuccessfulResponse: (dataRepresentations: DataRepresentation[]) => void, handleError = (error: HttpErrorResponse) => console.log(error)) {
    const httpOptions = {
      headers: new HttpHeaders({
        'Authorization': this.authenticatedUser.token
      })
    };

    let observable: Observable<DataRepresentation[]> = this.http.get<DataRepresentation[]>("/api/data-representations", httpOptions);

    observable.subscribe({
      next: handleSuccessfulResponse,
      error: error => {
        this.errorTokenExpirationHandler(error, handleError);
      }
    })
  }
}
