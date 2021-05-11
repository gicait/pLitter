function datasetTabNav() {
    // Enable dataset tab controls. See also: https://getbootstrap.com/docs/3.3/javascript/#tabs
    // And: http://stackoverflow.com/questions/12131273/twitter-bootstrap-tabs-url-doesnt-change
    var tabs = ["people", "overview", "explore", "download", "external", "termsofuse", "detection-2021", "demo", "maps", "help", "upload", "annotate", "zoom"];
    for( var i=0; i<tabs.length; i++ ) {
      $("#content").append('<div role="tabpanel" class="tab-pane fade" id="' + tabs[i] + '"></div>\n');
    }
    var loaded = {};
    $('.nav-tabs a').click(function (e) {
      if(this.hash) window.location.hash = this.hash;
      $('html,body').scrollTop(0);
    });
    $(window).bind( 'hashchange', function(e) {
      var hash = window.location.hash;
      var q=hash.replace('detections','detection').replace('challenge','');
      if(q!=hash) hash=window.location.hash=q;
      var q=hash.indexOf('?'); if(q!=-1) hash=hash.substring(0,q);
      if(!loaded[hash]) $(hash).load("pages/"+hash.substring(1)+".htm");
      loaded[hash]=true; $('a[href="'+hash+'"]').tab('show');
      $('html,body').scrollTop(0);
    });
    if(!window.location.hash) window.location.hash = '#home';
    $(window).trigger('hashchange');
  }
  

//   function populateHomePage() {
//     for( var p in cocoPeople ) {
//       $("#cocoPeople").append('<span class="fontBold">'+cocoPeople[p].name +
//       '</span> '+cocoPeople[p].short+'<br/>');
//     }
//   }