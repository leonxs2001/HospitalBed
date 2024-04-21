export const csrfMiddlewareToken = document.querySelector('[name=csrfmiddlewaretoken]');

/**
 * Function for deleting a UserDataRepresentation on server side.
 * @param {string|number} userDataRepresentationId - A parameter for the id of the UserDataRepresentation which should be deleted.
 * @param {function} handleSuccessfulResponseFunction - A parameter for the handling of a successful request.
 * @param {function} handleErrorFunction - A parameter for handling of a failed request. Has the error as parameter. Logs the error on the console if not given.
 */
export function deleteUserDataRepresentation(userDataRepresentationId, handleSuccessfulResponseFunction = () => {
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

/**
 * Function for creation a new UserDataRepresentation on server side.
 * @param {string} locationType - A parameter containing the string representation for the location.
 * @param {string} themeType - A parameter containing the string representation for the theme.
 * @param {string} timeType - A parameter containing the string representation for the time.
 * @param {function} handleSuccessfulResponseFunction - A parameter for the handling of a successful request. Has the returned data from the response as parameter.
 * @param {function} handleErrorFunction - A parameter for handling of a failed request. Has the error as given parameter. Logs the error on the console if not given.
 */
export function createNewUserDataRepresentation(locationType, themeType, timeType, handleSuccessfulResponseFunction = () => {
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

/**
 * Function for updating the order of all USerDataRepresentations
 * @param {Array<object>} idOrderPairList - A parameter for all UserDataRepresentations with its order. The first UserDataRepresentation has the order 0.
 * @param {function} handleSuccessfulResponseFunction - A parameter for the handling of a successful request.
 * @param {function} handleErrorFunction - A parameter for handling of a failed request. Has the error as given parameter. Logs the error on the console if not given.
 */
export function updateUserDataRepresentationOrder(idOrderPairList, handleSuccessfulResponseFunction = () => {
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
 * @param {number|string} userDataRepresentationId
 * @param {boolean} updateInputs
 * @param {boolean} downloadCSV
 * @param {number|string|null} locationId
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

/**
 * Function for downloading the data of a UserDataRepresentation as csv file.
 * @param {number|string} userDataRepresentationId - A parameter for the id of the UserDataRepresentation which data should be downloaded.
 */
export function downloadUserDataRepresentationDataAsCSV(userDataRepresentationId) {
    let url = createDataUrl(userDataRepresentationId, false, true, null, null, null);
    window.open(url, "_blank");
}

/**
 * Function for getting the data of a UserDataRepresentation from the server.
 * @param {number|string} userDataRepresentationId - A parameter for the id of the UserDataRepresentation which data should be downloaded.
 * @param {boolean} updateInputs - A parameter for updating the user inputs on the server side.
 * @param {string|null} time - A parameter for updating of the time attribute.
 * @param {string|null} endTime - A parameter for updating of the endTime attribute.
 * @param {string|number|null} locationId - A parameter for updating of the selected location with its locationId attribute.
 * @param {function} handleSuccessfulResponseFunction - A parameter for the handling of a successful request. Has the returned data from the response as parameter.
 * @param {function} handleErrorFunction - A parameter for handling of a failed request. Has the error as given parameter. Logs the error on the console if not given.
 */
export function getUserDataRepresentationData(userDataRepresentationId, updateInputs, time, endTime, locationId, handleSuccessfulResponseFunction = () => {
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