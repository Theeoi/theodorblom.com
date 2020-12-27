<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <meta name="description" content="Trying out HTML/CSS/JS and MySQL!">
        <meta name=viewport content="width=device-width, initial-scale=1.0">
        <title>TB - Timer</title>
    
        <link rel="stylesheet" type="text/css" href="../resources/css/main.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css"> <!-- Imports Icons --> 
    </head>

<?php
    require "../header.php";
?>

<main>
    <div class="main-content" style="text-align: center">
        <h2>Random Timer</h2>
        <br>
        <p>Starts a timer with a random time within the set interval.</p>

        <button id="timer-start" class="timer-btn">Start Timer</button>
        <button id="timer-cancel" class="timer-btn" hidden>Cancel Timer</button>
    
        <div id="tick-tock" hidden>
            <p>tick tock<span id="timer-loading"></span></p>
            <br> 
        </div>
     
        <div id="timer-done" hidden>
            <h4>TIMER IS DONE!</h4>
            <p>Elapsed time: <span id="elapsedTime"></span> seconds.</p>
            <br>
        </div>

        <p>
            <label>
                Minimum time:
                <input type="number" id="timer-min" min="1" value="1">
                seconds
            </label>
            <br>
            <label>
                Maximum time:
                <input type="number" id="timer-max" min="2" value="60">
                seconds
            </label>
            <br><br>
            <b>Timer end</b><br>
            <label>
                <input type="checkbox" id="timer-sound" checked> 
                Play sound
            </label>
        </p>
    </div>
    <script src="../resources/js/timer.js"></script>
</main>

<?php
    require "../footer.php";
?>
