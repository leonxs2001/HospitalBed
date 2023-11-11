import {User} from "./user";

export interface AuthenticatedUser extends User{
  token: string;
}
