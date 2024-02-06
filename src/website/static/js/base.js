/* Nav Toggle */

const navToggle = document.querySelector(".nav-toggle");
const navLinks = document.querySelectorAll(".nav__link");

navToggle.addEventListener("click", () => {
    document.body.classList.toggle("nav-open");
});

navLinks.forEach((link) => {
    link.addEventListener("click", () => {
        document.body.classList.remove("nav-open");
    });
});

/* Sticky Header */

window.onscroll = function() {
    stickyHeader();
};

var header = document.getElementById("sticky-header");
var sticky = header.offsetTop;

function stickyHeader() {
    if (window.pageYOffset > sticky) {
        header.classList.add("sticky");
    } else {
        header.classList.remove("sticky");
    }
}

// // Animated favicon

// var favicon_images = [
//     "/static/resources/icons/theodorblom-favicon-nocursor.svg",
//     "/static/resources/icons/theodorblom-favicon-cursor.svg",
// ];
// var counter = 0;

// setInterval(function() {
//     if (document.querySelector("link[rel='icon']") !== null)
//         document.querySelector("link[rel='icon']").remove();

//     document
//         .querySelector("head")
//         .insertAdjacentHTML(
//             "beforeend",
//             "<link rel='icon' href=" + favicon_images[counter] + "/>"
//         );

//     if (counter == favicon_images.length - 1) counter = 0;
//     else counter++;
// }, 500);
