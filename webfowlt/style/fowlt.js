cursor = null;
cursorid = null;
cursorindex = 0;
prevcursorindex = -1;
correction = "";
expertmode = false;
showclasses = false;

function initloader() {
    if ($('#loader').length > 0) {
        var rotation = function (){
           $("#loader").rotate({
              angle:0, 
              animateTo:360, 
              callback: rotation//,
              //easing: function (x,t,b,c,d){        // t: current time, b: begInnIng value, c: change In value, d: duration
              //    return c*(t/d)+b;
              //}
           });
        }
        rotation();
    }                
    
    /*$('#uploadfield').change(function(e){
        filename = $(this).val();
        var filename.replace("C:\\fakepath\\","")
        $('#filenamefield').val(filename);
    });*/
    


    
    if (($.browser.msie) && (parseInt($.browser.version, 10) <= 6) ) {
        $('#browsernotice').text("Your browser, Internet Explorer 6 or lower, is extremely old and is not supported by Fowlt.net! We recommend Firefox or Chrome!");
    } else if (($.browser.msie) && (parseInt($.browser.version, 10) < 9) ) {    
        $('#browsernotice').text("Fowlt does not support the browser you are currently using (probably an older version of Internet Explorer). We recommend Firefox or Chrome!");
    }
    $('#veil').click(function() {
        if( $('#sharedialog').is(":visible") ) {
            $('#veil').hide();
            $('#sharedialog').slideUp();
        }
    });
    $('#sharethis').click(function() {
        $('#veil').show(); 
        $('#sharedialog').slideDown();
    });    
    $('#startbutton').click(function() {        
        showloader();        
        window.setTimeout(function(){$('#inputform').submit()}, 10);
        return false;
    });
    $('#optintext').click(function(){$('#optin').click()});
    $('#editorarea textarea').change(function(){
        $('#filenamefield').val("");
    });    
}

function showloader() {
    $('#veil').show();
    $('#loaderwrapper').show();    
}

function hideloader() {    
    $('#veil').show();
    $('#loaderwrapper').hide();
}
