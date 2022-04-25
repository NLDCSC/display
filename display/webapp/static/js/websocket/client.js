namespace = '/display';

var socket = io(namespace);

$(document).ready(function () {

    // Event handler for new connections.
    // The callback function is invoked when a connection with the
    // server is established.
    socket.on('connect', function () {
        var con_stat = document.getElementById("con_status");
        con_stat.classList.remove("badge-danger");
        con_stat.classList.add("badge-success");
        socket.emit('async_mode');
    });

    socket.on('disconnect', function () {
        var con_stat = document.getElementById("con_status");
        con_stat.classList.remove("badge-success");
        con_stat.classList.add("badge-danger");
        $('#async_mode').text("NA");
        $('#ping_pong').text("NA ");
    });

    socket.on('con_request', function (msg, cb) {

        if (cb) {
            cb();
        }
    });

    socket.on('async_request', function (msg, cb) {

        $('#async_mode').text(msg.data);

        if (cb) {

            var response = {
                client_id: socket.sid,
                data: msg.data
            };
            cb(client_id = socket.sid, data = msg.data);
        }
    });

    // Interval function that tests message latency by sending a "ping"
    // message. The server then responds with a "pong" message and the
    // round trip time is measured.
    var ping_pong_times = [];
    var start_time;
    window.setInterval(function () {
        start_time = (new Date).getTime();
        socket.emit('my_ping');
    }, 1000);

    // Handler for the "pong" message. When the pong is received, the
    // time from the ping is stored, and the average of the last 30
    // samples is average and displayed.
    socket.on('my_pong', function () {
        var latency = (new Date).getTime() - start_time;
        ping_pong_times.push(latency);
        ping_pong_times = ping_pong_times.slice(-30); // keep last 30 samples
        var sum = 0;
        for (var i = 0; i < ping_pong_times.length; i++)
            sum += ping_pong_times[i];
        $('#ping_pong').text(Math.round(10 * sum / ping_pong_times.length) / 10 + " ");
    });

});