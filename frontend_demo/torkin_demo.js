document.getElementById('consultation-form').addEventListener('submit', function(event) {
    event.preventDefault();

    const firstName = document.getElementById('first-name').value;
    const lastName = document.getElementById('last-name').value;
    const phone = document.getElementById('phone').value;
    const email = document.getElementById('email').value;
    const address = document.getElementById('address').value;
    const serviceInterest = document.getElementById('service-interest').value;
    const projectTimeline = document.getElementById('project-timeline').value;

    // Basic validation
    if (!firstName || !lastName || !phone || !email || !address || !serviceInterest || !projectTimeline) {
        alert('Please fill out all required fields.');
        return;
    }

    const leadData = {
        first_name: firstName,
        last_name: lastName,
        phone: phone,
        email: email,
        address: address,
        source: 'torkin',
        service_requested: serviceInterest,
        notes: [{ "content": `Project Timeline: ${projectTimeline}` }]
    };

    fetch('https://lead-management-staging-backend.onrender.com/api/leads/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(leadData),
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            // Log the error response for more details
            response.json().then(err => console.error('API Error:', err));
            throw new Error('Network response was not ok.');
        }
    })
    .then(data => {
        console.log('Success:', data);
        alert('Thank you for your submission! A Torkin design expert will call you within minutes.');
        document.getElementById('consultation-form').reset();
    })
    .catch((error) => {
        console.error('Fetch Error:', error);
        alert('There was a problem with your submission. Please try again later.');
    });
});