/**
 * Library Management System - Client Side Script
 */

document.addEventListener("DOMContentLoaded", function () {
  // 1. Mobile Sidebar Toggle
  const sidebarToggleBtn = document.getElementById("sidebarToggleBtn");
  const sidebar = document.getElementById("sidebar");
  const sidebarBackdrop = document.getElementById("sidebarBackdrop");

  if (sidebarToggleBtn && sidebar) {
    sidebarToggleBtn.addEventListener("click", function () {
      sidebar.classList.toggle("show");
      if (sidebarBackdrop) {
        sidebarBackdrop.classList.toggle("show");
      }
    });
  }

  if (sidebarBackdrop) {
    sidebarBackdrop.addEventListener("click", function () {
      sidebar.classList.remove("show");
      sidebarBackdrop.classList.remove("show");
    });
  }

  // 2. Auto-dismiss alerts after 5 seconds
  const autoDismissAlerts = document.querySelectorAll(".alert-dismissible");
  autoDismissAlerts.forEach(function (alertEl) {
    setTimeout(function () {
      if (typeof bootstrap !== "undefined" && bootstrap.Alert) {
        const alertInstance = bootstrap.Alert.getOrCreateInstance(alertEl);
        if (alertInstance) {
          alertInstance.close();
        }
      }
    }, 6000);
  });

  // 3. Generic Delete Confirmation Modal Listener
  const deleteModal = document.getElementById("deleteConfirmModal");
  if (deleteModal) {
    deleteModal.addEventListener("show.bs.modal", function (event) {
      const button = event.relatedTarget;
      if (!button) return;

      const deleteUrl = button.getAttribute("data-delete-url");
      const itemName = button.getAttribute("data-item-name");
      const itemType = button.getAttribute("data-item-type") || "record";

      const form = deleteModal.querySelector("#deleteConfirmForm");
      const nameEl = deleteModal.querySelector("#deleteItemName");
      const typeEl = deleteModal.querySelector("#deleteItemType");

      if (form && deleteUrl) form.setAttribute("action", deleteUrl);
      if (nameEl && itemName) nameEl.textContent = itemName;
      if (typeEl && itemType) typeEl.textContent = itemType;
    });
  }

  // 4. Return Book Confirmation Modal Listener
  const returnModal = document.getElementById("returnBookModal");
  if (returnModal) {
    returnModal.addEventListener("show.bs.modal", function (event) {
      const button = event.relatedTarget;
      if (!button) return;

      const returnUrl = button.getAttribute("data-return-url");
      const bookTitle = button.getAttribute("data-book-title");
      const studentName = button.getAttribute("data-student-name");
      const estFine = button.getAttribute("data-est-fine") || "0.00";
      const overdueDays = button.getAttribute("data-overdue-days") || "0";

      const form = returnModal.querySelector("#returnBookForm");
      const bookEl = returnModal.querySelector("#returnModalBookTitle");
      const studentEl = returnModal.querySelector("#returnModalStudentName");
      const fineEl = returnModal.querySelector("#returnModalFineAmount");
      const daysEl = returnModal.querySelector("#returnModalOverdueDays");
      const fineAlertEl = returnModal.querySelector("#returnModalFineAlert");

      if (form && returnUrl) form.setAttribute("action", returnUrl);
      if (bookEl && bookTitle) bookEl.textContent = bookTitle;
      if (studentEl && studentName) studentEl.textContent = studentName;
      if (fineEl) fineEl.textContent = `$${parseFloat(estFine).toFixed(2)}`;
      if (daysEl) daysEl.textContent = overdueDays;

      if (fineAlertEl) {
        if (parseFloat(estFine) > 0) {
          fineAlertEl.classList.remove("d-none");
        } else {
          fineAlertEl.classList.add("d-none");
        }
      }
    });
  }
});
