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

//TODO angucken, warumd ata
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