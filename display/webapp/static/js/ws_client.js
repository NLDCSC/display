function SetAllEventListeners() {

    $('.nav-tabs').scrollingTabs({
        cssClassLeftArrow: "mdi mdi-arrow-left-bold",
        cssClassRightArrow: "mdi mdi-arrow-right-bold",
        disableScrollArrowsOnFullyScrolled: true,
    });

    let elementsTabArray = DOMRegex(/^tab\_/);

    elementsTabArray.forEach(function (elem) {
        elem.addEventListener("click", SetTabClick);
    });

    let elementsImgArray = DOMRegex(/^img\_content\_/);

    elementsImgArray.forEach(function (elem) {
        let my_id = elem.attributes["data-id"].nodeValue;
        let my_elem = $("#create_screenshot_" + my_id)
        let target_elem = $("#" + elem.id)

        target_elem.hover(function(){
            my_elem.show()
        }, function(){
            my_elem.hide()
        });
    });

    let elementsCSArray = DOMRegex(/^create\_screenshot\_/);

    elementsCSArray.forEach(function (elem) {
        let target_elem = $("#" + elem.id)

        target_elem.hover(function(){
            target_elem.show()
        }, function(){
            target_elem.hide()
        });

        elem.addEventListener("click", CreateCustomScreenshot);

    });

}

function SetTabClick(evt) {
    let attrs = evt.target.attributes;

    let selected_tab = attrs["data-name"].nodeValue;

    window.socket.emit("change_display_tab", {"data": selected_tab})
}


function CreateCustomScreenshot(evt) {
    let attrs = evt.target.attributes;

    let screenshot_id = attrs["data-id"].nodeValue;

    window.socket.emit("create_custom_screenshot", {"data": screenshot_id})

    showMessage("success", "Create screenshot request send!")
}
