
// Password toggle and auth form validation
document.addEventListener("DOMContentLoaded", function () {
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    document.querySelectorAll(".password-toggle").forEach(function (btn) {
        btn.addEventListener("click", function () {
            const targetId = btn.getAttribute("data-target");
            const input = document.getElementById(targetId);
            const icon = btn.querySelector("i");

            if (!input) return;

            if (input.type === "password") {
                input.type = "text";
                icon.classList.remove("bi-eye");
                icon.classList.add("bi-eye-slash");
            } else {
                input.type = "password";
                icon.classList.remove("bi-eye-slash");
                icon.classList.add("bi-eye");
            }
        });
    });

    function setError(id, message) {
        const el = document.getElementById(id);
        if (el) el.textContent = message;
    }

    function clearErrors(ids) {
        ids.forEach(id => setError(id, ""));
    }

    const loginForm = document.getElementById("loginForm");
    if (loginForm) {
        loginForm.addEventListener("submit", function (e) {
            clearErrors(["loginEmailError", "loginPasswordError"]);

            const email = document.getElementById("loginEmail").value.trim();
            const password = document.getElementById("loginPassword").value.trim();
            let valid = true;

            if (!email) {
                setError("loginEmailError", "Email is required.");
                valid = false;
            } else if (!emailPattern.test(email)) {
                setError("loginEmailError", "Enter a valid email address.");
                valid = false;
            }

            if (!password) {
                setError("loginPasswordError", "Password is required.");
                valid = false;
            } else if (password.length < 6) {
                setError("loginPasswordError", "Password must be at least 6 characters.");
                valid = false;
            }

            if (!valid) e.preventDefault();
        });
    }

    const registerForm = document.getElementById("registerForm");
    if (registerForm) {
        registerForm.addEventListener("submit", function (e) {
            clearErrors([
                "fullNameError",
                "registerEmailError",
                "phoneError",
                "registerPasswordError",
                "confirmPasswordError"
            ]);

            const fullName = document.getElementById("fullName").value.trim();
            const email = document.getElementById("registerEmail").value.trim();
            const phone = document.getElementById("phoneNumber").value.trim();
            const password = document.getElementById("registerPassword").value.trim();
            const confirmPassword = document.getElementById("confirmPassword").value.trim();

            let valid = true;

            if (!fullName) {
                setError("fullNameError", "Full name is required.");
                valid = false;
            } else if (fullName.length < 3) {
                setError("fullNameError", "Full name must be at least 3 characters.");
                valid = false;
            }

            if (!email) {
                setError("registerEmailError", "Email is required.");
                valid = false;
            } else if (!emailPattern.test(email)) {
                setError("registerEmailError", "Enter a valid email address.");
                valid = false;
            }

            if (phone && !/^[0-9]{10}$/.test(phone)) {
                setError("phoneError", "Phone number must be 10 digits.");
                valid = false;
            }

            if (!password) {
                setError("registerPasswordError", "Password is required.");
                valid = false;
            } else if (password.length < 6) {
                setError("registerPasswordError", "Password must be at least 6 characters.");
                valid = false;
            } else if (!/[A-Za-z]/.test(password) || !/[0-9]/.test(password)) {
                setError("registerPasswordError", "Password must contain letters and numbers.");
                valid = false;
            }

            if (!confirmPassword) {
                setError("confirmPasswordError", "Confirm password is required.");
                valid = false;
            } else if (password !== confirmPassword) {
                setError("confirmPasswordError", "Passwords do not match.");
                valid = false;
            }

            if (!valid) e.preventDefault();
        });
    }
});
