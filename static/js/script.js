const dragData = document.querySelector("#drag-data");
const contentViewTemplate = document.querySelector("#content-view-template");
const timeInputSpanTemplate = document.querySelector("#template-div .time-input-span.time-template");
const fromInputSpanTemplate = document.querySelector("#template-div .time-input-span.from-template");
const toInputSpanTemplate = document.querySelector("#template-div .time-input-span.to-template");
const locationSelectTemplate = document.querySelector("#template-div .selection-input");
const occupancyChartCanvasTemplate = document.querySelector("#template-div .information-chart-canvas");
const occupancyHistoryChartCanvasTemplate = document.querySelector("#template-div .occupancy-history-chart-canvas");
const locationListHeadDivTemplate = document.querySelector("#template-div .location-list-head-div.location-template");
const locationListDivTemplate = document.querySelector("#template-div .location-list-div.location-template");
const locationDivTemplate = document.querySelector("#template-div .location-div.location-template");
const bedListHeadDivTemplate = document.querySelector("#template-div .location-list-head-div.bed-template");
const bedListDivTemplate = document.querySelector("#template-div .location-list-div.bed-template");
const bedDivTemplate = document.querySelector("#template-div .location-div.bed-template");
const roomDataDiv = document.querySelector("#template-div .room-data-div");
const loaderTemplate = document.querySelector("#template-div .loader");


window.addEventListener("load", () => {
    const newViewSelects = document.querySelectorAll(".selection.time");
    if (newViewSelects) {
        newViewSelects.forEach((newViewSelect) => {
            newViewSelect.addEventListener("click", onNewViewSelection);
        });
    }

    const contentViews = document.querySelectorAll('.content-view');
    contentViews.forEach((contentView) => {
        setContentViewHeading(contentView, contentView.dataset.location, contentView.dataset.theme);
        buildContentViewDataDiv(contentView, contentView.dataset.location, contentView.dataset.theme);
        setAllEventListeners(contentView);

        const locationSelect = contentView.querySelector(".selection-input");
        if (locationSelect != null && locationSelect.querySelectorAll("option").length == 0) {
            addEmptyOptionToSelect(locationSelect);//TODO add error message
        }
        fetchDataForContentViewDataDiv(contentView);

    });
});

document.addEventListener("DOMContentLoaded", () => {

    /*new Chart(newInformationCanvasTemplate, {//TODO erst beim befüllen
            type: 'doughnut',
            data: {
                labels: ["Männer", 'Frauen', 'Diverse', 'Leer'],
                datasets: [
                    {
                        data: [5, 6, 1, 10],
                        backgroundColor: ["blue", "orange", "green", "grey"],
                    },
                    {
                        data: [12, 20, 60],
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
                    ctx.textBaseline = "top"
                    ctx.fillText(`${data[2]}%`, x, y);
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
                        labels: {
                            generateLabels: chart => {
                                const datasets = chart.data.datasets;
                                return datasets[0].data.map((data, i) => ({
                                    text: `${chart.data.labels[i]} ${datasets[0].data[i]} / ${datasets[1].data[1]}`,
                                    fillStyle: datasets[0].backgroundColor[i],
                                    index: i
                                }))
                            }
                        }
                    }
                },
            }
        });
    let ctx2 = document.querySelector('#myChart2');
    var bar_chart = new Chart(ctx2, {
        type: 'bar',
        data: {
            labels: ["Fachbereichname"],
            datasets: [{
                label: "belegt",
                data: [10],
                backgroundColor: "green"
            }, {
                label: "leer",
                data: [10],
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
        } // options
    });


    let ctx3 = document.querySelector('#myChart3');
    let chart3 = new Chart(ctx3, {
        type: 'line',
        data: {
            labels: ["1.1.2023", "2.1.2023", "3.1.2023", "4.1.2023", "5.1.2023", "6.1.2023", "7.1.2023", "8.1.2023", "9.1.2023", "10.1.2023"],
            datasets: [{
                label: "Auslastung",
                data: [100, 140, 130, 170, 90, 80, 60, 120, 121, 134],
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
        }
    });*/
});

// drag and drop methods

function onDragEnd(event) {
    event.target.classList.remove("dragged-content-view");
}

function onDragOver(event) {
    event.preventDefault();
}

function updateOrderOfContentViews() {
    const contentViews = document.querySelectorAll(".content-view");
    let orderIdDictList = [];
    contentViews.forEach((contentView) => {
        orderIdDictList.push({
            id: contentView.dataset.id,
            order: contentView.dataset.order
        })
    });

    fetch("/update/order", {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify(orderIdDictList)
    }).then((response) => {
        if (response.ok) {
            return response.text();
        }
        throw new Error("Request fehlgeschlagen.");
    }).catch((error) => console.log(error));
}

function onDragStart(event) {
    const contentView = event.target;
    dragData.value = contentView.dataset.order;
    contentView.classList.add("dragged-content-view");
}

function onDragEnter(event) {
    const newContentViews = document.querySelectorAll('.content-view');
    const order = parseInt(dragData.value);
    const startContentView = newContentViews[order];
    const contentView = event.target.closest(".content-view");
    if (contentView != startContentView) {

        const parentElement = startContentView.parentNode;
        if (order < parseInt(event.target.closest(".content-view").dataset.order)) {
            parentElement.insertBefore(startContentView, contentView.nextElementSibling);
        } else {
            parentElement.insertBefore(startContentView, contentView);
        }

        //Change ordering
        resetOrderForContentViews(startContentView, newContentViews);

        dragData.value = startContentView.dataset.order;
    }
}


// adding of new data representation
function onNewViewSelection(event) {
    const element = event.target;
    const locationType = element.dataset.location;
    const themeType = element.dataset.theme;
    const timeType = element.dataset.time;

    fetch("/create/user-data_representation", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
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
        createNewContentView(data_representation, user_data_representation, locations);

    }).catch((error) => console.log(error));
}


//deletion of a data representation
function onDeletionOfView(event) {
    if (confirm("Sind sie sicher, dass sie diese Datenrepräsentation löschen wollen?")) {
        const element = event.target;
        const contentView = element.closest(".content-view");

        const location = contentView.dataset.location;
        const theme = contentView.dataset.theme;
        const time = contentView.dataset.time;

        //delete contentView
        contentView.remove();

        fetch("/delete/user-data-representation", {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                id: contentView.dataset.id
            })
        }).then((response) => {
            if (response.ok) {
                return response.text();
            }
            throw new Error("Request fehlgeschlagen.");
        }).catch((error) => console.log(error));
    }

    resetOrderForContentViews();
    updateOrderOfContentViews();
}

// redirect to the download of csv data
function onDownloadDataForView(event) {
    const element = event.target;
    const contentView = element.closest(".content-view");

    const location = contentView.dataset.location;
    const theme = contentView.dataset.theme;
    const time = contentView.dataset.time;

    //TODO redirect to new tab and download with all important data
}

//changement of the time inputs or the location selct
function onInputChange(event) {
    console.log("test");
    const element = event.target;
    const contentView = element.closest(".content-view");
    fetchDataForContentViewDataDiv(contentView, true);
}

function fillLocationSelect(locations, locationSelect, locationType, user_data_representation) {
    if (locations != null && locations.length != 0) {
        locations.forEach((location) => {
            const newOption = document.createElement("option");
            const locationId = location["id"];
            newOption.value = locationId;
            newOption.innerText = location["name"];

            locationSelect.appendChild(newOption);

            if (locationType == "D" && locationId == user_data_representation["department"] || locationType == "W" && locationId == user_data_representation["ward"] || locationType == "R" && locationId == user_data_representation["room"]) {
                locationSelect.value = locationId;
            }
        });
    } else {
        addEmptyOptionToSelect(locationSelect);
    }
}

// content view creation
function createNewContentView(data_representation, user_data_representation, locations) {
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

    setContentViewHeading(contentView, locationType, themeType);
    buildContentViewDataDiv(contentView, locationType, themeType);
    setAllEventListeners(contentView);

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
        fillLocationSelect(locations, locationSelect, locationType, user_data_representation);

        contentView.querySelector(".location-input-div").appendChild(locationSelect);
    }

    document.querySelector("#content-div").appendChild(contentView);
    contentView.scrollIntoView();
    fetchDataForContentViewDataDiv(contentView, true);
}

function setContentViewHeading(contentView, locationType, themeType) {

    //add the heading
    const contentViewHeading = contentView.querySelector(".content-view-heading");
    let headingText = "";
    switch (themeType) {
        case "I":
            headingText = "Informationen";
            break
        case "D":
            headingText = "Fachabteilungen";
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

    switch (locationType) {
        case "D":
            headingText += " der Fachabteilung";
            break
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

function buildContentViewDataDiv(contentView, locationType, themeType) {
    const contentDataDiv = contentView.querySelector(".content-view-data-div");

    if (themeType == "I") {
        contentDataDiv.appendChild(loaderTemplate.cloneNode(true));
        if (locationType == "R") {
            contentDataDiv.appendChild(roomDataDiv.cloneNode(true));
        } else {
            contentDataDiv.appendChild(occupancyChartCanvasTemplate.cloneNode(true));
        }
    } else if (themeType == "H") {
        contentDataDiv.appendChild(loaderTemplate.cloneNode(true));
        contentDataDiv.appendChild(occupancyHistoryChartCanvasTemplate.cloneNode(true));
    } else if (themeType == "B") {
        contentDataDiv.appendChild(bedListHeadDivTemplate.cloneNode(true));
        const bedListDiv = bedListDivTemplate.cloneNode(true);
        bedListDiv.appendChild(loaderTemplate.cloneNode(true));
        contentDataDiv.appendChild(bedListDiv);
    } else {
        const locationListHeadDiv = locationListHeadDivTemplate.cloneNode(true);
        const locationNameHead = locationListHeadDiv.querySelector(".location-name-head");
        if (themeType == "W") {
            locationNameHead.innerText = "Station";
        } else if (themeType == "D") {
            locationNameHead.innerText = "Fachabteilung";
        } else if (themeType == "R") {
            locationNameHead.innerText = "Zimmer";
        }

        contentDataDiv.appendChild(locationListHeadDiv);
        const locationListDiv = locationListDivTemplate.cloneNode(true)
        locationListDiv.appendChild(loaderTemplate.cloneNode(true));
        contentDataDiv.appendChild(locationListDiv);
    }
}

//adds all event listeners
function setAllEventListeners(contentView) {
    //drag and drop
    contentView.addEventListener('dragstart', onDragStart);
    contentView.addEventListener("dragend", onDragEnd);
    contentView.addEventListener("dragenter", onDragEnter);
    contentView.addEventListener("drop", updateOrderOfContentViews);
    contentView.addEventListener("dragover", onDragOver)

    //other event listeners
    contentView.querySelector(".delete-image").addEventListener("click", onDeletionOfView);
    contentView.querySelector(".download-image").addEventListener("click", onDownloadDataForView);
    const inputElements = contentView.querySelectorAll(".selection-input, .from-input, .to-input, .time-input");
    if (inputElements) {
        inputElements.forEach((inputElement) => {
            addEventListener("change", onInputChange);
        });
    }
}

//resets order of the content views
function resetOrderForContentViews() {
    const newContentViews = document.querySelectorAll('.content-view');
    if (newContentViews.length != 0) {
        const parent = newContentViews[0].parentElement;
        newContentViews.forEach((contentViewElement) => {
            contentViewElement.dataset.order = Array.prototype.indexOf.call(parent.children, contentViewElement);
        });
    }
}

// checks if select is empty and adds error option if this is true
function addEmptyOptionToSelect(select) {// TODO add error message
    const newOption = document.createElement("option");
    newOption.innerText = "-- leer --";
    newOption.value = -1;
    newOption.selected = true;
    newOption.disabled = true;

    select.appendChild(newOption);
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
    let url = new URL(location.protocol + "//" + location.host + "/get_data" + "/" + locationType + "/" + themeType + "/" + timeType + "/");

    url.searchParams.append("id", contentView.dataset.id);

    url.searchParams.append("update_flag", updateInputs.toString());

    //add the id param, if it's a list of occupancies
    if (locationType != "H") {
        let selectionElement = contentView.querySelector(".selection-input");
        const location_id = selectionElement.value
        url.searchParams.append("location_id", location_id);
    }

    //add the time params, if its a time type
    if (timeType == "T") {
        const timeElement = contentView.querySelector(".time-input");
        const time = timeElement.value;
        if (!time) {
            throw new Error("There is no given time.");
        }
        url.searchParams.append("time", time);
    } else if (timeType == "P") {
        const fromTimeElement = contentView.querySelector(".from-input");
        const fromTime = fromTimeElement.value;
        const toTimeElement = contentView.querySelector(".to-input");
        const toTime = toTimeElement.value;
        if (!toTime || !fromTime) {
            throw new Error("There is no given time for from or to.");
        }
        url.searchParams.append("time", fromTime);
        url.searchParams.append("end_time", toTime);
    }

    fetch(url.toString(), {
        method: "GET",
        headers: {
            "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
        },
    }).then((response) => {
        console.log(response);
        if (response.ok) {
            return response.json();
        }
        throw new Error("Request failed.");
    }).then(data => {
        console.log(data);
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
    }

    loader.hidden = true;


}

function fillRoomInformationDataDiv(dataDiv, data) {
    const roomDataDiv = dataDiv.querySelector(".room-data-div");
    const ageH4 = roomDataDiv.querySelector(".room-age-h4");
    const sexRectangle = roomDataDiv.querySelector(".sex-rectangle-span");
    const sexSpan = roomDataDiv.querySelector(".sex-span");

    roomDataDiv.hidden = false;

    const roomData = data["data"];
    if (roomData.length == 0) {
        //TODO show error!
    } else {
        const singleRoomData = roomData[0];
        sexRectangle.classList.remove(...sexRectangle.classList);
        sexRectangle.classList.add("sex-rectangle-span");
        if (singleRoomData.number_of_men > 0) {
            sexRectangle.classList.add("male-rectangle");
            sexSpan.innerText = "Männlich";
        } else if (singleRoomData.number_of_women > 0) {
            sexRectangle.classList.add("female-rectangle");
            sexSpan.innerText = "Weiblich";
        } else if (singleRoomData.number_of_diverse > 0) {
            sexRectangle.classList.add("diverse-rectangle");
            sexSpan.innerText = "Divers";
        } else {
            sexRectangle.classList.add("empty-rectangle");//TODO add empty view!
            sexSpan.innerText = "Leer";
        }

        ageH4.innerText = singleRoomData.average_age;
    }
}

function fillLocationInformationDataDiv(dataDiv, data, locationType) {
    const locationData = data["data"];
    const canvas = dataDiv.querySelector(".information-chart-canvas");

    if (locationData.length == 0) {
        //TODO show error!
        canvas.hidden = true;
        canvas.style.display = 'none';
        console.log(locationData, locationData.length, canvas.hidden, canvas);
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
                labels: ["Männer", 'Frauen', 'Diverse', 'Leer'],
                datasets: [
                    {
                        data: [5, 6, 1, 10],
                        backgroundColor: ["blue", "orange", "green", "grey"],
                    },
                    {
                        data: [12, 20, 60],
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

