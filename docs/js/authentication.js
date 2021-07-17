function setUserCookie(user) {
    Cookies.set('user', JSON.stringify(user));
}

function getUserCookie() {
    let userString = Cookies.get('user');
    if (userString) {
        return JSON.parse(userString);
    }
    else {
        return false;
    }
}

function getToken() {
    let user = getUserCookie();
    return user?.id?.$oid;
}

function getUsername() {
    let user = getUserCookie();
    return user?.username;
}

function signOut() {
    Cookies.set('user', null);
    window.location.reload()
}


$("#navbar-header").ready(
    function() {
        let user = getUserCookie();
        if(user)  {
            document.getElementById("signin").innerHTML = user.username;
        }
    }
)