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

class ContentView {
    static dragData = document.querySelector("#drag-data");
    static parent = document.querySelector("#content-div");
    static contentViews = [];
    #order;
    #contentView;
    #locationType;
    #themeType;
    #timeType;
    #userDataRepresentationId;

    static createContentViewFromElement(contentView) {
        new ContentView(contentView);
    }

    static createNewContentViewFromEvent(event) {
        const element = event.target;
        const locationType = element.dataset.location;
        const themeType = element.dataset.theme;
        const timeType = element.dataset.time;

        fetch("/create/user-data_representation", {
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
            throw new Error("Request fehlgeschlagen.");
        }).then(data => {
            const locations = "locations" in data ? data["locations"] : null;
            const user_data_representation = data["user_data_representation"];
            const data_representation = data["data_representation"];
            new ContentView(this.#createNewContentViewElement(data_representation, user_data_representation, locations));

        }).catch((error) => console.log(error));
    }

    static #createNewContentViewElement(data_representation, user_data_representation, locations) {
        const contentView = contentViewTemplate.cloneNode(true);
        contentView.removeAttribute("id");
        contentView.classList.add("content-view");

        const locationType = data_representation["location_type"];
        const themeType = data_representation["theme_type"];
        const timeType = data_representation["time_type"];

        //set all data-attributes
        contentView.dataset.location = locationType;
        contentView.dataset.theme = themeType;
        contentView.dataset.time = timeType;
        contentView.dataset.order = user_data_representation["order"];
        contentView.dataset.id = user_data_representation["id"];

        const timeInputDiv = contentView.querySelector(".time-input-div");
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
            this.#fillLocationSelect(locations, locationSelect, locationType, user_data_representation);

            contentView.querySelector(".location-input-div").appendChild(locationSelect);
        }

        document.querySelector("#content-div").appendChild(contentView);
        contentView.scrollIntoView();
        return contentView;
    }

    static removeContentView(contentView){
        this.contentViews.splice(this.contentViews.indexOf(contentView),1);
    }

    static #fillLocationSelect(locations, locationSelect, locationType, user_data_representation) {
        if (locations != null && locations.length != 0) {
            locations.forEach((location) => {
                const newOption = document.createElement("option");
                const locationId = location["id"];
                newOption.value = locationId;
                newOption.innerText = location["name"];

                locationSelect.appendChild(newOption);

                if (locationType == "W" && locationId == user_data_representation["ward"] || locationType == "R" && locationId == user_data_representation["room"]) {
                    locationSelect.value = locationId;
                }
            });
        } else {
            addEmptyOptionToSelect(locationSelect);
        }
    }

    static resetOrderForContentViews() {//Todo reset order of list
        this.contentViews.forEach((contentView, index) => {
            contentView.contentView.dataset.order = index;
            contentView.order = index;
        });
    }

    static updateOrderOfContentViews() {
        let orderIdDictList = [];
        ContentView.contentViews.forEach((contentView) => {
            orderIdDictList.push({
                id: contentView.userDataRepresentationId,
                order: contentView.order
            })
        });

        fetch("/update/order", {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfMiddlewareToken.value
            },
            body: JSON.stringify(orderIdDictList)
        }).then((response) => {
            if (response.ok) {
                return response.text();
            }
            throw new Error("Request failed.");
        }).catch((error) => console.log(error));
    }

    static insort(contentView) {
        let found = false;
        for (let i = 0; i < ContentView.contentViews.length; i++) {
            if (contentView.order < ContentView.contentViews[i].order) {
                ContentView.contentViews.splice(i, 0, this);
                found = true;
                break;
            }
        }
        if (!found) {
            ContentView.contentViews.push(contentView);
        }
    }

    constructor(contentView) {
        this.#contentView = contentView;
        this.#order = parseInt(contentView.dataset.order);
        this.#locationType = contentView.dataset.location;
        this.#themeType = contentView.dataset.theme;
        this.#timeType = contentView.dataset.time;
        this.#userDataRepresentationId = contentView.dataset.id;
        this.#buildContentViewDataDiv();
        this.#setContentViewHeading();
        this.#addEventListeners();
        const locationSelect = this.#contentView.querySelector(".selection-input");//TODO add to class
        if (locationSelect != null && locationSelect.querySelectorAll("option").length == 0) {
            this.#addEmptyOptionToSelect(locationSelect);//TODO add error message
        }
        //this.#fetchDataForContentViewDataDiv();

        ContentView.insort(this);
    }

    #buildContentViewDataDiv() {
        const contentDataDiv = this.#contentView.querySelector(".content-view-data-div");// TODO add to class

        if (this.#themeType == "I") {
            contentDataDiv.appendChild(loaderTemplate.cloneNode(true));
            if (this.#locationType == "R") {
                contentDataDiv.appendChild(roomDataDiv.cloneNode(true));
            } else {
                contentDataDiv.appendChild(occupancyChartCanvasTemplate.cloneNode(true));
            }
        } else if (this.#themeType == "H") {
            contentDataDiv.appendChild(loaderTemplate.cloneNode(true));
            contentDataDiv.appendChild(occupancyHistoryChartCanvasTemplate.cloneNode(true));
        } else if (this.#themeType == "B") {
            contentDataDiv.appendChild(bedListHeadDivTemplate.cloneNode(true));
            const bedListDiv = locationListDivTemplate.cloneNode(true);
            bedListDiv.appendChild(loaderTemplate.cloneNode(true));
            contentDataDiv.appendChild(bedListDiv);
        } else {
            const locationListHeadDiv = locationListHeadDivTemplate.cloneNode(true);
            const locationNameHead = locationListHeadDiv.querySelector(".location-name-head");
            if (this.#themeType == "W") {
                locationNameHead.innerText = "Station";
            } else if (this.#themeType == "R") {
                locationNameHead.innerText = "Zimmer";
            }

            contentDataDiv.appendChild(locationListHeadDiv);
            const locationListDiv = locationListDivTemplate.cloneNode(true)
            locationListDiv.appendChild(loaderTemplate.cloneNode(true));
            contentDataDiv.appendChild(locationListDiv);
        }
    }

    #setContentViewHeading() {

        //add the heading
        const contentViewHeading = this.#contentView.querySelector(".content-view-heading");//TODO add to class
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

    #addEventListeners() {
        this.#contentView.addEventListener('dragstart', this.onDragStart.bind(this));
        this.#contentView.addEventListener("dragend", this.onDragEnd.bind(this));
        this.#contentView.addEventListener("dragenter", this.onDragEnter.bind(this));
        this.#contentView.addEventListener("drop", ContentView.updateOrderOfContentViews);
        this.#contentView.addEventListener("dragover", this.onDragOver.bind(this))

        this.#contentView.querySelector(".delete-image").addEventListener("click", this.onDeletionOfView.bind(this));
        this.#contentView.querySelector(".download-image").addEventListener("click", this.onDownloadDataForView.bind(this));
        const inputElements = this.#contentView.querySelectorAll(".selection-input, .from-input, .to-input, .time-input");//TODO add to class4
        if (inputElements) {
            inputElements.forEach((inputElement) => {
                addEventListener("change", this.onInputChange.bind(this));
            });
        }

    }

    // checks if select is empty and adds error option if this is true
    #addEmptyOptionToSelect(select) {// TODO add error message
        const newOption = document.createElement("option");
        newOption.innerText = "-- leer --";
        newOption.value = -1;
        newOption.selected = true;
        newOption.disabled = true;

        select.appendChild(newOption);
    }

    #fetchDataForContentViewDataDiv(updateInputs = false) {
        fetchDataForContentViewDataDiv(this.#contentView ,updateInputs);
    }

    onInputChange(){
        this.#fetchDataForContentViewDataDiv(true);
    }
    onDragEnd(event) {
        event.target.classList.remove("dragged-content-view");
    }

    onDragOver(event) {
        event.preventDefault();
    }

    onDragStart() {
        ContentView.dragData.value = this.#order;
        this.#contentView.classList.add("dragged-content-view");
    }

    onDragEnter() {
        const startOrder = parseInt(ContentView.dragData.value);
        const startContentView = ContentView.contentViews[startOrder];
        if (this.#contentView != startContentView.contentView) {
            // delete the content view from the array
            ContentView.contentViews.splice(this.#order, this.#order);
            if (startOrder < this.#order) {
                ContentView.parent.insertBefore(startContentView.contentView, this.#contentView.nextElementSibling);
                // add content view to the right place
                ContentView.contentViews.splice(startOrder + 1, 0, this);
            } else {
                ContentView.parent.insertBefore(startContentView.contentView, this.#contentView);
                // add content view to the right place
                ContentView.contentViews.splice(startOrder - 1, 0, this);
            }

            //Change ordering
            ContentView.resetOrderForContentViews();

            ContentView.dragData.value = startContentView.order;
        }
    }

    onDeletionOfView() {
        if (confirm("Sind sie sicher, dass sie diese Datenrepräsentation löschen wollen?")) {
            fetch("/delete/user-data-representation", {
                method: "DELETE",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfMiddlewareToken.value
                },
                body: JSON.stringify({
                    id: this.userDataRepresentationId
                })
            }).then((response) => {
                if (response.ok) {
                    return response.text();
                }
                throw new Error("Request fehlgeschlagen.");
            }).catch((error) => console.log(error));
        }

        ContentView.removeContentView(this);

        //delete contentView
        this.#contentView.remove();

        ContentView.resetOrderForContentViews();
        ContentView.updateOrderOfContentViews();
    }

    // redirect to the download of csv data
    onDownloadDataForView() {

        let url = this.#createUrl(false, true);
        window.open(url, "_blank");
    }

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
}


window.addEventListener("load", () => {
    const newViewSelects = document.querySelectorAll(".selection.time");
    if (newViewSelects) {
        newViewSelects.forEach((newViewSelect) => {
            newViewSelect.addEventListener("click", ContentView.createNewContentViewFromEvent);//onNewViewSelection);
        });
    }

    const contentViews = document.querySelectorAll('.content-view');
    contentViews.forEach((contentView) => {
        ContentView.createContentViewFromElement(contentView)
    });
});

//deletion of a data representation


function fillLocationSelect(locations, locationSelect, locationType, user_data_representation) {
    if (locations != null && locations.length != 0) {
        locations.forEach((location) => {
            const newOption = document.createElement("option");
            const locationId = location["id"];
            newOption.value = locationId;
            newOption.innerText = location["name"];

            locationSelect.appendChild(newOption);

            if (locationType == "W" && locationId == user_data_representation["ward"] || locationType == "R" && locationId == user_data_representation["room"]) {
                locationSelect.value = locationId;
            }
        });
    } else {
        addEmptyOptionToSelect(locationSelect);
    }
}

//fills the content view with the right data
function fetchDataForContentViewDataDiv(contentView, updateInputs = false) {
    const locationType = contentView.dataset.location;// TODO change inconsistent format
    const themeType = contentView.dataset.theme;
    const timeType = contentView.dataset.time;

    const loader = contentView.querySelector(".loader");
    const dataHolder = contentView.querySelector(".data-holder");
    if (dataHolder) {
        dataHolder.hidden = true;
    } else {
        const locationListDiv = contentView.querySelector(".location-list-div");
        const locationDivs = locationListDiv.querySelectorAll(".location-div");
        locationDivs.forEach(locationDiv => {
            locationListDiv.removeChild(locationDiv);
        });
    }
    loader.hidden = false;


    // create the right url
    let url = ContentView.createUrl(locationType, themeType, timeType, contentView, updateInputs, false);

    fetch(url.toString(), {
        method: "GET",
        headers: {
            "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
        },
    }).then((response) => {
        if (response.ok) {
            return response.json();
        }
        throw new Error("Request failed.");
    }).then(data => {
        if (updateInputs) {
            const locations = data.locations;
            const user_data_representation = data.user_data_representation;
            const locationSelect = contentView.querySelector(".selection-input");

            if (locationType != "H") {
                //delete all old options
                while (locationSelect.options.length > 0) {
                    locationSelect.remove(0);
                }
                fillLocationSelect(locations, locationSelect, locationType, user_data_representation);
            }

        }

        fillContentViewDataDivWithData(contentView, data, locationType, themeType);
    }).catch((error) => console.log(error));
}

function fillContentViewDataDivWithData(contentView, data, locationType, themeType) {
    const dataDiv = contentView.querySelector(".content-view-data-div");
    const loader = dataDiv.querySelector(".loader");

    if (themeType == "I") {
        if (locationType == "R") {
            fillRoomInformationDataDiv(dataDiv, data);
        } else {
            fillLocationInformationDataDiv(dataDiv, data, locationType);
        }
    } else if (themeType == "H") {
        fillLocationHistoryDataDiv(dataDiv, data, locationType);
    } else if (themeType == "B") {
        fillBedsInformationDataDiv(dataDiv, data);
    } else {
        fillLocationsInformationDataDiv(dataDiv, data);
    }

    loader.hidden = true;


}

function setClassForSexRectangle(locationData, sexRectangle, sexSpan) {
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
        sexRectangle.classList.add("empty-rectangle");//TODO add empty view!
        sexSpan.innerText = "Leer";
    }
}

function fillRoomInformationDataDiv(dataDiv, data) {
    const roomDataDiv = dataDiv.querySelector(".room-data-div");
    const ageH4 = roomDataDiv.querySelector(".room-age-h4");
    const sexRectangle = roomDataDiv.querySelector(".sex-rectangle-span");
    const sexSpan = roomDataDiv.querySelector(".sex-span");
    const occupancyH4 = roomDataDiv.querySelector(".room-occupancy-h4");
    const freeBedsH4 = roomDataDiv.querySelector(".room-free-beds-h4");

    const roomData = data["data"];
    if (roomData.length == 0) {
        //TODO show error!
        console.log("ja");
        roomDataDiv.hidden = true;
        roomDataDiv.style.display = 'none';
    } else {
        const singleRoomData = roomData[0];

        setClassForSexRectangle(singleRoomData, sexRectangle, sexSpan);

        ageH4.innerText = singleRoomData.average_age;
        occupancyH4.innerText = singleRoomData.occupancy + "%";
        freeBedsH4.innerText = singleRoomData.max_number - singleRoomData.number;

        roomDataDiv.hidden = false;
        roomDataDiv.style.display = 'flex';
    }
}

function fillLocationInformationDataDiv(dataDiv, data, locationType) {
    const locationData = data["data"];
    const canvas = dataDiv.querySelector(".information-chart-canvas");

    if (locationData.length == 0) {
        console.log("ja", locationData);
        //TODO show error!
        canvas.hidden = true;
        canvas.style.display = 'none';
    } else {
        const singleLocationData = (locationType == "H") ? locationData : locationData[0];

        const chart = getOrCreateInformationChart(canvas);

        chart.data.datasets[0].data = [
            singleLocationData.number_of_men,
            singleLocationData.number_of_women,
            singleLocationData.number_of_diverse,
            singleLocationData.max_number - singleLocationData.number
        ];

        chart.data.datasets[1].data = [
            singleLocationData.number,
            singleLocationData.max_number,
            singleLocationData.occupancy,
        ];
        canvas.hidden = false;
        canvas.style.display = 'block';

        chart.update();
    }
}

function getOrCreateInformationChart(canvas) {
    let chart = Chart.getChart(canvas);
    if (!chart) {
        chart = new Chart(canvas, {//TODO erst beim befüllen
            type: 'doughnut',
            data: {
                labels: ["Männlich", "Weiblich", "Divers", "Leer"],
                datasets: [
                    {
                        data: [0, 0, 0, 0],
                        backgroundColor: ["blue", "orange", "green", "grey"],
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
                    const x = chart.getDatasetMeta(0).data[0].x;
                    const y = chart.getDatasetMeta(0).data[0].y;
                    const data = chart.data.datasets[1].data;

                    const {ctx} = chart;
                    ctx.save();
                    ctx.fillStyle = "#000000";
                    ctx.font = "1.2em Arial";
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

function fillLocationHistoryDataDiv(dataDiv, data, locationType) {
    const locationHistoryData = data["data"];
    const canvas = dataDiv.querySelector(".occupancy-history-chart-canvas");

    if (!("locations" in data)) {
        //TODO show error!
        canvas.hidden = true;
        canvas.style.display = 'none';
    } else {
        const chart = getOrCreateHistoryChart(canvas);
        const labels = []
        const data = []
        for (let key in locationHistoryData) {
            let value = locationHistoryData[key];
            if (locationType != "H") {
                value = value[0];
            }

            [, year, month, day, hours, minutes] = DATETIME_REGEX.exec(key);
            const datetime = new Date(year, month, day, hours, minutes);
            labels.push(`${datetime.getDay()}.${datetime.getMonth()}.${datetime.getFullYear()} ${datetime.getHours()}:${datetime.getMinutes()}`);
            let occupancy = (value) ? value.occupancy : null;//TODO warum ist es leer an manchen stellen?

            data.push(occupancy);

        }
        chart.data.labels = labels;
        chart.data.datasets[0].data = data;
        canvas.hidden = false;
        canvas.style.display = 'block';

        chart.update();
    }
}

function getOrCreateHistoryChart(canvas) {
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

function fillLocationsInformationDataDiv(dataDiv, data) {
    const locationsData = data["data"];
    const locationListDiv = dataDiv.querySelector(".location-list-div");

    locationsData.forEach(locationData => {
        const newLocationDiv = locationDivTemplate.cloneNode(true);
        const nameSpan = newLocationDiv.querySelector(".location-name-span");
        const occupancySpan = newLocationDiv.querySelector(".location-occupancy-span");
        const chartCanvas = newLocationDiv.querySelector(".location-occupancy-chart-canvas");

        nameSpan.innerText = locationData.name;
        occupancySpan.innerText = locationData.occupancy + "%";

        new Chart(chartCanvas, {
            type: 'bar',
            data: {
                labels: [locationData.name],
                datasets: [{
                    label: "belegt",
                    data: [locationData.number],
                    backgroundColor: "green"
                }, {
                    label: "leer",
                    data: [locationData.max_number - locationData.number],
                    backgroundColor: "grey",
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

function fillBedsInformationDataDiv(dataDiv, data) {
    const bedsData = data["data"];
    const bedListDiv = dataDiv.querySelector(".location-list-div");

    bedsData.forEach(bedData => {
        const newBedDiv = bedDivTemplate.cloneNode(true);
        const nameSpan = newBedDiv.querySelector(".bed-name-span");
        const ageSpan = newBedDiv.querySelector(".bed-age-span");
        const sexSpan = newBedDiv.querySelector(".bed-sex-span");
        const sexRectangle = newBedDiv.querySelector(".sex-rectangle");
        setClassForSexRectangle(bedData, sexRectangle, sexSpan);
        nameSpan.innerText = bedData.name;
        ageSpan.innerText = bedData.average_age;

        bedListDiv.appendChild(newBedDiv);
    });
}

