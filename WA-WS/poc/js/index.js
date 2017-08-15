function monthAsName(month_val) {
  const months = ['January',  'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

  return months[month_val];
};

function dayAsName(day_val) {
  const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  return days[day_val];
};

function makeCORSRequest(url, target_function, target) {
  $.ajax(url, {
    type: 'GET',
    contentType: 'text/plain',
    dataType: 'jsonp',
    xhrFields: {
      withCredentials: true
    },
    headers: {

    },
    success: function(data) {
      let store_time = new Date()
      localStorage[target + '_last_stored'] = store_time.toString();
      localStorage[target] = JSON.stringify(data);
      target_function(data, '*');
    },
    error: function(e) {
      console.log(e);
      createErrorObjects(target);
    }
  });
};

function returnDataFromCORSRequest(url, store_name) {
  $.ajax(url, {
    type: 'GET',
    contentType: 'text/plain',
    dataType: 'jsonp',
    xhrFields: {
      withCredentials: true
    },
    headers: {

    },
    success: function(data) {
      let store_time = new Date()
      localStorage[store_name + '_last_stored'] = store_time.toString();
      localStorage[store_name] = JSON.stringify(data);
      return data;
    },
    error: function(e) {
      console.log('Error getting', store_name, ':', e);
    }
  });
};

function createErrorObjects(target) {

};

function loadData(url, target, target_function, returnData) {
  let events_last_stored = localStorage[target + '_last_stored'];
  events_last_stored = Date.parse(events_last_stored);
  events_last_stored = new Date(events_last_stored);

  const current = new Date();
  const difference = ((current - events_last_stored) / 1000 / 60);

  console.log('Minutes sinces last ' + target + ' collection:', difference);

  if (isNaN(difference) || difference >= 30) {
    if (returnData) {
      returnDataFromCORSRequest(url, target)
    } else {
      makeCORSRequest(url, target_function, target);
    }
  } else {
    if (returnData) {
      let data_stored = localStorage[target];
      data_stored = JSON.parse(data_stored);
      return data_stored
    } else {
      const events_stored = localStorage[target];
      const events_data = JSON.parse(events_stored);
      target_function(events_data, '*')
    }
  }
};

function loadAll() {
  loadData('http://webapi.legistar.com/v1/seattle/Events', 'recent_events', createRecentEventsObjects, false)

  //makeCORSRequest('http://webapi.legistar.com/v1/seattle/Bodies', createIndexObjects, 'indexes')
};

function createRecentEventsObjects(data, where) {
  let event_data_5;

  if (where == '*') {
    event_data_5 = alasql('SELECT TOP 5 * FROM ? ORDER BY EventDate DESC', [data]);
  } else {
    event_data_5 = alasql('SELECT TOP 5 * FROM ? WHERE EventBodyName="' + where + '" ORDER BY EventDate DESC', [data]);
  }

  console.log('5 recent events:', event_data_5);

  $('#recent_events_data').children().remove();

  event_data_5.forEach((event) => {
    let event_date = Date.parse(event.EventDate);
    event_date = new Date(event_date);

    let event_time = event.EventTime;

    $('#recent_events_data').append(
      $('<div/>')
      .attr('id', 'event_' + event.EventId)
      .on('click', () => {
        window.location = event.EventAgendaFile
      })
      .addClass('event_container transition_all_100')
      .append(
        $('<h4/>')
        .attr('id', 'event_' + event.EventId + '_body')
        .addClass('event_body font_standard font_bold')
        .text(event.EventBodyName)
      )
      .append(
        $('<p/>')
        .attr('id', 'event_' + event.EventId + '_date')
        .addClass('event_date font_standard')
        .text(dayAsName(event_date.getDay()) + ', ' + event_date.getDate() + ' ' + monthAsName(event_date.getMonth()) + ' ' + event_date.getFullYear() + ', ' + event_time)
      )
      .append(
        $('<p/>')
        .attr('id', 'event_' + event.EventID + '_location')
        .addClass('event_location font_standard font_light')
        .text(event.EventLocation)
      )
    );
  });
};

function createIndexObjects(data) {
  console.log(data);
};

function updateListData(where, target_data, target_function) {
  let json_target_data = localStorage[target_data];
  json_target_data = JSON.parse(json_target_data);

  target_function(json_target_data, where);
};
