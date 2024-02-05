function onUpdateClick() {
  // Reloads page with new query which includes new dates
  let startDate = document.getElementById("start").value;
  let endDate = document.getElementById("end").value;

  let currentParams = new URLSearchParams(location.search);

  currentParams.delete("start");
  currentParams.delete("end");

  currentParams.append("start", startDate);
  currentParams.append("end", endDate);

  // A change in location.search reloads page automatically
  location.search = currentParams.toString();
}

var userChartData = userChartData;

const ctx = document.getElementById("userChart");
var userChart = new Chart(ctx, {
  type: "line",
  data: {
    datasets: [
      {
        label: "Hits",
        data: userChartData[0],
        fill: false,
        borderColor: "hsl(135, 94%, 65%)",
        pointBackgroundColor: "hsl(135, 94%, 65%)",
        lineTension: 0.2,
      },
      {
        label: "Unique users",
        data: userChartData[1],
        fill: false,
        borderColor: "hsl(191, 97%, 77%)",
        pointBackgroundColor: "hsl(191, 97%, 77%)",
        lineTension: 0.2,
      },
    ],
  },
  options: {
    responsive: true,
    animation: false,
    legend: {
      display: false,
      labels: {
        fontColor: "hsl(60, 30%, 96%)",
      },
    },
    scales: {
      xAxes: [
        {
          type: "time",
          time: {
            unit: "day",
          },
          ticks: {
            fontColor: "hsl(60, 30%, 96%)",
          }
        },
      ],
      yAxes: [
        {
          ticks: {
            beginAtZero: true,
            precision: 0,
            fontColor: "hsl(60, 30%, 96%)",
          },
          gridLines: {
            color: "hsla(60, 30%, 96%, 0.5)",
          },
        },
      ],
    },
  },
});
