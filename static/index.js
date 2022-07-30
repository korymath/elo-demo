$(function () {
    $('a#reset').on('click', function (e) {
        e.preventDefault()
        $.ajax({
            type: 'GET',
            url: '/api/reset',
            data: {},
            success: function (data) {
                console.log(data);
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
        var filtered_candidate_value = candidate_values.filter(
            (ff) => ff !== e.target.value)

        console.log('Selected candidate', e.target.value)
        console.log('Non-selected candidate', filtered_candidate_value[0])

        $.ajax({
            type: 'GET',
            url: '/api/submit_preference/',
            data: {
                selected_name: e.target.value,
                non_selected_name: filtered_candidate_value[0]
            },
            success: function (data) {
                console.log(data);
                window.location.replace("/");
            }
        });
    });
});
