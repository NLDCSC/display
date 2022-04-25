function toggle_source(el) {
    if (el.classList.contains("badge-success")){
        el.classList.remove("badge-success");
        el.classList.add("badge-secondary");
        window.socket.emit("remove_source", {"data": el.id});
    } else {
        el.classList.remove("badge-secondary");
        el.classList.add("badge-success");
        window.socket.emit("add_source", {"data": el.id});
    }

}

function remove_filter(el) {

    el.parentNode.removeChild(el);

    window.socket.emit("filter", {"data": el.textContent, "action": "DEL"})

}

function toggle_play() {

    $('#play').find('svg').toggleClass('fa-pause fa-play');

    var el = $('#play').find('svg')[0];

    if (el.classList.contains("fa-pause")){
        window.socket.emit("toggle_stream", {"data": 1})
    } else {
        window.socket.emit("toggle_stream", {"data": 0})
    }

}
