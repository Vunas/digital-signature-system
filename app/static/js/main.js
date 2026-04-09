// --- QUẢN LÝ API VÀ TOKEN ---
const API_URL = ''; // Để trống vì FE và BE chạy chung host

// Hàm gọi API tự động đính kèm Token
async function fetchAPI(endpoint, method = 'GET', body = null, isFormData = false) {
    const token = localStorage.getItem('access_token');
    
    const headers = {};
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    if (!isFormData) {
        headers['Content-Type'] = 'application/json';
    }

    const options = { method, headers };
    
    if (body) {
        options.body = isFormData ? body : JSON.stringify(body);
    }

    try {
        const response = await fetch(`${API_URL}${endpoint}`, options);
        
        // Nếu token hết hạn (401), văng ra trang login
        if (response.status === 401 && endpoint !== '/auth/login') {
            logout();
            return null;
        }

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || data.message || 'Lỗi hệ thống');
        }
        return data;
    } catch (error) {
        // Hiện popup lỗi xịn xò
        Swal.fire({
            icon: 'error',
            title: 'Thất bại',
            text: error.message,
            confirmButtonColor: '#4f46e5'
        });
        throw error;
    }
}

// --- HÀM TIỆN ÍCH UI ---
function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('username');
    window.location.href = '/login';
}

function showToast(message, icon = 'success') {
    const Toast = Swal.mixin({
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true,
    });
    Toast.fire({ icon: icon, title: message });
}

// Kiểm tra đăng nhập khi vào trang (trừ login/register)
document.addEventListener("DOMContentLoaded", () => {
    const path = window.location.pathname;
    const token = localStorage.getItem('access_token');
    
    if (!token && path !== '/login' && path !== '/register') {
        window.location.href = '/login';
    }
    
    // Đổ tên user lên header
    const usernameDisplay = document.getElementById('username-display');
    if (usernameDisplay && localStorage.getItem('username')) {
        usernameDisplay.textContent = localStorage.getItem('username');
    }
});