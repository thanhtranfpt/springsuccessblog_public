// Wait for the HTML document to be fully loaded
document.addEventListener("DOMContentLoaded", function () {
    // Create a new XMLHttpRequest object
    var xhr = new XMLHttpRequest();

    // Define the path to your .txt file
    var txtFilePath = "../img/Cers of Tran Xuan Thanh/result.txt";

    // Open a GET request to the .txt file
    xhr.open("GET", txtFilePath, true);

    // Set up an event listener for when the request is complete
    xhr.onload = function () {
        if (xhr.status === 200) {
            // Get the text content from the response
            var textContent = xhr.responseText;

            // Get the HTML container where you want to insert the text
            var textContainer = document.getElementById("certificates_images");

            // Insert the text content as HTML
            textContainer.innerHTML = textContent;
        }
    };

    // Send the request
    xhr.send();
});
