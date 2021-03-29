var iconsSelected = [];

var imIdList = [];

var categories = {
  'plastic': [{'supercategory': 'plastic', 'id': 1, 'name': 'plastic'}, {'supercategory': 'plastic', 'id': 2, 'name': 'pile'}, {'supercategory': 'plastic', 'id': 3, 'name': 'trash bin'}, {'supercategory': 'plastic', 'id': 4, 'name': 'face mask'}]
};

var superCats = [
  'plastic'
];

var catNames = [
  'plastic', 'pile', 'trash bin', 'face mask'
];

var catToId = {
  'plastic': 1, 'pile': 2, 'trash bin': 3, 'face mask': 4
};

var idToCat = {
  1: 'plastic', 2: 'pile', 3: 'trash bin', 4: 'face mask'
};

function populateExplorer() {
  // create icons html
  var div = '', i, j;
  for( i=0; i<superCats.length; i++ ){
    div += '<div class="exploreIconSubpanel">';
    var cats = categories[superCats[i]];
    for( j=0; j<cats.length; j++ ){
      div += '<img title="' + cats[j].name + '" id="icon_' + cats[j].id;
      div += '" class="exploreIconSelect" src="icons/'+cats[j].id+'.jpg"/>';
    }
    div += '</div>';
  }
  $('#exploreIconPanel').append(div);
  // add functionality to icons
  var icons = $(".exploreIconSelect");
  for ( i=0; i<icons.length; i++ ) {
    var icon = $(icons[i]);
    icon.data('state', false);
    icon.mousedown(function(ev) {
      var state = $(this).data('state');
      var cat = $(this).attr('title');
      if(!state)  $("#exploreTags").tagit("createTag", cat);
      if(state) $("#exploreTags").tagit("removeTagByLabel", cat);
    });
    iconsSelected.push(icon.attr('title'));
  }
  // setup tagit controls
  var setTag = function(tag,state) {
    var icons = $(".exploreIconSelect");
    for( i=0; i<icons.length; i++ ) {
      var icon = $(icons[i]);
      if( icon.attr('title')==tag ) {
        icon.data('state', state);
        var color = state?'#00DD00':'transparent';
        icon.css('border-color', color);
      }
    }
  };
  $("#exploreTags").tagit({
    availableTags: catNames,
    allowDuplicates: false,
    afterTagAdded: function(e, ui) {
      var lbl=ui.tagLabel, valid=iconsSelected.indexOf(lbl)!=-1 || !isNaN(lbl);
      if(!valid) { $("#exploreTags").tagit("removeTagByLabel", lbl); return; }
      setTag(lbl,true);
    },
    afterTagRemoved: function(e, ui){setTag(ui.tagLabel,false)}
  });
  // enable search button / disable other controls
  $('#exploreSearchBtn').click(function(){clearCanvas(); loadSearch()});
  $('#exploreLoading').hide();
  $('#exploreDone').hide();
  // if hash is #explore?id then go to given image id on load
  var hash, args, id;
  hash = window.location.hash;
  hash = hash.substring(hash.indexOf('?')+1);
  args = hash.split('&').map(function(x) {return x.split('=')});
  for (var i=0; i<args.length; i++) if (args[i][0] == 'id') id = args[i][1];
  if(id!=undefined){ $("#exploreTags").tagit("createTag",id); loadSearch(); }
}

$(window).scroll(function() {
  if ($(window).scrollTop() >= $(document).height() - $(window).height() - 10) {
    if ($('#exploreSearchBtn').prop('disabled') == false) {
      var randInds = popRandImageIds();
      if(randInds.length > 0) {
        $('#exploreSearchBtn').prop("disabled", true);
        $('#exploreLoading').show();
        loadSearch(randInds);
      } else {
        $('#exploreDone').show();
      }
    }
  }
});

function popRandImageIds() {
  var randImIds = [];
  var N = imIdList.length;
  for (var i=0; i<Math.min(N, 5); i++){
    var M = imIdList.length;
    var randInd = Math.floor(Math.random(M) * M);
    randImIds.push(imIdList[randInd]);
    imIdList.splice(randInd, 1);
  }
  return randImIds
}

function loadImageByCats(tags) {
  var categoryIds = tags.map(function(x){return catToId[x];});
  if (categoryIds.length == 0) categoryIds = [-1];
  var req= {"category_ids": categoryIds, "querytype": "getImagesByCats"};
  $.ajax({
    type: 'POST',
    url: 'https://images.plitter.plitter/',
    data: req,
  }).done( function(data) {
    imIdList = data;
    $('#exploreSearchCount').text(imIdList.length + ' results');
    loadVisualizations(popRandImageIds());
  }) ;
}

function loadImageData(imageIds, callback) {
  var promises = [];
  var querytypes = ["getImages", "getInstances", "getCaptions"];
  for (var i = 0; i < 3; i++) {
    var req= {"image_ids": imageIds, "querytype": querytypes[i]};
    promises.push($.ajax({
      type: 'POST',
      url: 'https://images.plitter.plitter',
      data: req,
    }).done(function(data){
      return data
    }));
  }
  Promise.all(promises).then(function(data) {
    var images = data[0];
    var instances = data[1];
    var captions = data[2];
    var imageData = {};
    for (var i=0; i<images.length; i++){
      var imgId = images[i]['id']
      imageData[imgId] = {};
      imageData[imgId]['flickr_url'] = images[i]['flickr_url'];
      imageData[imgId]['coco_url'] = images[i]['coco_url'];
      imageData[imgId]['instances'] = [];
      imageData[imgId]['captions'] = [];
    }
    for (var i=0; i<instances.length; i++){
      var imgId = instances[i]['image_id'];
      imageData[imgId]['instances'].push(instances[i]);
    }
    for (var i=0; i<captions.length; i++){
      var imgId = captions[i]['image_id'];
      imageData[imgId]['captions'].push(captions[i]['caption'].toLowerCase());
    }
    callback(imageData);
  });
}

function loadVisualizations(imageIds) {
  if (imageIds.length > 0){
    loadImageData(imageIds, function (dataImage) {
      var imageIds = Object.keys(dataImage);
      for (var j = 0; j < imageIds.length; j++) {
        var imageId = imageIds[j];
        var instances = dataImage[imageId]['instances'];
        var captions = dataImage[imageId]['captions'];
        var flickrUrl = dataImage[imageId]['flickr_url'];
        var cocoUrl = dataImage[imageId]['coco_url'];
        var catToSegms = {};
        for (var i = 0; i < instances.length; i++) catToSegms[instances[i]['category_id']] = [];
        for (var i = 0; i < instances.length; i++) {
          catToSegms[instances[i]['category_id']].push(instances[i]);
        }
        createDisplay(imageId, captions, catToSegms, flickrUrl, cocoUrl);
      }
      // unlock search button
      $('#exploreSearchBtn').prop("disabled", false);
      $('#exploreLoading').hide();
    });
  }else{
    // unlock search button
    $('#exploreSearchBtn').prop("disabled", false);
    $('#exploreLoading').hide();
  }
}

function createDisplay(imageId, captions, catToSegms, flickrUrl, cocoUrl) {
  // url
  var urlIcon = '<span class="exploreIcon" title="url to share this image"><img id="exploreURLIcon" class="exploreIconImage" src="icons/url.jpg"></span>'
  var cocoURL = '<a href="#explore?id=' + imageId + '" target="_blank">' + 'http://plitter.plitter/#explore?id=' + imageId + '</a>';
  var flickrURL = '<a href="' + flickrUrl + '" target="_blank">' + flickrUrl + '</a>';
  var urlText = cocoURL + '<br>' + flickrURL;
  // caption
  var captionIcon = '<span class="exploreIcon" style="margin-right:10px" title="show captions"><img id="exploreCaptionIcon" class="exploreIconImage" src="images/cocoicons/sentences.jpg"></span>'
  var captionText = '<span>' + captions.join('<br>') + '</span>';
  // icon
  var catIcons = '';
  var iconIds = Object.keys(catToSegms);
  for (var i = 0; i < iconIds.length; i++) {
    catIcons += '<span class="exploreIcon" title="' + idToCat[iconIds[i]] + '"><img data="' + iconIds[i] + '" class="exploreIconImage exploreCategoryImage" src="images/cocoicons/' + iconIds[i] + '.jpg"></span>';
  }
  // blank
  var blankIcon = '<span class="exploreIcon" title="hide segmentations"><img id="exploreBlankIcon" class="exploreIconImage" src="images/cocoicons/blank.jpg"></span>';
  // Create explore image display
  var display =
  '<div class="imageDisplay" id="imageDisplay' + imageId + '" style="margin-bottom:15px">' +
  '<div class="icons" style="display:inline-block">' + urlIcon + captionIcon + catIcons + blankIcon + '</div>' +
  '<div class="url" style="display:none">' + urlText + '</div>' +
  '<div class="caption" style="display:none">' + captionText + '</div>' +
  '<div style="margin-top:1px"><canvas class="canvas"></canvas></div>' +
  '</div>';
  // Create DOMs
  $('#exploreImageDisplayList').append(display);
  var display = $('#imageDisplay' + imageId)
  // Draw polygon on the image
  var canvas = display.find('.canvas')[0];
  var ctx = canvas.getContext("2d");
  var img = new Image;
  img.src = cocoUrl.replace("http://images.plitter.plitter", "https://images.plitter.plitter");
  img.onload = function () {
    canvas.width = this.width;
    canvas.height = this.height;
    renderImage(ctx, this);
    renderSegms(ctx, this, catToSegms);
  }
  // set up data for display
  display.data('image', img); // store image object in display
  display.data('catToSegms', catToSegms); // store image object in display
  // Add listener to URL icon
  display.find('#exploreURLIcon').on('click', function () {
    var x = $(this).parents('.imageDisplay').find('.url');
    if (x.css('display') == 'none') x.css('display', 'block');
    else x.css('display', 'none');
  });
  // Add listeners category icon(s)
  display.find('#exploreCaptionIcon').on('click', function () {
    var x = $(this).parents('.imageDisplay').find('.caption');
    if (x.css('display') == 'none') x.css('display', 'block');
    else x.css('display', 'none');
  });
  // Add listener to category icons
  var categoryIcons = display.find('.exploreCategoryImage');
  for (var i = 0; i < categoryIcons.length; i++) {
    $(categoryIcons[i]).mouseenter(function () {
      var iconId = $(this).attr('data');
      var img = $(this).parents('.imageDisplay').data('image');
      var catToSegms = $(this).parents('.imageDisplay').data('catToSegms');
      renderImage(ctx, img);
      renderSegms(ctx, img, {iconId: catToSegms[iconId]});
    });
    $(categoryIcons[i]).mouseout(function () {
      var img = $(this).parents('.imageDisplay').data('image');
      var catToSegms = $(this).parents('.imageDisplay').data('catToSegms');
      renderImage(ctx, img);
      renderSegms(ctx, img, catToSegms);
    });
  }
  // Add listener to blank icon
  display.find('#exploreBlankIcon').mouseover(function () {
    renderImage(ctx, $(this).parents('.imageDisplay').data('image'));
  });
  display.find('#exploreBlankIcon').mouseout(function () {
    var img = $(this).parents('.imageDisplay').data('image');
    var catToSegms = $(this).parents('.imageDisplay').data('catToSegms');
    renderImage(ctx, img);
    renderSegms(ctx, img, catToSegms);
  });
}

function renderSegms(ctx, img, data) {
  var cats = Object.keys(data);
  for (var i=0; i<cats.length; i++){
    // set color for each object
    var segms = data[cats[i]];
    for (var j=0; j<segms.length; j++){
      var r = Math.floor(Math.random() * 255);
      var g = Math.floor(Math.random() * 255);
      var b = Math.floor(Math.random() * 255);
      ctx.fillStyle = 'rgba('+r+','+g+','+b+',0.7)';
      var polys = JSON.parse(segms[j]['segmentation']);
      // loop over all polygons
      for (var k=0; k<polys.length; k++){
        var poly = polys[k];
        ctx.beginPath();
        ctx.moveTo(poly[0], poly[1]);
        for (m=0; m<poly.length-2; m+=2){
          // let's draw!!!!
          ctx.lineTo(poly[m+2],poly[m+3]);
        }
        ctx.lineTo(poly[0],poly[1]);
        ctx.lineWidth = 3;
        ctx.closePath();
        ctx.fill();
        ctx.strokeStyle = 'black';
        ctx.stroke();
      }
    }
  }
}

function renderImage(ctx, img) {
  ctx.clearRect(0, 0, img.width, img.height);
  ctx.drawImage(img, 0, 0);
}

function loadSearch(ids) {
  var tags = $("#exploreTags").tagit("assignedTags");
  // disable search button and show loading
  $('#exploreSearchBtn').prop("disabled", true);
  $('#exploreLoading').show();
  $('#exploreDone').hide();
  if (ids != undefined){
    loadVisualizations(ids);
  } else if($.isNumeric(tags[0])){
    loadVisualizations([tags[0]]);
    imIdList = [];
  } else {
    loadImageByCats(tags);
  }
}

function clearCanvas() {
  imIdList = [];
  $('.imageDisplay').remove();
}
