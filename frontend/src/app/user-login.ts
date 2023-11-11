import {User} from "./user";

export interface UserLogin extends User {
  password: string;
}
