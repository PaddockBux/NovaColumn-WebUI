document.getElementById('findServerButton').addEventListener('click', function() {
    // Replace 'https://api.example.com/data' with the actual API endpoint
    fetch('http://localhost:5000/api/main')
        .then(response => response.json()) // Parse the JSON from the response
        .then(data => {
            // Assuming the API returns a JSON object with a 'message' field
            document.getElementById('serverInfo').innerText = data.ip;
        })
        .catch(error => {
            console.error('Error fetching data:', error);
        });
});
