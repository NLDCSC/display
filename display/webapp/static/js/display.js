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
