function SetAllEventListeners() {

    $('.nav-tabs').scrollingTabs({
        cssClassLeftArrow: "mdi mdi-arrow-left-bold",
        cssClassRightArrow: "mdi mdi-arrow-right-bold"
    });

    let elementsTabArray = DOMRegex(/^tab\_/);

    elementsTabArray.forEach(function (elem) {
        elem.addEventListener("click", SetTabClick);
    });

    // $("input[data-bootstrap-switch]").each(function () {
    //   $(this).bootstrapSwitch("state", $(this).prop("checked"));
    // });
    //
    // var elementsDELArray = DOMRegex(/^del_event_/);
    //
    // elementsDELArray.forEach(function (elem) {
    //   elem.addEventListener("click", EventDelete);
    // });

    // var change_profile_image = document.getElementById("change_profile_image");
    // change_profile_image.addEventListener("click", ChangeProfilePic);
    //
    // var asm_popup = document.getElementById("asmpopup_asms");
    // asm_popup.addEventListener("mouseover", AsmPopup);
}

function SetTabClick(evt) {
    let attrs = evt.target.attributes;

    let selected_tab = attrs["data-name"].nodeValue;

    window.socket.emit("change_display_tab", {"data": selected_tab})
}
