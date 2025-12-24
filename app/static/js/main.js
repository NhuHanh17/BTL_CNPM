    document.addEventListener('DOMContentLoaded', function() {
        document.getElementById('inputDate').valueAsDate = new Date();
        
        let now = new Date();
        let timeString = now.toTimeString().slice(0, 5); 
        document.getElementById('inputTime').value = timeString;

        calculateTotal();
    });

    function adjustDuration(delta) {
        let input = document.getElementById('inputDuration');
        let val = parseInt(input.value) || 0;
        val += delta;
        if (val < 1) val = 1;
        if (val > 12) val = 12; 
        input.value = val;
        
        calculateTotal(); 
    }

    function calculateTotal() {
        let basePrice = parseInt(document.getElementById('basePrice').value);
        let duration = parseInt(document.getElementById('inputDuration').value);
        
        let total = basePrice * duration;
        
        // Format tiền Việt
        document.getElementById('totalPrice').innerText = new Intl.NumberFormat('vi-VN').format(total) + 'đ';
    }