$(document).ready(function(){
    // Sidenav mobile functionality
    $('.sidenav').sidenav();
    // Character counter for all inputs and textarea
    $('input, textarea').characterCounter();
    // Form select for the continent dropdown
    $('select').formSelect();
    // Modal functionality
    $('.modal').modal();
    // Hero-image parallax
    $('.parallax').parallax();
  });