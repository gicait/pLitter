var response_data = {}
var user = {}
var set_user = false
var images = {}
var anno;
var new_image_id;



function drawBoxes_annotorius(predictions){
    console.log(predictions)
}

async function predict_on_this() {
    alert("start")
    const model = await tf.automl.loadObjectDetection(MODEL_URL);
    const image = document.getElementById('ann-img');
    alert("model loaded")
    // These are the default options.
    const options = {score: 0.2, iou: 0.5, topk: 20};
    const predictions = await model.detect(image, options);
    alert(predictions)
    // Show the resulting object on the page.
    const pre = document.createElement('pre');
    pre.textContent = JSON.stringify(predictions, null, 2);
    // document.body.append(pre);

    drawBoxes_annotorius(predictions);
}


var cat_dict = {
    "Plastic":28,
    "Pile":28,
    "Trash Bin":28,
    "Face Mask":28,
  };


function save_anntations_in_coco(im_id){
    var anns = anno.getAnnotations()
    console.log(anns)
    var ann_id;
    var ann;
    for(ann_id in anns){
        ann = anns[ann_id]
        if(ann.target.selector.type === 'FragmentSelector' & ann.target.selector.conformsTo === "http://www.w3.org/TR/media-frags/"){
            var value = ann.target.selector.value    
            var format = value.includes(':') ? value.substring(value.indexOf('=') + 1, value.indexOf(':')) : 'pixel';
            var coords = value.includes(':') ? value.substring(value.indexOf(':') + 1) : value.substring(value.indexOf('=') + 1); 
            var [ x, y, w, h ] = coords.split(',').map(parseFloat)
            var cat_name = ann.body[0].value
            var cat_id = cat_dict[cat_name]
            console.log(x, y, w, h, cat_id)

            var seg = [[x,y,x+w,y,x+w,y+h,x,y+h]]
            // [[140,273,170,273,170,280,140,280]]
            // "{\"image_id\":"+image_id+",\"category_id\":"+cat_id+",\"isbbox\":true,\"segmentation\":"+segmentation+"}",
            
            fetch("http://203.159.29.187:8080/api/annotation/", {
                "headers": {
                  "accept": "application/json, text/plain, */*",
                  "accept-language": "en-US,en;q=0.9",
                  "content-type": "application/json;charset=UTF-8"
                },
                "referrer": "http://203.159.29.187:8080/",
                "referrerPolicy": "strict-origin-when-cross-origin",
                "body": JSON.stringify({
                    image_id: im_id,
                    category_id: cat_id,
                    isbbox: true,
                    segmentation: seg  
                }),
                "method": "POST",
                "mode": "cors",
                "credentials": "include"
              });

              im_status = im_id+"_status"
              document.getElementById(im_status).innerHTML="true" 

        }
    }
}

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
    document.getElementById("image-veiwer").innerHTML = "<div id='save'></div><img id='ann-img' src='http://203.159.29.187:8080/api/image/"+image_id+"' width=100% height=auto onload='"+predict_on_this()+"'/>"
    // document.getElementById("image-veiwer").innerHTML("<img src='http://203.159.29.187:8080/api/image/"+image_id.toString()+"' />" )


    anno = Annotorious.init({
        image: 'ann-img',
        locale: 'auto',
        // disableEditor: true
        widgets: [
            // { widget: 'COMMENT' },
            // { widget: return    },
            { widget: 'TAG', vocabulary: [ 'Plastic', 'Pile', 'Trash Bin', 'Face mask'] }
        ]
    })
    
    // model_run()
    document.getElementById("save").innerHTML = "<button onclick='save_anntations_in_coco("+image_id+")'>Save</button>"
    
    anno.on('createSelection', async function(selection) {
        selection.body = [{
        type: 'TextualBody',
        purpose: 'tagging',
        value: 'Plastic'
        }];
    
        await anno.updateSelected(selection);
        anno.saveSelected();
    })
    
    anno.on('selectAnnotation', function(a) {
        console.log('selectAnnotation', a);
    })
    
    anno.on('cancelSelected', function(a) {
        console.log('cancelSelected', a);
    })
    
    anno.on('createAnnotation', function(a) {
        console.log('created', a);
    })
    
    anno.on('updateAnnotation', function(annotation, previous) {
        console.log('updated', previous, 'with', annotation);
    })
    
    // var toolToggle = document.getElementById('current-tool');
    // toolToggle.addEventListener('click', function() {
    //     if (toolToggle.innerHTML == 'RECTANGLE') {
    //     toolToggle.innerHTML = 'POLYGON';
    //     anno.setDrawingTool('polygon');
    //     } else {
    //     toolToggle.innerHTML = 'RECTANGLE';
    //     anno.setDrawingTool('rect');
    //     }
    // })
    
    var editorToggle = document.getElementById('toggle-editor');
    editorToggle.addEventListener('click', function() {
        const updatedState = !anno.disableEditor;
        console.log('setting disableEditor', updatedState);
        anno.disableEditor = updatedState;
    })
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
                    $(imagelist).find('tbody').append("<tr id="+image.id+" onclick='open_image("+image.id+")'><td>"+image.id+"</td><td>"+image.file_name+"</td><td id='"+image.id+"_status' >"+image.annotated+"</td></tr>")
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
            ele.innerHTML='Logged in as: <b>'+user["name"]+'</b> <button onclick="logout_from_coco()">Log out</button>'
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
            $(imagelist).find('tbody').innerHTML=""
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

function add_with_id(res_id, im_name){
    $(imagelist).find('tbody').prepend("<tr id="+res_id+" onclick='open_image("+res_id+")'><td>"+res_id+"</td><td>"+im_name+"</td><td id='"+res_id+"_status' >false</td></tr>")
}

function upload_to_coco_backend(){
    var uploaded_images = document.getElementById("uploadFile");
      for (var i = 0; i < uploaded_images.files.length; i++) {
        var im_name = uploaded_images.files[i].name
        let form = new FormData();
        form.append("image", uploaded_images.files[i]);
        form.append("dataset_id", 55);
        // alert(uploaded_images.files[i].size)
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
        .then(function(response) {
            console.log(response.status); // Will show you the status
            if (!response.ok) {
                throw new Error("HTTP status " + response.status);
            }
            return response.json();
        })
        .then(data => new_image_id = data)
        .then(() => console.log(new_image_id))
        .then(() => add_with_id(new_image_id, im_name))
        // .then($('tbody').prepend('<tr><td>'+new_image_id+'</td><td>else here3</td></tr>'))
        // .then($('<tr id='+new_image_id+' onclick="open_image("'+new_image_id+'")"><td>'+new_image_id+'</td><td>'+uploaded_images.files[i].name+'</td><td id='+new_image_id+'"_status" >false</td></tr>').insertBefore('table > tbody > tr:first'))
        .catch(error => console.log(error))
      }
}

$(document).ready(function(){
    user_from_coco()
    if(set_user){
        get_images_from_coco()
    }
    get_images_from_coco()
})