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


    voteButtons.forEach(function (button) {

        button.addEventListener(
            "click",
            async function () {

                const voteUrl =
                    button.dataset.voteUrl;

                const voteType =
                    button.dataset.voteType;


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
                                        getCookie("csrftoken"),

                                    "X-Requested-With":
                                        "XMLHttpRequest",
                                },

                                body: formData,
                            }
                        );


                    const data =
                        await response.json();


                    if (!data.success) {

                        alert(
                            data.message ||
                            "Unable to record your vote."
                        );

                        return;
                    }


                    // ----------------------------------------
                    // UPDATE COUNTS
                    // ----------------------------------------

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


                    // ----------------------------------------
                    // UPDATE BUTTON STATES
                    // ----------------------------------------

                    const upvoteButton =
                        document.getElementById(
                            "upvote-button"
                        );

                    const downvoteButton =
                        document.getElementById(
                            "downvote-button"
                        );


                    upvoteButton.classList.remove(
                        "active"
                    );

                    downvoteButton.classList.remove(
                        "active"
                    );


                    if (data.user_vote === "UP") {

                        upvoteButton.classList.add(
                            "active"
                        );

                    }


                    if (data.user_vote === "DOWN") {

                        downvoteButton.classList.add(
                            "active"
                        );

                    }


                    // ----------------------------------------
                    // UPDATE MESSAGE
                    // ----------------------------------------

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