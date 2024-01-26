const adminToggle = document.querySelector(".btn-dropdown");
const dropdownMenu = document.querySelector(".dropdown-menu");

adminToggle.addEventListener("click", () => {
  dropdownMenu.classList.toggle("show");
});

window.onclick = function(event) {
  if (
    !event.target.matches(".btn-dropdown") &&
    !event.target.closest(".admin-dropdown")
  ) {
    var openDropdown = document.querySelector(".dropdown-menu.show");
    if (openDropdown) {
      openDropdown.classList.remove("show");
    }
  }
};
