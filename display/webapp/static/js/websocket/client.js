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
                let tab_hash = item.attributes["data-hash"].nodeValue;
                socket.emit("change_display_tab", {"tab_name": current_selected, "tab_hash": tab_hash})
            }
        });
    });

    socket.on('connect_error', function (err){
        console.log('Connection error due to: ' + err)
    });

    // Event handler for disconnecting connections.
    socket.on('disconnect', function () {
        let con_stat = document.getElementById("con_status");
        con_stat.classList.remove("badge-success");
        con_stat.classList.add("badge-danger");
        $('#async_mode').text("NA");
        $('#ping_pong').text("NA ");
    });

    socket.on('push_all_screenshots', function (msg, cb) {

        if ("data" in msg) {

            let tab_hash = msg["tab_hash"]
            let tab_content = $("#content_" + tab_hash)

            try {
                msg["data"].forEach(item => {

                    let img_content = $("#img_content_" + tab_hash + '_' + item.sc_id)
                    let defaced_button = $("#defaced_" + tab_hash + '_' + item.sc_id)
                    let mod_time = $("#mod_time_" + tab_hash + '_' + item.sc_id)
                    let sc_header = $("#sc_header_" + tab_hash + '_' + item.sc_id)

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

                    if (item.defaced === "1") {
                        SetDefaced(defaced_button, "1");
                        if (!img_content.hasClass('assessed_defaced')) {
                            img_content.addClass('assessed_defaced');
                        }
                    }

                    if (item.defaced === "0") {
                        SetDefaced(defaced_button, "0");
                        if (img_content.hasClass('assessed_defaced')) {
                            img_content.removeClass('assessed_defaced');
                        }
                    }

                    mod_time.toggleClass("active");
                    if (window.FULL_SCREEN) {
                        if (!sc_header.hasClass("active")){
                            sc_header.toggleClass("active")
                        }
                    }
                    setTimeout(function () {
                        mod_time.toggleClass("active");
                        if (window.FULL_SCREEN) {
                            sc_header.toggleClass("active")
                        }
                    }, 8000);

                })
            } catch (e) {

            }

            SetTabContentFilter();

            $("#tab_change_loading").hide()
            tab_content.removeClass("grey_out")

            SetAllEventListeners();
            JustifyTabContent(tab_hash);

            if (window.FULL_SCREEN) {
                AdjustLayoutFullscreen()
            }

        } else if ("html_data" in msg) {

            let tab_hash = msg["tab_hash"]
            let tab_content = $("#content_" + tab_hash)

            if (tab_content[0].firstElementChild.id === "loading_spinner") {
                tab_content.html(msg["html_data"])
            }

            let images_containers = $('div[id^=do_open-sc_'+ tab_hash +']')

            images_containers.each(function(value){
                let isLastElement = value === images_containers.length - 1;

                if (isLastElement) {
                    socket.emit("get_hash_screenshot", images_containers[value].attributes["data-id"].nodeValue, tab_hash, isLastElement)
                } else {
                    socket.emit("get_hash_screenshot", images_containers[value].attributes["data-id"].nodeValue, tab_hash)
                }

            })

            SetAllEventListeners();
            JustifyTabContent(tab_hash);

            if (window.FULL_SCREEN) {
                AdjustLayoutFullscreen()
            }
        }

        $('.template-row').hide();

        if (cb) {
            cb(client_id = socket.sid, data = msg["tab_hash"]);
        }

    });

    socket.on('push_hash_screenshot', function (msg, cb) {

        if (msg["url_screenshot"] !== 'undefined') {

            let tab_content = $("#content_" + msg["tab_hash"])

            let img_content = $("#img_content_" + msg["tab_hash"] + '_' + msg["url_screenshot"].sc_id)
            let defaced_button = $("#defaced_" + msg["tab_hash"] + '_' + msg["url_screenshot"].sc_id)
            let mod_time = $("#mod_time_" + msg["tab_hash"] + '_' + msg["url_screenshot"].sc_id)

            if (msg["url_screenshot"].hasOwnProperty('sc_src')) {
                img_content.attr("src", msg["url_screenshot"].sc_src);
            }

            mod_time.text(msg["url_screenshot"].mod_time);

            if (msg["url_screenshot"].changed === "0") {
                if (!img_content.hasClass('red-src')) {
                    img_content.addClass('red-src');
                }
            }

            if (msg["url_screenshot"].changed === "1") {
                if (img_content.hasClass('red-src')) {
                    img_content.removeClass('red-src');
                }
            }

            if (msg["url_screenshot"].defaced === "1") {
                SetDefaced(defaced_button, "1");
                if (!img_content.hasClass('assessed_defaced')) {
                    img_content.addClass('assessed_defaced');
                }
            }

            if (msg["url_screenshot"].defaced === "0") {
                SetDefaced(defaced_button, "0");
                if (img_content.hasClass('assessed_defaced')) {
                    img_content.removeClass('assessed_defaced');
                }
            }

            if (cb) {
                cb(client_id = socket.sid, data = msg["tab_hash"]);
            }

            if (msg["last_element"]) {
                SetTabContentFilter();

                $("#tab_change_loading").hide()
                tab_content.removeClass("grey_out")

                if (window.FULL_SCREEN === true) {
                    AdjustLayoutFullscreen();
                }
                JustifyTabContent(msg["tab_hash"]);
            }
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
        let tabselectordiv = $("#tab-selector")

        if (msg["data"] !== null) {
            contentdiv.html(msg["data"]["content"])
            tabselectordiv.html(msg["data"]["tab_selector"])
        }

        SetTabEvents();

        let tab_select = $("#tab_" + msg["tab"])

        DestroyScrollingTabs()
        ReEnableDisplayFilter();
        SetKeyDownEvents();

        SetTabContentFilter();

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
        JustifyTabContent(msg["tab"]);

        if (window.FULL_SCREEN === true) {
            AdjustLayoutFullscreen();
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

        $("#do_open-sc_" + msg["tab-hash"] + "_" + msg["url-hash"]).css("cursor", "pointer");

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
