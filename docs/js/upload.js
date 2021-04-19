var response_data = {}
var user = {}
var set_user = false


var images = {}

function open_image(image_id){
    // fetch("http://203.159.29.187:8080/api/annotator/data/"+image_id.toString(), {
    //     "headers": {
    //         "accept": "application/json",
    //         "accept-language": "en-GB,en-US;q=0.9,en;q=0.8"
    //     },
    //     "referrer": "http://203.159.29.187:8080",
    //     "referrerPolicy": "strict-origin-when-cross-origin",
    //     "body": null,
    //     "method": "GET",
    //     "mode": "cors",
    //     "credentials": "include"
    // })
    // .then(res => res.json())
    // .then(data => console.log(data))
    // .catch(error => console.log(error))
    // $( "image-veiwer" ).remove();
    document.getElementById("image-veiwer").innerHTML = "<img src='http://203.159.29.187:8080/api/image/"+image_id+"' />"
    // document.getElementById("image-veiwer").innerHTML("<img src='http://203.159.29.187:8080/api/image/"+image_id.toString()+"' />" )
}

function get_images_from_coco(){
    fetch("http://203.159.29.187:8080/api/dataset/55/data?page=1&limit=50&annotated=false", {
        "headers": {
            "accept": "application/json",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8"
        },
        "referrer": "http://203.159.29.187:8080/",
        "referrerPolicy": "strict-origin-when-cross-origin",
        "body": null,
        "method": "GET",
        "mode": "cors",
        "credentials": "include"
    })
    .then(response => response.json())
    .then(data => images = data)
        .then(() => {
            if(images.total > 0){
                for (let index = 0; index < images.total; index++) {
                    const image = images.images[index];
                    $(imagelist).find('tbody').append("<tr id="+image.id+" onclick='open_image("+image.id+")'><td>"+image.id+"</td><td>"+image.file_name+"</td><td>"+image.annotated+"</td></tr>")
                }
            }
        })
    .catch(error => console.log(error))
}


function login_from_coco(){

    var userName = document.getElementById("user").value;
    var passWord = document.getElementById("pass").value;

    fetch("http://203.159.29.187:8080/api/user/login", {
        "headers": {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json;charset=UTF-8"
        },
        "referrer": "http://203.159.29.187:8080/",
        "referrerPolicy": "strict-origin-when-cross-origin",
        "body": JSON.stringify({
            username: userName,
            password: passWord
        }),
        "method": "POST",
        "mode": "cors",
        "credentials": "include"
    })
    .then(res => res.json())
    .then(data => response_data = data)
    .then(() => {
        if(response_data["success"] === true){
            set_user = true
            user = response_data["user"];
            var ele = document.getElementById("login")
            ele.innerHTML='Logged in as: <b>'+user["name"]+'</b> <button onclick="getUser()">Log out</button>'
            get_images_from_coco();
        }
        else {
            alert("Could not authenticate user")
        }
    })
    .catch((error) => {
        console.log(error)
        })
}

function logout_from_coco(){
    fetch("http://203.159.29.187:8080/api/user/logout", {
        "headers": {
            "accept": "application/json",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8"
        },
        "referrer": "http://203.159.29.187:8080/",
        "referrerPolicy": "strict-origin-when-cross-origin",
        "body": null,
        "method": "GET",
        "mode": "cors",
        "credentials": "include"
    })
    .then(res => res.json())
    .then(data => response_data = data)
    .then(() => {
        if(response_data["success"] === true){
            var ele = document.getElementById("login")
            ele.innerHTML='<input type = "text" id = "user"/><input type = "password" id = "pass"/><button onclick="login_from_coco()">Log in</button>'
        }
        else {
            console.log(response_data)            
        }
    })
    .catch((error) => {
        console.log(error)
    })
}

function user_from_coco(){

fetch("http://203.159.29.187:8080/api/user/", {
    "headers": {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-GB,en-US;q=0.9,en;q=0.8"
    },
    "referrer": "http://203.159.29.187:8080/",
    "referrerPolicy": "strict-origin-when-cross-origin",
    "body": null,
    "method": "GET",
    "mode": "cors",
    "credentials": "include"
    })
    .then(res => res.json())
    .then(data => response_data = data)
    .then(() => {
        if(response_data["success"] === false){
            $('#login-modal').modal('toggle')
        }
        else {
            set_user = true;
            user = response_data["user"];
            var ele = document.getElementById("login")
            ele.innerHTML='Logged in as: <b>'+user["name"]+'</b> <button onclick="logout_from_coco()">Log out</button>'
        }
    })
    .catch((error) => {
        console.log(error)
    })
}



function upload_to_coco_backend(){
    var uploaded_images = document.getElementById("uploadFile");
      for (var i = 0; i < uploaded_images.files.length; i++) {
        let form = new FormData();
        form.append("image", uploaded_images.files[i]);
        form.append("dataset_id", 55);
        alert(uploaded_images.files[i].size)
        fetch("http://203.159.29.187:8080/api/image/", {
            "headers": {
                "accept": "application/json, text/plain, */*",
                "accept-language": "en-US,en;q=0.9"
                // "content-type": "multipart/form-data;"
            },
            "referrer": "http://203.159.29.187:8080/",
            "referrerPolicy": "strict-origin-when-cross-origin",
            "body": form,
            "method": "POST",
            "mode": "cors",
            "credentials": "include"
        })
        .then(response => response.json())
        .then(data => console.log(data))
        .catch(error => console.log(error))
      }
}

$(document).ready(function(){
    user_from_coco()
    if(set_user){
        get_images_from_coco();
    }
    // get_images_from_coco()
})