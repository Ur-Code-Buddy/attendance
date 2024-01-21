function handlePrevious() {
    console.log("Previous Week Requested");

    // Ajax call to server to handle previous week action
    $.ajax({
      type: "GET",
      url: "/previous_week",
      success: function (response) {
        console.log("Server response for previous week:", response);
        // Refresh the page after getting a successful response
        window.location.reload(true);
      },
      error: function (error) {
        console.error("Error with previous week:", error);
      },
    });
  }

  function handleNext() {
    console.log("Next Week Requested");

    // Ajax call to server to handle next week action
    $.ajax({
      type: "GET",
      url: "/next_week",
      success: function (response) {
        console.log("Server response for next week:", response);
        // refresh the page after getting a successful response
        window.location.reload(true);
      },
      error: function (error) {
        console.error("Error with next week:", error);
      },
    });
  }

  function toggleDate(checkbox, day, name, date, month) {
    console.log(
      "Toggled:",
      checkbox.checked,
      "for",
      name,
      day,
      "Date:",
      date,
      "Month:",
      month
    );

    var postData = {
      name: name,
      day: day,
      date: date,
      month: month,
      checked: checkbox.checked,
    };

    // Ajax call to server to handle date toggle
    $.ajax({
      type: "POST",
      url: "/process_date",
      contentType: "application/json;charset=UTF-8",
      data: JSON.stringify(postData),
      success: function (response) {
        console.log("Server response:", response);
        if (
          response.message &&
          response.message === "Not Accepted,not an ADMIN"
        ) {
          alert("You don't have Admin privileges");
        }
      },
      error: function (error) {
        console.error("error:", error);
      },
    });
  }
