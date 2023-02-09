const display_cookie = CookieList("display_filter");

function SetAllEventListeners() {
    SetTabEvents();

    let elementsImgArray = DOMRegex(/^img\_content\_/);

    elementsImgArray.forEach(function (elem) {
        let my_id = elem.attributes["data-id"].nodeValue;
        let action_elem = $("#actions_" + my_id);
        let target_elem = $("#" + elem.id);

        target_elem.hover(
            function () {
                action_elem.show();
            },
            function () {
                action_elem.hide();
            }
        );
    });

    let elementsCSArray = DOMRegex(/^create\_screenshot\_/);

    elementsCSArray.forEach(function (elem) {
        let my_id = elem.attributes["data-id"].nodeValue;
        let target_elem = $("#" + elem.id);
        let action_elem = $("#actions_" + my_id);

        target_elem.hover(
            function () {
                action_elem.show();
            },
            function () {
                action_elem.hide();
            }
        );

        elem.addEventListener("click", CreateCustomScreenshot);
    });

    let elementsClipArray = DOMRegex(/^do\_open-sc\_/);

    elementsClipArray.forEach(function (elem) {
        let my_id = elem.attributes["data-id"].nodeValue;
        let target_elem = $("#" + elem.id);
        let action_elem = $("#actions_" + my_id);

        target_elem.hover(
            function () {
                action_elem.show();
            },
            function () {
                action_elem.hide();
            }
        );

        elem.addEventListener("click", OpenScreenshot);
    });

    let elementsDownloadArray = DOMRegex(/^do\_download\_/);

    elementsDownloadArray.forEach(function (elem) {
        let my_id = elem.attributes["data-id"].nodeValue;
        let target_elem = $("#" + elem.id);
        let action_elem = $("#actions_" + my_id);

        target_elem.hover(
            function () {
                action_elem.show();
            },
            function () {
                action_elem.hide();
            }
        );

        elem.addEventListener("click", Download);
    });

    let elementsTimelineArray = DOMRegex(/^show\_timeline\_/);

    elementsTimelineArray.forEach(function (elem) {
        let my_id = elem.attributes["data-id"].nodeValue;
        let target_elem = $("#" + elem.id);
        let action_elem = $("#actions_" + my_id);

        target_elem.hover(
            function () {
                action_elem.show();
            },
            function () {
                action_elem.hide();
            }
        );

        elem.addEventListener("click", Timeline);
    });

    let DisplayFilter = DOMRegex(/^display-filter/);

    DisplayFilter.forEach(function (elem) {
        elem.addEventListener("click", SetDisplayFilter)
    })

    let BtnClose = DOMRegex(/^btn_close/)

    BtnClose.forEach(function (elem) {
        elem.addEventListener("click", CloseDisplayFilter)
    })

    let CheckBoxes = DOMRegex(/^cb\_/)

    CheckBoxes.forEach(function (elem) {
        elem.addEventListener("click", SetTabVisibility)
    })

}

function SetDisplayFilter() {

    $('#checkbox_div > .row > .col-sm').children('input').each(function () {
        let tab_element = $("#tab_" + this.value)

        if (tab_element.is(":visible")) {
            $("#cb_" + this.value).prop('checked', true)
        } else {
            $("#cb_" + this.value).prop('checked', false)
        }
    });

    $("#check_all").click(function () {
        $('input:checkbox').not(this).prop('checked', true);
        $('#checkbox_div > .row > .col-sm').children('input').each(function () {
            let vis_tab = $("#tab_" + this.value)
            if (vis_tab.is(":hidden")) {
                SetTabVisibility(this.value)
            }
        })
    });

    $("#uncheck_all").click(function () {
        $('input:checkbox').prop('checked', false);
        $('#checkbox_div > .row > .col-sm').children('input').each(function () {
            let vis_tab = $("#tab_" + this.value)
            if (vis_tab.is(":visible")) {
                SetTabVisibility(this.value)
            }
        })
    });

    $("#popup1").show()
}

function SetTabVisibility(el) {

    if (typeof el === 'string' || el instanceof String) {
        var tab_value = el
    } else {
        var tab_value = el.target.value
    }

    let tab_element = $("#tab_" + tab_value)
    tab_element.toggle()

    if (tab_element.is(":visible")) {
        display_cookie.remove(tab_value)
        // check if this the only visible tab; if so, click it...
        if ($('button[id^="tab_"]:visible').length === 1) {
            tab_element.click()
        }
    } else {
        display_cookie.add(tab_value)
    }

}

function CloseDisplayFilter() {
    DestroyScrollingTabs()
    InitScrollingTabs()

    let check_visible = $('button[id^="tab_"]:visible')

    if (!check_visible.hasClass('active')){
        check_visible[0].click()
    }

    $("#popup1").hide()
}

function ReEnableDisplayFilter() {
    display_cookie.items().forEach(function (value) {
        SetTabVisibility(tab_val = value)
    })

    let check_visible = $('button[id^="tab_"]:visible')

    if (!check_visible.hasClass('active')){
        check_visible[0].click()
    }
}

function SetKeyDownEvents() {
    $(document).keydown(function (event) {
        if (event.keyCode === 27) {
            let modal_sel = $('#the-modal')
            let popup_sel = $('#popup1')
            if (modal_sel.is(":visible")) {
                modal_sel.hide();
            }
            if (popup_sel.is(":visible")) {
                CloseDisplayFilter();
            }
        }
    });
}

function SetTabEvents() {
    let elementsTabArray = DOMRegex(/^tab\_/);

    elementsTabArray.forEach(function (elem) {
        elem.addEventListener("click", SetTabClick);
    });

}

function DestroyScrollingTabs() {
    $('.nav-tabs').scrollingTabs('destroy');
}

function InitScrollingTabs() {
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

function SetTabClick(evt) {
    let attrs = evt.target.attributes;

    let selected_tab = attrs["data-name"].nodeValue;

    let tab_hash = attrs["data-hash"].nodeValue;

    if($('#content_' + tab_hash).find('div.loading-container').length === 0){
        let tab_change = $("#tab_change_loading")
        tab_change.show()
        tab_change.addClass("put_on_top")
        $("#content_" + tab_hash).addClass("grey_out")
    }

    window.socket.emit("change_display_tab", {"data": selected_tab});

}

function CreateCustomScreenshot(evt) {
    let attrs = evt.target.attributes;

    let screenshot_id = attrs["data-id"].nodeValue;

    window.socket.emit("create_custom_screenshot", {"data": screenshot_id});

    showMessage("success", "Create screenshot request send!");
}

function OpenScreenshot(evt) {
    let attrs = evt.target.attributes;

    let screenshot_id = attrs["data-id"].nodeValue;

    window.socket.emit("see_custom_screenshot", {"data": screenshot_id});

}

function Download(evt) {
    let attrs = evt.target.attributes;

    let screenshot_id = attrs["data-id"].nodeValue;

    var link = document.createElement("a");
    link.download = "Download_" + screenshot_id;
    link.href = BasePath + "screenshot/" + screenshot_id;
    link.click();
}

function Timeline(evt) {
    let attrs = evt.target.attributes;

    let screenshot_id = attrs["data-id"].nodeValue;

    let url = BasePath + "timeline/" + screenshot_id

    window.open(url, '_blank');

}
