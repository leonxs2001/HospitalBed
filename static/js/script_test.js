const ctx = document.getElementById('myChart');
const DATA_COUNT = 5;
const NUMBER_CFG = {count: DATA_COUNT, min: 0, max: 100};

const data = {
    labels: ['Red', 'Orange', 'Yellow', 'Green', 'Blue'],
    datasets: [
        {
            label: 'Dataset 1',
            data: [2, 3, 4, 5, 6],
            backgroundColor: ["red", "orange", "yellow", "green", "blue"],
        }
    ]
};

document.addEventListener("DOMContentLoaded", () => {
    let mychart = new Chart(ctx, {
        type: 'doughnut',
        data: data,
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right',
                },
                title: {
                    display: true,
                    text: 'Chart.js Doughnut Chart'
                }
            }
        },
    });
    //console.log(mychart.data.datasets[0].data = [1,2,3,4,5])
    addEventListener("resize", (event) => {
        mychart.resize()
    });
    var value = 57866; // your value
    var max = 80000; // the max

    var ctx2 = document.getElementById('myChart2');

    var bar_chart = new Chart(ctx2, {
        type: 'bar',
        data: {
            labels: ["Fachbereichname"],
            datasets: [{
                label: "belegt",
                data: [value],
                backgroundColor: "rgba(51,230,125,1)"
            }, {
                label: "leer",
                data: [max - value],
                backgroundColor: "lightgrey",
            },]
        },
        options: {
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

});

function onSelection(span){
    console.log(span)
}