/* Copyright (c) 2011 Securo S.r.L. <info@securo.it> */

function showErrorNotification(msg) {
    var alertDiv = [
        '<div class="alert alert-error fade in"><a class="close" data-dismiss="alert">×</a>',
        msg,
        '</div>'
    ];
    $('#notification-section').append(alertDiv.join('\n'));
}

/* TODO: avoid sending the thumbnail.  See ThumbnailOffset and ThumbnailLength in:
 *   exiftool -All pic.jpg -v5
 *
 */
function extractExifData(data) {

    if (data.getByteAt(0) != 0xFF || data.getByteAt(1) != 0xD8) {
        console.log("ERROR: not a valid jpeg");
        return []; // not a valid jpeg
    }

    var iOffset = 2;
    var iLength = data.getLength();
    while (iOffset < iLength) {
        if (data.getByteAt(iOffset) != 0xFF) {
            console.log("ERROR: Not a valid marker at offset " + iOffset + ", found: " + data.getByteAt(iOffset));
            return []; // not a valid marker, something is wrong
        }

        var iMarker = data.getByteAt(iOffset+1);
        //console.log("read: " + data.getByteAt(iOffset) + ":" + data.getByteAt(iOffset+1));

        if (iMarker == 225) {
            // 0xE1 = Application-specific 1 (for EXIF)
            exifLength = data.getShortAt(iOffset+2, true) - 2;
            console.log("Found 0xFFE1 marker at: " + iOffset + ".");
            console.log("Exif length: " + exifLength );
            var exifStart = iOffset + 4;
            var exifdata = data.getRawData().slice(exifStart, exifStart+exifLength);
            //exifdata = data.getRawData().slice(0, 2+4+exifLength);
            //exifdata = data.getRawData().slice(0, 2+4+exifLength)
            return exifdata;
            //return readEXIFData(data, iOffset + 4, data.getShortAt(iOffset+2, true)-2);
        } else {
            iOffset += 2 + data.getShortAt(iOffset+2, true);
        }
    }
}

function extractMetadata(data) {

    if (data.getByteAt(0) != 0xFF || data.getByteAt(1) != 0xD8) {
        console.log("ERROR: not a valid jpeg");
        return []; // not a valid jpeg
    }

    var iOffset = 0;
    var iLength = data.getLength();
    var metaLength = 0;
    var segLength;

    while (iOffset < iLength) {
        if (data.getByteAt(iOffset) != 0xFF) {
            console.log("Not a valid marker at offset " + iOffset + ", found: 0x" + data.getByteAt(iOffset).toString(16));
            metaLength = iOffset;
            break;
        }

        var iMarker = data.getByteAt(iOffset+1);
        //console.log("read: " + data.getByteAt(iOffset) + ":" + data.getByteAt(iOffset+1));

        // from 0xE0 to 0xEE (app segments) - from 0xF0 to 0xFD (jpeg extensions) and 0xFE (jpeg comment) and 0xDB (DQT, define quantization tables).  Note that DQT is necessary for extractig metadata.  It is not clear why.
        if ((iMarker >= 0xE0 && iMarker <= 0xFF) || iMarker == 0xDB) {
            segLength = data.getShortAt(iOffset+2, true) - 2;
            console.log("Found marker 0xff" + iMarker.toString(16) + " at: " + iOffset);
            console.log("Segment length: " + segLength);

            iOffset += segLength+2;

            //padding
            while (data.getByteAt(iOffset) == 0x00 && data.getByteAt(iOffset+1) == 0x00) {
                console.log('skipping two bytes');
                iOffset += 2;
                continue;
            }
        } else {
            console.log('false alarm. found: 0xff' + iMarker.toString(16) + ' at: ' + iOffset);
            iOffset += 2;
        }
    }

    if( metaLength != 0 ) {
        var exifdata = data.getRawData().slice(0, metaLength);
        exifdata += data.getRawData().slice(iLength-3); // Add an EOI
        return exifdata;
    } else {
        return [];
    }
    //return readEXIFData(data, iOffset + 4, data.getShortAt(iOffset+2, true)-2);
}


/**  Update the metadata associated to the supplied uimp retrieving the metadata from file, exifdata, url or uimpSrc.
 *
 * uimp (required): the uimpId to update
 * format (required): json (for now)
 *
 * file (optional):
 * url (optional):
 * exifdata (optional):
 * uimpSrc (optional): useful for merging
 *
 */
function postMetadata(params) {

    // REST Convention:
    //   POST /expense-report
    //   PUT /expense-report/10929

    console.log('postMetadata');
    console.log(params);

    var postdata = {
        action: 'metadata-post',
        format: params.format,
        uimpId: params.uimp
    }

    if( params.file ) {
        getExifLocal(params.file, function(exif) {
            console.log("completed getExifLocal for file.");
            // trasmorm the params object.
            params.file = null;
            params.exifdata = exif;
            postMetadata(params);
        }, function(errormsg) {
            showErrorNotification(errormsg);
        });
        return;
    } else if( params.exifdata ) {
        var data = Crypto.util.bytesToBase64( Crypto.charenc.Binary.stringToBytes(params.exifdata) );
        postdata.exifdata = JSON.stringify(data);
    } else if( params.uimpSrc ) {
        postdata.uimpSrcId = params.uimpSrc;
    } else if( params.url ) {
        postdata.imageUrl = params.url;
    }

    console.log('postdata:');
    console.log(postdata);

    $.ajax({
        type: 'POST',
        url: 'view.php',
        data: postdata,
        success: params.success,
        dataType: params.format
    });
}

/** Get the metadata from file, url, exifdata (binary) or uimpId.  Params is an object with:
 *
 *  format (required): html or json
 *  file (optional)
 *  uimpId (optional)
 *  exifdata (optional)
 *  url (optional): is also used when format is html to show an image preview.
 *  success (optional): success callback
 *
 * */
function getMetadata(params) {
    console.log(['getMetadata params: ', params]);

    var postdata = {
        action: 'metadata-get',
        format: params.format
    }
    if( params.url ) {
        postdata.imageUrl = params.url;
    }

    if( params.file ) {
        getExifLocal(params.file, function(exif) {
            console.log("completed getExifLocal for file.");
            //showErrorNotification("").fadeOut();

            //postToUrl('view.php', { exifdata: data } );
            //getMetadata({exifdata: exif, format: params.format, success: params.success});

            // trasmorm the params object.
            params.file = null;
            params.exifdata = exif;
            getMetadata(params);
        }, function(errormsg) {
            showErrorNotification(errormsg);
        });
        return;
    }
    else if( params.exifdata ) {
        var data = Crypto.util.bytesToBase64( Crypto.charenc.Binary.stringToBytes(params.exifdata) );
        postdata.exifdata = JSON.stringify(data);
    }
    else if( params.uimpId ) {
        postdata.uimpId = params.uimpId;
    }
    else if( params.url ) {
        // do nothing
    }

    console.log(['getMetadata postdata: ', postdata]);

    $.ajax({
        type: 'POST',
        url: 'view.php',
        data: postdata,
        success: params.success,
        error: function (xhr, textStatus, errorThrown) {
            // ajaxError(xhr, textStatus, errorThrown);  /this expects that the returned format is json
            console.log('ajax error status: ' + textStatus + '; error: ' + JSON.stringify(errorThrown));
            console.log('xhr.responseText: ' + xhr.responseText);
            params.error && params.error();
        },
        dataType: params.format
    });
}

/** Efficient function to read only part of the binary data... unfortunately it does not work for ObjectUrls. 
 *
 */
/*
function getExifLocal(imgsrc, completeCb) {
    BinaryAjax(
        imgsrc,
        function(oHTTP) {
            var data = oHTTP.binaryResponse;
            //parseExifData(data.getRawData());
            var exifdata = extractExifData(data);
            parseExifData(exifdata, completeCb);
        },
        function() {
            console.log("Something went wrong in BinaryAjax");
        },
        [0, 65536]
    )
}
*/

/** */
function getExifLocal(file, successCb, errorCb) {
    var reader = new FileReader();

    reader.onerror = function(e) {
        errorCb("Error reading file: " + e.target.error.code);
    };

    /*
    reader.onprogress = function(e) {
        if( e.lengthComputable ) {
            var loaded = Math.round(e.loaded / e.total);
            console.log('loaded: '+loaded);
        }
        console.log("onprogress:");
        console.log(e);
    };
    */

    reader.onload = (function() {
        return function(event) {
            //console.log(event.target.result);
            data = event.target.result;
            data = new BinaryFile(data, 0, data.length);
            var exifdata = extractMetadata(data);
            if( exifdata.length == 0 ) {
                errorCb("Problems extracting exif data");
            } else {
                successCb(exifdata);
            }
        }
    })();

    // Read in the image file as a data url.
    //reader.readAsDataURL(file);
    reader.readAsBinaryString(file);
    //reader.readAsText(file);
}

function accountLogout() {
    hasher.authenticated = false;
    location.href = "flickr.php?action=logout";
}

function accountRefreshPictures() {
    console.log("Refreshing...");
    updateUserPictures(hasher.user);
    loadManager();
}

function accountRefresh() {
    console.log("Refreshing...");
    updateUser(hasher.user);
    updateUserPictures(hasher.user);
}

function updateUserForm(e) {
    if( typeof e != 'undefined' ) {
        code = (e.keyCode ? e.keyCode : e.which);
        if (code != 13) 
            return;
        e.preventDefault();
    }
    var username = $(':input[name=fuid]')[0].value;
    username = $.trim(username);
    console.log("updateUserForm.  username: " + username + "; hasher.user.username = " + hasher.user.username);

    if( username == hasher.user.username ) {
        console.log("username did not change");
        return;
    }

    hasher.user.username = username;
    updateUserPictures(hasher.user);
}

function checkReturnedData(params) {
    params.format = params.format || 'json';
    //console.log('ajax return data: ');console.log(params.data);

    if( typeof params.data == 'undefined' ) {
        showErrorNotification('Server error... try later.');
        return false;
    }

    if( params.format == 'json' && params.data.status != 'success' ) {
        showErrorNotification('Error: ' + params.data.message );
        return false;
    }

    //showErrorNotification('').fadeOut();
    return true;
}

function updateUserPictures(user) {
    //force = (typeof force == 'undefined') ? false : force;
    if( user.username == "" ) {
        console.log("Empty username");
        return;
    }

    console.log("username: " + user.username);
    $('#account-loading').show();

    var checker;
    var updateInProgress = true;
    //$('#account-refresh-update').html('0%').fadeIn();
    checker = setInterval(function () {
        $.ajax({
            type: 'POST',
            url: 'flickr.php',
            timeout: 2000,
            data: {action: 'progress'},
            success: function(data) {
                if( ! checkReturnedData({data: data}) ) {
                    clearInterval(checker);
                    return;
                }
                var stored = (data.uimpsStored + data.instancesStored) / 2;
                //$('#account-refresh-update').html("Computed: " + data.hashesComputed + " / " + data.hashesTotal + " Stored: " + stored + " / " + data.hashesTotal);
                var percent = Math.ceil( ((data.hashesComputed + stored) / (data.hashesTotal*2)) * 100 );
                if( updateInProgress ) {
                    $('#account-refresh-update').html( percent + '%').fadeIn();
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                clearInterval(checker);
                $('#account-loading').hide();
                if( textStatus !== 'timeout' ) {
                    console.log('error in action progress: ' + textStatus + '; ' + errorThrown);
                    showErrorNotification('Server error, please retry later.');
                }
            },
            dataType: 'json'
        });
    }, 3 * 1000);

    /*
    var updater = setInterval(function () {
        hasher.uimps = null; // This is ugly, but forces a server query.
        loadManager();
    }, 10 * 1000);
    */

    // Remember that if this long running ajax call enables the throbber, launching the ajax call in a timer should solve the problem.

    $.ajax({
        type: 'POST',
        url: 'flickr.php',
        data: {action: 'update', user: user.username},
        success: function (data) {
            updateInProgress = false;
            clearInterval(checker);
            //clearInterval(updater)

            if( ! checkReturnedData({data: data}) )
                return;

            $('#account-loading').hide();

            $('#account-refresh-update').html(data.newPhotos+" new pictures").fadeIn(200);
            hasher.user = data.user; // Is this necessary?

            // Update cached uimps and instances.
            console.log('merging new uimps and instances');

            $.extend(hasher.uimps    , data.newUimps)
            $.extend(hasher.instances, data.newInstances)
        },
        dataType: 'json'
    } );
}

// insertAdjacentHTML(), insertAdjacentText() and insertAdjacentElement 
// for Netscape 6/Mozilla by Thor Larholm me@jscript.dk 
if (typeof HTMLElement != "undefined" && !HTMLElement.prototype.insertAdjacentElement) {
    HTMLElement.prototype.insertAdjacentElement = function (where, parsedNode) {
        switch (where) {
            case 'beforeBegin':
                this.parentNode.insertBefore(parsedNode, this)
                    break;
            case 'afterBegin':
                this.insertBefore(parsedNode, this.firstChild);
                break;
            case 'beforeEnd':
                this.appendChild(parsedNode);
                break;
            case 'afterEnd':
                if (this.nextSibling) this.parentNode.insertBefore(parsedNode, this.nextSibling);
                else this.parentNode.appendChild(parsedNode);
                break;
        }
    }

    HTMLElement.prototype.insertAdjacentHTML = function (where, htmlStr) {
        var r = this.ownerDocument.createRange();
        r.setStartBefore(this);
        var parsedHTML = r.createContextualFragment(htmlStr);
        this.insertAdjacentElement(where, parsedHTML)
    }


    HTMLElement.prototype.insertAdjacentText = function (where, txtStr) {
        var parsedText = document.createTextNode(txtStr)
            this.insertAdjacentElement(where, parsedText)
    }
}

function onDragEnter(e) {
    e = e.originalEvent;
    e.stopPropagation();
    e.preventDefault();
}

function onDragOver(e) {
    e = e.originalEvent;
    e.stopPropagation();
    e.preventDefault();
    if($claimerDropbox)
        $claimerDropbox.addClass('rounded');
    if($viewerDropbox)
        $viewerDropbox.addClass('rounded');
}

function onDragLeave(e) {
    e = e.originalEvent;
    e.stopPropagation();
    e.preventDefault();
    if($claimerDropbox)
        $claimerDropbox.removeClass('rounded');
    if($viewerDropbox)
        $viewerDropbox.removeClass('rounded');
}

function hamming(h1, h2) {
    var h = 0
    if( typeof h1 == "number" ) {
        // Beware of overflows! 64bit integers in javascript are not available!
        var d = h1 ^ h2
        while (d) {
            h += 1
            d &= d - 1
        }
    } else if ( typeof h1 == "string" ) {
        //h1.text.charAt(i)
        // or 
        //var chars = str.toLowerCase().split('')
        //for(c in chars) ...
    } else if ( Object.prototype.toString.apply(h1) === '[object Array]' ) {
        for (var i=0, n = h1.length; i < n; i++) {
            h += h1[i] != h2[i]
        }
    }
    return h
}

function average_hash(data, hash) {
    var hash = new Array(8*8); 
    var avg = 0;
    for (var i = 0, j = 0, n = data.length; i < n; i += 4, j += 1) {
        //hash[j] = 0.2126*data[i+0] + 0.7152*data[i+1] + 0.0722*data[i+2];
        hash[j] = 0.299*data[i+0] + 0.587*data[i+1] + 0.114*data[i+2];
        avg += hash[j];
    }
    avg /= hash.length;
    //console.log( "Average: " + avg);

    // This does not work because it does not modify the values in the array...
    /* hash.forEach(function(v) { v = v > avg ? 1 : 0; }); */

    // This does not work for some other reason (maybe it does not have access to avg?)
    //hash.map(function(v) { return (v > avg ? 1 : 0); });
    for (var i=0, n = hash.length; i < n; i++) {
        hash[i] = hash[i] >= avg ? 1 : 0;
    }
    console.log( "hash: " + hash.join('') );

    //return reduce(lambda x, (y, z): x | (z << y),
    /*
    var h = 0;
    for (var i=0, n = hash.length; i < n; i++) {
        h |= (hash[i] << i)
        console.log( "h   : " + h );
    }
    console.log( "h   : " + h );
    */

    return hash;
}

/** Credit: http://stackoverflow.com/questions/133925/javascript-post-request-like-a-form-submit/133997#133997 */
function postToUrl(path, params, method) {
    method = method || "post"; // Set method to post by default, if not specified.

    // The rest of this code assumes you are not using a library.
    // It can be made less wordy if you use one.
    var form = document.createElement("form");
    form.setAttribute("method", method);
    form.setAttribute("action", path);

    for(var key in params) {
        var hiddenField = document.createElement("input");
        hiddenField.setAttribute("type", "hidden");
        hiddenField.setAttribute("name", key);
        hiddenField.setAttribute("value", params[key]);
        console.log( "created hidden field with: " + key + " => " + params[key] )

        form.appendChild(hiddenField);
    }

    document.body.appendChild(form);
    form.submit();
}

/** Returns the parameter with the given 'name' or null if not found.
 * 
 * See http://stackoverflow.com/questions/901115/get-query-string-values-in-javascript 
 */
function getParameterByName(name) {
    //var match = RegExp('[?&]' + name + '(=[^&]*)').exec(window.location.href);
    //return match && decodeURIComponent(match[1].substring(1).replace(/\+/g, ' '));
    const search = window.location.href.split('?', 2)[1];
    const urlParams = new URLSearchParams(search);
    const param = urlParams.get(name);
    console.log(param);
    return param;
}

function loadClaimer() {

    $('#claimer-result').empty();
    $('#claimer-nav').empty();

    //$('#claimer-result').html("Loading...").fadeIn();

    //console.log('paginator'); console.log(claimer.paginator);

    var nu = Object.keys(claimer.queries).length;
    claimer.paginator.setMaxItems(nu);
    var queries = Object.splice(claimer.queries, claimer.paginator.start, claimer.paginator.end - claimer.paginator.start);
    console.log('comparing: '); console.log(queries);

    var threshold = 15;
    var maxMatches = 5;

    $.each(queries, function(imgId, query) {
        if( query.type == 'url' )
            createThumbnail(hasher.urls[imgId], imgId);
        if( query.type == 'file' )
            createThumbnail(hasher.objectUrls[imgId], imgId);
    });

    // Separate new from already computed queries 
    var alreadyComputedQueries = {};
    $.each(queries, function(imgId, query) {
        if( query.results !== null ) {
            console.log('queries[' + imgId + '] alread computed');
            alreadyComputedQueries[imgId] = query;
            delete queries[imgId];
        }
    });

    compareQuery(queries, function(queriesResults) {
        //console.log('returned queries:'); console.log(queriesResults);

        // Merge results
        $.each(queriesResults, function(imgId, results) {
            claimer.queries[imgId].results = results;
            results = sortObjectsByValue(results, 'hamdist')

            claimer.queries[imgId].matches = Object.splice(
                Object.filter(results, function(uimpId, result) { return (result.hamdist <= threshold); } ),
                0, maxMatches 
            );
        });

        claimer.queriesDisplayed = $.extend({}, queries, alreadyComputedQueries);
        populateClaimerResult(claimer.queriesDisplayed);

        $('#claimer-actions').fadeIn();

    });

    //var navbar = createNavigationBar(claimer.paginator)

    // Create the navigation bar
    var nav = [];
    nav.push('<div>');
    if(claimer.paginator.start != 0)
        nav.push('<a href="javascript:claimer.paginator.prev();loadClaimer();">&lt; prev</a>')
    nav.push('' + (claimer.paginator.start+1) + ' - ' + Math.min(claimer.paginator.end, nu)+ ' of ' + nu);
    if( nu - claimer.paginator.end > 0 )
        nav.push('<a href="javascript:claimer.paginator.next();loadClaimer();">next &gt;</a>')
    nav.push('</div>');
    document.getElementById('claimer-nav').insertAdjacentHTML('afterBegin', nav.join('\n'));

}

function populateClaimerResult(queries) {
    // $('#claimer-result').empty();
    console.log('populating claimer with queries:'); console.log(queries);

    var imgdiv;
    var autoselectThreshold = 10;

    $.each(queries, function(imgId, query) {

        // TODO: it seems that for big images the divparent could still be in creation.
        var divparent = $('#'+imgId).parents('div')[0];
        var caption = $('#'+imgId+' > .caption')[0];

        if( Object.keys(query.matches).length == 0 ) {
            imgdiv = ['<div id="imgx" class="thumbnail">',
                '<div class="noimage shadow-in">No results</div>',
                '</div>',
            ].join('\n');
            divparent.insertAdjacentHTML('beforeEnd', imgdiv);
            //caption.innerText = "No similar pictures";
        } else {
            //caption.innerText = "Similarity: " + Math.round((64-matches[0].hamdist)/64 * 100) + '%';
        }

        // caution to revoked objectUrls.
        // TODO: this should be more robust.
        var imgsrc = $('#'+imgId+' img')[0].src;
        caption.innerText = "";

        //caption.appendChild(createViewExifAnchor(imgId, imgsrc));
        var getExifAnchor = document.createElement('a');
        getExifAnchor.innerHTML = "View metadata";
        getExifAnchor.href = "#viewer?imgId=" + encodeURIComponent(imgId) + "&imgsrc=" + encodeURIComponent(imgsrc);
        caption.appendChild(getExifAnchor);

        var first = true;
        $.each( query.matches, function(uimpId, match) {
            var matchId = imgId + '-' + uimpId; //uniquely identify each match for each query
            imgdiv = document.createElement('div'); 
            imgdiv.setAttribute('id', matchId);
            imgdiv.setAttribute('class', 'thumbnail');
            imgdiv.innerHTML = [
                '<div class="image shadow-in">',
                '<img src="', match.thumbUrl, '" alt="thumb" />',
                '</div>',
            ].join('\n');
            divparent.insertAdjacentElement('beforeEnd', imgdiv);
            //console.log("  inserting match. hamdist =  " + match.hamdist);

            // jquery helps with closure here
            $(imgdiv).click({matchId: matchId}, function(event) {
                toggleImageSelect(event.data.matchId);
            });
            $(imgdiv).mouseenter({match: match}, function(event) {
                console.log('similarity: ' + event.data.match.hamdist);
            });

            if( first ) {
                first = false;
                $(imgdiv).data('selected', match.hamdist < autoselectThreshold );
                toggleImageSelect(matchId, match.hamdist < autoselectThreshold );
            }
        });

        //Object.keys(matches)[0]

        divparent.insertAdjacentHTML('afterEnd', '<div style="clear:both;"></div>');
    });
}

function compareQuery(queries, complete) {
    if( Object.keys(queries).length == 0 ) {
        complete({});
        return;
    }

    computeHashes(queries, function(hashes) {
        // hashes contains hashes or urls
        var realhashes = Object.filter(hashes, function(key, val) {return queries[key].type == 'file' } );
        var urls       = Object.filter(hashes, function(key, val) {return queries[key].type == 'url' } );

        actionCompare(JSON.stringify(realhashes), JSON.stringify(urls), complete);
    });
}

function actionCompare(hashes, urls, complete) {

    var expectedTime = 1000;
    var ticksTot = 10;
    var ticks = ticksTot;
    var up = setInterval( function() {
        hasher.updateProgress( 0.8/ticksTot );
    }, expectedTime / ticksTot);

    var postdata = {
        action: 'compare',
        userId: hasher.user.userId
    }

    if( hashes != null )
        postdata.hash = hashes;

    if( urls != null )
        postdata.urls = urls;

    console.log('actionCompare;  postdata:');
    console.log(postdata);

    //http://api.jquery.com/jQuery.ajax/
    $.ajax({
        type: 'POST',
        url: 'flickr.php',
        data: postdata,
        success: function(data){
            clearInterval(up);

            // setTimeout("document.getElementById('progress_bar').className='';", 500);
            hasher.setProgress(hasher.totalProgress);

            if( ! checkReturnedData({data: data}) )
                return;

            complete(data.result);
        },
        dataType: 'json'
    });

}

function toggleImageSelect(imgId, select) {
    // console.log('toggleImageSelect for img: ' + imgId);
    var $img = $('#'+imgId);
    var data = $img.data();
    if( typeof select != 'undefined' )
        data.selected = select;
    else
        data.selected = !data.selected;

    var $imgobj = $img.find('.image');
    if( data.selected )
        $imgobj.addClass('image-selected');
    else
        $imgobj.removeClass('image-selected');

    /*
    $img=$('#'+imgId);
    console.log($img.data());
    //$img.data({selected: ! $img.data('selected')});
    $img.data('selected', $img.data('selected') ? false : true);
    console.log($img.data());
    */
}

function mergeStatusUpdate(data, uimpId, match, mergeStatus) {
    console.log('finished metadata-post of x');
    if( data === null ) {
        ++mergeStatus.numErrors;
    } else {
        ++mergeStatus.numSuccess;
        manager.uimps[data.uimp.uimpId] = data.uimp;
        $.extend(manager.instances, data.instances)
    }
    console.log(mergeStatus);
    console.log(match);

    if( mergeStatus.numTotal == (mergeStatus.numSuccess + mergeStatus.numErrors)) {
        $('#success-notification').html('Metadata has been merged!');

        // remove queries from the claimer
        $.each(claimer.queriesDisplayed, function(imgId, query) {
            delete claimer.queries[imgId];
        });

        location.hash = '#manager?merge=';
        $(window).trigger('hashchange');
    }
}

function claimerConfirm() {
    console.log("confirming selection");
    //console.log("TODO: confirm only paginated elements")
    //return;

    $.each(claimer.queriesDisplayed, function(imgId, query) {
        // Filter only selected matches.
        // careful with the matchId.
        var selected = Object.filter(query.matches, function(uimpId, match) { return $('#'+imgId+'-'+uimpId).data('selected'); } );

        var mergeStatus = {
            numSuccess: 0,
            numErrors: 0,
            numTotal: Object.keys(selected).length
        };

        // Update metadata of each selected uimp.
        $.each(selected, function(uimpId, match) {
            postMetadata({
                uimp: match.uimp.uimpId,
                url: imgId in hasher.urls ? hasher.urls[imgId] : null,
                file: imgId in hasher.files ? hasher.files[imgId] : null,
                //uimpSrc:
                // Maybe a complete callback here is better?
                success: function (data) {
                    if( ! checkReturnedData({data: data}) )
                        data = null;
                    mergeStatusUpdate(data, uimpId, match, mergeStatus);
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    mergeStatusUpdate(null, uimpId, match, mergeStatus);
                },
                format: 'json'
            });
        });

    });
    location.hash = '#manager?merge=';
}

function createThumbnail(imgsrc, imgId) {
    var img = new Image();
    img.src = imgsrc;
    // http://www.alistapart.com/articles/practicalcss/
    var imgdiv = document.createElement('div'); 
    imgdiv.innerHTML = [
                  '<div id="'+imgId+'" class="thumbnail" >',
                      '<div class="image shadow-out" style="border: 2px solid #FB9500">',
                      '<img src="'+imgsrc+'" alt="thumb" />',
                      '</div>',
                      '<div class="caption"><img src="images/loading-big.gif" /></div>',
                  '</div>',
                  /*
                  '<div id="'+imgId+'-res" class="thumbnail">',
                      '<div class="image shadow">',
                      '<img src="images/loading.gif" alt="loading" style="height:auto; width:auto"/>',
                      '</div>',
                  '</div>',
                  */
                 ].join('\n');
    document.getElementById('claimer-result').insertAdjacentElement('afterBegin', imgdiv);

    /*
    $(imgdiv).data('selected', false);
    $(imgdiv).click(function() {
        toggleImageSelect(imgId)
    });
    */

}

// This function should not be used...
function resizeWithCanvas(imgsrc, w, h) {
    var img = new Image();
    img.src = imgsrc;
    var canvas = document.createElement('canvas'); 
    canvas.width = w;
    canvas.height = h;
    var context = canvas.getContext('2d');
    img.onload = function () {
        context.drawImage(this, 0, 0, w, h);
        //console.log( 'wxh: '+canvas.width+'x'+canvas.height );
        console.log( canvas.toDataURL("image/jpeg") );
    }
}

//id = 0;
function computeHash(query, imgId, complete_cb) {

    // Ugly and temporary hack.
    if( imgId in hasher.urls ) {
        complete_cb(query, imgId);
        return;
    }

    var imgsrc = hasher.objectUrls[imgId];
    var img = new Image();
    img.src = imgsrc;

    //var canvas = document.getElementById('canvas');
    //There could be a leak here because the canvas variable is reassigned?
    var canvas = document.createElement('canvas'); 
    canvas.width  = 8; 
    canvas.height = 8;
    var context = canvas.getContext('2d');

    //context.drawImage(img, 0, 0);
    //context.drawImage(img, 0, 0, canvas.width, canvas.height);
    console.log( 'Image start loading on canvas' );

    // We have to be sure that the browser has loaded the image before extracting the pixel data
    img.onload = function () {

        try{
            context.drawImage(this, 0, 0, canvas.width, canvas.height);
        } catch (err)  {
            console.log(err);
        }
        console.log( 'Image '+imgId+' completely loaded' )
        //console.log( 'wxh: '+img.width+'x'+img.height );
        //resizeWithCanvas(imgsrc, img.width, img.height);

        //var context = this.onload.context;
        var imgdata = context.getImageData(0, 0, canvas.width, canvas.height);

        var hash = average_hash(imgdata.data);

        /*
        var data = imgdata.data;
        var i=0;
        hash.forEach(function(v) { 
            data[i] = data[i+1] = data[i+2] = (v == 0 ? 0 : 255); //just for visualization
            i+=4;
        });
        */

        // DOES NOT WORK, because data is not an array but an object CanvasPixelArray.  Moreover, this will invert the transparency too!
        //data.forEach(function(value) { });

        //imgdata.data = data; // Is this necessary?
        //context.putImageData(imgdata, 0, 0); // show the perceptual hash

        complete_cb( hash.join(''), imgId ); // from array to binary string.
    };

}

/*
var h;
hashes.forEach( function(h1, i1) {
    hashes.forEach( function(h2, i2) {
        h = hamming(h1, h2);
        console.log( '('+i1+','+i2+') -> '+h );
    });
});
*/

// The reader does not seem necessary anymore since i am using the objectUrl
function readFiles(files) {
    for (var i = 0, file; file = files[i]; i++) {
        if (!file.type.match('image.*')) {
            continue;
        }
        var reader = new FileReader();

        reader.onerror = function(e) {
            alert('Error code: ' + e.target.error.code);
        };

        /*
        var sp = hasher.progress;
        reader.onprogress = function(e) {
            if( e.lengthComputable ) {
                var loaded = Math.round(e.loaded / e.total);
                console.log('loaded: '+loaded);
                hasher.setProgress( sp + (loaded) );
            }
        };
        */

        // Static local variables: see: http://aymanh.com/9-javascript-tips-you-may-not-know
        // or use closure (since static local variables seem to create problems in firefox)
        /*
        reader.onload = (function() {
            var counter = 0;
            return function(event) {
                dostuff(event.target.result);

                if( ++counter == nf ) {
                    console.log( 'finished reading' );
                }

                hasher.updateProgress( 1.0 / nf );
            }
        })();
        */

        // Read in the image file as a data url.
        //reader.readAsDataURL(file);
        //reader.readAsBinaryString(file);

    }
}

/** This function (will) extract the URL from a dropped image. */
function readUrlFromClipboard(clip) {

    // Cross-site image processing:  http://www.maxnov.com/getimagedata/

    console.log(clip.types);
    // a possible result of types: 
    // ["text/html", "text", "text/uri-list", "url", "text/plain"]
    // clip.types.forEach( function(s) { console.log( clip.getData( s ) ); } );

    //http://www.maxnov.com/getimagedata/
    var s = clip.getData( "text/html" );
    console.log( "clipboard data: " + s );

    //TODO: Validate and sanitize clipboard.
    var $s = $('<div>'+s+'</div>');
    var imgsrc = $s.find('img').attr('src');
    console.log('imgsrc: ' + imgsrc);
    return imgsrc;
}

function computeHashes(queries, complete) {

    var opStatus = {
        numHashesTotal: Object.keys(queries).length,
        numHashesComputed: 0,
        hashes: {},
        complete: complete
    };

    if( Object.keys(queries).length == 0 )
        opStatus.complete(opStatus.hashes);

    for (var imgId in queries) {
        computeHash(queries[imgId].query, imgId, function (hash, imgId) {
            opStatus.hashes[imgId] = hash;
            ++opStatus.numHashesComputed;

            if( opStatus.numHashesComputed == opStatus.numHashesTotal ) {
                console.log( 'Finished computing hashes' );
                // TODO: revoke all objectUrls... no, they are still displayed!
                //windowUrl.revokeObjectURL(hasher.objectUrls[imgId]);
                opStatus.complete(opStatus.hashes);
            }
            //hasher.updateProgress( 1.0 / nf );
        });
    }
}

function onViewerSelect(param) {
    console.log('onViewerSelect');
    console.log(param);

    $('#error-notification').fadeOut();

    viewerProcessFiles(param);
}

function viewerProcessFiles(files_arr) {

    hasher.reset();
    var files = {};
    for (var i = 0, file; file = files_arr[i]; i++) {
        if( ! file.type.match('image.*') ) {
            console.log( "type is not image but: " + file.type );
            continue;
        }

        imgId = hasher.genImgId();
        files[imgId] = file;
        hasher.files[imgId] = file;
        hasher.objectUrls[imgId] = windowUrl.createObjectURL(file);

        viewer.queries[imgId] = new Query(file, 'file');

        // new query should be prepended!
        //claimer.queries = $.extend({}, {imgId: new Query(file, 'file')}, claimer.queries);

        loadViewer(imgId, hasher.objectUrls[imgId], null);
        break;
    }

    var nf = Object.keys(files).length;
    console.log('User dropped ' + files_arr.length + ' files.  ' + nf + ' are images' );
    if( nf == 0 ) {
        showErrorNotification("You can only drop <b>images</b> from your desktop.");
    }

    //loadViewer(imgId, null, null);
}

function onLinkerInputChange(param) {
    var urlenc = encodeURIComponent($('#linker-input-url').val());

    if( urlenc.length == 0 ) {
        $('#linker-result-newtab-text').hide();
        $('#linker-result-newtab-html').hide();
        $('#linker-result-popup-text').hide();
        $('#linker-result-popup-html').hide();
    } else {
        $('#linker-result-newtab-text').fadeIn();
        $('#linker-result-newtab-html').fadeIn();
        $('#linker-result-popup-text').fadeIn();
        $('#linker-result-popup-html').fadeIn();
    }


    var l = 'http://'+location.host+'/#landing?imgsrc='+urlenc;

    var link = '<a href="'+l+'" target="_blank">try it</a>';

    var opts = [
        'width=940',
        'height=640',
        'location=no',
        'menubar=no',
        'toolbar=no',
    ].join(',');

    var popup = '<a href="javascript:void(0)" onclick="window.open(\''+l+'\',\'metapicz\',\''+opts+'\');">try it</a>';

    $('#linker-result-newtab-text').html('<b>Link that opens in new tab</b><br>' + link);
    $('#linker-result-newtab-html').text(link);

    //$('#linker-result-popup-text').html('<p><code>' + popup + '</code></p>');
    $('#linker-result-popup-text').html('<b>Link that opens in popup</b><br>' + popup);
    $('#linker-result-popup-html').text(popup);
}

function onViewerDrop(e) {
    e = e.originalEvent;
    e.stopPropagation();
    e.preventDefault();

    $viewerDropbox.removeClass('rounded');
    $('#error-notification').fadeOut();

    var imgId;
    if( $.inArray("text/html", e.dataTransfer.types) != -1 ) {
        imgsrc = readUrlFromClipboard(e.dataTransfer);
        if( imgsrc == null || imgsrc == '' ) {
            showErrorNotification("Sorry, not a valid image.");
            return;
        }
        var urls = {};

        imgId = hasher.genImgId();
        //urls[imgId] = imgsrc;

        hasher.urls[imgId] = imgsrc;
        viewer.queries[imgId].query = new Query(imgsrc, 'url');

        loadViewer(imgId, imgsrc, null);
        return false;
    }

    viewerProcessFiles(e.dataTransfer.files);
    return false;
}


function onDrop(e) {
    e = e.originalEvent;
    e.stopPropagation();
    e.preventDefault();

    $claimerDropbox.removeClass('rounded');

    if( hasher.user.username == "" ) {
        console.log( "username field is empty" );
        showErrorNotification('Please login before dropping images.');
        /*
        var usernameInput = $(':input[name=fuid]')[0];
        usernameInput.style.background='#D8000C'
        setTimeout(function() {
            usernameInput.style.background='#fff'
        } , 500);
        */

        return false;
    }

    var imgId;
    if( $.inArray("text/html", e.dataTransfer.types) != -1 ) {
        imgsrc = readUrlFromClipboard(e.dataTransfer);
        if( imgsrc == null || imgsrc == '' ) {
            showErrorNotification("Sorry, not a valid image.");
            return;
        }
        var urls = {};

        imgId = hasher.genImgId();
        urls[imgId] = imgsrc;
        hasher.urls[imgId] = imgsrc;

        claimer.queries[imgId].query = new Query(imgsrc, 'url');

        loadClaimer();
        return;
    }

    //readUrlFromClipboard(e.dataTransfer);
    //var readFileSize = 0;
    var files_arr = e.dataTransfer.files;

    // files is not an array
    //var nf = files.reduce(function(a, b){ return a + (file.type.match('image.*') ? 1 : 0); });

    hasher.reset();
    // document.getElementById('progress_bar').className = 'loading';

    var files = {};
    for (var i = 0, file; file = files_arr[i]; i++) {
        if( ! file.type.match('image.*') ) {
            console.log( "type is not image but: " + file.type );
            continue;
        }
        imgId = hasher.genImgId();
        files[imgId] = file;
        hasher.files[imgId] = file;
        hasher.objectUrls[imgId] = windowUrl.createObjectURL(file);

        claimer.queries[imgId] = new Query(file, 'file');

        // new query should be prepended!
        //claimer.queries = $.extend({}, {imgId: new Query(file, 'file')}, claimer.queries);
    }

    var nf = Object.keys(files).length;
    console.log('User dropped ' + files_arr.length + ' files.  ' + nf + ' are images' );
    if( nf == 0 ) {
        showErrorNotification("You can only drop <b>images</b> from your desktop.");
    }

    loadClaimer();

    return false;
}

function restoreSession() {
    if( typeof sessionStorage.hasher != 'undefined' ) {
        console.log("restoring session...");
        hasher = JSON.parse(sessionStorage.hasher);
        console.log(hasher);

        //$(':input[name=fuid]')[0].value = username;
        updateUserPictures(hasher.user);

        // Unfortunately objectUrls are not preserved...
        //compareFiles(hasher.files);
    }
}

function checkBrowserCompatibility() {

    /*
    Modernizr.addTest('file', function () {
        return !!(window.File && window.FileList && window.FileReader && window.Blob);
    });

    if( ! Modernizr.file || ! Modernizr.canvas ) {
        console.log('Missing file API or canvas.')
        showErrorNotification('Please update your browser.');
        return false;
    }
    */

    /*
    if( typeof FileReader == "undefined" ) {
        console.log('FileReader undefined');
        return false;
    }

    try {
        var fr = new FileReader();
    } catch(err) {
        console.log('Cannot instantiate FileReader');
        return false;
    }
    */


    return true;
}

function populateUseraccount(user) {

    //$('#account-template').clone().removeAttr("id").attr('id', 'useraccount-info').insertAfter('#account-template')
    var $account = $('#account-template').clone().attr('id', 'account').insertAfter('#account-template').fadeIn();
    $account.find('#main-account h2').text('User: ' + user.username);

    var possibleIdentities = {
        'flickr': '',
        'facebook': '',
        'twitter': '',
        'picasa': ''
    };

    var $identity = $account.find('#identity-template');
    for( id in user.identities ) {
        var account = user.identities[id].account;
        $identity.clone().html('<a target="_blank" href="http://www.flickr.com/photos/' + user.identities[id].flickrUserId + '">' + account + '</a>').insertAfter($identity).show();

        delete possibleIdentities[account];
    }

    var $linkableIdentity = $account.find('#linkable-identity-template');
    for( account in possibleIdentities ) {
        $linkableIdentity.clone().html('' + account).insertAfter($linkableIdentity).show();
    }
}

function updateUser(user, success, error) {
    console.log('updateUser...');
    $.ajax({
        type: 'POST',
        url: 'user.php',
        data: { action: 'view', username: user.username, userId: user.userId, format: 'json' },
        success: function(data) {
            if( ! checkReturnedData({data: data}) )
                return;

            hasher.user = data.user;
            if( success )
                success(data.user);
        },
        error: function(jqXHR, textStatus, errorThrown) {
            if(error)
                error();
        },
        dataType: 'json'
    });
}

function showNewUserMessage(user) {
    var out = [
        '<h2>Welcome <b>' + user.username + '</b>!</h2>',
        '<p><em>picapica is cataloguing your pictures... please be patient.</em></p>',
        '<p>In the meantime you can:</p>',
        '<ul>',
            '<li>see your list of uimps growing in the <b><a href="#manager">manager</a></b></li>',
            '<li>extract and view metadata simply dragging pictures in the <b><a href="#extractor">extractor</a></b></li>',
            '<li>link and manage more online identities by clicking the linkabale accounts below</li>',
            '<li>...</li>',
        '</ul>',
        '<p>At the end of the process you will be able to claim your metadata in the <b><a href="#claimer">claimer</a></b>.',
    ].join('\n');

    var $message = $('<div>').html( out );
    $message.attr('class', 'infoblock message');
    $message.css('width', '600');
    $message.css('margin-bottom', '20px');

    // the click is attached to the whole div!
    $message.append('<p><a href="javascript:void(0)">Click here to hide this message.</a></p>').click( function() {
        $message.hide();

        var $undoClose = $('<a href="javascript:void(0)">show help</a>');
        $undoClose.click(function() {
            $undoClose.hide();
            $message.fadeIn();
            setTimeout(function() {
            }, 60*1000);
        });
        $('#useraccount').find('.message-section').prepend($undoClose);
    });

    $('#useraccount').find('.message-section').append($message);
    $('#useraccount').find('.message-section').append('<div style="clear:both; height: 10px"></div>');
}

function loadUseraccount() {
    if( ! hasher.authenticated ) {
        showErrorNotification('Please login to view your account details.');
        return;
    }

    var newUser = getParameterByName('newUser');
    console.log( 'newUser: ' + newUser )
    console.log('loadUseraccount: ' + hasher.user.username + ' (' + hasher.user.userId + ').');

    $('#account').empty();
    $('#account').remove();

    if( newUser !== null ) {
        updateUserPictures(hasher.user);
        showNewUserMessage(hasher.user);
    }

    if( hasher.user !== null ) {
        console.log( "using cached user info" );
        populateUseraccount(hasher.user);
        return;
    }

    // ... we never get here ?

    updateUser(hasher.user, function (user) {
        populateUseraccount(user);
    });
    //var $linkable-identity = $account.find('#linkable-identity-template');

}

function ajaxError(xhr, textStatus, errorThrown) {
    var msg = 'ajax error status: ' + textStatus + '; error: ' + JSON.stringify(errorThrown);
    console.log(msg);
    //remoteLog(msg, 'alert');

    var data = {};
    try{
        data = JSON.parse(xhr.responseText);
        checkReturnedData({ data: data, status: xhr.status });
    } catch(err) {
        console.log(err);
        checkReturnedData({ data: {status: 'failure' }, status: xhr.status });
    }
}

function loadViewer(imgId, imgsrc, uimpId) {

    $('#back-to-claimer').hide();
    if( ! imgId && ! imgsrc && ! uimpId ) {

        imgId = getParameterByName('imgId');
        imgsrc = getParameterByName('imgsrc');
        uimpId = getParameterByName('uimpId');

        if( ! imgId && ! imgsrc && ! uimpId ) {
            return;
        }

        if( uimpId ) {
            $('#back-to-claimer').click(function () {
                location.hash = hasher.locationHistory[hasher.locationHistory.length-2];
            }).show();;
        }
    }

    //$('#exif').remove();
    //$('#exif').empty();

    console.log( "viewer loading." );
    console.log( "params: imgId=" + imgId + "; imgsrc=" + imgsrc + "; uimpId: " + uimpId);

    console.log( "retrieving exif data..." );

    $('#exif').html('<div class="center" style="margin-top: 18px;"><img src="images/loading-big.gif" /></div>').fadeIn();

    if(imgId == null && imgsrc != null) {
        getMetadata({
            format: 'html',
            success: function (data) {
                if( ! checkReturnedData({data: data, format: 'html'}) )
                    return;
                $('#exif').html(data);
            },
            error: function (err) {
                //$('#exif').html(err || 'Unknown error.');
                showErrorNotification('Sorry, a problem occurred.');
                $('#exif').empty();
                location.href = "#landing";
                return;
            },
            //url: imgId in hasher.urls ? imgsrc : null,
            url: imgsrc,
            //file: imgId in hasher.files ? hasher.files[imgId] : null,
            file: null,
            uimpId: null
        });
        return;
    }

    /*
    getMetadata({
        format: 'html',
        success: function (data) {
            if( ! checkReturnedData({data: data, format: 'html'}) )
                return;
            $('#exif').html(data);
        },
        //url: imgId in hasher.urls ? imgsrc : null,
        url: imgsrc,
        file: imgId in hasher.files ? hasher.files[imgId] : null,
        uimpId: uimpId || null
    });
    */

    var xhr = new XMLHttpRequest
    /*
    upload = xhr.upload;
    upload.onload = function(){
        console.log("Data fully sent");
    };
    */

    xhr.onreadystatechange = function() {
        if (xhr.readyState != 4)  { return; }

        if(xhr.status != 200) {
            //$('#exif').html('Sorry, a problem occurred.');
            showErrorNotification('Sorry, a problem occurred.');
            $('#exif').empty();
            location.href = "#landing";
            return;
        }
        $('#exif').html(xhr.responseText);
    };

    var reencodedImgsrc = encodeURIComponent(decodeURIComponent(imgsrc));
    xhr.open("post", 'view.php?action=metadata-get&binary=&format=html&imageUrl='+reencodedImgsrc+'', true);
    //xhr.open("post", 'view.php?action=metadata-get&binary=&format=json&imageUrl='+imgsrc+'', true);
    //xhr.setRequestHeader("Content-length", 1);

    //xhr.send(Crypto.charenc.Binary.stringToBytes('ciao'));
    xhr.send(hasher.files[imgId]);

    //$('#exif').html(data);
    return;

}

/** Create a list of uimps with details.  Params:
* uimpsId (required)
* uimps (required)
* instances (required)
*/
function populateUimpListFromUimpsId(params) {
    console.log('populateUimpListFromUimpsId');
    //console.log(params);
    $('#uimps-list').empty();

    var uimp;
    var out = [];
    out.push('<table>');
    //$.each(params.uimps, function(uimpId, uimp) {
    $.each(params.uimpsId, function(idx, uimpId) {
        uimp = params.uimps[uimpId];
        //out.push('<div style="clear:both;"></div>');
        out.push('<tr class="infoblock">');

        out.push('<td style="width: 150px">');
        out.push( [
            '<a href="#viewer?uimpId=' + uimpId + '" >',
            '<div id="imgx" class="thumbnail">',
                '<div class="image shadow-out" style="border: 2px solid #FB9500">',
                    '<img src="' + uimp.thumbUrl + '" alt="thumb" />',
                '</div>',
            '</div>',
            '</a>',
            ].join('\n') );
        out.push('</td>');
        out.push('<td style="width: 300px">');
        out.push('<div>')
        out.push('<p><b>This photo is on:</b></p>');
        out.push('<ul>');
        var fid; 
        $.each(uimp.instances, function(nada, instanceId) {
            fid = instanceId;
            var instance = params.instances[instanceId];
            //out.push('<p><b>' + instanceId + '</b></p>');
            //out.push('<p><a href="http://www.flickr.com/photos/'+instance.data.owner+'/'+instance.data.id+'">' + instanceId + '</a></p>');
            out.push( '<li><a target="_blank" href="http://www.flickr.com/photos/'+instance.data.owner+'/'+instance.data.id+'">flickr</a></li>' );
            //out.push(JSON.stringify(instance));
        });
        out.push('</ul>');

        out.push('</div>');
        out.push('</td>');

        out.push('<td style="width: 300px">');
        out.push('<p><b>Actions:</b></p>');
        out.push('<ul>');
        out.push('<li><a target="_blank" href="flickr.php?action=link-back&instanceId=' + fid + '">Add link to uimp</a></li>');
        out.push('<li><a href="#viewer?uimpId=' + uimpId + '" >View metadata</a></li>');
        out.push('<li><a href="javascript:alert(\'not yet implemented\')" >Find duplicates</a></li>');
        out.push('</ul>');

        out.push('</td>');

        out.push('</tr>');
    });
    out.push('</table>');
    document.getElementById('uimps-list').insertAdjacentHTML('afterBegin', out.join('\n'));
}

function populateUimpList(params) {
    if( Object.keys(params.uimps).length == 0 )
        return;

    $('#uimps-list').empty();
    $('#uimps-nav').empty();

    var nu = Object.keys(params.uimps).length;
    manager.paginator.setMaxItems(nu);

    console.log(manager.paginator);

    var uimpsId = buildUimpList({uimps: params.uimps, sortBy: '', start: manager.paginator.start, end: manager.paginator.end});
    populateUimpListFromUimpsId({uimpsId: uimpsId, uimps: params.uimps, instances: params.instances});

    var numShowing = Math.min(nu, manager.paginator.perPage);
    var nav = [];
    nav.push('<div>');
    //nav.push('Showing ' + numShowing + ' of '+ nu +' uimps. ');
    if(manager.paginator.start != 0)
        nav.push('<a href="javascript:manager.paginator.prev();loadManager();">&lt; prev</a>')
    nav.push('' + (manager.paginator.start+1) + ' - ' + Math.min(manager.paginator.end, nu)+ ' of ' + nu);
    if( nu - manager.paginator.end > 0 )
        nav.push('<a href="javascript:manager.paginator.next();loadManager();">next &gt;</a>')
    nav.push('</div>');

    document.getElementById('uimps-nav').insertAdjacentHTML('afterBegin', nav.join('\n'));
}

/** Sort and splice uimps into an array.
*
* uimps (required) the uimps associative array
* sort (optional)
* start (optional)
* end (optional) required if start is supplied.
*
* returns the array of uimpsId
*/
function buildUimpList(params) {
    var sorted = [];
    console.log('buildUimpList');
    switch(params.sortBy) {
    case 'data':
        console.log('sorting by ' + params.sortBy);
    break;
    default:
        // http://stackoverflow.com/questions/280713/elements-order-for-in-loop-in-javascript
        $.each(params.uimps, function(uimpId, uimp) {
            sorted.push(uimpId);
        });
    break;
    }

    if( 'start' in params && 'end' in params ) {
        sorted = sorted.splice(params.start, params.end-params.start);
    } else if ( 'start' in params ) {
        sorted = sorted.splice(params.start);
    }

    return sorted;
}

function onUimpsOrInstancesRetrieved(data, params) {
    if( ! checkReturnedData({data: data}) ) {
        //$('#account-loading').hide();
        return;
    }

    if( 'uimps' in data ) {
        params.uimps = data.uimps;
    }
    if( 'instances' in data ) {
        params.instances = data.instances;
    }

    if( params.uimps && params.instances ) {
        //$('#account-loading').hide();

        // cache retrieved uimps and instances.
        hasher.uimps = params.uimps;
        hasher.instances = params.instances;

        populateUimpList({uimps: hasher.uimps, instances: hasher.instances});
    }
}

function loadManager() {
    console.log( "manager loading." );

    $('#uimps-list').empty();
    $('#uimps-nav').empty();

    var merge = getParameterByName('merge');
    if( merge !== null ) {
        console.log( "merge op" );
        $('#uimps-list').html('Merging...').fadeIn();
        populateUimpList({uimps: manager.uimps, instances: manager.instances});
        return;
    }

    if( hasher.uimps !== null ) {
        console.log( "using cached uimps" );
        populateUimpList({uimps: hasher.uimps, instances: hasher.instances});
        return;
    }

    console.log( "retrieving uimps data..." );
    $('#uimps-list').html('Loading...').fadeIn();

    // This will keep the partial data
    var params = {
        uimps:  null,
        instances:  null
    }

    $.ajax({
        type: 'GET',
        url: 'flickr.php',
        data: {action: 'uimps-get', format: 'json', userId: hasher.user.userId},
        success: function (data) {
            onUimpsOrInstancesRetrieved(data, params);
        },
        dataType: 'json'
    });

    $.ajax({
        type: 'GET',
        url: 'flickr.php',
        data: {action: 'instances-get', format: 'json', userId: hasher.user.userId},
        success: function (data) {
            onUimpsOrInstancesRetrieved(data, params);
        },
        dataType: 'json'
    });
}

function showBrowserIncompatible() {
    // location.hash = '#features';
    // $(window).trigger('hashchange'); // Is this necessary?

    $('.main-tab').each(function() {
        $(this).hide();
    });

    var out = [
        '<div style="margin: 50px; padding: 10px; border: 1px solid black;">',
            '<b style="color:red;">Your browser is not fully supported :(</b><br>',
            'We suggest installing the latest version of <a href="http://www.mozilla.com/">firefox</a> or <a href="http://www.google.com/chrome">chrome</a>',
        '</div>',
    ];
    //$('.subtitle').after(out.join('\n'));
    $('#browser-old').html(out.join('\n')).show();
}

$(window).bind('hashchange', function() {
    console.log( "hashchange : " + location.hash );

    if(['#camera-box', '#copyright-box', '#location-box', '#exif-box', '#xmp-box', '#icc-box', '#makernotes-box'].indexOf(location.hash) != -1) {
        //if($('a[name="'+location.hash.substring(1)+'"]').length !== 0) {
        if($(location.hash).length !== 0) {
            $(location.hash).animateHighlight();
            return;
        }
    }

    var imgsrc = getParameterByName('imgsrc');

    if( !imgsrc && !checkBrowserCompatibility() ) {
        showBrowserIncompatible();

        remoteLog( {
                msg: hasher.err,
                browser: $.browser
            },
            'alert'
        );
        //return;
    }

    if( imgsrc ) {
        hasher.viewerMode = true;
        $('#viewer-dropbox').hide();
        $('#viewer-url').hide();
    } else {
        $('#viewer-dropbox').show();
        $('#viewer-url').show();
    }


    var currentHash = location.hash.split('?',1)[0];
    hasher.locationHistory.push(location.hash);

    $('.main-tab').each(function() {
        $(this).hide();
    });

    var subtitle = hasher.subtitles[currentHash.substring(1)];
    $('.title-container .subtitle').html(subtitle);

    $('#main-nav > li').each(function() {
        $(this).removeClass('active');
    });
    $('#main-nav a[href="'+currentHash+'"]').closest('li').addClass('active');

    $(currentHash).fadeIn(200);

    switch(currentHash) {
    case '#useraccount':
        //loadUseraccount();
    break;
    case '#claimer':
        //loadClaimer();
    break;
    case '#viewer':
        loadViewer();
    break;
    case '#landing':
        if(imgsrc)
            loadViewer(null, imgsrc, null);
    break;
    case '#extractor':
    break;
    case '#manager':
        //loadManager();
    break;
    case '#linker':
    break;
    default:
        //showErrorNotification('The page does not exist');
        location.hash='#landing';
    break;
    }
});

if (!Array.prototype.indexOf) {
    Array.prototype.indexOf = function(obj, start) {
        for (var i = (start || 0), j = this.length; i < j; i++) {
            if (this[i] === obj) { return i; }
        }
        return -1;
    }
}

/** See: http://stackoverflow.com/questions/5072136/javascript-filter-for-objects */
Object.filter = function(obj, predicate) {
    var result = {}, key;
    for (key in obj) {
        if (obj.hasOwnProperty(key) && predicate(key, obj[key])) {
            result[key] = obj[key];
        }
    }
    return result;
}

Object.splice = function(obj, start, len) {
    var i = 0;
    var spliced = {};
    var end = start + len;
    for (var key in obj) {
        if( i >= end )
            break;

        if( i >= start )
            spliced[key] = obj[key];

        ++i;
    }
    return spliced;
}

function sortObjectsByValue(objs, valueName) {

    var sorted = {};
    var pairs = [];

    $.each(objs, function(key, obj) {
        pairs.push( {key: key, val: obj[valueName]} );
    });

    //console.log('pairs'); console.log(pairs);

    pairs.sort(function(p1, p2) {
        return p1.val > p2.val;
    });

    // reinsert objects in order...
    for (var i in pairs){
        // console.log('inserting pairs['+i+'].key: '+pairs[i].key);
        sorted[pairs[i].key] = objs[pairs[i].key];
    }

    //for (var i in sorted) console.log('sorted['+i+'] value: ' + sorted[i][valueName]);

    return sorted;
}

function testObjectFunctions() {
    var testobj = { 
        obj2: { 'a': 2},
        obj3: { 'a': 3},
        obj1: { 'a': 1},
        obj5: { 'a': 5},
        obj4: { 'a': 4}
    }
    var sorted = sortObjectsByValue(testobj, 'a');
    //Object.filter(results, function(uimpId, result) { return (result.hamdist <= threshold); } ),
    var filtered = Object.filter(sorted, function(key, val) { return (val.a <= 3); } );
    console.log('filtered: '); console.log(filtered);
    var spliced = Object.splice(filtered, 1, 2 );
    console.log('spliced: '); console.log(spliced);
}

if( typeof console == 'undefined' ) {
    console = {};
    console.log = function(msg) {
        hasher.err = msg;
    };
} else {
    // Override the default console.log method to store the latest message
    defaultlog = console.log;
    console.log = function(msg) {
        hasher.err = msg;
        // In IE9, the log does not have a method `call`. See http://stackoverflow.com/questions/5472938/does-ie9-support-console-log-and-is-it-a-real-function
        if(typeof defaultlog.call !== 'undefined')
            defaultlog.call(this, msg);
    }
}

function remoteLog(msg, severity) {
    if( typeof severity == 'undefined' )
        severity = 'info';

    $.ajax({
        type: 'POST',
        url: 'view.php',
        data: {action: 'log', msg: msg, severity: severity}
    });
}


//restoreSession();

//define global objects and variables.
var hasher = {};

hasher.user = null;
// hasher.user.username = ''; //let's not risk that this overwrites some other value
// hasher.user.account = 'flickr'; // This is used for unautheticated queries

hasher.uimps = null; // keeps the cached uimps.
hasher.instances = null; // keeps the cached uimps.

hasher.authenticated = false;

hasher.files = {};
hasher.objectUrls = {}; // local urls corresponding to dragged files
hasher.urls = {}; // urls of dragged (remote) images

hasher.locationHistory = [''];

hasher.err = '';

hasher.subtitles = {
    'landing': '[ view your metadata ]',
    'links': '[ make links to metadata ]',
    'manager': '[ manage your metadata ]',
    'extractor': '[ extract metadata ]',
    'useraccount': '[ user account ]',
    'viewer': '[ view your metadata ]',
    'claimer': '[ claim your metadata ]'
}

/*
var createRingBuffer = function(length){

  var pointer = 0, buffer = []; 

  return {
    get  : function(key){return buffer[key];},
    push : function(item){
      buffer[pointer] = item;
      pointer = (length + pointer +1) % length;
    }
  };
};
*/

function Paginator () {

    this.currentPage = 0;
    this.start = 0,
    this.end = 0,
    this.perPage = 0,
    this.maxItems = 0,

    this.init = function(params) {
        this.perPage = params.perPage;
        this.maxItems = params.maxItems;

        this.currentPage = 0;
        this.start = 0;
        this.end = Math.min(this.start + this.perPage, this.maxItems);
    },
    this.next = function() {
        this.start += this.perPage;
        this.end = Math.min(this.start + this.perPage, this.maxItems);
        ++this.currentPage;
    },
    this.prev = function() {
        this.start -= this.perPage;
        if( this.start < 0 )
            this.start = 0;
        this.end = Math.min(this.start + this.perPage, this.maxItems);
        --this.currentPage;
    },
    this.setMaxItems = function(maxItems) {
        this.maxItems = maxItems;
        this.end = Math.min(this.start + this.perPage, this.maxItems);
    }
}

function Query (query, type) {
    this.results = null; // results of a query
    this.matches = null; // results under threshold
    this.query = query; // a file or a url, based on type
    this.type = type;  // the string 'file' or 'url'
}

var claimer = {
    queries: {}, // array of query objects
    queriesDisplayed: {}, // array of currently shown query objects
    paginator: new Paginator()
}
claimer.paginator.init({perPage: 5, maxItems: 0})
var $claimerDropbox;

var manager = {
    uimps: {},
    instances: {},
    paginator: new Paginator()
};
manager.paginator.init({perPage: 10, maxItems: 0})

var viewer = {
    queries: {} // array of query objects
}
var $viewerDropbox;

var windowUrl = typeof window.URL != 'undefined' ? window.URL : window.webkitURL;

var picapica = {};

function picapicaInit() {
    console.log('picapicaInit.')

    hasher.setProgress = function(val) {
        this.progress = Math.round(val/this.totalProgress * 100);
        var v = this.progress;
        //console.log('setProgress: ' + v);
        if( v > 100 )
        v = 100;
        //document.querySelector('.percent').style.width = v + '%';
        // this.progressBar.style.width = v + '%';
        // this.progressBar.textContent = v + '%';
    }

    hasher.updateProgress = function(val) {
        //console.log('updateProgress: ' + val);
        hasher.setProgress((this.progress*this.totalProgress)/100 + val);
    };

    hasher._imgIdCounter = 0;
    hasher.genImgId = function() {
        ++hasher._imgIdCounter;
        return 'img-' + hasher._imgIdCounter;
    }

    hasher.reset = function() {

        hasher.progress = 0;
        hasher.setProgress(0);
    }
    //hasher.progressBar = document.querySelector('.percent'); // This creates problems when stringifying the hasher.
    hasher.totalProgress = 3;

    $claimerDropbox = $('#drop_it_like_its_hot');
    if( $claimerDropbox ) {
        // Setup drag and drop handlers.
        $claimerDropbox.on('dragenter', onDragEnter);
        $claimerDropbox.on('dragover', onDragOver);
        $claimerDropbox.on('dragleave', onDragLeave);
        $claimerDropbox.on('drop', onDrop);
    }

    $viewerDropbox = $('#viewer-dropbox');
    // Setup drag and drop handlers.
    if( $viewerDropbox ) {
        $viewerDropbox.on('dragenter', onDragEnter);
        $viewerDropbox.on('dragover', onDragOver);
        $viewerDropbox.on('dragleave', onDragLeave);
        $viewerDropbox.on('drop', onViewerDrop);
    }

    $('#error-notification').click( function() {
        $(this).fadeOut();
    });
    $('#success-notification').click( function() {
        $(this).fadeOut();
    });

    var metadataFromUrl = function() {
        var url = $('#viewer-url-input').val();
        if(url.length == 0) {
            showErrorNotification('Please enter a valid image URL');
            return;
        }

        if(url.indexOf('data:image') !== -1) {
            showErrorNotification('Extraction of metadata from a data URI currently not supported.')
            return;
        }

        if(url.indexOf('http') !== 0)
            url = 'http://' + url;
        $('#viewer-url-input').val(url);

        var urlenc = encodeURIComponent(url);
        var l = 'http://'+location.host+'/#landing?imgsrc='+urlenc;
        console.log('redirecting to: ' + l)
        location.href = l;
    }

    $('#viewer-url-go').click(function(e) {
        console.log('click');
        metadataFromUrl();
        e.preventDefault();
    });
    $('#viewer-url-input').keypress(function(event) {
        if(event.which == 13) {
            console.log('enter');
            return true; // will trigger the #viewer-url-go click event
            //metadataFromUrl();
            //return false; // avoid triggering #viewer-url-go click event
        }
    });

    //testObjectFunctions();
    //return;

    var testClaimer = false;
    var testViewer = false;
    if( testClaimer ) {
        hasher.authenticated = true;
        hasher.user = { 'username': 'mrucci', 'userId': 'dd98ce1e-9512-4a9f-ace3-839dda4f0b65' }
        hasher.user = { 'username': 'lj2shoes', 'userId': '11f6c206-8428-4c51-9978-7fa70abca578' }

        //var imgId = hasher.genImgId();
        //hasher[imgId] = imgId;
        //hasher.urls[imgId] = 'http://upload.wikimedia.org/wikipedia/commons/b/be/Tahrir_Square_on_July_08_2011.jpg';
        //hasher.urls[imgId] = 'http://farm6.static.flickr.com/5014/5541585467_08ef601263_t.jpg';
        //hasher.urls[imgId] = 'http://regex.info/i/_JEF1348.jpg';
        //hasher.urls[imgId] = 'images/_JEF1348.jpg';

        for( var i=0; i < 12 ; i++ ) {
            var imgId = hasher.genImgId();
            hasher[imgId] = imgId;
            hasher.urls[imgId] = 'images/sanyo-vpcg250.jpg';
            claimer.queries[imgId] = new Query('images/sanyo-vpcg250.jpg', 'url');
        }
        location.hash = '#claimer';
        loadClaimer();
    }

    if( testViewer ) {
        hasher.user = { 'username': 'lj2shoes', 'userId': '11f6c206-8428-4c51-9978-7fa70abca578' }
        //location.hash = '#viewer?uimpId=fb614fae-6dbd-405b-bc02-c15d88e853fa'
        //location.hash = '#viewer?uimpId=85bdaf38-8c9b-4693-9239-cf0cfab39b63'
        location.hash = '#viewer?uimpId=e1a1e1c1-bf54-47a0-95b2-afd43f0e08be'
    }

    //showErrorNotification('err');
    //$('#success-notification').html('succ');
}

$.fn.animateHighlight = function(highlightColor, duration) {
    //var highlightBg = highlightColor || "#FFFF9C";
    var highlightBg = highlightColor || "#ffbb00";
    var animateMs = duration || 1500;
    this.stop(true,true);
    var originalBg = this.css("backgroundColor");
    return this.css("background-color", highlightBg).animate({backgroundColor: originalBg}, animateMs);
};

/* vim:set et: */