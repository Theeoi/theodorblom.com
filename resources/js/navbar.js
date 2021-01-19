
function responsiveBar() {
    var x = document.getElementById("topnav");
    if (x.className == "topnav") {
        x.className += " responsive";
    }
    else {
        x.className = "topnav";
    }
}

function topDropFunc() {
  document.getElementById("utility-navdrop").classList.toggle("navdrop-show");
}

// Close the dropdown menu if the user clicks outside of it
window.onclick = function(event) {
  if (!event.target.matches('.navdrop-link')) {
    var dropdowns = document.getElementsByClassName("navdrop-content");
    var i;
    for (i = 0; i < dropdowns.length; i++) {
      var openDropdown = dropdowns[i];
      if (openDropdown.classList.contains('navdrop-show')) {
        openDropdown.classList.remove('navdrop-show');
      }
    }
  }
}
