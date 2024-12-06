function DOMRegex(regex) {
  let output = [];
  for (let i of document.querySelectorAll("*")) {
    if (regex.test(i.id)) {
      // or whatever attribute you want to search
      output.push(i);
    }
  }
  return output;
}

function showMessage(msg_type, message) {
  const Toast = Swal.mixin({
    toast: true,
    position: "bottom-end",
    showConfirmButton: false,
    timer: 3000,
    timerProgressBar: true,
    onOpen: (toast) => {
      toast.addEventListener("mouseenter", Swal.stopTimer);
      toast.addEventListener("mouseleave", Swal.resumeTimer);
    },
  });
  Toast.fire({
    icon: msg_type,
    title: "&nbsp;&nbsp;" + message,
  });
}

function getBootstrapBreakpoint(){
  var w = $(document).innerWidth();
  return (w < 576) ? 'xs' : ((w < 768) ? 'sm' : ((w < 992) ? 'md' : ((w < 1200) ? 'lg' : 'xlg')));
}

function getColumnCount(){

  var breakpoint = getBootstrapBreakpoint();

  if (breakpoint === "xs") {
    return 1
  } else if (breakpoint === "sm") {
    return 2
  } else if (breakpoint === "md") {
    return 3
  } else if (breakpoint === "lg") {
    return 4
  } else {
    return 6
  }
}

function resizeEnd() {
  // console.log("Current bootstrap breakpoint:" + getBootstrapBreakpoint())
  let check_visible = $('button[id^="tab_"]:visible').filter(".active")

  let data_hash = check_visible[0].attributes['data-hash'].nodeValue
  JustifyTabContent(data_hash);
  $('.template-row').hide();
  $('.img-wrap').show();
}

function resizeCutColumns() {
  // console.log("Adjusting column count...")

  let column_count = getColumnCount()

  //console.log(column_count)

  if (column_count !== 6) {
    let new_i = 6 - (6 - column_count)
    for (let i = 1; i <= column_count; i++){
      let my_id = $("#template_item_" + i)
      // console.log(my_id)
      my_id.show()
    }
    for (let i = 1; i <= (6 - new_i); i++){
      let my_id = $("#template_item_" + (new_i + i))
      // console.log(my_id)
      my_id.hide()
    }
  } else {
    for (let i = 1; i <= 6; i++){
      let my_id = $("#template_item_" + i)
      // console.log(my_id)
      my_id.show()
    }
  }
  // for (let i = new_i; i <= 6; i++){
  //   let my_id = $("#template_item_" + (6 - i))
  //   // console.log(my_id)
  //   my_id.hide()
  // }

}

function setWaitCursor(el = null) {

    if (el !== null) {
        $(el).css({"cursor": "wait"})
    }

    $("#content-wrapper").addClass("waiting")

}

function removeWaitCursor(el = null) {
    if (el !== null) {
        $(el).css({"cursor": "default"})
    }

    $("#content-wrapper").removeClass("waiting")

}
