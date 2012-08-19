$(document).ready(function() { 
    $(function() {
        $('#' + UPLOADPROGRESS_FORM_ID).uploadProgress({
            jqueryPath: JQUERY_URL,
            progressBar: '#progress_indicator',
            progressUrl: '../progress/',
            start: function() {
                $('#' + UPLOADPROGRESS_FORM_ID).hide();
                filename = 'gallery';
                $('#progress_filename').html('Uploading ' + filename + '...');
                $('#progress_container').show();
            },
            uploadProgressPath: JQUERY_UPLOADPROGRESS_URL,
            uploading: function(upload) {
                if (upload.percents == 100 || !upload.percents) {
                    $('#progress_filename').html('Processing ' + filename + '...');
                } else {
                    $('#progress_filename').html('Saving ' + filename + ': ' + upload.percents + '%');
                }
            },
            interval: 5000
        });
    });
});
