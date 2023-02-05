function parseCookieValue(cookiedata) {
    var parsed_data = cookiedata
        .split(';')
        .map(v => v.split('='))
        .reduce((acc, v) => {
            acc[decodeURIComponent(v[0].trim())] = decodeURIComponent(v[1].trim());
        })

    return parsed_data[1].split(",")
}

function onlyUnique(value, index, self) {
    return self.indexOf(value) === index;
}

function CookieList(cookieName, exdays = 1) {
    //When the cookie is saved the items will be a comma seperated string
    //So we will split the cookie by comma to get the original array
    const d = new Date();
    d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
    let expires = "expires=" + d.toGMTString();
    // var cookie = (document.cookie = cookieName + "=" + items + ";" + expires + ";path=/;SameSite=Lax");

    var cookie = (document.cookie)

    //Load the items or a new array if null.
    var items = cookie ? parseCookieValue(cookie) : new Array();


    return {
        "add": function (val) {
            //Add to the items.
            items.push(val);
            items = items.filter(onlyUnique)
            //Save the items to a cookie.
            document.cookie = cookieName + "=" + items.join(',') + ";" + expires + ";path=/;SameSite=Lax";
        },
        "remove": function (val) {
            // remove from the cookie
            let indx = items.indexOf(val);
            if (indx !== -1) items.splice(indx, 1);
            items = items.filter(onlyUnique)
            document.cookie = cookieName + "=" + items.join(',') + ";" + expires + ";path=/;SameSite=Lax";
        },
        "clear": function () {
            items = null;
            //clear the cookie.
            document.cookie = cookieName + '=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";';
        },
        "items": function () {
            //Get all the items.
            return items;
        }
    }
}
