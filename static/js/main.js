/**
 * ProblemPool global JavaScript
 */

document.addEventListener("DOMContentLoaded", function () {

    /*
     * Automatically close Django message alerts
     * after a short period.
     */
    const alerts = document.querySelectorAll(".alert");

    alerts.forEach(function (alert) {

        setTimeout(function () {

            if (alert.classList.contains("show")) {

                const closeButton =
                    alert.querySelector(".btn-close");

                if (closeButton) {
                    closeButton.click();
                }

            }

        }, 5000);

    });

});