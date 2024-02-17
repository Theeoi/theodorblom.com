/* Admin Dropdown */

const adminToggle = document.querySelector(".admin-dropdown button");
const dropdownMenu = document.querySelector(".admin-dropdown ul");

adminToggle.addEventListener("click", () => {
  adminToggle.classList.toggle("active");
  dropdownMenu.classList.toggle("show");
});

window.onclick = function(event) {
  if (
    !event.target.matches(".admin-dropdown button") &&
    !event.target.closest(".admin-dropdown")
  ) {
    var openDropdown = document.querySelector(".admin-dropdown ul.show");
    if (openDropdown) {
      adminToggle.classList.remove("active");
      openDropdown.classList.remove("show");
    }
  }
};
