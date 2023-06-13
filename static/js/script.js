const dragData = document.querySelector("#drag-data");
const contentViewTemplate = document.querySelector("#content-view-template");
const timeInputSpanTemplate = document.querySelector("#time-input-span-template");
const fromInputSpanTemplate = document.querySelector("#from-input-span-template");
const locationSelectTemplate = document.querySelector("#template-div .selection-input");
const toInputSpanTemplate = document.querySelector("#to-input-span-template");

window.addEventListener("load", () => {
    const timeSelections = document.querySelectorAll(".selection .time");
    timeSelections.forEach((timeSelection) => {
        timeSelection.addEventListener("click", onNewViewSelection);
    });

    const deleteImages = document.querySelectorAll(".delete-image");
    deleteImages.forEach((deleteImage) => {
        deleteImage.addEventListener("click", onDeletionOfView);
    });

    const downloadImages = document.querySelectorAll(".download-image");
    downloadImages.forEach((downloadImage) => {
        downloadImage.addEventListener("click", onDownloadDataForView);
    });

    const inputs = document.querySelectorAll(".selection-input, .from-input, .to-input, .time-input");
    inputs.forEach((input) => {
        input.addEventListener("change", onInputChange);
    });

    const contentViews = document.querySelectorAll('.content-view');
    contentViews.forEach((contentView) => {
        setContentViewHeading(contentView, contentView.dataset.location, contentView.dataset.theme);
        setDragAndDropEventListeners(contentView);
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

function setDragAndDropEventListeners(contentView) {
    contentView.addEventListener('dragstart', onDragStart);
    contentView.addEventListener("dragend", onDragEnd);
    contentView.addEventListener("dragenter", onDragEnter);
    contentView.addEventListener("drop", onDrop);
    contentView.addEventListener("dragover", onDragOver)
}

function onDragEnd(event) {
    event.target.classList.remove("dragged-content-view");
}

function onDragOver(event) {
    event.preventDefault();
}

function onDrop(event) {
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
        const parent = startContentView.parentElement;
        newContentViews.forEach((contentViewElement) => {
            contentViewElement.dataset.order = Array.prototype.indexOf.call(parent.children, contentViewElement);
        });

        dragData.value = startContentView.dataset.order;
    }
}


// adding of new data representation
function onNewViewSelection(event) {
    const element = event.target;
    const location_type = element.dataset.location;
    const theme_type = element.dataset.theme;
    const time_type = element.dataset.time;

    console.log(location_type);
    fetch("/create/user-data_representation", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            location_type: location_type,
            theme_type: theme_type,
            time_type: time_type,
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
        console.log(locations, user_data_representation);
        createNewContentView(data_representation, user_data_representation, locations)
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
    const element = event.target;
    const contentView = element.closest(".content-view");
    const location_type = contentView.dataset.location;
    const theme_type = contentView.dataset.theme;
    const time_type = contentView.dataset.time;

    // create the right url
    let url = new URL(location.protocol + "//" + location.host + "/" + location_type + "/" + theme_type + "/" + time_type + "/");
    console.log(url);
    //add the id param, if it's a list of occupancies
    if (location_type != "H") {
        let selectionElement = contentView.querySelector(".selection-input");
        url.searchParams.append("id", selectionElement.value);
    }

    //add the time params, if its a time type
    if (time_type == "T") {
        const timeElement = contentView.querySelector(".time-input");
        const time = timeElement.value;
        console.log(time);
        if (!time) {
            throw new Error("There is no given time.");
        }
        url.searchParams.append("time", time);
    } else if (time_type == "P") {
        const fromTimeElement = contentView.querySelector(".from-input");
        const fromTime = fromTimeElement.value;
        const toTimeElement = contentView.querySelector(".to-input");
        const toTime = toTimeElement.value;
        if (!toTime || !fromTime) {
            throw new Error("There is no given time for from or to.");
        }
        url.searchParams.append("from", fromTime);
        url.searchParams.append("to", toTime);
    }

    //TODO send ajax for the new data
}

// content view creation
function createNewContentView(data_representation, user_data_representation, locations) {
    //TODO als konstant ganz oben und laden des Skripts unter allem html
    const contentView = contentViewTemplate.cloneNode(true);
    contentView.removeAttribute("id");
    contentView.classList.add("content-view");

    const location_type = data_representation["location_type"];
    const theme_type = data_representation["theme_type"];
    const time_type = data_representation["time_type"];

    //set all data-attributes
    contentView.dataset.location_type = location_type;
    contentView.dataset.theme_type = theme_type;
    contentView.dataset.time_type = time_type;
    contentView.dataset.order = user_data_representation["order"];
    contentView.dataset.id = user_data_representation["id"];

    setContentViewHeading(contentView, location_type, theme_type);
    setDragAndDropEventListeners(contentView);

    const timeInputDiv = contentView.querySelector(".time-input-div");
    if (time_type == "T") {
        const timeInputSpan = timeInputSpanTemplate.cloneNode(true);
        timeInputSpan.removeAttribute("id");

        timeInputSpan.querySelector(".time-input").value = user_data_representation["time"];
        timeInputDiv.appendChild(timeInputSpan);
    } else if (time_type == "P") {
        const fromInputSpan = fromInputSpanTemplate.cloneNode(true);
        fromInputSpan.removeAttribute("id");
        fromInputSpan.querySelector(".from-input").value = user_data_representation["time"];
        timeInputDiv.appendChild(fromInputSpan);

        const toInputSpan = toInputSpanTemplate.cloneNode(true);
        toInputSpan.removeAttribute("id");
        toInputSpan.querySelector(".to-input").value = user_data_representation["end_time"];
        timeInputDiv.appendChild(toInputSpan);
    }

    if (location_type != "H") {
        const locationSelect = locationSelectTemplate.cloneNode(true);
        locations.forEach((location) => {
            const newOption = document.createElement("option");
            const locationId = location["id"];
            newOption.value = locationId;
            newOption.innerText = location["name"];

            locationSelect.appendChild(newOption);

            if (location_type == "D" && locationId == user_data_representation["department"] || location_type == "W" && locationId == user_data_representation["ward"] || location_type == "R" && locationId == user_data_representation["room"]) {
                locationSelect.value = locationId;
            }
        });

        contentView.querySelector(".location-input-div").appendChild(locationSelect);
    }

    document.querySelector("#content-div").appendChild(contentView);
    contentView.scrollIntoView();
}

function setContentViewHeading(contentView, location_type, theme_type) {

    //add the heading
    const contentViewHeading = contentView.querySelector(".content-view-heading");
    let headingText = "";
    switch (theme_type) {
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
        case "B":
            headingText = "Auslastungsverlauf";
            break
    }

    switch (location_type) {
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