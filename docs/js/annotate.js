//to do: mobile friendly and full screen mode, youtube player example

const base_link = "https://annotator.ait.ac.th"
const dataset_id = 81

var rejectedList = [] // when rejected add image_id to this list, on load_random,, i will send this request
var raisedList = []
var submittedList = []
var user = {}
var user_name = 'Anonymous' // change it user_name after sign in, otherwise overrides as system, hard to maintain stats after
var present_image_id
var image_annotating_status = false // make it true after image loading, make it false when annotation saving 
// var new_image_id;
var stats = {}
var dataset = {}
var annotator_response = {}
var deleted_ids = []
var loading_status = false // to avoid calling loading function while its already executing, othetrwise skips unlacking image if image is reloading

var annotatorSubmitted = 0
var annotatorRejected = 0
var annotatorRaised = 0

var cat_dict = {}

var isFullScreen = false;
var tags = [];

fetch(base_link + "/api/dataset/" + String(dataset_id) + "/cats", {
    "headers": {
        "accept": "application/json",
        "accept-language": "en-GB,en-US;q=0.9,en;q=0.8"
    },
    "referrer": base_link,
    "referrerPolicy": "strict-origin-when-cross-origin",
    "body": null,
    "method": "GET",
    "mode": "cors",
    "credentials": "include"
})
    .then(response => response.json())
    .then(data => cats_response = data)
    .then(() => {
        console.log("Catgeory dictionary fecthed.")
        cat_dict = cats_response.categories
    })
    .catch(error => console.log(error))

function popup_label(ann) {
    console.log("mouse enter", ann)
    let id = ann.id
    let value = ann.target.selector.value
    let format = value.includes(':') ? value.substring(value.indexOf('=') + 1, value.indexOf(':')) : 'pixel';
    let coords = value.includes(':') ? value.substring(value.indexOf(':') + 1) : value.substring(value.indexOf('=') + 1);
    let [x, y, w, h] = coords.split(',').map(parseFloat)
    let label = ann.body[0].value
    // let ele = $("[data-id=" + id + "]");
    let ele = document.getElementsByTagName('g')[0]
    console.log(ele)
    let text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    text.setAttribute('x', x + w / 2);
    text.setAttribute('y', y);
    text.setAttribute('dy', 1);
    text.setAttribute('dx', 1);
    text.setAttribute('class', 'label');
    text.setAttribute('id', 'label');
    text.setAttribute('style', 'font-size: 20px; fill: white; text-anchor: middle;')
    text.textContent = `${label}`;

    ele.append(text);
}

let TagSelectorWidget = (args) => {
    var tempArgs;
    tempArgs = args;
    window.arguments = tempArgs;

    tags = args.annotation ?
        args.annotation.bodies.filter(function (b) {
            return b.purpose == 'tagging' && b.type == 'TextualBody';
        }) : [];

    let createDropDown = function (options) {
        var dropDown = document.createElement('select');
        dropDown.setAttribute('data-native-menu', 'false')
        dropDown.setAttribute('id', 'object-type-select');

        options.forEach(optionValue => {
            let optionElement = document.createElement('option');
            optionElement.setAttribute('class', 'select-option')

            function capitalize(word) {
                const lower = word.toLowerCase();
                return word.charAt(0).toUpperCase() + lower.slice(1);
            }
            optionElement.appendChild(document.createTextNode(capitalize(optionValue)));
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

        dropDown.addEventListener('touchstart', function () {
            var element = document.getElementById("object-type-select")
            element.size = element.options.length;
            element.style.position = 'absolute';
            element.style.zIndex = 99999;
        });

        return dropDown;
    }

    var container = document.createElement('div');
    container.className = 'tagselector-widget';

    const VOCABULARY = Object.keys(cat_dict);
    container.appendChild(createDropDown(VOCABULARY));

    return container;
};

//   fetches annotations, converts to Annotorius format and sets
async function get_annots_from_coco(ran_anno, im_id) {
    await fetch(base_link + "/api/annotator/data/" + String(im_id), {
        "headers": {
            "accept": "application/json",
            "accept-language": "en-US,en;q=0.9"
        },
        "referrer": base_link + "/api/",
        "referrerPolicy": "strict-origin-when-cross-origin",
        "body": null,
        "method": "GET",
        "mode": "cors",
        "credentials": "include"
    })
        .then(response => response.json())
        .then(data => annotator_response = data)
        .then(() => {
            // console.log(annotator_response)
            var annotations_format = []
            for (cat_num in annotator_response.categories) {
                var category = annotator_response.categories[cat_num]
                var cat_name = category["name"]
                // console.log(cat_name)
                var annotations = category["annotations"]
                const image = document.getElementById('ran-ann-img');
                annotations.forEach(annotation => {
                    box = annotation["bbox"]
                    box = box.flat()
                    left = box[0]
                    atop = box[1]
                    width = box[2]
                    height = box[3]
                    // console.log(left, atop, width, height)
                    var anno_dict = {}
                    anno_dict["type"] = "Annotation"
                    anno_dict["body"] = []
                    anno_dict_body = {}
                    anno_dict_body["type"] = "TextualBody"
                    anno_dict_body["purpose"] = "tagging"
                    anno_dict_body["value"] = cat_name
                    anno_dict["body"].push(anno_dict_body)
                    anno_dict["target"] = {}
                    // modify below with id
                    anno_dict["target"]["source"] = base_link + "/api/image/28568",
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
                    anno_dict["target"]["selector"]["value"] = "xywh=pixel:" + String(a_left) + "," + String(a_top) + "," + String(a_width) + "," + String(a_height)
                    anno_dict["@context"] = ""
                    anno_dict["id"] = annotation["id"]
                    // ************ add condition that bbox exists
                    annotations_format.push(anno_dict)
                });
            }
            // console.log(annotations_format)
            ran_anno.setAnnotations(annotations_format)
        })
        .catch(error => console.log(error))
}

function raise_image(image_id) {
    // alert("im working")
    console.log(image_id)
    if (!raisedList.includes(image_id)) {
        raisedList.push(image_id)
        annotatorRaised = raisedList.length
        // document.getElementById("raised-count").innerHTML=`${annotatorRaised}`        
    }
    // to do send request, check api/image/flag
}

function reject_image(image_id) {
    if (!rejectedList.includes(image_id)) {
        rejectedList.push(image_id)
        annotatorRejected = rejectedList.length
        // document.getElementById("rejected-count").innerHTML=`${annotatorRejected}`        
    }
    load_random()
}


async function load_random() {
    if (loading_status === true) {
        console.log("Loading, Please wait!")
    }
    else {
        loading_status = true
        if (!!present_image_id & image_annotating_status === true) {
            console.log("image skipping without annotating")
            await fetch(base_link + "/api/image/" + String(present_image_id), {
                "headers": {
                    "accept": "application/json, text/plain, */*",
                    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8"
                },
                "referrer": base_link + "/",
                "referrerPolicy": "strict-origin-when-cross-origin",
                "body": JSON.stringify({
                    cs_annotating: false,
                    is_annoatations_added: false,
                }),
                "method": "PUT",
                "mode": "cors",
                "credentials": "include"
            })
                .then(response => response.json())
                .then(data => {
                    console.log(data)
                    present_image_id = null
                })
                .catch(error => console.log(error))
            image_annotating_status = false
        }

        await fetch(base_link + "/api/dataset/" + String(dataset_id) + "/random_image", {
            "headers": {
                "accept": "application/json, text/plain, */*",
                "accept-language": "en-US,en;q=0.9",
                "content-type": "application/json;charset=UTF-8"
            },
            "referrer": base_link + "/",
            "referrerPolicy": "strict-origin-when-cross-origin",
            "body": JSON.stringify({
                dummy: true,
                rejected: rejectedList
            }),
            "method": "POST",
            "mode": "cors",
            "credentials": "include"
        })
            .then(response => response.json())
            .then(data => image = data)
            .then(() => {
                console.log(image)
                const image_id = image.image_id
                console.log(image_id)
                console.log("check bf?af")
                present_image_id = image_id

                // change image annoattion status to true
                image_annotating_status = true

                document.getElementById("openseadragon").innerHTML = '' //@nischal, in case of error we will losee reload button, try catch
                // document.getElementById("toolbar").innerHTML = ''
                var viewer = OpenSeadragon({
                    id: "openseadragon",
                    prefixUrl: "./icons/openseadragon/",
                    tileSources: {
                        type: "image",
                        url: String(base_link) + '/api/image/' + String(image_id)
                    },
                    gestureSettingsTouch: {
                        pinchRotate: true
                    },
                    autoHideControls: false,
                    maxZoomPixelRatio: 6
                });

                viewer.fullPageButton.removeAllHandlers();
                viewer.fullPageButton.addHandler("click", function () {
                    if (isFullScreen === false) {
                        viewer.setFullScreen(true)
                        screen.orientation.lock("landscape-primary")
                        isFullScreen = true
                    } else if (isFullScreen === true) {
                        viewer.setFullScreen(false)
                        screen.orientation.unlock();
                        isFullScreen = false
                    }
                });

                ran_anno = OpenSeadragon.Annotorious(viewer, {
                    locale: 'auto',
                    allowEmpty: true,
                    widgets: [TagSelectorWidget]
                });

                viewer.addHandler('open', () => {
                    let ignoreButton = new OpenSeadragon.Button({
                        tooltip: 'Pan',
                        srcRest: `./icons/openseadragon/pan-tool.png`,
                        srcGroup: `./icons/openseadragon/pan-tool.png`,
                        srcHover: `./icons/openseadragon/pan-tool.png`,
                        srcDown: `./icons/openseadragon/pan-tool.png`,
                        onClick: () => { ran_anno.setDrawingEnabled(false); },
                        //   onClick: () => {console.log('ignoring'); rejectedList.push(image_id); load_random()},
                    });
                    viewer.addControl(ignoreButton.element, { anchor: OpenSeadragon.ControlAnchor.TOP_LEFT });
                });

                viewer.addHandler('open', () => {
                    let reloadButton = new OpenSeadragon.Button({
                        tooltip: 'Reload',
                        srcRest: `./icons/openseadragon/reload.png`,
                        srcGroup: `./icons/openseadragon/reload.png`,
                        srcHover: `./icons/openseadragon/reload.png`,
                        srcDown: `./icons/openseadragon/reload.png`,
                        onClick: () => { console.log('refresh'); load_random() },
                        //   onPress: console.log('refresh'),
                        //   onRelease: console.log('refresh'),
                        //   onEnter: console.log('refresh'),
                    });

                    viewer.addControl(reloadButton.element, { anchor: OpenSeadragon.ControlAnchor.TOP_RIGHT });
                });

                viewer.addHandler('open', () => {

                    let ignoreButton = new OpenSeadragon.Button({
                        tooltip: 'Ignore',
                        srcRest: `./icons/openseadragon/ignore.png`,
                        srcGroup: `./icons/openseadragon/ignore.png`,
                        srcHover: `./icons/openseadragon/ignore.png`,
                        srcDown: `./icons/openseadragon/ignore.png`,
                        onClick: () => { console.log('ignoring'); reject_image(image_id); },
                        //   onClick: () => {console.log('ignoring'); rejectedList.push(image_id); load_random()},
                    });
                    viewer.addControl(ignoreButton.element, { anchor: OpenSeadragon.ControlAnchor.TOP_RIGHT });
                });

                viewer.addHandler('open', () => {
                    let saveButton = new OpenSeadragon.Button({
                        tooltip: 'Save',
                        srcRest: `./icons/openseadragon/save.png`,
                        srcGroup: `./icons/openseadragon/save.png`,
                        srcHover: `./icons/openseadragon/save.png`,
                        srcDown: `./icons/openseadragon/save.png`,
                        onClick: () => { console.log('saving'); save_annots_to_coco(image_id); },
                    });
                    viewer.addControl(saveButton.element, { anchor: OpenSeadragon.ControlAnchor.TOP_RIGHT });
                });

                viewer.addHandler('open', () => {
                    let raiseButton = new OpenSeadragon.Button({
                        tooltip: 'Flag',
                        srcRest: `./icons/openseadragon/bookmark.png`,
                        srcGroup: `./icons/openseadragon/bookmark.png`,
                        srcHover: `./icons/openseadragon/bookmark.png`,
                        srcDown: `./icons/openseadragon/bookmark.png`,
                        onClick: () => { console.log('raising'); raise_image(image_id); },
                    });
                    viewer.addControl(raiseButton.element, { anchor: OpenSeadragon.ControlAnchor.TOP_RIGHT });
                });

                viewer.addHandler('open', () => {
                    let rectButton = new OpenSeadragon.Button({
                        tooltip: 'Draw',
                        srcRest: `./icons/openseadragon/rect.png`,
                        srcGroup: `./icons/openseadragon/rect.png`,
                        srcHover: `./icons/openseadragon/rect.png`,
                        srcDown: `./icons/openseadragon/rect.png`,
                        onClick: () => { console.log('rect'); ran_anno.setDrawingTool('rect'); ran_anno.setDrawingEnabled(true); },
                    });
                    viewer.addControl(rectButton.element, { anchor: OpenSeadragon.ControlAnchor.TOP_RIGHT });
                });

                // Annotorious.Toolbar(ran_anno, document.getElementById('toolbar'));

                //     viewer.addControl(printButton, { anchor: OpenSeadragon.ControlAnchor.TOP_LEFT });
                // });

                // need to add reject button @nischal, 
                // is it better to keep the button, jsut disbale them, instead adding everytime
                // loading button has to stay disabled when image is laoding
                // gif while image loading

                let flagButton = document.createElement("button");
                flagButton.id = 'button-flag';
                flagButton.className = "a9s-toolbar-btn";
                flagButton.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 36 36">
                <path d="M19 6a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v14.66h.01c.01.1.05.2.12.28a.5.5 0 0 0 .7.03l5.67-4.12 5.66 4.13a.5.5 0 0 0 .71-.03.5.5 0 0 0 .12-.29H19V6zm-6.84 9.97L7 19.64V6a1 1 0 0 1 1-1h9a1 1 0 0 1 1 1v13.64l-5.16-3.67a.49.49 0 0 0-.68 0z" fill-rule="evenodd"></path>
                </svg>`;
                flagButton.addEventListener('click', function () { raise_image(image_id); });


                let reloadButton = document.createElement("button");
                reloadButton.id = 'button-reload';
                reloadButton.className = "a9s-toolbar-btn";
                reloadButton.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 36 36">
                    <path d="M26.47 9.53C24.3 7.35 21.32 6 18 6 11.37 6 6 11.37 6 18s5.37 12 12 12c5.94 0 10.85-4.33 11.81-10h-3.04c-.91 4.01-4.49 7-8.77 7-4.97 0-9-4.03-9-9s4.03-9 9-9c2.49 0 4.71 1.03 6.34 2.66L20 16h10V6l-3.53 3.53z" />
                </svg>`;
                reloadButton.addEventListener('click', load_random);

                let saveButton = document.createElement("button");
                saveButton.id = 'button-save';
                saveButton.className = "a9s-toolbar-btn";
                saveButton.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 36 36">
                    <path d="M13.5 24.26L7.24 18l-2.12 2.12 8.38 8.38 18-18-2.12-2.12z" />
                </svg>`
                saveButton.addEventListener('click', function () { save_annots_to_coco(image_id); });

                let rejectButton = document.createElement("button");
                rejectButton.id = 'button-reject';
                rejectButton.className = "a9s-toolbar-btn";
                rejectButton.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 36 36">
                    <path d="M18 3C9.71 3 3 9.71 3 18s6.71 15 15 15 15-6.71 15-15S26.29 3 18 3zm7.5 20.38l-2.12 2.12L18 20.12l-5.38 5.38-2.12-2.12L15.88 18l-5.38-5.38 2.12-2.12L18 15.88l5.38-5.38 2.12 2.12L20.12 18l5.38 5.38z"/>
                </svg> `;
                // TODO: persist the rejected list with cookies @nischal
                rejectButton.addEventListener('click', function () { rejectedList.push(image_id); load_random() });

                // document.getElementById('toolbar').prepend(flagButton)
                // document.getElementById('toolbar').prepend(saveButton)
                // document.getElementById('toolbar').prepend(reloadButton)
                // document.getElementById('toolbar').prepend(rejectButton)

                // document.getElementsByClassName('a9s-toolbar')[0].prepend(saveButton);
                // document.getElementsByClassName('a9s-toolbar')[0].prepend(reloadButton);
                // document.getElementsByClassName('a9s-toolbar')[0].prepend(rejectButton);

                ran_anno.on('createSelection', async function (selection) {
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

                let rectButton = document.createElement("button");
                rectButton.id = 'button-rect';
                rectButton.className = "a9s-toolbar-btn";
                rectButton.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 70 50">
                    <g>
                        <rect x="12" y="10" width="46" height="30" />
                        <circle cx="12"  cy="10"  r="5" />
                        <circle cx="58" cy="10"  r="5" />
                        <circle cx="12"  cy="40" r="5" />
                        <circle cx="58" cy="40" r="5" />
                    </g>
                </svg> `;
                rectButton.addEventListener('click', function () { console.log('selected rect'); ran_anno.setDrawingTool('rect'); ran_anno.setDrawingEnabled(true) });
                // document.getElementById('toolbar').prepend(rectButton)

                if (screen.width < 480) {
                    // console.log('aa')
                    $('div[title="Zoom in"]').parent().parent().css('display', 'block') // document.querySelector('[title="Zoom in"]').setAttribute("style", "display:block")
                    $('div[title="Zoom in"]').css('display', 'block') // document.querySelector('[title="Zoom in"]').setAttribute("style", "display:block")
                    $('div[title="Zoom out"]').css('display', 'block') // document.querySelector('[title="Zoom out"]').setAttribute("style", "display:block")
                    $('div[title="Go home"]').css('display', 'block') // document.querySelector('[title="Go home"]').setAttribute("style", "display:block")
                    $('div[title="Toggle full page"]').css('display', 'block') // document.querySelector('[title="Toggle full page"]').setAttribute("style", "display:block")
                    // document.querySelector('[title="Pan"]').setAttribute("style", "display:block")
                    // document.querySelector('[title="Reload"]').setAttribute("style", "display:block")
                    // document.querySelector('[title="Ignore"]').setAttribute("style", "display:block")
                    // document.querySelector('[title="Save"]').setAttribute("style", "display:block")
                    // document.querySelector('[title="Draw"]').setAttribute("style", "display:block")
                    // document.querySelector('[title="Flag"]').setAttribute("style", "display:block")
                }
                else {
                    console.log('bbbb')
                }

                ran_anno.on('selectAnnotation', function (a) {
                    if (document.contains(document.getElementById('label'))) {
                        document.getElementById('label').remove();
                    }
                    console.log('selectAnnotation', a);
                    // ran_anno.setDrawingTool('rect');
                    ran_anno.setDrawingEnabled(false);
                })

                ran_anno.on('cancelSelected', function (a) {
                    console.log('cancelSelected', a);
                    ran_anno.setDrawingTool('rect');
                    ran_anno.setDrawingEnabled(true);
                })

                ran_anno.on('createAnnotation', function (a) {
                    console.log('created', a);
                    ran_anno.selectAnnotation(a);
                })

                ran_anno.on('updateAnnotation', function (annotation, previous) {
                    console.log('updated', previous, 'with', annotation);
                    ran_anno.setDrawingTool('rect');
                    ran_anno.setDrawingEnabled(true);
                })

                // to do, on delete 
                ran_anno.on('deleteAnnotation', function (annotation) {
                    console.log('deleted', annotation.id);
                    if (typeof annotation.id === "number") {
                        console.log("will be deleted from coco-annotator after saving")
                        deleted_ids.push(annotation.id)
                    }
                })

                ran_anno.on('mouseEnterAnnotation', function (annotation, event) {
                    //
                    popup_label(annotation)
                })

                ran_anno.on('mouseLeaveAnnotation', function (annotation, event) {
                    //
                    if (document.contains(document.getElementById('label'))) {
                        document.getElementById('label').remove();
                    }
                })

                // load annoatations and append on image
                if (!!image_id) {
                    get_annots_from_coco(ran_anno, image_id)
                }
            })
            .catch(error => console.log(error))

        loading_status = false
        if (present_image_id === null) {
            alert("Please reload!")
        }
    }
}

async function save_annots_to_coco(im_id) {
    var anns = ran_anno.getAnnotations()
    // confirm("Are you sure that image completely annotated and confirm saving "+anns.length+" annotations? please submit only if image is completely annotated.")
    console.log(anns)
    var ann_id;
    var ann;
    for (ann_id in anns) {
        ann = anns[ann_id]
        if (ann.target.selector.type === 'FragmentSelector') {
            var is_it_bbox = true
            var value = ann.target.selector.value
            var format = value.includes(':') ? value.substring(value.indexOf('=') + 1, value.indexOf(':')) : 'pixel';
            var coords = value.includes(':') ? value.substring(value.indexOf(':') + 1) : value.substring(value.indexOf('=') + 1);
            var [x, y, w, h] = coords.split(',').map(parseFloat)
            var cat_name = ann.body[0].value
            var cat_id = cat_dict[cat_name]
            console.log(x, y, w, h, cat_id, ann.id)
            var box = [x, y, w, h]
            var seg = [[x, y, x + w, y, x + w, y + h, x, y + h]]
        }
        else if (ann.target.selector.type === "SvgSelector") {
            var is_it_bbox = false
            console.log("svg")
            var value = ann.target.selector.value
            var coords = value.includes('=') ? value.substring(value.indexOf('=\"') + 3, value.indexOf('\">')) : ""
            var cat_name = ann.body[0].value
            var cat_id = cat_dict[cat_name]
            var sep_coords = coords.split(' ')
            var flat_coords = []
            sep_coords.forEach(sep_coord => {
                var temp_cord = sep_coord.split(',').map(i => Number(i))
                flat_coords = flat_coords.concat(temp_cord)
            });
            var xs = []
            var ys = []
            for (i = 0; i < flat_coords.length; i++) {
                if (i % 2 === 0) {
                    xs.push(flat_coords[i])
                }
                else {
                    ys.push(flat_coords[i])
                }
            }
            var min_x = Math.min(...xs), max_x = Math.max(...xs)
            var min_y = Math.min(...ys), max_y = Math.max(...ys)
            var w = max_x - min_x
            var h = max_y - min_y
            var box = [min_x, min_y, w, h]
            var seg = [flat_coords]
            console.log(xs, ys, min_x, min_y, w, h, seg, cat_id)
        }
        else {
            console.log("type error")
            continue;
        }
        // if annotatation is newly created
        // id is string, then send post
        // else id is int, send put

        // "Authorization": "token from cookies"
        if (typeof ann.id === 'number') {
            fetch(base_link + "/api/annotation/" + String(ann.id), {
                "headers": {
                    "accept": "application/json, text/plain, */*",
                    "accept-language": "en-US,en;q=0.9",
                    "content-type": "application/json;charset=UTF-8"
                },
                "referrer": base_link + "/",
                "referrerPolicy": "strict-origin-when-cross-origin",
                "body": JSON.stringify({
                    category_id: cat_id,
                    bbox: box,
                    segmentation: seg,
                }),
                "method": "PUT",
                "mode": "cors",
                "credentials": "include"
            });
        }
        else if (typeof ann.id === 'string') {
            fetch(base_link + "/api/annotation/", {
                "headers": {
                    "accept": "application/json, text/plain, */*",
                    "accept-language": "en-US,en;q=0.9",
                    "content-type": "application/json;charset=UTF-8"
                },
                "referrer": base_link + "/",
                "referrerPolicy": "strict-origin-when-cross-origin",
                "body": JSON.stringify({
                    image_id: im_id,
                    category_id: cat_id,
                    isbbox: is_it_bbox,
                    segmentation: seg,
                    bbox: box,
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
    }

    // deal with deleted
    deleted_ids.forEach(deletedataset_id => {
        fetch(base_link + "/api/annotation/" + String(deletedataset_id), {
            "headers": {
                "accept": "application/json, text/plain, */*",
                "accept-language": "en-GB,en-US;q=0.9,en;q=0.8"
            },
            "referrer": base_link + "/",
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

    // to do (use sockets or normal put?)
    // image.cs_annotated.append(user), if user not signin: user,user_name = Anonymous
    if (!submittedList.includes(im_id)) {
        submittedList.push(im_id)
        annotatorSubmitted = submittedList.length
        // document.getElementById("submitted-count").innerHTML=`${annotatorSubmitted}`        
    }

    if (image_annotating_status === true) {
        console.log("confirmed as image is complete annotation")
        await fetch(base_link + "/api/image/" + String(im_id), {
            "headers": {
                "accept": "application/json, text/plain, */*",
                "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
                "content-type": "application/json;charset=UTF-8"
            },
            "referrer": base_link + "/",
            "referrerPolicy": "strict-origin-when-cross-origin",
            "body": JSON.stringify({
                cs_annotating: false,
                is_annotations_added: true,
            }),
            "method": "PUT",
            "mode": "cors",
            "credentials": "include"
        })
            .then(response => response.json())
            .then(data => {
                console.log(data)
                present_image_id = null
            })
            .catch(error => console.log(error))

        image_annotating_status = false
    }
    // alert("loading next image")
    load_random()
}

function get_dataset_stats() {
    // console.log("progress bar")
    fetch(base_link + "/api/dataset/" + String(dataset_id) + "/stats", {
        "headers": {
            "accept": "application/json",
            "accept-language": "en-US,en;q=0.9"
        },
        "referrer": base_link + "/api/",
        "referrerPolicy": "strict-origin-when-cross-origin",
        "body": null,
        "method": "GET",
        "mode": "cors"
    })
        .then(response => response.json())
        .then(data => stats = data)
        .then(() => {
            console.log("Dataset stats are fecthed.")
            let totalImages = stats.total.Images;
            let nonAnnotatedImages = stats.total["CS Annotated Images"];
            let annotatedImages = totalImages - nonAnnotatedImages
            let percentage = (annotatedImages / totalImages) * 100;
            document.getElementById("progress-bar").innerHTML
                =
                `
         <label for="file">Annotation progress: ${annotatedImages}/${totalImages}</label><br>
        <progress id="file" value="${annotatedImages}" max="${totalImages}"> ${percentage} </progress> 
        `
        })
        .catch(error => console.log(error))
}

function make_live() {
    console.log("live count")
    api_key = getToken()
    if (!!api_key) {
        // console.log(api_key)
        fetch(base_link + "/api/user/live?api_key=" + api_key, {
            "headers": {
                "accept": "application/json",
                "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
                "sec-ch-ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"90\", \"Google Chrome\";v=\"90\"",
                "sec-ch-ua-mobile": "?0",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "cross-site"
            },
            "referrer": "http://localhost:8000/",
            "referrerPolicy": "strict-origin-when-cross-origin",
            "body": null,
            "method": "GET",
            "mode": "cors",
            "credentials": "omit"
        })
            .then(response => response.json())
            .then(data => {
                console.log(data)
                document.getElementById("live-count").innerHTML = `${data.live_count} <img src="./icons/person-icon.png" height="24" width="24">`
            })
    }
}


$(document).ready(function () {
    // get_dataset_stats()
    // make_live()
    // setInterval(get_dataset_stats, 60*1000);
    // setInterval(make_live, 60*1000);
    // load_buttons()
    // load_random();
    // get_dataset_stats()

    $('body').on('click touchstart', '#object-type-select option.select-option', function () {

        var element = document.getElementById("object-type-select")
        element.value = $(this).val();
        element.size = 0;
        element.style.position = 'relative';
        element.style.zIndex = 0;

        if (tags.length > 0) {
            window.arguments.onUpdateBody(tags[0], {
                type: 'TextualBody',
                purpose: 'tagging',
                value: $(this).val()
            });
        } else {
            window.arguments.onAppendBody({
                type: 'TextualBody',
                purpose: 'tagging',
                value: $(this).val()
            });
        }
    });
})