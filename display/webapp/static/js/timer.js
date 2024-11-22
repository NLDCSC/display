const FULL_DASH_ARRAY = 283;

let timePassed = 0;
let timeLeft = TIME_LIMIT;
let timerInterval = null;
let remainingPathColor = "green";

function onTimesUp() {
    clearInterval(timerInterval);
    SwitchToNextTab();
}

function getColorCodes(wrn_treshold, alert_treshold) {
    return {
        info: {
            color: "green"
        },
        warning: {
            color: "orange",
            threshold: wrn_treshold
        },
        alert: {
            color: "red",
            threshold: alert_treshold
        }
    }
}

function startTimer() {
    timePassed = 0;

    let timer_setting = get_cookie("display-timer")
    if (timer_setting !== "") {
        TIME_LIMIT = parseInt(timer_setting);
    }

    timeLeft = TIME_LIMIT;
    timerInterval = null;

    let color_codes = getColorCodes(TIME_LIMIT / 2, TIME_LIMIT / 4)

    remainingPathColor = color_codes.info.color;

    document.getElementById("app").innerHTML =
        `
                <div id="display_timer" class="base-timer set-pointer">
                  <svg class="base-timer__svg" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                    <g class="base-timer__circle">
                      <circle class="base-timer__path-elapsed" cx="50" cy="50" r="45"></circle>
                      <path
                        id="base-timer-path-remaining"
                        stroke-dasharray="283"
                        class="base-timer__path-remaining ${remainingPathColor}"
                        d="
                          M 50, 50
                          m -45, 0
                          a 45,45 0 1,0 90,0
                          a 45,45 0 1,0 -90,0
                        "
                      ></path>
                    </g>
                  </svg>
                  <span id="base-timer-label" class="base-timer__label">${formatTime(timeLeft)}</span>
                </div>
        `;


    timerInterval = setInterval(() => {
        timePassed = timePassed += 1;
        timeLeft = TIME_LIMIT - timePassed;
        document.getElementById("base-timer-label").innerHTML = formatTime(
            timeLeft
        );
        setCircleDasharray();
        setRemainingPathColor(timeLeft);

        if (timeLeft === 0) {
            onTimesUp();
        }
    }, 1000);
}


function formatTime(time) {
    const minutes = Math.floor(time / 60);
    let seconds = time % 60;

    if (seconds < 10) {
        seconds = `0${seconds}`;
    }

    return `${minutes}:${seconds}`;
}

function setRemainingPathColor(timeLeft) {
    const { alert, warning, info } = getColorCodes(TIME_LIMIT / 2, TIME_LIMIT / 4);
    if (timeLeft <= alert.threshold) {
        document
            .getElementById("base-timer-path-remaining")
            .classList.remove(warning.color);
        document
            .getElementById("base-timer-path-remaining")
            .classList.add(alert.color);
    } else if (timeLeft <= warning.threshold) {
        document
            .getElementById("base-timer-path-remaining")
            .classList.remove(info.color);
        document
            .getElementById("base-timer-path-remaining")
            .classList.add(warning.color);
    }
}

function calculateTimeFraction() {
    const rawTimeFraction = timeLeft / TIME_LIMIT;
    return rawTimeFraction - (1 / TIME_LIMIT) * (1 - rawTimeFraction);
}

function setCircleDasharray() {
    const circleDasharray = `${(
        calculateTimeFraction() * FULL_DASH_ARRAY
    ).toFixed(0)} 283`;
    document
        .getElementById("base-timer-path-remaining")
        .setAttribute("stroke-dasharray", circleDasharray);
}
