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

var ctx = document.getElementById("userChart");
var userChart = new Chart(ctx, {
  type: "line",
  data: {
    datasets: [
      {
        label: "Hits",
        data: userChartData[0],
        fill: false,
        borderColor: "#50fa7b",
      },
      {
        label: "Unique users",
        data: userChartData[1],
        fill: false,
        borderColor: "#8be9fd",
      },
    ],
  },
  options: {
    responsive: true,
    title: {
      display: false,
      position: "top",
      text: "Hits for all routes",
    },
    animation: false,
    scales: {
      xAxes: [
        {
          type: "time",
          time: {
            unit: "day",
          },
        },
      ],
      yAxes: [
        {
          ticks: {
            beginAtZero: true,
            precision: 0,
          },
        },
      ],
    },
  },
});
