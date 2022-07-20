$(function () {
    $('a#reset').on('click', function (e) {
        e.preventDefault()
        $.ajax({
            type: 'GET',
            url: '/api/reset',
            data: {},
            success: function (data) {
                console.log(data);
                for (var i = 0; i < data.length; i++) {
                    console.log(data[i]['candidate_id'])
                    document.getElementById(`candidate_id_${data[i]['candidate_id']}`).innerHTML = `<li id="${data[i]['candidate_id']}"> ${data[i]['candidate_id']}: ${data[i]['score']}</li>`
                }
                window.location.replace("/");
            }
        });
    });
});

$(function () {
    $('a.prefer_candidate').on('click', function (e) {
        e.preventDefault()
        var candidate_collection = document.getElementsByClassName("btn-pref");
        var candidate_values = [];
        for (var i = 0; i < candidate_collection.length; i++) {
            candidate_values.push(candidate_collection[i].value)
        }
        var filtered_candidate_value = candidate_values.filter(function (ff) { return ff !== e.target.value })

        console.log('Selected candidate', e.target.value)
        console.log('Non-selected candidate', filtered_candidate_value[0])

        $.ajax({
            type: 'GET',
            url: '/api/submit_preference/',
            data: {
                selected_candidate_id: e.target.value,
                non_selected_candidate_id: filtered_candidate_value[0]
            },
            success: function (data) {
                console.log(data);
                for (var i = 0; i < data.length; i++) {
                    console.log(data[i]['candidate_id'])
                    document.getElementById(`candidate_id_${data[i]['candidate_id']}`).innerHTML = `<li id="${data[i]['candidate_id']}"> ${data[i]['candidate_id']}: ${data[i]['score']}</li>`
                }
                window.location.replace("/");
            }
        });
    });
});
