
document.addEventListener("DOMContentLoaded", function () {

    // Validate the internship search form only.
    const profileField = document.querySelector(
        'input[name="qualification"], select[name="qualification"], textarea[name="qualification"]'
    );

    if (profileField) {
        const profileForm = profileField.closest("form");

        if (
            profileForm &&
            profileForm.id !== "studentProfileForm"
        ) {
            profileForm.addEventListener("submit", function (event) {
                const fields = [
                    "qualification",
                    "field",
                    "skills",
                    "location",
                    "interests"
                ];

                const hasValue = fields.some(function (name) {
                    const input = profileForm.elements.namedItem(name);
                    return input && input.value.trim() !== "";
                });

                if (!hasValue) {
                    event.preventDefault();
                    alert(
                        "Please enter at least one profile detail before searching."
                    );
                }
            });
        }
    }

    // Profile picture preview
    const pictureInput = document.getElementById("profile_picture");
    const picturePreview = document.getElementById("picturePreview");

    if (pictureInput && picturePreview) {
        pictureInput.addEventListener("change", function () {
            const file = this.files[0];

            if (!file) {
                return;
            }

            const allowedTypes = ["image/jpeg", "image/png"];

            if (!allowedTypes.includes(file.type)) {
                alert("Please select a JPG or PNG image.");
                this.value = "";
                return;
            }

            if (file.size > 3 * 1024 * 1024) {
                alert("Image size must be less than 3 MB.");
                this.value = "";
                return;
            }

            picturePreview.src = URL.createObjectURL(file);
        });
    }

    // Confirm profile picture removal
    const removePictureForm = document.getElementById("removePictureForm");

    if (removePictureForm) {
        removePictureForm.addEventListener("submit", function (event) {
            if (!confirm("Are you sure you want to remove your profile picture?")) {
                event.preventDefault();
            }
        });
    }
});
