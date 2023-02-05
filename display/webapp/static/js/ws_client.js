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

    $('#checkbox_div').children('input').each(function () {

        let tab_element = $("#tab_" + this.value)

        if (tab_element.is(":visible")) {
            $("#cb_" + this.value).prop('checked', true)
        } else {
            $("#cb_" + this.value).prop('checked', false)
        }
    });

    $("#popup1").show()
}

function SetTabVisibility(el) {

    let tab_element = $("#tab_" + el.target.value)
    tab_element.toggle()

    if (tab_element.hasClass("active")) {
        $('#checkbox_div').children('input').each(function () {
            let vis_tab = $("#tab_" + this.value)
            if (vis_tab.is(":visible")) {
                if (this.value !== el.target.value) {
                    vis_tab.click()
                    return false;
                }
            }
        })
    }

}

function CloseDisplayFilter() {
    DestroyScrollingTabs()
    InitScrollingTabs()
    $("#popup1").hide()
}

function SetTabEvents() {
    let elementsTabArray = DOMRegex(/^tab\_/);

    elementsTabArray.forEach(function (elem) {
        elem.addEventListener("click", SetTabClick);
    });

}

function DestroyScrollingTabs(){
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
