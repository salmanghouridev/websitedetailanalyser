document.addEventListener('DOMContentLoaded', function() {
    const getDetailsBtn = document.getElementById('getDetailsBtn');
    const urlInput = document.getElementById('urlInput');
    const loadingElement = document.getElementById('loading');
    const detailsElement = document.getElementById('details');

    getDetailsBtn.addEventListener('click', function() {
        const url = urlInput.value;
        if (!url) {
            alert('Please enter a URL.');
            return;
        }

        loadingElement.style.display = 'block';
        detailsElement.style.display = 'none';

        fetch('http://127.0.0.1:5000/api/details', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url: url })
        })
        .then(response => response.json())
        .then(data => {
            loadingElement.style.display = 'none';
            detailsElement.style.display = 'block';
            document.getElementById('url-tab').innerHTML = `<p><strong>URL:</strong> ${data.url}</p>`;
            document.getElementById('ip-tab').innerHTML = `<p><strong>IP Address:</strong> ${data.ip_address}</p>`;
            document.getElementById('technologies-tab').innerHTML = `<p><strong>Technologies:</strong> ${JSON.stringify(data.technologies)}</p>`;
            document.getElementById('domain-tab').innerHTML = `<p><strong>Domain Info:</strong> ${JSON.stringify(data.domain_info)}</p>`;
            document.getElementById('ssl-tab').innerHTML = `<p><strong>SSL Info:</strong> ${JSON.stringify(data.ssl_info)}</p>`;
            document.getElementById('performance-tab').innerHTML = `<p><strong>Page Load Time:</strong> ${data.page_load_time} seconds</p>`;
            document.getElementById('recommendations-tab').innerHTML = `<p><strong>Recommendations:</strong> ${data.recommendations.join('<br>')}</p>`;
        })
        .catch(error => {
            loadingElement.style.display = 'none';
            detailsElement.style.display = 'block';
            detailsElement.innerHTML = `<p>Error fetching details: ${error.message}</p>`;
        });
    });
});

function openTab(evt, tabName) {
    const tabcontent = document.getElementsByClassName('tabcontent');
    for (let i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = 'none';
    }
    const tablinks = document.getElementsByClassName('tablink');
    for (let i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(' active', '');
    }
    document.getElementById(tabName).style.display = 'block';
    evt.currentTarget.className += ' active';
}

// Initialize the first tab to be active by default
document.addEventListener('DOMContentLoaded', function() {
    document.querySelector('.tablink').click();
});
