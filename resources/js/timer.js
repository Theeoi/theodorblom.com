var timeout = null;
var sound = new Audio();
sound.volume = 0;
sound.muted = true;
sound.src = "../resources/mp3/timer.mp3"

document.getElementById("timer-start").addEventListener("click", startTimer);

function startTimer() {
    
    var min = parseInt(document.getElementById("timer-min").value, 10);
    var max = parseInt(document.getElementById("timer-max").value, 10);

    if (min < 1) {
		min = 1;
	}
	if (max < 2) {
		max = min + 1;
	}
	if (min > max) {
		var temp = max;
		max = min;
		min = temp;
	}

    var timer = getRandom(min, max);
    document.getElementById("timer-start").hidden = true;
    document.getElementById("timer-cancel").hidden = false;

    clearTimeout(timeout);
    timeout = setTimeout(function() {
        document.getElementById("timer-done").hidden = false;
        document.getElementById("elapsedTime").innerText = timer;
    }, timer * 1000);
}

window.addEventListener("click", function() {
    if (!document.getElementById("timer-done").hidden) {
        reset();
    }
});

function getRandom(min, max) {
    min = parseInt(min, 10);
    max = parseInt(max, 10);

    return Math.floor(Math.random() * (max - min + 1)) + min;
}

document.getElementById("timer-cancel").addEventListener("click", function() {
    reset();
});

function reset() {
    clearTimeout(timeout);
    document.getElementById("timer-start").hidden = false;
    document.getElementById("timer-cancel").hidden = true;
    document.getElementById("timer-done").hidden = true;
}
