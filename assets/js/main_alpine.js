
function manageDetailsPage() {
    return {

        dataDetail(url) {

            console.log(url)
            
            fetch(url)
                .then(response => response.text())
                .then(data => {
                    $('#detailsPage').html(data)
                    htmx.process('#detailsPage');
                    console.log('htmx process detailsPage')
                })
        },

    }
}




