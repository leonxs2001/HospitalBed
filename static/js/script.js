import {
    deleteUserDataRepresentation,
    createNewUserDataRepresentation,
    updateUserDataRepresentationOrder
} from "./server-communication.js";

const csrfMiddlewareToken = document.querySelector('[name=csrfmiddlewaretoken]');
const contentViewTemplate = document.querySelector("#content-view-template");
const timeInputSpanTemplate = document.querySelector("#template-div .time-input-span.time-template");
const fromInputSpanTemplate = document.querySelector("#template-div .time-input-span.from-template");
const toInputSpanTemplate = document.querySelector("#template-div .time-input-span.to-template");
const locationSelectTemplate = document.querySelector("#template-div .selection-input");
const occupancyChartCanvasTemplate = document.querySelector("#template-div .information-chart-canvas");
const occupancyHistoryChartCanvasTemplate = document.querySelector("#template-div .occupancy-history-chart-canvas");
const locationListHeadDivTemplate = document.querySelector("#template-div .location-list-head-div.location-template");
const locationListDivTemplate = document.querySelector("#template-div .location-list-div");
const locationDivTemplate = document.querySelector("#template-div .location-div.location-template");
const bedListHeadDivTemplate = document.querySelector("#template-div .location-list-head-div.bed-template");
const bedDivTemplate = document.querySelector("#template-div .location-div.bed-template");
const roomDataDiv = document.querySelector("#template-div .room-data-div");
const loaderTemplate = document.querySelector("#template-div .loader");

const DATETIME_REGEX = /(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/

/**
 * Method for getting the percentage of a given value to a given maxValue.
 * The percentage is a string rounded to 2 digits.
 * @param value
 * @param maxValue
 * @returns string
 */
function percentage(value, maxValue) {
    if (value == undefined || maxValue == undefined || maxValue == 0) {
        return 0;
    }
    return ((value / maxValue) * 100).toFixed(2);
}

/**
 * The Manager class for the ContentViews.
 */
class ContentViewManager {
    #contentViews = [];
    #draggedContentView;
    #parent = document.querySelector("#content-div");

    /**
     * Factory-method for the right ContentView based on the given html-contentView.
     * @param contentView
     * @returns ContentView
     */
    createContentView(contentView) {
        // get the locationType and themeType from the html-contentView
        const locationType = contentView.dataset.location;
        const themeType = contentView.dataset.theme;

        let contentViewInstance = null;

        if (themeType == "I") {
            if (locationType == "R") {
                contentViewInstance = new RoomInformationContentView(contentView, this);
            } else {
                contentViewInstance = new LocationInformationContentView(contentView, this);
            }
        } else if (themeType == "H") {
            contentViewInstance = new LocationHistoryContentView(contentView, this);
        } else if (themeType == "B") {
            contentViewInstance = new BedsInformationContentView(contentView, this);
        } else {
            contentViewInstance = new LocationsInformationContentView(contentView, this);
        }

        // inssert the new ContentView into the ContentView list
        this.#contentViews.push(contentViewInstance);

        return contentViewInstance;
    }

    /**
     * Factory-method for creating a new ContentView based on the parameters.
     * @param locationType
     * @param themeType
     * @param timeType
     * @returns ContentView
     */
    createNewContentView(locationType, themeType, timeType) {
        let contentView = null;
        createNewUserDataRepresentation(locationType, themeType, timeType,  data => {
            // get all the data from the response
            const locations = "locations" in data ? data["locations"] : null;
            const user_data_representation = data["user_data_representation"];
            const data_representation = data["data_representation"];

            // create the right html-ContentView
            let htmlContentView = this.createNewContentViewElement(data_representation, user_data_representation, locations);

            // call the factory-method to create a ContentView from the new html-ContentView
            contentView = this.createContentView(htmlContentView);
        })

        return contentView;
    }

    /**
     * Factory-method for creating a new html-ContentView based on the given parameters.
     * @param data_representation
     * @param user_data_representation
     * @param locations
     * @returns Node
     */
    createNewContentViewElement(data_representation, user_data_representation, locations) {

        // clone the contentView template
        const contentView = contentViewTemplate.cloneNode(true);
        contentView.removeAttribute("id");
        contentView.classList.add("content-view");

        const locationType = data_representation["location_type"];
        const themeType = data_representation["theme_type"];
        const timeType = data_representation["time_type"];

        // set all data-attributes
        contentView.dataset.location = locationType;
        contentView.dataset.theme = themeType;
        contentView.dataset.time = timeType;
        contentView.dataset.order = user_data_representation["order"];
        contentView.dataset.id = user_data_representation["id"];

        const timeInputDiv = contentView.querySelector(".time-input-div");

        // build the timeInputDiv based on the timeType
        if (timeType == "T") {
            const timeInputSpan = timeInputSpanTemplate.cloneNode(true);

            timeInputSpan.querySelector(".time-input").value = user_data_representation["time"];
            timeInputDiv.appendChild(timeInputSpan);
        } else if (timeType == "P") {
            const fromInputSpan = fromInputSpanTemplate.cloneNode(true);
            fromInputSpan.querySelector(".from-input").value = user_data_representation["time"];
            timeInputDiv.appendChild(fromInputSpan);

            const toInputSpan = toInputSpanTemplate.cloneNode(true);
            toInputSpan.querySelector(".to-input").value = user_data_representation["end_time"];
            timeInputDiv.appendChild(toInputSpan);
        }
        if (locationType != "H") {
            const locationSelect = locationSelectTemplate.cloneNode(true);
            this.fillLocationSelect(locations, locationSelect, locationType, user_data_representation);

            contentView.querySelector(".location-input-div").appendChild(locationSelect);
        }

        // add the new html-ContentView to the parent html-element of the html-ContentViews
        ContentView.parent.appendChild(contentView);

        contentView.scrollIntoView();

        return contentView;
    }

    /**
     * Method for filling the given locationSelect with the given locations.
     * @param locations
     * @param locationSelect
     * @param locationType
     * @param user_data_representation
     */
    fillLocationSelect(locations, locationSelect, locationType, user_data_representation) {
        // create a new option for every location and add it to the locationSelect
        locations.forEach((location) => {
            const newOption = document.createElement("option");
            const locationId = location["id"];
            newOption.value = locationId;
            newOption.innerText = location["name"];

            locationSelect.appendChild(newOption);

            // set the current selected location from the UserDataRepresentation if the locationType has the right value
            if (locationType == "W" && locationId == user_data_representation["ward"] || locationType == "R" && locationId == user_data_representation["room"]) {
                locationSelect.value = locationId;
            }
        });
    }

    /**
     * Method for handling the start of the drag process.
     * @param contentView
     */
    ondDragStart(contentView) {
        // set the ContentView as the new draggedContentView
        this.#draggedContentView = contentView;
    }

    /**
     * Method for handling the entering of another ContentView while the drag process.
     * @param contentView
     */
    onDragEnter(contentView) {
        // only chang the ContentViews order if the entered ContentView ist not the dragged one
        if (contentView != this.#draggedContentView) {
            // delete the content view from the array
            this.#contentViews.splice(this.#draggedContentView.order, 1)

            // change the position of the ContentViews to get the right drag and drop behavior
            if (this.#draggedContentView.order < contentView.order) {
                // add content view to the right place
                this.#parent.insertBefore(this.#draggedContentView.contentView, contentView.contentView.nextElementSibling);
                this.#contentViews.splice(contentView.order, 0, this.#draggedContentView);
            } else {
                // add content view to the left place
                this.#parent.insertBefore(this.#draggedContentView.contentView, contentView.contentView);
                this.#contentViews.splice(contentView.order, 0, this.#draggedContentView);
            }

            // reset the order of all ContentViews
            this.resetOrder();
        }
    }

    /**
     * Method for resetting the order of all ContentViews in the contentViews attribute.
     */
    resetOrder() {
        this.#contentViews.forEach((contentView, index) => {
            contentView.contentView.dataset.order = index;
            contentView.order = index;
        });
    }

    /**
     * Method for updating of all ContentViews in the contentViews attribute at the server.
     */
    updateOrder() {
        // convert the contentViews in a list of dicts with the id and the order of the DataRepresentation
        let orderIdDictList = [];
        this.#contentViews.forEach((contentView) => {
            orderIdDictList.push({
                id: contentView.userDataRepresentationId,
                order: contentView.order
            })
        });

        updateUserDataRepresentationOrder(orderIdDictList);
    }

    /**
     * Method for removing the given ContentView
     * @param contentView
     */
    removeContentView(contentView) {
        this.#contentViews.splice(this.#contentViews.indexOf(contentView), 1);
        this.resetOrder();
        contentView.contentView.remove();
        this.updateOrder();

    }

    /**
     * Method for setting the color of the given html-sexRectangle and the text of the given html-sexSpan
     * based on the given locationData and its numbers of sexes.
     * @param locationData
     * @param sexRectangle
     * @param sexSpan
     */
    setRectangleClassAndTextForSex(locationData, sexRectangle, sexSpan) {
        sexRectangle.classList.remove("male-rectangle", "female-rectangle", "diverse-rectangle", "empty-rectangle");
        if (locationData.number_of_men > 0) {
            sexRectangle.classList.add("male-rectangle");
            sexSpan.innerText = "Männlich";
        } else if (locationData.number_of_women > 0) {
            sexRectangle.classList.add("female-rectangle");
            sexSpan.innerText = "Weiblich";
        } else if (locationData.number_of_diverse > 0) {
            sexRectangle.classList.add("diverse-rectangle");
            sexSpan.innerText = "Divers";
        } else {
            sexRectangle.classList.add("empty-rectangle");
            sexSpan.innerText = "Leer";
        }
    }

    /**
     * Method for clearing the given select adding an empty select and making it disabled.
     * @param select
     */
    addEmptyOptionToSelect(select) {
        const newOption = document.createElement("option");
        newOption.innerText = "-- leer --";
        newOption.value = -1;
        newOption.selected = true;
        newOption.disabled = true;

        select.appendChild(newOption);
    }
}

/**
 * Base class for the ContentViews.
 * Represents a html-ContentView in the Code.
 */
class ContentView {
    static parent = document.querySelector("#content-div");
    #contentViewManager;
    #order;
    #contentView;
    #contentDataDiv;
    #locationType;
    #themeType;
    #timeType;
    #userDataRepresentationId;
    #interval = null;

    constructor(contentView, contentViewManager) {
        // initialize all attributes
        this.#contentViewManager = contentViewManager;
        this.#contentView = contentView;
        this.#contentDataDiv = contentView.querySelector(".content-view-data-div");
        this.#order = parseInt(contentView.dataset.order);
        this.#locationType = contentView.dataset.location;
        this.#themeType = contentView.dataset.theme;
        this.#timeType = contentView.dataset.time;
        this.#userDataRepresentationId = contentView.dataset.id;

        // buidl all parts of the html-ContentView
        this.buildContentViewDataDiv();
        this.#setContentViewHeading();
        this.#addEventListeners();

        // fill the ContentView with data
        this.fetchDataForContentView();

        // setting an interval for a neartime reset the data of the ContentView every 5 minutes
        if (this.#timeType == "N") {
            this.#interval = setInterval(this.fetchDataForContentView.bind(this), 300000);
        }
    }

    /**
     * Abstract template method.
     */
    buildContentViewDataDiv() {
        throw new Error("Not defined.")
    }

    /**
     * Method for building the html-heading of the html-ContentView.
     */
    #setContentViewHeading() {
        //add the heading
        const contentViewHeading = this.#contentView.querySelector(".content-view-heading");
        let headingText = "";
        switch (this.#themeType) {
            case "I":
                headingText = "Informationen";
                break
            case "W":
                headingText = "Stationen";
                break
            case "R":
                headingText = "Zimmer";
                break
            case "B":
                headingText = "Betten";
                break
            case "H":
                headingText = "Auslastungsverlauf";
                break
        }

        switch (this.#locationType) {
            case "W":
                headingText += " der Station";
                break
            case "R":
                headingText += " des Zimmers";
                break
            case "H":
                headingText += " des Krankenhauses";
                break
        }
        contentViewHeading.innerText = headingText;
    }

    /**
     * Method for adding all important event listeners to the html-elements.
     */
    #addEventListeners() {
        // drag and drop event listeners
        this.#contentView.addEventListener('dragstart', this.onDragStart.bind(this));
        this.#contentView.addEventListener("dragenter", this.onDragEnter.bind(this));
        this.#contentView.addEventListener("drop", this.onDrop.bind(this));
        this.#contentView.addEventListener("dragover", (event) => event.preventDefault());

        // deletion event listener
        this.#contentView.querySelector(".delete-image").addEventListener("click", this.onDeletionOfContentView.bind(this));

        // download event listener
        this.#contentView.querySelector(".download-image").addEventListener("click", this.onDownloadDataForView.bind(this));

        // add the event listeners for the input change to all important inputs
        let inputElements = this.#contentView.querySelectorAll(".selection-input, .from-input, .to-input, .time-input");
        if (inputElements) {
            for (const inputElement of inputElements) {
                inputElement.addEventListener("change", this.onInputChange.bind(this));
            }
        }

    }

    /**
     * Method for fetching data from the server and filling the ContentView.
     * @param updateInputs
     */
    fetchDataForContentView(updateInputs = false) {
        const loader = this.#contentView.querySelector(".loader");

        const dataHolder = this.#contentView.querySelector(".data-holder");
        if (dataHolder) {
            dataHolder.hidden = true;
        } else {
            const locationListDiv = this.#contentView.querySelector(".location-list-div");
            const locationDivs = locationListDiv.querySelectorAll(".location-div");
            locationDivs.forEach(locationDiv => {
                locationListDiv.removeChild(locationDiv);
            });
        }

        loader.hidden = false;


        // create the right url
        let url = this.#createUrl(updateInputs, false);

        // fetch data from server
        fetch(url.toString(), {
            method: "GET",
            headers: {
                "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
            },
        }).then((response) => {
            if (response.ok) {
                return response.json();
            }
            throw new Error(`Request failed with statuscode ${response.status}.`);
        }).then(data => {
            // reset the locationSelect of the ContentView
            if (this.#locationType != "H") {
                const locations = data.locations;
                const user_data_representation = data.user_data_representation;
                const locationSelect = this.#contentView.querySelector(".selection-input");

                //delete all old options
                while (locationSelect.options.length > 0) {
                    locationSelect.remove(0);
                }
                // fill the select with the locations
                if (locations != null && locations.length != 0) {
                    this.#contentViewManager.fillLocationSelect(locations, locationSelect, this.#locationType, user_data_representation)
                } else {

                    this.contentViewManager.addEmptyOptionToSelect(locationSelect);
                }
            }

            // fill the html-ContentView with the resulting data
            this.fillContentViewDataDivWithData(data);

            loader.hidden = true;
        }).catch((error) => console.log(error));

    }

    /**
     * Abstract template method for filling the ContentView with the given data.
     * @param data
     */
    fillContentViewDataDivWithData(data) {
        throw Error("Not defined.");
    }

    /**
     * Method for handeling the input change.
     */
    onInputChange() {
        // call the method for fetching the data
        this.fetchDataForContentView(true);
    }

    /**
     * Method for handling the start of drag process.
     */
    onDragStart() {
        this.#contentViewManager.ondDragStart(this);
    }

    /**
     * Method for handling the entering of another ContentView while the drag process.
     */
    onDragEnter() {
        this.#contentViewManager.onDragEnter(this);
    }

    /**
     * Method for handling the drop of a ContentView while the drag process.
     */
    onDrop() {
        // update the order of all ContentViews
        this.#contentViewManager.updateOrder();
    }

    /**
     * Method for deleting a ContentView.
     */
    onDeletionOfContentView() {
        if (confirm("Sind sie sicher, dass sie diese Datenrepräsentation löschen wollen?")) {
            deleteUserDataRepresentation(this.userDataRepresentationId, () => {
                // clear the intervall if the ContentView was a neartime ContentView.
                if (this.#interval) {
                    clearInterval(this.#interval);
                }

                // remove the ContentView also on the managers side.
                this.#contentViewManager.removeContentView(this);
            });
        }
    }

    /**
     * Method for downloading the data in csv format.
     */
    onDownloadDataForView() {
        // redirect to the download-url of csv data
        let url = this.#createUrl(false, true);
        window.open(url, "_blank");
    }

    /**
     * Method for creating the right url for the ContentView.
     * @param updateInputs
     * @param downloadCSV
     * @returns URL
     */
    #createUrl(updateInputs, downloadCSV) {
        let url = new URL(location.protocol + "//" + location.host + "/get_data" + "/" + this.#locationType + "/" + this.#themeType + "/" + this.#timeType + "/");

        url.searchParams.append("id", this.#userDataRepresentationId);

        url.searchParams.append("update_flag", updateInputs.toString());

        url.searchParams.append("download", downloadCSV.toString());

        //add the id param, if it's a list of occupancies
        if (this.#locationType != "H") {
            let selectionElement = this.#contentView.querySelector(".selection-input");//TODO add to class
            const location_id = selectionElement.value
            url.searchParams.append("location_id", location_id);
        }

        //add the time params, if its a time type
        if (this.#timeType == "T") {
            const timeElement = this.#contentView.querySelector(".time-input");//TODO add to class
            const time = timeElement.value;
            if (!time) {
                throw new Error("There is no given time.");
            }
            url.searchParams.append("time", time);
        } else if (this.#timeType == "P") {
            const fromTimeElement = this.#contentView.querySelector(".from-input");//TODO add to class
            const fromTime = fromTimeElement.value;
            const toTimeElement = this.#contentView.querySelector(".to-input");
            const toTime = toTimeElement.value;
            if (!toTime || !fromTime) {
                throw new Error("There is no given time for from or to.");
            }
            url.searchParams.append("time", fromTime);
            url.searchParams.append("end_time", toTime);
        }
        return url;
    }

    // Setters and Getters
    get contentView() {
        return this.#contentView;
    }

    get order() {
        return this.#order;
    }

    set order(order) {//TODO add handeling for wrong id
        this.#order = order;
    }

    get locationType() {
        return this.#locationType;
    }

    get themeType() {
        return this.#themeType;
    }

    get timeType() {
        return this.#timeType;
    };

    get userDataRepresentationId() {
        return this.#userDataRepresentationId;
    }

    get contentDataDiv() {
        return this.#contentDataDiv;
    }

    get contentViewManager() {
        return this.#contentViewManager;
    }
}

/**
 * Class for the ContentViews with room-information.
 */
class RoomInformationContentView extends ContentView {
    buildContentViewDataDiv() {
        this.contentDataDiv.appendChild(loaderTemplate.cloneNode(true));
        this.contentDataDiv.appendChild(roomDataDiv.cloneNode(true));
    }

    fillContentViewDataDivWithData(data) {
        const dataDiv = this.contentView.querySelector(".content-view-data-div");//TODO add to class
        const roomDataDiv = dataDiv.querySelector(".room-data-div");
        const ageH4 = roomDataDiv.querySelector(".room-age-h4");
        const sexRectangle = roomDataDiv.querySelector(".sex-rectangle-span");
        const sexSpan = roomDataDiv.querySelector(".sex-span");
        const occupancyH4 = roomDataDiv.querySelector(".room-occupancy-h4");
        const freeBedsH4 = roomDataDiv.querySelector(".room-free-beds-h4");

        const roomData = data["data"];
        if (roomData.length == 0) {
            roomDataDiv.hidden = true;
            roomDataDiv.style.display = 'none';
        } else {
            const singleRoomData = roomData[0];

            this.contentViewManager.setRectangleClassAndTextForSex(singleRoomData, sexRectangle, sexSpan);

            ageH4.innerText = (singleRoomData.average_age) ? singleRoomData.average_age : "/";
            occupancyH4.innerText = percentage(singleRoomData.number, singleRoomData.max_number) + "%";
            freeBedsH4.innerText = `${singleRoomData.max_number - singleRoomData.number} von ${singleRoomData.max_number}`;

            roomDataDiv.hidden = false;
            roomDataDiv.style.display = 'flex';
        }
    }
}

/**
 * Class for the ContentViews with single-location-information.
 */
class LocationInformationContentView extends ContentView {
    buildContentViewDataDiv() {
        this.contentDataDiv.appendChild(loaderTemplate.cloneNode(true));
        this.contentDataDiv.appendChild(occupancyChartCanvasTemplate.cloneNode(true));
    }

    fillContentViewDataDivWithData(data) {
        const dataDiv = this.contentView.querySelector(".content-view-data-div");//TODO add to class
        const locationData = data["data"];
        const canvas = dataDiv.querySelector(".information-chart-canvas");

        if (locationData.length == 0) {
            canvas.hidden = true;
            canvas.style.display = 'none';
        } else {
            const singleLocationData = (this.locationType == "H") ? locationData : locationData[0];

            const chart = this.#getOrCreateInformationChart(canvas);

            chart.data.datasets[0].data = [
                singleLocationData.number_of_men,
                singleLocationData.number_of_women,
                singleLocationData.number_of_diverse,
                singleLocationData.max_number - singleLocationData.number
            ];
            chart.data.datasets[1].data = [
                singleLocationData.number,
                singleLocationData.max_number,
                percentage(singleLocationData.number, singleLocationData.max_number),
            ];
            canvas.hidden = false;
            canvas.style.display = 'block';

            chart.update();
        }
    }

    /**
     * Method for creating or getting the current chart for the data.
     * @param canvas
     * @returns Chart
     */
    #getOrCreateInformationChart(canvas) {
        let chart = Chart.getChart(canvas);
        if (!chart) {
            chart = new Chart(canvas, {
                type: 'doughnut',
                data: {
                    labels: ["Männlich", "Weiblich", "Divers", "Leer"],
                    datasets: [
                        {
                            data: [0, 0, 0, 0],
                            backgroundColor: ["#41cff6", "#d341f6", "#f6a541", "#41f67c"],
                        },
                        {
                            data: [0, 0, 0],
                            hidden: true
                        }
                    ]
                },
                plugins: [{
                    id: 'text_in_doughnut_chart',
                    beforeDraw: (chart, args, options) => {
                        const height = canvas.getBoundingClientRect().height
                        const x = chart.getDatasetMeta(0).data[0].x;
                        const y = chart.getDatasetMeta(0).data[0].y;
                        const data = chart.data.datasets[1].data;

                        const {ctx} = chart;
                        ctx.save();
                        ctx.fillStyle = "#000000";
                        ctx.font = `${1.2 * height / 290}em Arial`;
                        ctx.textAlign = "center";
                        ctx.textBaseline = "bottom"
                        ctx.fillText(`${data[0]} / ${data[1]}`, x, y);
                        ctx.textBaseline = "top";
                        let occupancy = data[2];
                        if (!occupancy) {
                            occupancy = 0;
                        }
                        ctx.fillText(`${occupancy}%`, x, y);
                        ctx.restore();
                    },
                    defaults: {
                        color: 'lightGreen'
                    }
                }],
                options: {
                    cutout: "60%",
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'right',
                        }
                    },
                }
            });
        }

        return chart;
    }
}

/**
 * Class for the ContentViews with single-location-history.
 */
class LocationHistoryContentView extends ContentView {
    buildContentViewDataDiv() {
        this.contentDataDiv.appendChild(loaderTemplate.cloneNode(true));
        this.contentDataDiv.appendChild(occupancyHistoryChartCanvasTemplate.cloneNode(true));
    }

    fillContentViewDataDivWithData(data) {
        const dataDiv = this.contentView.querySelector(".content-view-data-div");//TODO add to class
        const locationHistoryData = data["data"];
        const canvas = dataDiv.querySelector(".occupancy-history-chart-canvas");

        if (!("locations" in data) && this.locationType != "H") {//TODO= better handling
            //TODO show error!
            canvas.hidden = true;
            canvas.style.display = 'none';
        } else {
            const chart = this.#getOrCreateHistoryChart(canvas);
            const labels = []
            const data = []
            for (let key in locationHistoryData) {
                let value = locationHistoryData[key];
                if (this.locationType != "H") {
                    value = value[0];
                }

                const exec_date = DATETIME_REGEX.exec(key);
                const datetime = new Date(exec_date[1], exec_date[2], exec_date[3], exec_date[4], exec_date[5]);
                labels.push(`${datetime.getDate()}.${datetime.getMonth()}.${datetime.getFullYear()} ${datetime.getHours()}:${datetime.getMinutes()}`);
                let occupancy = (value) ? percentage(value.number, value.max_number) : null;

                data.push(occupancy);

            }
            chart.data.labels = labels;
            chart.data.datasets[0].data = data;
            canvas.hidden = false;
            canvas.style.display = 'block';

            chart.update();
        }
    }

    /**
     * Method for creating or getting the current chart for the data.
     * @param canvas
     * @returns Chart
     */
    #getOrCreateHistoryChart(canvas) {
        let chart = Chart.getChart(canvas);
        if (!chart) {
            chart = new Chart(canvas, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: "Auslastung",
                        data: [],
                        fill: false,
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            display: false,
                        }
                    },
                    scales: {
                        y: {
                            text: "%",
                            max: 100,   // Set the maximum value for the y-axis,
                            min: 0
                        },
                    }
                }
            });
        }
        return chart;
    }
}

/**
 * Class for the ContentViews with multiple-beds-information.
 */
class BedsInformationContentView extends ContentView {
    buildContentViewDataDiv() {
        this.contentDataDiv.appendChild(bedListHeadDivTemplate.cloneNode(true));
        const bedListDiv = locationListDivTemplate.cloneNode(true);
        bedListDiv.appendChild(loaderTemplate.cloneNode(true));
        this.contentDataDiv.appendChild(bedListDiv);
    }

    fillContentViewDataDivWithData(data) {
        const dataDiv = this.contentView.querySelector(".content-view-data-div");//TODO add to class
        const bedsData = data["data"];
        const bedListDiv = dataDiv.querySelector(".location-list-div");
        bedsData.forEach(bedData => {
            const newBedDiv = bedDivTemplate.cloneNode(true);
            const nameSpan = newBedDiv.querySelector(".bed-name-span");
            const ageSpan = newBedDiv.querySelector(".bed-age-span");
            const sexSpan = newBedDiv.querySelector(".bed-sex-span");
            const sexRectangle = newBedDiv.querySelector(".sex-rectangle");
            this.contentViewManager.setRectangleClassAndTextForSex(bedData, sexRectangle, sexSpan);
            nameSpan.innerText = bedData.name;
            ageSpan.innerText = bedData.average_age;

            bedListDiv.appendChild(newBedDiv);
        }, this);
    }
}

/**
 * Class for the ContentViews with multiple-locations-information.
 */
class LocationsInformationContentView extends ContentView {
    buildContentViewDataDiv() {
        const locationListHeadDiv = locationListHeadDivTemplate.cloneNode(true);
        const locationNameHead = locationListHeadDiv.querySelector(".location-name-head");
        if (this.themeType == "W") {
            locationNameHead.innerText = "Station";
        } else if (this.themeType == "R") {
            locationNameHead.innerText = "Zimmer";
        }

        this.contentDataDiv.appendChild(locationListHeadDiv);
        const locationListDiv = locationListDivTemplate.cloneNode(true)
        locationListDiv.appendChild(loaderTemplate.cloneNode(true));
        this.contentDataDiv.appendChild(locationListDiv);
    }

    fillContentViewDataDivWithData(data) {
        const dataDiv = this.contentView.querySelector(".content-view-data-div");//TODO add to class
        const locationsData = data["data"];
        const locationListDiv = dataDiv.querySelector(".location-list-div");

        locationsData.forEach(locationData => {
            const newLocationDiv = locationDivTemplate.cloneNode(true);
            const nameSpan = newLocationDiv.querySelector(".location-name-span");
            const occupancySpan = newLocationDiv.querySelector(".location-occupancy-span");
            const chartCanvas = newLocationDiv.querySelector(".location-occupancy-chart-canvas");

            nameSpan.innerText = locationData.name;
            occupancySpan.innerText = percentage(locationData.number, locationData.max_number) + "%";

            new Chart(chartCanvas, {
                type: 'bar',
                data: {
                    labels: [locationData.name],
                    datasets: [{
                        label: "belegt",
                        data: [locationData.number],
                        backgroundColor: "#f64141"
                    }, {
                        label: "leer",
                        data: [locationData.max_number - locationData.number],
                        backgroundColor: "#41f67c",
                    },]
                },
                options: {
                    events: [],
                    plugins: {
                        legend: {
                            display: false,
                        }
                    },
                    indexAxis: 'y',
                    interaction: {
                        intersect: false,
                    },
                    scales: {
                        x: {
                            stacked: true,
                            display: false
                        },
                        y: {
                            stacked: true,
                            display: false
                        },
                    }
                }
            });

            locationListDiv.appendChild(newLocationDiv);
        });
    }
}

// listener for the load event of the window
// important to initialize everything
window.addEventListener("load", () => {
    // create a new ContentViewManager
    const contentViewManager = new ContentViewManager();

    // get all initial html-ContentViews and create the code ContentView representation
    const contentViews = document.querySelectorAll('.content-view');
    contentViews.forEach((contentView) => {
        contentViewManager.createContentView(contentView);
    });

    // Add the click event to all the elements for creating a new ContentView
    const newViewSelects = document.querySelectorAll(".selection.time");
    if (newViewSelects) {
        newViewSelects.forEach((newViewSelect) => {
            newViewSelect.addEventListener("click", (event) => {
                const element = event.target;
                const locationType = element.dataset.location;
                const themeType = element.dataset.theme;
                const timeType = element.dataset.time;
                contentViewManager.createNewContentView(locationType, themeType, timeType);
            });
        });
    }
});






