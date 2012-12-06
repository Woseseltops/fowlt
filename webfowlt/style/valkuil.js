cursor = null;
cursorid = null;
cursorindex = 0;
prevcursorindex = -1;
correction = "";
expertmode = false;
showclasses = false;

function initerrors() {    
    referenceoffset = $('#error').offset()['top'];

    current_errors = get_current_errors();
    errorcount = current_errors.length;

    if (errorcount == 0) {
        $('#suggestionarea').hide();
    }
    $('#cursorleft').click(cursorleft);
    $('#cursorright').click(cursorright);    
    $('#ignorebutton').click(ignore);
    $('#correctbutton').click(correct);
    $('#downloadbutton').click(function(){
        $('#veil').show();    
        $('#downloaddialog').slideDown();    
    });    
    $('#infobutton').click(function(){
        $('#veil').show();    
        $('#infodialog').slideDown();    
    });    
    $('#logo').click(function(){window.location='/';});
    $('#header').click(function(){window.location='/';});
    /*$('body, div, span').keyup(function(event) {
        if (event.which == '39') {
            cursorright();
            event.preventDefault();
        } else if (event.which == '37') {
            cursorleft();
            event.preventDefault();
        }
    });*/
    $('#editword').keypress(function(event){
        if (event.which == '13') {
            $('#dialogsubmit').click();
        }
    });


    /*$('#expertswitch').click(function(){
        if (expertmode) {
            expertmode = false;
            $('#expertswitch').text('Toon meer details');
            $('#expertlegenda').hide();
            $('head link:last-child').remove();            
        } else {
            expertmode = true;
            $('#expertswitch').text('Toon minder details');
            $('#expertlegenda').show();
            $('head').append('<link rel="stylesheet" href="/style/classes.css" type="text/css" />');            
        }
    });*/
    $('#classtoggle').click(function(){   
        if (showclasses) {
            $('#errorclass').css({'visibility':'hidden'});
            $('#classtoggle').text('Show mistake type');
            showclasses = false;
        } else {
            $('#errorclass').css({'visibility':'visible'});
            $('#classtoggle').text('Hide mistake type');
            showclasses = true;
        }                    
    });
    
    $('#veil').click(function(){
        $('#editdialog').slideUp();
        $('#downloaddialog').slideUp();
        $('#sharedialog').slideUp();
        $('#errordialog').slideUp();
        $('#infodialog').slideUp();
        $('#veil').hide();        

    });
    
    
   reflag_errors(errors,0);
    
    /*$.each(errors, function(i,error){
        //select the element
        var e = document.getElementById(error['wordid'])
        //mark it as an error (simple mode)
	if(error['confidence'] == 1)
        {$(e).addClass("error");}
        
        //set error classes (expert mode)
        /*$.each( error['classes'], function(j, cls) {
           $(e).addClass(cls)
        });      
        
        if (error['multispan']) {
            $.each(error['multispan'], function(j, multispanwordid){
                var emultispan = document.getElementById(multispanwordid)
                $(emultispan).addClass("error");
            });
        }
        
        //when clicked on the element    
        /*$(e).click(function() {

        });*/
        
  
        
        //when moving over the element
        /*$(e).mouseenter(function(){
            var wordid = $(this).attr('id');  
            hint(wordid);
        });
        
        $(e).mouseleave(function(){
            $('#hint').hide();
        });

    });*/
    
    //set click events
    $('.word').each(function(){$(this).click(clickword)});        

    //alot easter egg (works with middle mouse button, ctrl+click and alt+click)

    $('.alot').hide();

    $('span').click(function(evt)
	{
		if($(this).html() == 'alot') 
		{
			if(evt.which == 2 || evt.ctrlKey || evt.altKey || evt.shiftKey) 
			{$('.alot').toggle();}
		}
	});

}

function clickword() {
    //determine id            
    var wordid = $(this).attr('id');  
    
    //is this word part of a multispan? then grab the wordid of the first of the span
    abort = false;
    $.each(errors, function(j, error){
        if (errors[j]['multispan']) {
            $.each(errors[j]['multispan'], function(k,multispanwordid){
                if ((!abort) && (wordid == multispanwordid)) {
                    wordid = errors[j]['wordid'];
                    abort = true;
                }
            });
        }
    });

    if (cursorindex != -1) prevcursorindex = cursorindex;                
    cursorindex = -1;
    $.each(errors, function(j, error){
        if (errors[j]['wordid'] == wordid) cursorindex = j;
    });
                
    //unset old cursor
    if (cursor) $(cursor).removeClass('cursor');
    //set new cursor
    cursor = this;     
    cursorid = wordid;  
    $(cursor).addClass('cursor');
    $(cursor).fadeTo(400,0.6);
    $(cursor).fadeTo(400,1.0);
    if (!cursor) showerror("Unable to set cursor, this shouldn't happen!");
    
    updatesidebar(cursorid);  
    aligncursor();    
}

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
        $('#browsernotice').text("Your browser, Internet Explorer 6 or lower, is extremely old and is not supported by Fowlt.net!");
    } else if (($.browser.msie) && (parseInt($.browser.version, 10) < 9) ) {    
        $('#browsernotice').text("Fowlt works better in a newer browser than the one you're currently using! We recommend Firefox or Chrome!");
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


function processed(wordid) {
    var e = document.getElementById(wordid)
    if (!e) { showerror("Processed: Couldn't find element with word id " + wordid); return; }
    $(e).removeClass("error");
    $(e).removeClass("cursor");
    found = -1;
    $.each(errors, function(j, error){
        if (errors[j]['wordid'] == wordid) found = j
    });        
    if (found > -1) {        
        $.each(errors[found]['multispan'], function(j, multispanid) {
            var e2 = document.getElementById(multispanid)
            $(e2).hide();
            $(e2).removeClass("error");
            $(e2).removeClass("cursor");            
        });         
        errors.splice(found,1);        
        errorcount = errors.length;
        $('#errorcount').text(errorcount);
        if (errorcount == 0) {
            $('#suggestionarea').hide();
            $('#currenterror').val('none');
        }
    }
    if ((cursor == e) && (errorcount > 0)) {
        if (cursorindex >= errorcount) cursorindex = errorcount - 1;
        cursorto(cursorindex);
    }
}

function ignore() {
    if ((cursor) && (cursorid)) {
        $.ajax({ 
            type: "POST", 
            url:  "ignore/",
            dataType: "html", 
            data: {'wordid': cursorid },        
            success: function(){},
            error: function(){
                showerror("Er is een fout opgetreden bij het negeren van een woord.");
            }
         });
         processed(cursorid);
    }
}



function cursorleft() {        
    if (errorcount == 0) return;
    if (cursorindex == -1) {
        cursorindex = prevcursorindex;
    } else {
        cursorindex = cursorindex - 1;
    }
    if (cursorindex < 0) cursorindex = errorcount - 1;
    cursorto(cursorindex)
}

function cursorright() {    
    if (errorcount == 0) return;
    if (cursorindex == -1) {
        cursorindex = prevcursorindex;    
    } else {
        cursorindex = cursorindex + 1;
    }
    if (cursorindex >= errorcount) cursorindex = 0;
    cursorto(cursorindex)    
}

function cursorto(index) {

    current_errors = get_current_errors();
    errorcount = current_errors.length;

    if (cursor) $(cursor).removeClass('cursor');
    if (errorcount > 0)
    {        
        cursorindex = index;
        cursorid = current_errors[cursorindex]['wordid']
        cursor = document.getElementById(cursorid);
        if (!cursor) { showerror("Unable to set cursor to " + cursorid + "! this shouldn't happen!"); return; }
    
        $(cursor).addClass('cursor');
        $(cursor).fadeTo(400,0.6);
        $(cursor).fadeTo(400,1.0);    
        aligncursor();
    }
    else
    {
       cursorid = 0;
    }
    
    updatesidebar(cursorid);
    
}



function aligncursor() {    
    $('#suggestionarea').show();
    if (!cursor) { showerror("Error: cursor lost? This shouldn't happen!"); return; }
    delta = $(cursor).offset()['top'] - referenceoffset
    
    /*if ($.browser.mozilla) {            
     delta = delta + $(cursor).height();
    } else {*/
    //}
    //if (($.browser.msie) && (parseInt($.browser.version, 10) <= 8) ) {
    // delta = delta + 4 + ($(cursor).height() / 2);
    //} else {
    delta = delta + ($(cursor).height() / 2) - 3;
    //}
    
    $('#ruler').top =referenceoffset;
    
    //offset =  $('#error').offset()['top'] - $('#textarea').offset()['top'];
        
    $(document).scrollTo(delta, 200 );
}

function hint(wordid) {
   $.each(errors, function(i,error){                                
        if (error['wordid'] == wordid) {
            var e = document.getElementById(errors[i]['wordid'])
            //show current error
            $('#hintsuggestions').empty();                
            var donelist = [];
            //show suggestions
            if (error['suggestions']) {
                $.each(error['suggestions'], function(j,suggestion){
                    var found = false;
                    $.each(donelist, function(k,suggestion2){ if (suggestion2 == suggestion) { found = true; } });
                    if (!found) {
                        done.append(suggestion);
                        $('#hintsuggestions').append('<li>' + suggestion + '?</li>');
                    }
                });   
            }
            $("#hint").css( { "left": $(e).offset()['left'] + "px", "top": ($(e).offset()['top']+25) + "px" } );
            $('#hint').show();            
        }
    });            
    
}

function updatesidebar(wordid) {   
   
   $('#suggestionarea').show();
   $('#ruler').show();
    
   var e = document.getElementById(wordid)
   $('#currenterror').val('free');
   $('#errorclass').text('no errors found');
   $('#error').text($(e).text()); 
   $('#suggestions').empty(); 
   $('#correctall').hide();          
   $('#correctbutton').hide();
   $('#ignorebutton').hide();
   $('#correctall').hide();
   $('#freecorrectbutton').unbind('click');   
   $('#freecorrectbutton').click(function(){
        $('#veil').show();    
        $('#editdialog').slideDown();    
        $('#editword').val($(e).text());
        $('#editword').focus();
        $('#dialogsubmit').unbind('click');
        $('#dialogsubmit').click(function(){
             $('#editdialog').slideUp();
             $('#veil').hide();                            
             $(e).text("(bezig)");
             $.ajax({ 
                type: "POST", 
                url:  "correct/",
                dataType: "html", 
                data: {'wordid': wordid, 'class': 'manual','new':$('#editword').val()},        
                success: function(){            
                    $(e).text($('#editword').val());
                    $(e).addClass('corrected');                    
                    ignore(); //TODO
                }
             });                    
        });
   });
   
   current_errors = get_current_errors();
   errorcount = current_errors.length;

   $.each(current_errors, function(i,error){                                
        if (error['wordid'] == wordid) {
            //show current error
            $('#currenterror').val(i+1+' / '+errorcount); 
            $('#errorclass').text(error['classes'][0]);
            $('#error').text(error['text']);                
                           
            //show suggestions
            if ((error['suggestions']) && (error['suggestions'].length > 0)) {
                $.each(error['suggestions'], function(j,suggestion){
                    $('#suggestions').append('<li>' + suggestion + '</li>');
                });                    
                selectsuggestion($('#suggestions li:first-child'));
                $('#correctbutton').show();
                $('#suggestions li').click(function(){
                    selectsuggestion(this);
                });            
            } else {
                $('#suggestions').append('<li class="msg">No suggestions</li>');
            }

            $('#ignorebutton').show();
            if (error['occ'] > 1) {
                $('#sameerror').text(error['occ']);
                //$('#correctall').show();
            } else {
                $('#correctall').hide();
            }
        }
    });            
}

function selectsuggestion(e) {
    correction = $(e).text();
    for (var i = 0; i < errors[cursorindex]['suggestions'].length; i++) {
        if (errors[cursorindex]['suggestions'][i] == correction)
            correctionclass = errors[cursorindex]['classes'][i];            
        
        $('#suggestions li').each(function(){
                if (this != e) {
                 $(this).removeClass('selected');
                }
        });
          
        //$(e).fadeTo(400,0.6);             
        $(e).addClass('selected'); 
        //$(e).fadeTo(400,1.0);
    }
}

function correct() {
    if ((cursorindex >= 0) && (cursorid) && (correction)) {
     var e = document.getElementById(cursorid)
     var correctid = cursorid;
     $(e).text("(bezig)");
     $.ajax({ 
        type: "POST", 
        url:  "correct/",
        dataType: "html", 
        data: {'wordid': errors[cursorindex]['wordid'], 'class': 'manual','new':correction,'correctionid':errors[cursorindex]['correctionid'] },        
        success: function(){            
            $(e).text(correction);
            $(e).addClass('corrected');
            processed(correctid);
        },
        error: function(){
            showerror("Er is een fout opgetreden bij het corrigeren, misschien is er nog een correctie gaande?");
        }
     });
    } else {
        showerror("Pick a word first!");
    }
       
}

function unselect() {
    if (cursorindex > -1) {
        prevcursorindex = cursorindex;
        cursorindex = -1;    
        cursorid = null;    
    }
    $('#currenterror').val('free');    
    $('#suggestionarea').hide();
    $('#ruler').hide();
}


function showerror(msg) {
    $('#errordialog p').text(msg);
    $('#veil').show();
    $('#errordialog').show();
}

function reflag_errors(errors,threshold) {

	for(error in errors)
	{
		var e = document.getElementById(errors[error]['wordid']);
		if(100 - threshold > errors[error]['confidence'] * 100)
		{
			$(e).removeClass('error');

        		if (errors[error]['multispan']) 
			{
         			$.each(errors[error]['multispan'], function(j, multispanwordid){
			                var emultispan = document.getElementById(multispanwordid)
			                $(emultispan).removeClass("error");
        			    });
        		}
		}
		else
		{
			$(e).addClass('error');

        		if (errors[error]['multispan']) 
			{
         			$.each(errors[error]['multispan'], function(j, multispanwordid){
			                var emultispan = document.getElementById(multispanwordid)
			                $(emultispan).addClass("error");
        			    });
        		}

		}	
	}

	cursorto(0);
}

function get_current_errors() {
 
  current_errors = [];
  threshold = document.getElementById('value').value;
   for(error in errors)
   {
       var e = document.getElementById(errors[error]['wordid']);
       if(errors[error]['confidence'] == 1 || 100 - threshold < errors[error]['confidence'] * 100)
       {current_errors.push(errors[error]);}	
   }

  return current_errors;
}
