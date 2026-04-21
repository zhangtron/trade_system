// Login page functionality

const loginForm = document.getElementById('loginForm');
const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('password');
const rememberMeInput = document.getElementById('rememberMe');
const errorMessage = document.getElementById('errorMessage');

// Check if already logged in
function checkExistingAuth() {
    const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
    if (token) {
        // Verify token is still valid
        fetch('/api/auth/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            if (response.ok) {
                // Already logged in, redirect to home
                window.location.href = '/';
            } else {
                // Token invalid, clear it
                localStorage.removeItem('auth_token');
                sessionStorage.removeItem('auth_token');
                localStorage.removeItem('user_info');
                sessionStorage.removeItem('user_info');
            }
        })
        .catch(() => {
            // Error checking auth, clear tokens
            localStorage.removeItem('auth_token');
            sessionStorage.removeItem('auth_token');
            localStorage.removeItem('user_info');
            sessionStorage.removeItem('user_info');
        });
    }
}

// Show error message
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    setTimeout(() => {
        errorMessage.style.display = 'none';
    }, 5000);
}

// Handle login form submission
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = usernameInput.value.trim();
    const password = passwordInput.value;
    const rememberMe = rememberMeInput.checked;

    if (!username || !password) {
        showError('请输入用户名和密码');
        return;
    }

    // Disable form during submission
    const submitButton = loginForm.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    submitButton.textContent = '登录中...';

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username,
                password,
                remember_me: rememberMe
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || '登录失败');
        }

        // Store token
        const storage = rememberMe ? localStorage : sessionStorage;
        storage.setItem('auth_token', data.access_token);
        storage.setItem('user_info', JSON.stringify(data.user));

        // Clear other storage to avoid confusion
        if (rememberMe) {
            sessionStorage.removeItem('auth_token');
            sessionStorage.removeItem('user_info');
        } else {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user_info');
        }

        // Redirect to home page
        window.location.href = '/';

    } catch (error) {
        showError(error.message);
        submitButton.disabled = false;
        submitButton.textContent = '登录';
    }
});

// Check for existing auth on page load
checkExistingAuth();

// Handle Enter key in form
usernameInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        passwordInput.focus();
    }
});

passwordInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        loginForm.dispatchEvent(new Event('submit'));
    }
});
