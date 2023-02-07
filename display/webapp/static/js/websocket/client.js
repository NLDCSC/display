namespace = '/display';

var socket = io(namespace);

$(document).ready(function () {

    // Event handler for new connections.
    socket.on('connect', function () {
        let con_stat = document.getElementById("con_status");
        con_stat.classList.remove("badge-danger");
        con_stat.classList.add("badge-success");
        socket.emit('async_mode');
        let elementsTabArray = DOMRegex(/^tab\_/);

        elementsTabArray.forEach(item => {
            if ($("#" + item.id).hasClass('active')) {
                let current_selected = item.attributes["data-name"].nodeValue;
                socket.emit("change_display_tab", {"data": current_selected})
            }
        });
    });

    socket.on('connect_error', function (err){
        console.log('Connection error due to: ' + err)
        // revert to classic upgrade
        socket.io.opts.transports = ["polling", "websocket"];
    });

    // Event handler for disconnecting connections.
    socket.on('disconnect', function () {
        let con_stat = document.getElementById("con_status");
        con_stat.classList.remove("badge-success");
        con_stat.classList.add("badge-danger");
        $('#async_mode').text("NA");
        $('#ping_pong').text("NA ");
    });

    socket.on('push_all_screenshots', function (msg) {
        if (msg["data"] !== null) {

            let tab_content = $("#content_" + msg["tab_hash"])

            tab_content.html(msg["html_data"])

            msg["data"].forEach(item => {

                let img_content = $("#img_content_" + item.sc_id)
                let mod_time = $("#mod_time_" + item.sc_id)

                if (item.hasOwnProperty('sc_src')) {
                    img_content.attr("src", item.sc_src);
                }

                mod_time.text(item.mod_time);

                if (item.changed === "0") {
                    if (!img_content.hasClass('red-src')) {
                        img_content.addClass('red-src');
                    }
                }

                if (item.changed === "1") {
                    if (img_content.hasClass('red-src')) {
                        img_content.removeClass('red-src');
                    }
                }

                mod_time.toggleClass("active");
                setTimeout(function () {
                    mod_time.toggleClass("active");
                }, 8000);

            })
        }
    });

    socket.on('config_change', function (msg) {

        let flashcontainer = $("#flash-container")
        let flash = $("#flash")

        flash.text("Configuration change detected; rebuilding page....")
        flashcontainer.fadeIn("slow")

        let delay = (Math.floor(Math.random() * 8) * 0.5) * 1000;

        setTimeout(function () {
            socket.emit('rebuild_request')
        }, delay);

    });

    socket.on('rebuild_page', function (msg) {

        let flashcontainer = $("#flash-container")
        let contentdiv = $("#display-content")

        if (msg["data"] !== null) {
            contentdiv.html(msg["data"])
        }

        SetTabEvents();

        let tab_select = $("#tab_" + msg["tab"])

        DestroyScrollingTabs()
        ReEnableDisplayFilter();
        SetKeyDownEvents();

        if (tab_select.length) {
            tab_select.click();
            $(".nav-tabs")
                .scrollingTabs({
                    cssClassLeftArrow: "mdi mdi-arrow-left-bold",
                    cssClassRightArrow: "mdi mdi-arrow-right-bold",
                    disableScrollArrowsOnFullyScrolled: true,
                    bootstrapVersion: 4
                })
                .on("ready.scrtabs", function () {
                    $(".tab-content").show();
                    SetAllEventListeners();

                    setTimeout(() => {
                        $('.nav-tabs').scrollingTabs('scrollToActiveTab');
                    }, 2000);
                });
        } else {
            let elementsTabArray = DOMRegex(/^tab\_/);
            let tab_select = $("#" + elementsTabArray[0].id);
            tab_select.click();
            $(".nav-tabs")
                .scrollingTabs({
                    cssClassLeftArrow: "mdi mdi-arrow-left-bold",
                    cssClassRightArrow: "mdi mdi-arrow-right-bold",
                    disableScrollArrowsOnFullyScrolled: true,
                    bootstrapVersion: 4
                })
                .on("ready.scrtabs", function () {
                    $(".tab-content").show();
                    SetAllEventListeners();
                });
        }

        flashcontainer.fadeOut("slow");
    });

    socket.on('show_screenshot', function (msg) {
        var modal = document.getElementById("the-modal");

        var modalImg = document.getElementById("img-placeholder");
        var captionText = document.getElementById("caption");

        modal.style.display = "block";
        modalImg.src = msg["data"];
        captionText.innerHTML = msg["url"];

        // Get the <span> element that closes the modal
        var span = document.getElementsByClassName("close")[0];

        span.onclick = function () {
            modal.style.display = "none";
        }

    });

    socket.on('con_request', function (msg, cb) {

        if (cb) {
            cb();
        }
    });

    socket.on('async_request', function (msg, cb) {

        $('#async_mode').text(msg.data);

        if (cb) {
            cb(client_id = socket.sid, data = msg.data);
        }
    });

    // Interval function that tests message latency by sending a "ping"
    // message. The server then responds with a "pong" message and the
    // round trip time is measured.
    let ping_pong_times = [];
    let start_time;
    window.setInterval(function () {
        start_time = (new Date).getTime();
        socket.emit('my_ping');
    }, 1000);

    // Handler for the "pong" message. When the pong is received, the
    // time from the ping is stored, and the average of the last 30
    // samples is average and displayed.
    socket.on('my_pong', function () {
        let latency = (new Date).getTime() - start_time;
        ping_pong_times.push(latency);
        ping_pong_times = ping_pong_times.slice(-30); // keep last 30 samples
        let sum = 0;
        ping_pong_times.forEach(item => {
            sum += item;
        });
        $('#ping_pong').text(Math.round(10 * sum / ping_pong_times.length) / 10 + " ");
    });

});