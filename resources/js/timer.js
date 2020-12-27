var timeout = null;
var dots = null;
var sound = new Audio();
sound.volume = 1;
sound.muted = false;
sound.src = "../resources/mp3/GongGong.mp3"

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
    document.getElementById("tick-tock").hidden = false;

    clearInterval(dots);
    var dots = window.setInterval( function() {
        var tick = document.getElementById("timer-loading");
        if ( tick.innerHTML.length >= 3 ) 
            tick.innerHTML = "";
        else 
            tick.innerHTML += ".";
    }, 500);

    clearTimeout(timeout);
    timeout = setTimeout(function() {
        if (document.getElementById("timer-sound").checked) {
            sound.play();
        }
        document.getElementById("timer-done").hidden = false;
        document.getElementById("tick-tock").hidden = true;
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
    clearInterval(dots);
    document.getElementById("timer-start").hidden = false;
    document.getElementById("timer-cancel").hidden = true;
    document.getElementById("tick-tock").hidden = true;
    document.getElementById("timer-done").hidden = true;
}
