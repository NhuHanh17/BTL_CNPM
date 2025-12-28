document.addEventListener("DOMContentLoaded", function() {
    const now = new Date();

    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const today = `${year}-${month}-${day}`;
    document.getElementById("inputDate").value = today;

    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const currentTime = `${hours}:${minutes}`;
    document.getElementById("inputTime").value = currentTime;

    if (typeof calculateTotal === "function") {
        calculateTotal();
    }
});


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

function handleRoomAction(id, name, isAvailable, isLockedSoon, nextTime, bookingId) {
    const panel = document.getElementById("invoice-panel");
    
    if (!isAvailable) {
        panel.innerHTML = '<div class="text-center p-5"><div class="spinner-border text-info"></div></div>';
        fetch(`/api/get-invoice/${id}`)
            .then((res) => res.text())
            .then((html) => { panel.innerHTML = html; });
    } else {
        if (isLockedSoon) {
            panel.innerHTML = `
                <div class="p-4 text-center">
                    <h5 class="text-white">${name}</h5>
                    <div class="alert alert-warning small">Khách đặt trước: <b>${nextTime}</b></div>
                    <a href="/cashier/open-room/${bookingId}" class="btn btn-warning w-100 fw-bold">XÁC NHẬN NHẬN PHÒNG</a>
                </div>`;
        } else {
            panel.innerHTML = `
                <form action="/cashier/quick-book" method="POST" class="p-4 text-center">
                    <input type="hidden" name="room_id" value="${id}">
                    <h5 class="text-white">${name}</h5>
                    <div class="mb-3 mt-3 text-start">
                        <label class="form-label text-secondary small">Nhập số lượng khách:</label>
                        <input type="number" name="customer_quantity" class="form-control bg-dark text-white border-secondary" value="1" min="1">
                    </div>
                    <button type="submit" class="btn btn-success w-100 fw-bold">MỞ PHÒNG TRỰC TIẾP</button>
                </form>`;
        }
    }
}


function stepper(inputId, step, maxVal = 999) {
    let input = document.getElementById(inputId);
    if (input) {
        let currentVal = parseInt(input.value) || 1;
        let newVal = currentVal + step;

     
        if (newVal >= 1 && newVal <= maxVal) {
            input.value = newVal;
        } else if (newVal > maxVal) {
            alert("Số lượng yêu cầu đã đạt giới hạn tồn kho (" + maxVal + ")");
        }
    }
}

function showAddService(roomId) {
    document.getElementById('currentRoomId').value = roomId;
    var myModal = new bootstrap.Modal(document.getElementById('addServiceModal'));
    myModal.show();
}

function addServiceToBill(serviceId) {
    const roomId = document.getElementById('currentRoomId').value;
    const quantity = parseInt(document.getElementById('qty-' + serviceId).value);

    if (!roomId) {
        alert("Vui lòng chọn phòng trước!");
        return;
    }

    fetch('/api/add-service', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            'room_id': roomId,
            'service_id': serviceId,
            'quantity': quantity
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 200) {
            alert(data.message);
            location.reload(); // Load lại để thấy hóa đơn mới
        } else {
            alert("Lỗi: " + data.message);
        }
    })
    .catch(err => alert("Lỗi kết nối server!"));
}
