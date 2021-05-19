function setUserCookie(user) {
    Cookies.set('user', JSON.stringify(user));
}

function getUserCookie() {
    let userString = Cookies.get('user');
    if (userString) return JSON.parse(userString);
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
    document.getElementById("signin-tab").innerHTML = "signin";
}


$("#header").ready(
    function() {
        document.getElementById("signin-tab").innerHTML = "signin";
        if(getUserCookie())  {
            document.getElementById("signin-tab").innerHTML = "signout";
        }
    }
)