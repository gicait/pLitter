function datasetTabNav()
{
    // Enable dataset tab controls. See also: https://getbootstrap.com/docs/3.3/javascript/#tabs
    // And: http://stackoverflow.com/questions/12131273/twitter-bootstrap-tabs-url-doesnt-change
    var tabs = ["dataset",
                "termsofuse",
                "tryit",
                "map",
                "upload",
                "annotate",
                "leaderboard",
                "zoom",
                "user"];
    for( var i=0; i<tabs.length; i++ ) {
      $("#content").append('<div role="tabpanel" class="tab-pane fade" id="' + tabs[i] + '"></div>\n');
    }
    var loaded = {};
    $('.navbar-nav a').click(function (e) {
      // console.log("Aaa");
      $(".nav").find(".active").removeClass("active");
      if(this.hash) window.location.hash = this.hash;
      $('html,body').scrollTop(0);
    });
    $('#signin').click(function (e) {
      $(".nav").find(".active").removeClass("active");
      if(this.hash) window.location.hash = this.hash;
      $('html,body').scrollTop(0);
    });
    $(window).bind( 'hashchange', function(e) {
      var hash = window.location.hash;
      // console.log(hash)
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