function clearGameCode() {
    setGameCode("");
}

function setGameCode(gameCode) {
    document.cookie = "gameCode="+gameCode+"; SameSite=None; Secure";
}

function getGameCode() {

  const gc = document.cookie
  .split('; ')
  .find(row => row.startsWith('gameCode='))
  .split('=')[1];

   console.log("Game code (cookie): " + gc);
   return gc;
}

function startGame() {

    var gameCode = getGameCode();

    if (gameCode == '') {
        alert('Game code not found. Please play game from View game page and re-do the actions.')
    }

    encode_game_code = window.btoa(gameCode);
    redirect_url = window.location.protocol + '//' + window.location.hostname + '/play-game?gcode='+encode_game_code;
    window.location = redirect_url

}

function generateTickets() {

    var gameCode = getGameCode();
    $('.notification').hide();
    $("#notifyMessage").html('');

    $.ajax({
            url : '/generate-tickets?gcode='+gameCode,
            success: function(data) {
                if (data['message'] != '') {
                    $('.notification').show();
                    $("#notifyMessage").html(data['message']);
                }

                if (data['start_game']) {
                    $('#startGame').show();
                } else {
                    $('#startGame').hide();
                }
            }
    });

}

function numberClicked(row, col, songName) {

    // Number is clicked in the tambola ticket

    var elem = $("#tcell-"+row+"-"+col)
    if (elem.hasClass("ticket-cell-cut")) {
        alert("Ticket song has already been cut");
        return;
    }

    var tcode = $("#tcode").val();
    var email = $("#email").val();
    var song = songName

    $.ajax({
      url : '/cut-song?tcode='+tcode+"&row="+row+"&col="+col+"&song="+song,
      type: 'get',
      success: function(data){
        if (data['message'] != '') {
            alert(data['message'])
            return;
        }

        var elem = $("#tcell-"+row+"-"+col)
        console.log(elem);
        elem.removeClass("ticket-cell");
        elem.addClass("ticket-cell-cut");

      },
   });

}


function populateUsers(gameCode, notifyElem, tblElem, data ) {

    $('#'+tblElem).html('');

    if (!data['status']) {
        $("#"+notifyElem).html(data['message']);
        return;
    }

    participants = data["players"];

    if (participants.length <= 0) {
        $("#"+notifyElem).html("No user is found in the game");
        return;
    }

    setGameCode(gameCode);
    $("#generateTickets").show();

    console.log(participants)
    var column_data = '<tbody>';
    column_data += '<tr>';

    for (var key in participants[0]){
        //key = key.toUpperCase()
        column_data += '<th>' + key.toUpperCase() + '</th>'
    };

    column_data += '</tr>';
    $('#'+tblElem).append(column_data);

    var row_data = '';
    for (var arr in participants){
        console.log(arr);
        var obj = participants[arr];
        row_data += '<tr>';
        for (var key in obj){
            var value = obj[key];
            row_data += '<td>' + value + '</td>';
        };
        row_data += '</tr>'
    };
    row_data += '</tbody>';
    $('#'+tblElem).append(row_data);
}


$(function() {

    $('.notification').hide();
    // Play button is clicked

    $('#refreshSongs').click(function(){

        var tcode = $("#tcode").val();
        var email = $("#email").val();
        var gcode = $("#gcode").val();
        $.ajax({
              url : '/get-played-songs?tcode='+tcode+"&gcode="+gcode,
              type: 'get',
              success: function(data){
                if (data['message'] != '') {
                    alert(data['message']);
                }
                console.log(data);
                var songs = data['songs'];
                var songName = "";
                console.log(songs);
                songs.forEach(function(element){
                    if(element != null) {
                        var song = element.substr(0, element.length - 4);
                        songName += " | " + song;
                    }
                });

                $('#songsPlayed').text(songName);

              },
           });
    });

    $('#completeGame').click(function(){

        var gcode = $("#gcode").val();
        $.ajax({
              url : '/game-completed?gcode='+gcode,
              type: 'get',
              success: function(data){

                if(data['status']) {
                    alert(data['message']);
                    redirect_url = window.location.protocol + '//' + window.location.hostname + ':5000';
                    alert(redirect_url);
                    window.location = redirect_url
                } else {
                    alert(data['message']);
                    return;
                }
              },
           });
    });

    $('#playButton').click(function(){

        var gcode = getGameCode()

        $.ajax({
              url : '/next-song?gcode='+gcode,
              type: 'get',
              success: function(data){
                if (data['message'] != '') {
                    $('.notification').show();
                    $("#notifyMessage").html(data['message'])
                }

                var song = data['song']
                if (song != null) {
                    var songName = song.substr(0, song.length - 4);
                    $('#songsPlayed').append(" | " + songName);

                    var audio = document.getElementById('audioPlayer');

                    $("#songPlayer").attr("src", '/static/songs/'+song)
                    audio.load();
                    audio.play();

                }
                console.log("Song is empty. Re-try it");
              },
           });
    });

    // Create game is clicked
    $('#createGame').click(function() {

        $('.notification').hide();
        $("#notifyMessage").html('');
        var fd = new FormData($('#newGame')[0]);

        var gameName = $('#gameName').val();
        if(gameName == '') {
            alert("Please specify a game name");
            return;
        }
        fd.append('gameName', gameName);

        $.ajax({
              url : '/create-game',
              type: 'post',
              data: fd,
              contentType: false,
              processData: false,
              success: function(data){
                var gameCode = data['game_code'];
                $("#gameCode").html('Game Code (Please note it down for reference): <b>' + gameCode+'</b>');
                $("#gameCodeDiv").show();
                populateUsers(gameCode, 'notifyMessage', 'participants-list' , data);
              },
           });

    });

    $('#getGameDetails').click(function() {

        $('.notification').hide();
        $("#notifyMessage").html('');
        gameCode = document.getElementById('gameCode').value;
        console.log(gameCode);

        if (gameCode == '') {
            alert("Enter game code");
            return
        }

        $.ajax({
            url : '/get-game-details?gcode='+gameCode,
            success: function(data) {
                populateUsers(gameCode, 'notifyMessage', 'participants-list', data);
                $("#startGame").show();
            }
        });
    });
})