function adjustDuration(delta) {
  let input = document.getElementById("inputDuration");
  let val = parseInt(input.value) || 0;
  val += delta;
  if (val < 1) val = 1;
  if (val > 12) val = 12;
  input.value = val;

  calculateTotal();
}

function calculateTotal() {
  let basePrice = parseInt(document.getElementById("basePrice").value);
  let duration = parseInt(document.getElementById("inputDuration").value);

  let total = basePrice * duration;

  document.getElementById("totalPrice").innerText =
    new Intl.NumberFormat("vi-VN").format(total) + "đ";
}

document.addEventListener("DOMContentLoaded", function () {
  const flashMessages = document.querySelectorAll(".flash-item");

  flashMessages.forEach(function (message) {
    setTimeout(function () {
      message.style.transition = "opacity 0.5s ease";
      message.style.opacity = "0";

      setTimeout(function () {
        message.remove();
      }, 500);
    }, 3000);
  });
});

function filterRooms() {
  const q = document.getElementById("searchRoom").value.toLowerCase();
  const cap = parseInt(document.getElementById("inputCapacity").value) || 0;
  const status = document.getElementById("filterStatus").value;
  const items = document.querySelectorAll(".room-item");

  items.forEach((item) => {
    const isMatchName = item.getAttribute("data-name").includes(q);
    const isMatchCap = parseInt(item.getAttribute("data-capacity")) >= cap;
    const isMatchStatus =
      status === "all" || item.getAttribute("data-status") === status;

    item.style.display =
      isMatchName && isMatchCap && isMatchStatus ? "block" : "none";
  });
}

function showQuickBook(id, name) {
  document.getElementById("modal_room_id").value = id;
  document.getElementById("room_name_modal").innerText = name;
  new bootstrap.Modal(document.getElementById("quickBookModal")).show();
}

function handleRoomAction(id, name, isAvailable, isLockedSoon, nextTime) {
  const panel = document.getElementById("invoice-panel");
  if (!isAvailable) {
    panel.innerHTML =
      '<div class="text-center p-5"><div class="spinner-border text-info"></div></div>';
    fetch(`/api/get-invoice/${id}`)
      .then((res) => res.text())
      .then((html) => {
        panel.innerHTML = html;
      });
  } else {
    if (isLockedSoon) {
      panel.innerHTML = `
                <div class="p-4 text-center">
                    <i class="fa-solid fa-clock-rotate-left fs-1 text-warning mb-3"></i>
                    <h5 class="text-white">${name}</h5>
                    <div class="alert alert-warning small">Có khách đặt lúc ${nextTime}</div>
                </div>`;
    } else {
      panel.innerHTML = `
                <form action="/cashier/quick-book" method="POST" class="p-4 text-center">
                    <input type="hidden" name="room_id" value="${id}">
                    <i class="fa-solid fa-door-open fs-1 text-success mb-3"></i>
                    <h5 class="text-white">${name}</h5>
                    <div class="mb-3 mt-3 text-start">
                        <label class="form-label text-secondary small">Số lượng khách:</label>
                        <input type="number" name="customer_quantity" class="form-control form-control-sm bg-dark text-white border-secondary" value="1" min="1">
                    </div>
                    <button type="submit" class="btn btn-success w-100 fw-bold">MỞ PHÒNG NGAY</button>
                </form>`;
    }
  }
}
