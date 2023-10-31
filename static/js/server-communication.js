export const csrfMiddlewareToken = document.querySelector('[name=csrfmiddlewaretoken]');

// TODO löschen
/**
 * Function for deleting a UserDataRepresentation on server side.
 * @param {string|int} userDataRepresentationId - A parameter for the id of the UserDataRepresentation which should be deleted.
 * @param {function} handleSuccessfulResponseFunction - A parameter for the handling of a successful request.
 * @param {function} handleErrorFunction - A parameter for handling of a failed request. Has the error as parameter.
 */
export function deleteUserDataRepresentation2(userDataRepresentationId, handleSuccessfulResponseFunction = () => {
}, handleErrorFunction = (error) => console.log(error)) {

    if (userDataRepresentationId == null || userDataRepresentationId == undefined) {
        throw new Error("There is no given userDataRepresentationId.");
    }

    fetch("/delete/user-data-representation", {
        method: "DELETE",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfMiddlewareToken.value
        },
        body: JSON.stringify({
            id: userDataRepresentationId
        })
    }).then((response) => {
        if (response.ok) {
            handleSuccessfulResponseFunction();
        } else {
            throw new Error(`Request failed with statuscode ${response.status}.`);
        }
    }).catch(handleErrorFunction);
}

//TODO angucken löschen
/**
 * Function for creation a new UserDataRepresentation on server side.
 * @param {string} locationType - A parameter containing the string representation for the location.
 * @param {string} themeType - A parameter containing the string representation for the theme.
 * @param {string} timeType - A parameter containing the string representation for the time.
 * @param {function} handleSuccessfulResponseFunction - A parameter for the handling of a successful request. Has the returned data from the response as parameter.
 * @param {function} handleErrorFunction - A parameter for handling of a failed request. Has the error as given parameter.
 */
export function createNewUserDataRepresentation2(locationType, themeType, timeType, handleSuccessfulResponseFunction = () => {
}, handleErrorFunction = (error) => console.log(error)) {
    // create the new UserDataRepresentation at the server and use the given result to build the new ContentView
    fetch("/create/user-data-representation", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfMiddlewareToken.value
        },
        body: JSON.stringify({
            location_type: locationType,
            theme_type: themeType,
            time_type: timeType,
        })
    }).then((response) => {
        if (response.ok) {
            return response.json();
        }
        throw new Error(`Request failed with statuscode ${response.status}.`);
    }).then(handleSuccessfulResponseFunction).catch(handleErrorFunction);
}

// TODO Refactor!! PATCH?
/**
 * Function for updating the order of all USerDataRepresentations
 * @param {Array<object>} idOrderPairList - A parameter for all UserDataRepresentations with its order. The first UserDataRepresentation has the order 0.
 * @param {function} handleSuccessfulResponseFunction - A parameter for the handling of a successful request.
 * @param {function} handleErrorFunction - A parameter for handling of a failed request. Has the error as given parameter.
 */
export function updateUserDataRepresentationOrder2(idOrderPairList, handleSuccessfulResponseFunction = () => {
}, handleErrorFunction = (error) => console.log(error)) {
    // fetch the data to the server
    fetch("/update/order", {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfMiddlewareToken.value
        },
        body: JSON.stringify(idOrderPairList)
    }).then((response) => {
        if (response.ok) {
            handleSuccessfulResponseFunction();
        } else {
            throw new Error(`Request failed with statuscode ${response.status}.`);
        }
    }).catch(handleErrorFunction);
}


/**
 * Method for creating the right url for the ContentView.
 * @param {int|string} userDataRepresentationId
 * @param {boolean} updateInputs
 * @param {boolean} downloadCSV
 * @param {string|null} locationId
 * @param {string|null} time
 * @param {string|null} endTime
 * @returns {URL}
 */
function createDataUrl(userDataRepresentationId, updateInputs, downloadCSV, locationId, time, endTime) {
    let url = new URL(location.protocol + "//" + location.host + "/get_data/");

    url.searchParams.append("id", userDataRepresentationId);

    url.searchParams.append("update_flag", updateInputs.toString());

    url.searchParams.append("download", downloadCSV.toString());

    //add the id param, if it's a list of occupancies (locationId is given)
    if (locationId) {
        url.searchParams.append("location_id", locationId);
    }

    //add the time params, if its a time type
    if (time) {
        url.searchParams.append("time", time);
        if (endTime) {
            url.searchParams.append("end_time", endTime);
        }
    }

    return url;
}

// TODO make in front end
/**
 * Function for downloading the data of a UserDataRepresentation as csv file.
 * @param {int|string} userDataRepresentationId - A parameter for the id of the UserDataRepresentation which data should be downloaded.
 */
export function downloadUserDataRepresentationDataAsCSV(userDataRepresentationId) {
    let url = createDataUrl(userDataRepresentationId, false, true, null, null, null);
    window.open(url, "_blank");
}

/**
 * Function for getting the data of a UserDataRepresentation from the server.
 * @param {int|string} userDataRepresentationId - A parameter for the id of the UserDataRepresentation which data should be downloaded.
 * @param {boolean} updateInputs - A parameter for updating the user inputs on the server side.
 * @param {string|null} time - A parameter for updating of the time attribute.
 * @param {string|null} endTime - A parameter for updating of the endTime attribute.
 * @param {string|null} locationId - A parameter for updating of the selected location with its locationId attribute.
 * @param {function} handleSuccessfulResponseFunction - A parameter for the handling of a successful request. Has the returned data from the response as parameter.
 * @param {function} handleErrorFunction - A parameter for handling of a failed request. Has the error as given parameter.
 */
export function getUserDataRepresentationData2(userDataRepresentationId, updateInputs, time, endTime, locationId, handleSuccessfulResponseFunction = () => {
}, handleErrorFunction = (error) => console.log(error)) {
    let url = createDataUrl(userDataRepresentationId, updateInputs, false, locationId, time, endTime);

    fetch(url.toString(), {
        method: "GET",
        headers: {
            "X-CSRFToken": csrfMiddlewareToken.value
        },
    }).then((response) => {
        if (response.ok) {
            return response.json();
        }
        throw new Error(`Request failed with statuscode ${response.status}.`);
    }).then(handleSuccessfulResponseFunction).catch(handleErrorFunction);
}

/**
 * Function for getting the authorization token from the session storage.
 * @returns {string}
 */
export function getAuthorizationTokenFromSessionStorage() {
    return sessionStorage.getItem("sessionAuthorizationToken");
}

/**
 * Function for setting the authorization token in the session storage.
 * @param {string} token
 */
export function setAuthorizationTokenInSessionStorage(token) {
    sessionStorage.setItem("sessionAuthorizationToken", token);
}

/**
 * Function for authentication.
 * @param {string} username - A Parameter for the username of the  user to be authenticated.
 * @param {string} password - A Parameter for the password of the  user to be authenticated.
 * @param {function} handleSuccessfulResponseFunction- A parameter for the handling of a successful request. Has the returned token from the response as parameter. Every REST API call is possible with this token. The Token expires after 1 hour without a call of the API.
 * @param {function} handleErrorFunction - A parameter for handling of a failed request. Has the error as given parameter.
 */
export function authenticateUser(username, password, handleSuccessfulResponseFunction = (token) => {
}, handleErrorFunction = (error) => console.log(error)) {
    fetch("/api/token", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    }).then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error('Fehler bei der Token-Erstellung');
        }
    }).then(handleSuccessfulResponseFunction).catch(handleErrorFunction);
}

/**
 * Function for creation a new UserDataRepresentation on server side.
 * @param {string} token - A parameter for the token needed in the token based authentication.
 * @param {int|string} dataRepresentationId - A parameter for the DataRepresentation which should be used for the new USerDataRepresentation.
 * @param {function} handleSuccessfulResponseFunction - A parameter for the handling of a successful request. Has the returned data from the response as parameter.
 * @param {function} handleErrorFunction - A parameter for handling of a failed request. Has the error as given parameter.
 */
export function createNewUserDataRepresentation(token, dataRepresentationId, handleSuccessfulResponseFunction = () => {
}, handleErrorFunction = (error) => console.log(error)) {
    // create the new UserDataRepresentation at the server and use the given result to build the new ContentView
    fetch("/api/user-data-representation", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            'Authorization': token
        },
        body: JSON.stringify({
            dataRepresentationId: dataRepresentationId
        })
    }).then((response) => {
        if (response.ok) {
            return response.json();
        }
        throw new Error(`Request failed with statuscode ${response.status}.`);
    }).then(handleSuccessfulResponseFunction).catch(handleErrorFunction);
}

/**
 * Function for deleting a UserDataRepresentation on server side.
 * @param {string} token - A parameter for the token needed in the token based authentication.
 * @param {string|int} userDataRepresentationId - A parameter for the id of the UserDataRepresentation which should be deleted.
 * @param {function} handleSuccessfulResponseFunction - A parameter for the handling of a successful request.
 * @param {function} handleErrorFunction - A parameter for handling of a failed request. Has the error as parameter.
 */
export function deleteUserDataRepresentation(token, userDataRepresentationId, handleSuccessfulResponseFunction = () => {
}, handleErrorFunction = (error) => console.log(error)) {

    if (userDataRepresentationId == null || userDataRepresentationId == undefined) {
        throw new Error("There is no given userDataRepresentationId.");
    }

    fetch(`/api/user-data-representation/${userDataRepresentationId}`, {
        method: "DELETE",
        headers: {
            "Content-Type": "application/json",
            'Authorization': token
        },
    }).then((response) => {
        if (response.ok) {
            handleSuccessfulResponseFunction();
        } else {
            throw new Error(`Request failed with statuscode ${response.status}.`);
        }
    }).catch(handleErrorFunction);
}

/**
 * Function for updating the order of all USerDataRepresentations
 * @param {string} token - A parameter for the token needed in the token based authentication.
 * @param {Array<object>} idOrderPairList - A parameter for all UserDataRepresentations with its order. The first UserDataRepresentation has the order 0.
 * @param {function} handleSuccessfulResponseFunction - A parameter for the handling of a successful request.
 * @param {function} handleErrorFunction - A parameter for handling of a failed request. Has the error as given parameter.
 */
export function updateUserDataRepresentationOrder(token, idOrderPairList, handleSuccessfulResponseFunction = () => {
}, handleErrorFunction = (error) => console.log(error)) {
    // fetch the data to the server
    fetch("/api/user-data-representations", {
        method: "PATCH",
        headers: {
            "Content-Type": "application/json",
            'Authorization': token
        },
        body: JSON.stringify(idOrderPairList)
    }).then((response) => {
        if (response.ok) {
            handleSuccessfulResponseFunction();
        } else {
            throw new Error(`Request failed with statuscode ${response.status}.`);
        }
    }).catch(handleErrorFunction);
}

/**
 * Function for getting the data of a UserDataRepresentation from the server.
 * @param {string} token - A parameter for the token needed in the token based authentication.
 * @param {int|string} userDataRepresentationId - A parameter for the id of the UserDataRepresentation which data should be downloaded.
 * @param {function} handleSuccessfulResponseFunction - A parameter for the handling of a successful request. Has the returned data from the response as parameter.
 * @param {function} handleErrorFunction - A parameter for handling of a failed request. Has the error as given parameter.
 */
export function getUserDataRepresentationData(token, userDataRepresentationId, handleSuccessfulResponseFunction = () => {
}, handleErrorFunction = (error) => console.log(error)) {

    fetch(`/api/user-data-representation/${userDataRepresentationId}`, {
        method: "GET",
        headers: {
            'Authorization': token
        },
    }).then((response) => {
        if (response.ok) {
            return response.json();
        }
        throw new Error(`Request failed with statuscode ${response.status}.`);
    }).then(handleSuccessfulResponseFunction).catch(handleErrorFunction);
}

/**
 * Function for patching the UserDataRepresentation attributes.
 * @param {string} token - A parameter for the token needed in the token based authentication.
 * @param {int|string} userDataRepresentationId - A parameter for the id of the UserDataRepresentation which data should be downloaded.
 * @param {string|null} time - A parameter for updating of the time attribute.
 * @param {string|null} endTime - A parameter for updating of the endTime attribute.
 * @param {string|null} locationId - A parameter for updating of the selected location with its locationId attribute.
 * @param {function} handleSuccessfulResponseFunction - A parameter for the handling of a successful request.
 * @param {function} handleErrorFunction - A parameter for handling of a failed request. Has the error as given parameter.
 */
export function patchUserDataRepresentation(token, userDataRepresentationId, time, endTime, locationId, handleSuccessfulResponseFunction = () => {
}, handleErrorFunction = (error) => console.log(error)) {

    let userDataRepresentationPatch = {};

    if (time) {
        userDataRepresentationPatch.time = time;
    }

    if (endTime) {
        userDataRepresentationPatch.endTime = endTime;
    }

    if (locationId) {
        userDataRepresentationPatch.locationId = locationId;
    }

    fetch(`/api/user-data-representation/${userDataRepresentationId}`, {
        method: "PATCH",
        headers: {
            'Authorization': token
        },
        body: JSON.stringify(userDataRepresentationPatch)
    }).then((response) => {
        if (response.ok) {
            handleSuccessfulResponseFunction();
        } else {
            throw new Error(`Request failed with statuscode ${response.status}.`);
        }
    }).then(handleSuccessfulResponseFunction).catch(handleErrorFunction);
}

/**
 * Function for getting the DataRepresentation.
 * @param {string} token - A parameter for the token needed in the token based authentication.
 * @param {function} handleSuccessfulResponseFunction - A parameter for the handling of a successful request. Has the returned data from the response as parameter.
 * @param {function} handleErrorFunction - A parameter for handling of a failed request. Has the error as given parameter.
 */
export function getDataRepresentations(token, handleSuccessfulResponseFunction = () => {
}, handleErrorFunction = (error) => console.log(error)) {
    fetch("/api/data-representations", {
        method: "GET",
        headers: {
            'Authorization': token
        },
    }).then((response) => {
        if (response.ok) {
            return response.json();
        }
        throw new Error(`Request failed with statuscode ${response.status}.`);
    }).then(handleSuccessfulResponseFunction).catch(handleErrorFunction);
}
