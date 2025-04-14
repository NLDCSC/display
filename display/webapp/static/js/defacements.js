const create_plot = function (view_id) {
    fetch(`/_scatter_data?view-id=${view_id}`, {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        method: "GET",
    })
        .then(res => {
            if (res.ok) {
                return res.json()
            } else {
                throw res
            }
        })
        .then(plot_data => {
            if (view_id === null) {
                Plotly.newPlot('defacement_chart', plot_data, layout, options);
            } else {
                Plotly.newPlot('defacement_chart', plot_data["data"], plot_data["layout"], options);
            }
        })
        .catch(res => {
            console.log(res);
            if (res.status === 404) {
                Swal.fire({
                    title: "FAILED to fetch data!",
                    text: "View doesn't exist (anymore).",
                    icon: "error"
                })
            } else {
                Swal.fire({
                    title: "FAILED to fetch data!",
                    text: "Oh no",
                    icon: "error",
                });
            }
        });
}


const save_view = function (gd) {
    let plot_data = gd.data;
    let plot_layout = gd.layout;
    fetch("/_save_custom_view", {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        method: "POST",
        body: JSON.stringify({"data": plot_data, "layout": plot_layout})
    })
        .then(res => {
            if (res.ok) {
                return res.json()
            } else {
                throw res
            }
        })
        .then(data => {
            const url = `${location.protocol + '//' + location.host + location.pathname}?view-id=${data['view-id']}`;
            navigator.clipboard.writeText(url);
            Swal.fire({
                title: "Url copied to clipboard!",
                text: url,
                icon: "success"
            });
        })
        .catch(res => {
            Swal.fire({
                title: "FAILED to save view!",
                text: res.status,
                icon: "error"
            });
            console.log(res)
        });
};


const update_plot = function () {
    fetch(`/_scatter_data`, {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        method: "GET",
    })
        .then(res => {
            if (res.ok) {
                return res.json()
            } else {
                throw res
            }
        })
        .then(plot_data => {
            const gd = document.getElementById('defacement_chart');
            // Maintain visibility status, otherwise it's reset on every refresh.
            const team_visibility = {};
            gd.data.forEach(elem => {
                team_visibility[elem.name] = elem.visible ?? true;
            });
            plot_data = plot_data.map(team_data => {
                const team_name = team_data.name;
                if (team_name in team_visibility){
                    team_data.visible = team_visibility[team_name];
                } else {
                    team_data.visible = true;
                }
                return team_data
            });
            gd.data = plot_data;
            Plotly.redraw(gd);
        })
        .catch(res => {
            console.log(res);
            if (res.status === 404) {
                Swal.fire({
                    title: "FAILED to refresh data!",
                    text: "View doesn't exist (anymore).",
                    icon: "error"
                })
            } else {
                Swal.fire({
                    title: "FAILED to refresh data!",
                    text: "Oh no",
                    icon: "error",
                });
            }
        });
}

