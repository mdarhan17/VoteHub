document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".password-toggle").forEach(function (btn) {
        btn.addEventListener("click", function () {
            const targetId = btn.getAttribute("data-target");
            const input = document.getElementById(targetId);
            const icon = btn.querySelector("i");

            if (!input || !icon) return;

            if (input.type === "password") {
                input.type = "text";
                icon.classList.remove("bi-eye-fill");
                icon.classList.add("bi-eye-slash-fill");
            } else {
                input.type = "password";
                icon.classList.remove("bi-eye-slash-fill");
                icon.classList.add("bi-eye-fill");
            }
        });
    });
});
