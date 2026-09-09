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


/* ============================================================
   SOLUTION VOTING
   ============================================================ */

document.addEventListener("DOMContentLoaded", function () {

    const voteButtons =
        document.querySelectorAll(".vote-button");

    if (!voteButtons.length) {
        return;
    }


    /*
     * Read a cookie by name.
     */
    function getCookie(name) {

        let cookieValue = null;

        if (document.cookie && document.cookie !== "") {

            const cookies =
                document.cookie.split(";");

            for (let cookie of cookies) {

                cookie = cookie.trim();

                if (
                    cookie.substring(
                        0,
                        name.length + 1
                    ) === name + "="
                ) {

                    cookieValue = decodeURIComponent(
                        cookie.substring(
                            name.length + 1
                        )
                    );

                    break;
                }
            }
        }

        return cookieValue;
    }


    /*
     * ProblemPool uses a custom CSRF cookie name:
     *
     * CSRF_COOKIE_NAME = "problempool_csrftoken"
     *
     * Therefore we must read that cookie instead of
     * Django's default "csrftoken".
     */
    function getCSRFToken() {

        return getCookie("problempool_csrftoken");

    }


    voteButtons.forEach(function (button) {

        button.addEventListener(
            "click",
            async function () {

                const voteUrl =
                    button.dataset.voteUrl;

                const voteType =
                    button.dataset.voteType;


                if (!voteUrl || !voteType) {

                    console.error(
                        "Voting error: missing vote URL or vote type."
                    );

                    alert(
                        "Unable to record your vote."
                    );

                    return;

                }


                const csrfToken =
                    getCSRFToken();


                if (!csrfToken) {

                    console.error(
                        "Voting error: CSRF token cookie was not found."
                    );

                    alert(
                        "Your session security token is missing. Please refresh the page and try again."
                    );

                    return;

                }


                try {

                    button.disabled = true;


                    const formData =
                        new FormData();

                    formData.append(
                        "vote_type",
                        voteType
                    );


                    const response =
                        await fetch(
                            voteUrl,
                            {
                                method: "POST",

                                headers: {
                                    "X-CSRFToken":
                                        csrfToken,

                                    "X-Requested-With":
                                        "XMLHttpRequest",

                                    "Accept":
                                        "application/json",
                                },

                                body: formData,

                                credentials:
                                    "same-origin",
                            }
                        );


                    /*
                     * Try to read JSON safely.
                     * This prevents a generic JavaScript
                     * error if Django returns an HTML error page.
                     */
                    let data = null;

                    try {

                        data =
                            await response.json();

                    } catch (jsonError) {

                        console.error(
                            "Voting response was not valid JSON:",
                            jsonError
                        );

                        console.error(
                            "HTTP status:",
                            response.status
                        );

                        alert(
                            "Unable to record your vote. Please refresh the page and try again."
                        );

                        return;

                    }


                    if (!response.ok || !data.success) {

                        console.error(
                            "Voting request failed:",
                            data
                        );

                        alert(
                            data.message ||
                            "Unable to record your vote."
                        );

                        return;

                    }


                    /* ----------------------------------------
                       UPDATE COUNTS
                    ---------------------------------------- */

                    const upvoteCount =
                        document.getElementById(
                            "upvote-count"
                        );

                    const downvoteCount =
                        document.getElementById(
                            "downvote-count"
                        );

                    const scoreCount =
                        document.getElementById(
                            "score-count"
                        );


                    if (upvoteCount) {

                        upvoteCount.textContent =
                            data.upvotes;

                    }


                    if (downvoteCount) {

                        downvoteCount.textContent =
                            data.downvotes;

                    }


                    if (scoreCount) {

                        scoreCount.textContent =
                            data.score;

                    }


                    /* ----------------------------------------
                       UPDATE BUTTON STATES
                    ---------------------------------------- */

                    const upvoteButton =
                        document.getElementById(
                            "upvote-button"
                        );

                    const downvoteButton =
                        document.getElementById(
                            "downvote-button"
                        );


                    if (upvoteButton) {

                        upvoteButton.classList.remove(
                            "active"
                        );

                    }


                    if (downvoteButton) {

                        downvoteButton.classList.remove(
                            "active"
                        );

                    }


                    if (
                        data.user_vote === "UP" &&
                        upvoteButton
                    ) {

                        upvoteButton.classList.add(
                            "active"
                        );

                    }


                    if (
                        data.user_vote === "DOWN" &&
                        downvoteButton
                    ) {

                        downvoteButton.classList.add(
                            "active"
                        );

                    }


                    /* ----------------------------------------
                       UPDATE MESSAGE
                    ---------------------------------------- */

                    const message =
                        document.getElementById(
                            "vote-message"
                        );


                    if (message) {

                        if (data.user_vote === "UP") {

                            message.innerHTML =
                                '<i class="bi bi-check-circle"></i>' +
                                " You have upvoted this solution.";

                            message.classList.add(
                                "visible"
                            );

                        } else if (
                            data.user_vote === "DOWN"
                        ) {

                            message.innerHTML =
                                '<i class="bi bi-check-circle"></i>' +
                                " You have downvoted this solution.";

                            message.classList.add(
                                "visible"
                            );

                        } else {

                            message.innerHTML = "";

                            message.classList.remove(
                                "visible"
                            );

                        }

                    }


                } catch (error) {

                    console.error(
                        "Voting error:",
                        error
                    );

                    alert(
                        "Something went wrong while recording your vote."
                    );

                } finally {

                    button.disabled = false;

                }

            }
        );

    });

});