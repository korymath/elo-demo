$(function () {
    $('a#reset').on('click', function (e) {
        e.preventDefault()
        $.getJSON('/api/reset',
            function (data) {
                for (var i = 0; i < data.length; i++) {
                    document.getElementById(data[i]['candidate_id']).innerHTML = `<li id="${data[i]['candidate_id']}">${data[i]['candidate_id']}: ${data[i]['score']}</li>`
                }
            });
        return false;
    });
});

$(function () {
    $('a.prefer_candidate').on('click', function (e) {
        // e.preventDefault()
        var candidate_collection = document.getElementsByClassName("btn-pref");
        var candidate_values = [];
        for (var i = 0; i < candidate_collection.length; i++) {
            candidate_values.push(candidate_collection[i].value)
        }
        var filtered_candidate_value = candidate_values.filter(function (ff) { return ff !== e.target.value })
        $.ajax({
            type: 'GET',
            url: '/api/submit_preference/',
            data: {
                selected_candidate_id: e.target.value,
                // this only works for binary comparison
                non_selected_candidate_id: filtered_candidate_value[0]
            },
            success: function (data) {
                for (var i = 0; i < data.length; i++) {
                    document.getElementById(data[i]['candidate_id']).innerHTML = `<li id="${data[i]['candidate_id']}">${data[i]['candidate_id']}: ${data[i]['score']}</li>`
                }
            }
        });
    });
});
