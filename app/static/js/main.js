// --- QUẢN LÝ API VÀ TOKEN ---
const API_URL = "";

let isRefreshing = false;
let refreshSubscribers = [];

function onRefreshed(isSuccess) {
  refreshSubscribers.forEach((callback) => callback(isSuccess));
  refreshSubscribers = [];
}

async function fetchAPI(
  endpoint,
  method = "GET",
  body = null,
  isFormData = false,
) {
  const headers = {};
  if (!isFormData) {
    headers["Content-Type"] = "application/json";
  }

  // QUAN TRỌNG: "same-origin" hoặc "include" để trình duyệt tự động đính kèm HttpOnly Cookies
  const options = { method, headers, credentials: "same-origin" };

  if (body) {
    options.body = isFormData ? body : JSON.stringify(body);
  }

  try {
    let response = await fetch(`${API_URL}${endpoint}`, options);

    // NẾU LỖI 401 VÀ KHÔNG PHẢI LÀ API LOGIN HAY REFRESH
    if (response.status === 401 && !endpoint.includes("/auth/")) {
      // Xếp hàng các request bị fail trong lúc đang chờ refresh
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          refreshSubscribers.push(async (isSuccess) => {
            if (isSuccess) {
              resolve(await fetchAPI(endpoint, method, body, isFormData));
            } else {
              reject(new Error("Phiên đăng nhập hết hạn"));
            }
          });
        });
      }

      isRefreshing = true;
      try {
        // Gọi API refresh token
        const refreshRes = await fetch(`${API_URL}/auth/refresh`, {
          method: "POST",
          credentials: "same-origin",
        });

        if (refreshRes.ok) {
          isRefreshing = false;
          onRefreshed(true);

          // Thử gọi lại request ban đầu sau khi refresh thành công
          response = await fetch(`${API_URL}${endpoint}`, options);
        } else {
          throw new Error("Refresh failed");
        }
      } catch (err) {
        isRefreshing = false;
        onRefreshed(false);
        forceLogout();
        return null;
      }
    }

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || data.message || "Lỗi hệ thống");
    }
    return data;
  } catch (error) {
    Swal.fire({
      icon: "error",
      title: "Thất bại",
      text: error.message,
      confirmButtonColor: "#4f46e5",
    });
    throw error;
  }
}

// --- HÀM TIỆN ÍCH UI ---
async function forceLogout() {
  // Gọi backend để xóa HttpOnly Cookies
  try {
    await fetch(`${API_URL}/auth/logout`, {
      method: "POST",
      credentials: "same-origin",
    });
  } catch (e) {}

  localStorage.removeItem("username");
  window.location.href = "/login";
}
window.logout = forceLogout;

function showToast(message, icon = "success") {
  const Toast = Swal.mixin({
    toast: true,
    position: "top-end",
    showConfirmButton: false,
    timer: 3000,
    timerProgressBar: true,
  });
  Toast.fire({ icon: icon, title: message });
}

// Kiểm tra khi vào trang
document.addEventListener("DOMContentLoaded", () => {
  const username = localStorage.getItem("username");
  const path = window.location.pathname;

  if (!username && path !== "/login" && path !== "/register") {
    window.location.href = "/login";
  }

  const usernameDisplay = document.getElementById("username-display");
  if (usernameDisplay && username) {
    usernameDisplay.textContent = username;
  }
});
