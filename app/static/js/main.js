// 1. Truyền ID phòng vào Modal khi click
function openBookingModal(roomId, roomName) {
    document.getElementById('modalRoomId').value = roomId;
    document.getElementById('modalRoomName').innerText = roomName;
    var myModal = new bootstrap.Modal(document.getElementById('bookingModal'));
    myModal.show();
}

// 2. Gửi form bằng AJAX để không load lại trang
document.getElementById('bookingForm').onsubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    
    const response = await fetch('/api/book-room', {
        method: 'POST',
        body: formData
    });
    
    const result = await response.json();
    if(result.status === 'success') {
        alert('Chúc mừng Han! ' + result.message);
        location.reload(); // Load lại để cập nhật màu Badge trạng thái
    }
};