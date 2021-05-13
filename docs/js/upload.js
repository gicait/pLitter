// const base_link = "https://da6a1f661e52.ngrok.io"
const base_link = "https://annotator.ait.ac.th"
const d_id = 65
// const d_id = 55


var response_data = {}
var user = {}
var set_user = false
var images = {}
var anno;
var new_image_id;
var stats = {}
var dataset = {}
var annotator_response = {}

function drawBoxes_annotorius(image, predictions){
    // console.log(predictions)
    var preds_format = []
    var pred_count = 0
    predictions.forEach(prediction => {
        const {box, label, score} = prediction;
        const {left, top, width, height} = box;
        var pred_dict = {}
        pred_dict["type"] = "Annotation"
        pred_dict["body"] = []
        pred_dict_body = {}
        pred_dict_body["type"] =  "TextualBody"
        pred_dict_body["purpose"] = "tagging"
        // update it pred name
        pred_dict_body["value"] = "Plastic"
        pred_dict["body"].push(pred_dict_body)
        
        pred_dict["target"] = {}
        pred_dict["target"]["source"] = base_link+"/api/image/28568",
        pred_dict["target"]["selector"] = {}
        pred_dict["target"]["selector"]["type"] = "FragmentSelector"
        pred_dict["target"]["selector"]["conformsTo"] = "http://www.w3.org/TR/media-frags/"

        // convet to natual dimentions to img align dimensions

        a_left = left * (image.naturalWidth/image.width)
        a_top = top * (image.naturalHeight/image.height)
        a_width = width * (image.naturalWidth/image.width)
        a_height = height * (image.naturalHeight/image.height)
        
        pred_dict["target"]["selector"]["value"] = "xywh=pixel:"+String(a_left)+","+String(a_top)+","+String(a_width)+","+String(a_height)
        
        pred_dict["@context"] = ""
        pred_dict["id"] = String(pred_count)
        pred_count = pred_count+1

        preds_format.push(pred_dict)
    });
    console.log(preds_format)

    // if annotation is ready, first save it to backend and change with response id



    anno.setAnnotations(preds_format)


//     {
//     "type": "Annotation",
//     "body": [
//         {
//             "type": "TextualBody",
//             "purpose": "tagging",
//             "value": "Plastic"
//         }
//     ],
//     "target": {
//         "source": base_link+"/api/image/28568",
//         "selector": {
//             "type": "FragmentSelector",
//             "conformsTo": "http://www.w3.org/TR/media-frags/",
//             "value": "xywh=pixel:515.7105102539062,478.37109375,237.6204833984375,189.046142578125"
//         }
//     },
//     "@context": "http://www.w3.org/ns/anno.jsonld",
//     "id": "#29d84ed6-a1ea-46e4-aa4e-7b77fc06cae3"
// }
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

    drawBoxes_annotorius(image, predictions);
}

// to do
// find id by name


// var cat_dict = {
//     "Plastic":27,
//     "Pile":21,
//     "Trash Bin":29,
//     "Face Mask":30,
//     "wrapper/sachet":31,
//     "container":32,
//     "cup":4,
//     "plate":33,
//     "Cutleries":34,
//     "Beverage bottle":35,
//     "Other bottle":36,
//     "Bag":37,
//     "Foil":44,
//     "Fishing gear":38,
//     "Rope":39,
//     "Diaper":40,
//     "Textile":41, 
//     "Hand glove":42,
//     "protective gears":43,
//     "other":5
//   };


  var cat_dict = {
    "Plastic":1,
    "Pile":2,
    "Trash Bin":3,
    "Face Mask":4,
    "wrapper/sachet":5,
    "container":6,
    "cup":7,
    "plate":8,
    "cutleries":9,
    "beverage bottle":10,
    "other bottle":11,
    "bag":12,
    "foil":13,
    "fishing gear":14,
    "rope":15,
    "diaper":16,
    "textile":17, 
    "hand glove":18,
    "protective gears":19,
    "other":20
  };


var deleted_ids = []

//   "wrapper/sachet", "container", "cup", "plate", "Cutleries", "Beverage bottle", "Other bottle", "Bag", "Foil", "Fishing gear", "Rope", "Diaper", "Textile", "Hand glove", "protective gears", "other"

  

//   wrapper/sachet 31
// container 32
// cup 4 
// plate 33
// Cutleries  34
// Beverage bottle 35
// Other bottle 36
// Bag 37
// Foil 44
// Fishing gear 38
// Rope 39
// Diaper 40
// Textile 41 

// Hand glove 42
// protective gears 43
// other 5


function get_annots_from_coco(ran_anno, im_id){
    // alert("yeee")
    fetch(base_link+"/api/annotator/data/"+String(im_id), {
        "headers": {
            "accept": "application/json",
            "accept-language": "en-US,en;q=0.9"
        },
        "referrer": base_link+"/api/",
        "referrerPolicy": "strict-origin-when-cross-origin",
        "body": null,
        "method": "GET",
        "mode": "cors",
        "credentials": "include"
    })
    .then(response => response.json())
    .then(data => annotator_response = data)
    .then(() => {
        console.log(annotator_response)
        var annotations_format = []
        for(cat_num in annotator_response.categories){
            var category = annotator_response.categories[cat_num]
            var cat_name = category["name"]
            console.log(cat_name)
            var annotations = category["annotations"]

            const image = document.getElementById('ran-ann-img');

            // to do from below

            // *********************
            // *************

            annotations.forEach(annotation => {
                // if !=        
                // console.log(annotation)         
                box = annotation["bbox"]
                // console.log(box)
                // const {left, top, width, height} = box;
                box = box.flat()
                
                left = box[0]
                atop = box[1]
                width = box[2]
                height = box[3]
                // left = box[0][0]
                // atop = box[0][1]
                // width = box[0][2]
                // height = box[0][3]



                console.log(left, atop, width, height)
                var anno_dict = {}
                anno_dict["type"] = "Annotation"
                anno_dict["body"] = []
                anno_dict_body = {}
                anno_dict_body["type"] =  "TextualBody"
                anno_dict_body["purpose"] = "tagging"
                // anno_dict_body["value"] = "Plastic"
                anno_dict_body["value"] = cat_name
                anno_dict["body"].push(anno_dict_body)
        
                anno_dict["target"] = {}
                // modify below with id
                anno_dict["target"]["source"] = base_link+"/api/image/28568",
                anno_dict["target"]["selector"] = {}
                anno_dict["target"]["selector"]["type"] = "FragmentSelector"
                anno_dict["target"]["selector"]["conformsTo"] = "http://www.w3.org/TR/media-frags/"

        // convet to natual dimentions to img align dimensions

                // a_left = left * (image.naturalWidth/image.width)
                // a_top = atop * (image.naturalHeight/image.height)
                // a_width = width * (image.naturalWidth/image.width)
                // a_height = height * (image.naturalHeight/image.height)
                a_left = left
                a_top = atop
                a_width = width
                a_height = height
        
                anno_dict["target"]["selector"]["value"] = "xywh=pixel:"+String(a_left)+","+String(a_top)+","+String(a_width)+","+String(a_height)
        
                anno_dict["@context"] = ""
                anno_dict["id"] = annotation["id"]

                // ************ add condition that bbox exists
                // 
                annotations_format.push(anno_dict)
            });
        }
        console.log(annotations_format)
        ran_anno.setAnnotations(annotations_format)
    })
    .catch(error => console.log(error))
}


function save_annots_to_coco(im_id){
    var anns = ran_anno.getAnnotations()
    alert("Confirm saving"+anns.length+"annotations")
    console.log(anns)
    var ann_id;
    var ann;
    for(ann_id in anns){
        ann = anns[ann_id]
        // if(ann.target.selector.conformsTo === "http://www.w3.org/TR/media-frags/"){
            if(ann.target.selector.type === 'FragmentSelector'){
                var is_it_bbox = true
                var value = ann.target.selector.value
                var format = value.includes(':') ? value.substring(value.indexOf('=') + 1, value.indexOf(':')) : 'pixel';
                var coords = value.includes(':') ? value.substring(value.indexOf(':') + 1) : value.substring(value.indexOf('=') + 1); 
                var [ x, y, w, h ] = coords.split(',').map(parseFloat)
                var cat_name = ann.body[0].value
                var cat_id = cat_dict[cat_name]
                console.log(x, y, w, h, cat_id, ann.id)

                var box = [x, y, w, h]
                var seg = [[x,y,x+w,y,x+w,y+h,x,y+h]]
                // var annot_metadata = {'predicted':true}
            }
            else if(ann.target.selector.type === "SvgSelector"){
                var is_it_bbox = false
                console.log("svg")
                // var res = svgShape.getAttribute('points')
                //       .split(' ') // Split x/y tuples
                //       .map(xy => xy.split(',').map(str => parseFloat(str.trim())));
                
                // console.log(res)      

                var value = ann.target.selector.value
                var coords = value.includes('=') ? value.substring(value.indexOf('=\"') + 3, value.indexOf('\">')) : ""

                // var [ x, y, w, h ] = coords.split(',').map(parseFloat)
                var cat_name = ann.body[0].value
                var cat_id = cat_dict[cat_name]
                // console.log(x, y, w, h, cat_id, ann.id)

                // var box = [x, y, w, h]
                var sep_coords = coords.split(' ')
                var flat_coords = []
                sep_coords.forEach(sep_coord => {
                    var temp_cord = sep_coord.split(',').map(i=>Number(i))
                    flat_coords = flat_coords.concat(temp_cord)
                });
                var xs = []
                var ys = []
                for (i = 0; i < flat_coords.length; i++) {
                    if(i%2 === 0){
                        xs.push(flat_coords[i])
                    }
                    else{
                        ys.push(flat_coords[i])
                    }
                }
                var min_x = Math.min(...xs), max_x = Math.max(...xs)
                var min_y = Math.min(...ys), max_y = Math.max(...ys)
                var w = max_x-min_x
                var h = max_y-min_y
                var box = [min_x, min_y, w, h]
                var seg = [flat_coords]
                console.log(xs, ys, min_x, min_y, w, h, seg, cat_id)
                // var annot_metadata = {'predicted':true}
            }
            else{
                console.log("type error")
                continue;
            }
            
            // if annotatation is newly created
            // id is string, then send post
            // else id is int, send put
            if (typeof ann.id === 'number'){
                fetch(base_link+"/api/annotation/"+String(ann.id), {
                    "headers": {
                    "accept": "application/json, text/plain, */*",
                    "accept-language": "en-US,en;q=0.9",
                    "content-type": "application/json;charset=UTF-8"
                    },
                    "referrer": base_link+"/",
                    "referrerPolicy": "strict-origin-when-cross-origin",
                    "body": JSON.stringify({
                        category_id:cat_id,
                        // image_id: im_id,
                        // category_id: cat_id,
                        // isbbox: true,
                        bbox:box,
                        segmentation: seg,
                        // metadata: annot_metadata
                    }),
                    "method": "PUT",
                    "mode": "cors",
                    "credentials": "include"
                });
            }
            else if (typeof ann.id === 'string'){ 
                fetch(base_link+"/api/annotation/", {
                    "headers": {
                    "accept": "application/json, text/plain, */*",
                    "accept-language": "en-US,en;q=0.9",
                    "content-type": "application/json;charset=UTF-8"
                    },
                    "referrer": base_link+"/",
                    "referrerPolicy": "strict-origin-when-cross-origin",
                    "body": JSON.stringify({
                        image_id: im_id,
                        category_id: cat_id,
                        isbbox: is_it_bbox,
                        segmentation: seg,
                        bbox: box,
                        // metadata: annot_metadata
                    }),
                    "method": "POST",
                    "mode": "cors",
                    "credentials": "include"
                })
                .then(response => response.json())
                .then(data => console.log(data))
                .catch(error => console.log(error))
            }
            else {
                console.log("Something wrong with annotation id!")
            }
        // }
        // else{
        //     console.log("something wrong with confirmation")
        // }
    }

    // deal with deleted
    deleted_ids.forEach(deleted_id => {
        fetch(base_link+"/api/annotation/"+String(deleted_id), {
            "headers": {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8"
        },
        "referrer": base_link+"/",
        "referrerPolicy": "strict-origin-when-cross-origin",
        "body": null,
        "method": "DELETE",
        "mode": "cors",
        "credentials": "include"
        })
        .then(response => response.json())
        .then(data => console.log(data))
        .catch(error => console.log(error))
    })
    deleted_ids = []
    // update annotated to true in image    

    alert("loading next image")
    load_random()
}



function save_anntations_in_coco(im_id){
    var anns = anno.getAnnotations()
    alert("confirm saving"+anns.length+"annotations")
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

            var box = [[x,y,w,h]]
            var seg = [[x,y,x+w,y,x+w,y+h,x,y+h]]
            var annot_metadata = {'predicted':true}
            // annot_metadata["predicted"] = true
            // [[140,273,170,273,170,280,140,280]]
            // "{\"image_id\":"+image_id+",\"category_id\":"+cat_id+",\"isbbox\":true,\"segmentation\":"+segmentation+"}",
            
            fetch(base_link+"/api/annotation/", {
                "headers": {
                  "accept": "application/json, text/plain, */*",
                  "accept-language": "en-US,en;q=0.9",
                  "content-type": "application/json;charset=UTF-8"
                },
                "referrer": base_link+"/",
                "referrerPolicy": "strict-origin-when-cross-origin",
                "body": JSON.stringify({
                    image_id: im_id,
                    category_id: cat_id,
                    isbbox: true,
                    segmentation: seg,
                    bbox: box,
                    metadata: annot_metadata
                }),
                "method": "POST",
                "mode": "cors",
                "credentials": "include"
              });
        }
    }
    im_status = im_id+"_status"
    document.getElementById(im_status).innerHTML="true" 
}

let TagSelectorWidget = function (args) {

    const tags = args.annotation ?
        args.annotation.bodies.filter(function (b) {
            return b.purpose == 'tagging' && b.type == 'TextualBody';
        }) : [];

    let createDropDown = function (options) {
        var dropDown = document.createElement('select');

        options.forEach(optionValue => {
            let optionElement = document.createElement('option');
            optionElement.appendChild(document.createTextNode(optionValue));
            optionElement.value = optionValue;
            if (optionValue == tags[0]?.value) {
                optionElement.selected = 'selected';
            }
            dropDown.appendChild(optionElement);
        });

        dropDown.addEventListener('change', function () {
            if (tags.length > 0) {
                args.onUpdateBody(tags[0], {
                    type: 'TextualBody',
                    purpose: 'tagging',
                    value: this.value
                });
            } else {
                args.onAppendBody({
                    type: 'TextualBody',
                    purpose: 'tagging',
                    value: this.value
                });
            }
        });

        return dropDown;
    }

    var container = document.createElement('div');
    container.className = 'tagselector-widget';

    const VOCABULARY = ['Plastic', 'Pile', 'Trash Bin', 'Face mask', "wrapper/sachet", "container", "cup", "plate", "Cutleries", "Beverage bottle", "Other bottle", "Bag", "Foil", "Fishing gear", "Rope", "Diaper", "Textile", "Hand glove", "protective gears", "other"];
    container.appendChild(createDropDown(VOCABULARY));

    return container;
};

function load_random(){
    fetch(base_link+"/api/dataset/"+String(d_id)+"/data?page=1&limit=50", {
        // fetch(base_link+"/api/dataset/"+String(d_id)+"/data?page=1&limit=50&annotated=false", {
        "headers": {
            "accept": "application/json",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8"
        },
        "referrer": base_link+"/",
        "referrerPolicy": "strict-origin-when-cross-origin",
        "body": null,
        "method": "GET",
        "mode": "cors",
        "credentials": "include"
    })
    .then(response => response.json())
    .then(data => images = data)
    .then(() => {
        const random_index = Math.floor(Math.random() * images.images.length);
        const image = images.images[random_index];
        const image_id = image["id"]
        // document.getElementById("ran-img").innerHTML
        // = `<img id='ran-ann-img' crossorigin='anonymous' src='${base_link}/api/image/${image_id}' width=100% height=100%/>`

        document.getElementById("openseadragon").innerHTML = ''
        document.getElementById("toolbar").innerHTML = ''

        var viewer = OpenSeadragon({
            id: "openseadragon",
            prefixUrl: "./icons/openseadragon/",
            tileSources: {
            type: "image",
            url: String(base_link)+'/api/image/'+String(image_id)
            },
            gestureSettingsTouch: {
            pinchRotate: true
            }
        });
    
        ran_anno = OpenSeadragon.Annotorious(viewer, {
            locale: 'auto',
            allowEmpty: true,
    
            widgets: [ TagSelectorWidget ]
        });
    
        // Annotorious.Toolbar(ran_anno, document.getElementById('toolbar'));
    
          

        // ran_anno = Annotorious.init({
        //     image: 'ran-ann-img',
        //     locale: 'auto',
        //     // disableEditor: true
        //     widgets: [ TagSelectorWidget ]
        // })
        
        get_annots_from_coco(ran_anno, image_id)


        // model_run()
        document.getElementById("ran-save").innerHTML = 
        `<button class='button-save' onclick='save_annots_to_coco(${image_id})'>
            <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 36 36">
                <path d="M13.5 24.26L7.24 18l-2.12 2.12 8.38 8.38 18-18-2.12-2.12z" />
            </svg>
        </button>`
        
        ran_anno.on('createSelection', async function(selection) {
            selection.body = [{
            type: 'TextualBody',
            purpose: 'tagging',
            value: 'Plastic'

            }];
            // selection.id = "#0000"
            console.log(selection)
            await ran_anno.updateSelected(selection);
            ran_anno.saveSelected();
        })
        
        ran_anno.on('selectAnnotation', function(a) {
            console.log('selectAnnotation', a);
        })
        
        ran_anno.on('cancelSelected', function(a) {
            console.log('cancelSelected', a);
        })
        
        ran_anno.on('createAnnotation', function(a) {
            console.log('created', a);
        })
        
        ran_anno.on('updateAnnotation', function(annotation, previous) {
            console.log('updated', previous, 'with', annotation);
        })

        // to do, on delete 
        ran_anno.on('deleteAnnotation', function(annotation) {
            console.log('deleted', annotation.id);
            if(typeof annotation.id === "number"){
                console.log("will be deleted from coco-annotator after saving")
                deleted_ids.push(annotation.id)
            }
        })
    })
    .catch(error => console.log(error))
}



function open_image(image_id){
    // fetch(base_link+"/api/annotator/data/"+image_id.toString(), {
    //     "headers": {
    //         "accept": "application/json",
    //         "accept-language": "en-GB,en-US;q=0.9,en;q=0.8"
    //     },
    //     "referrer": base_link+"",
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
    // width=100% height=auto 
    document.getElementById("image-veiwer").innerHTML = "<div id='save'></div><img id='ann-img' crossorigin='anonymous' src="+base_link+"'/api/image/"+image_id+"' width=100% height=auto onload='predict_on_this()'/>"
    // document.getElementById("image-veiwer").innerHTML("<img src="+base_link+"'/api/image/"+image_id.toString()+"' />" )


    anno = Annotorious.init({
        image: 'ann-img',
        locale: 'auto',
        // disableEditor: true
        widgets: [ TagSelectorWidget ]
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
    
    // var editorToggle = document.getElementById('toggle-editor');
    // editorToggle.addEventListener('click', function() {
    //     const updatedState = !anno.disableEditor;
    //     console.log('setting disableEditor', updatedState);
    //     anno.disableEditor = updatedState;
    // })
}

function get_images_from_coco(){
    fetch(base_link+"/api/dataset/"+String(d_id)+"/data?page=1&limit=50&annotated=false", {
        "headers": {
            "accept": "application/json",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8"
        },
        "referrer": base_link+"/",
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

    fetch(base_link+"/api/user/login", {
        "headers": {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json;charset=UTF-8"
        },
        "referrer": base_link+"/",
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
    fetch(base_link+"/api/user/logout", {
        "headers": {
            "accept": "application/json",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8"
        },
        "referrer": base_link+"/",
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

fetch(base_link+"/api/user/", {
    "headers": {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-GB,en-US;q=0.9,en;q=0.8"
    },
    "referrer": base_link+"/",
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


function get_dataset_stats(){
    // alert("yee")
    fetch(base_link+"/api/dataset/"+String(d_id)+"/stats", {
        "headers": {
          "accept": "application/json",
          "accept-language": "en-US,en;q=0.9"
        },
        "referrer": base_link+"/api/",
        "referrerPolicy": "strict-origin-when-cross-origin",
        "body": null,
        "method": "GET",
        "mode": "cors",
        "credentials": "include"
    })
    .then(response => response.json())
    .then(data => stats = data)
    .then(() => {
        // alert("yeeee")
        // if(stats.total){
            document.getElementById("stats").innerHTML="<p>Total: "+String(stats.total.Images)+", Annotated Images: "+String(stats.total["Annotated Images"])
            // document.getElementById("stats").innerHTML="<p>"+String(stats.total)+"</p>"
        // }
        })
    .catch(error => console.log(error))

}


function upload_to_coco_backend(){
    var uploaded_images = document.getElementById("uploadFile");
      for (var i = 0; i < uploaded_images.files.length; i++) {
        var im_name = uploaded_images.files[i].name
        let form = new FormData();
        form.append("image", uploaded_images.files[i]);
        form.append("dataset_id", "+String(d_id)+");
        // alert(uploaded_images.files[i].size)
        fetch(base_link+"/api/image/", {
            "headers": {
                "accept": "application/json, text/plain, */*",
                "accept-language": "en-US,en;q=0.9"
                // "content-type": "multipart/form-data;"
            },
            "referrer": base_link+"/",
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
    get_dataset_stats()
}


$(document).ready(function(){
    get_dataset_stats()
    user_from_coco()
    if(set_user){
        get_images_from_coco()
    }
    get_images_from_coco()
})








// var sampleAnnotation = { 
//     "@context": "http://www.w3.org/ns/anno.jsonld",
//     "id": "#07475897-d2eb-4dce-aa12-ecb50771c734",
//     "type": "Annotation",
//     "body": [{
//       "type": "TextualBody",
//       "value": "Annotation"
//     }],
//     "target": {
//       "selector": {
//         "type": "FragmentSelector",
//         "conformsTo": "http://www.w3.org/TR/media-frags/",
//         "value": "xywh=540,240,180,340"
//       }
//     }
//   };

//   function osd_open() {
//     var viewer = OpenSeadragon({
//       id: "openseadragon",
//       prefixUrl: "/icons/openseadragon/",
//       tileSources: {
//         type: "image",
//         url: "../graphics/active_learning.PNG"
//       },
//       gestureSettingsTouch: {
//         pinchRotate: true
//       }
//     });

//     var anno = OpenSeadragon.Annotorious(viewer, {
//       locale: 'auto',
//       allowEmpty: true,

//       widgets: [ TagSelectorWidget ]
//     });

//     Annotorious.Toolbar(anno, document.getElementById('toolbar'));

//     anno.addAnnotation(sampleAnnotation);
//   }