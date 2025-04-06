$(function () {
    const rateButton = document.getElementById("rateButton");
    const scoreField = document.getElementById("id_score");
    const systemCommentsField = document.getElementById("id_system_comments");
    const otherCommentField = document.getElementById("otherCommentField");
    const numberPlateField = document.getElementById("id_motor_car_number");

    function checkRequiredFields() {
        const numberPlate = numberPlateField ? numberPlateField.value.trim() : "";
        const score = parseFloat(scoreField.value) || 0;
        const selectedComments = document.querySelectorAll(".comment-option.selected");
        const otherSelected = document.querySelector(".comment-option[textContent='Other']")?.classList.contains("selected") || false; // Handle case where "Other" might not exist yet
        return (numberPlate !== "" && score > 0 && selectedComments.length > 0 && (!otherSelected || otherCommentField.value.trim() !== ""));
    }

    function updateButtonState() {
        rateButton.disabled = !checkRequiredFields();
    }

    function generateComments(rating) {
        const commentsContainer = document.getElementById("ratingComments");
        commentsContainer.innerHTML = "";
        let comments = [];
        if (rating <= 2.5) {
            comments = [
                "Drove too fast or recklessly",
                "Ignored traffic rules",
                "Sudden braking or jerky driving",
                "Car was unclean or uncomfortable",
                "Driver was late or caused delays",
                "Distracted while driving",
                "Other"
            ];
        } else if (rating > 2.5 && rating <= 4) {
            comments = [
                "Decent driving but could improve",
                "Followed most traffic rules",
                "Car cleanliness could be better",
                "Minor delays during the trip",
                "Driving was okay but not outstanding",
                "Other"
            ];
        } else {
            comments = [
                "Polite and professional driver",
                "Smooth and safe driving",
                "Followed traffic rules",
                "Clean and comfortable car",
                "Punctual and timely",
                "Attentive to road conditions",
                "Other"
            ];
        }

        comments.forEach(function (comment) {
            const div = document.createElement("div");
            div.className = "comment-option";
            div.textContent = comment;
            div.onclick = function () {
                selectComment(div, comment);
            };
            commentsContainer.appendChild(div);
        });
    }

    function restoreSelectedComments() {
        if (!systemCommentsField) return;
        const saved = systemCommentsField.value;
        if (!saved) return;

        const savedComments = saved.split(',').map(s => s.trim());
        document.querySelectorAll(".comment-option").forEach(function (option) {
            if (savedComments.includes(option.textContent)) {
                option.classList.add("selected");
            }
            if (option.textContent === "Other") {
                const otherSaved = savedComments.find(s => s.startsWith("Other:"));
                if (otherSaved) {
                    option.classList.add("selected");
                    otherCommentField.style.display = "block";
                    otherCommentField.value = otherSaved.substring(6).trim();
                    otherCommentField.required = true; // Make sure it's required when restored
                }
            }
        });

        updateButtonState();
    }

    function updateSystemComments() {
        let selectedComments = Array.from(document.querySelectorAll(".comment-option.selected"))
            .filter(el => el.textContent !== "Other")
            .map(el => el.textContent);
        systemCommentsField.value = selectedComments.join(", ");
    }

    function selectComment(element, comment) {
        element.classList.toggle("selected");
        if (comment === "Other") {
            otherCommentField.style.display = element.classList.contains("selected") ? "block" : "none";
            otherCommentField.required = element.classList.contains("selected");
        }
        updateSystemComments();
        updateButtonState();
    }

    let initialRating = parseFloat(scoreField.value) || 0.0;
    $("#rateYo").rateYo({
        rating: initialRating,
        halfStar: true,
        starWidth: "30px",
        ratedFill: "#F39C12",
        normalFill: "#C0C0C0",
        onSet: function (rating) {
            scoreField.value = rating;
            updateButtonState();
            generateComments(rating);
            setTimeout(restoreSelectedComments, 50);
        }
    });

    if (initialRating > 0) {
        rateButton.disabled = false;
        generateComments(initialRating);
        setTimeout(restoreSelectedComments, 50);
    } else {
        rateButton.disabled = true;
    }

    otherCommentField.addEventListener("input", function () {
        updateButtonState();
    });

    if (numberPlateField) {
        numberPlateField.addEventListener("input", updateButtonState);
    }

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function (position) {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                const locationField = document.getElementById("id_location");
                if (locationField) {
                    locationField.value = `${lat},${lng}`;
                } else {
                    console.error("Location field not found in the form.");
                }
            },
            function (error) {
                alert("Unable to capture location. Please allow location access in your browser settings.");
                console.error("Geolocation error:", error.message);
            },
            { enableHighAccuracy: true }
        );
    } else {
        alert("Geolocation is not supported by your browser.");
        console.error("Geolocation is not supported by this browser.");
    }
});