$(document).ready(() => {
  const committees = loadData('http://webapi.legistar.com/v1/seattle/Bodies', 'committee_names', undefined, true);

  addDropdownElements('recent_events_committee_lookup', committees, 'BodyName', '_committee', createRecentEventsObjects, 'BodyActiveFlag');
});

function addDropdownElements(target, data, element_target, naming_target, target_function, check_flag) {
  let recent_events_dropdown_toggled = false;
  let recent_events_dropdown_created = false;

  const element_container = target.substring(0, target.indexOf(naming_target));

  $('#' + target).on('click', () => {
    if (recent_events_dropdown_created) {
      if (recent_events_dropdown_toggled) {
        // hide
        $('#' + target + '_elements')
        .hide();

        $('#' + target + '_drop')
        .toggleClass('fa-angle-up fa-angle-down');

        recent_events_dropdown_toggled = false;
      } else {
        // show
        $('#' + target + '_elements')
        .show();

        $('#' + target + '_drop')
        .toggleClass('fa-angle-down fa-angle-up');

        recent_events_dropdown_toggled = true;
      }
    } else {
        // create
        $('#' + target + '_drop')
        .toggleClass('fa-angle-down fa-angle-up');

        $(
          $('<div/>')
          .attr('id', target + '_elements')
          .addClass('dropdown_elements_container')
        ).insertAfter('#' + target);

        $('#' + target + '_elements').append(
          $('<div/>')
          .attr('id', target + '_datum')
          .addClass('dropdown_element transition_all_200')
          .on('click', () => {
            $('#' + target + '_elements')
            .hide();

            $('#' + target + '_drop')
            .toggleClass('fa-angle-up fa-angle-down');

            label = '#' + element_container + naming_target + '_label';

            $(label)
            .text('All Data');

            updateListData('*', element_container, target_function);

            recent_events_dropdown_toggled = false;
          })
          .append(
            $('<p/>')
            .addClass('font_standard')
            .text('All Data')
          )
        );

        data.forEach((datum) => {
          console.log(datum[check_flag]);
          if (datum[check_flag] != 0) {
            console.log(datum[element_target]);
            $('#' + target + '_elements').append(
              $('<div/>')
              .attr('id', target + '_datum')
              .addClass('dropdown_element transition_all_200')
              .on('click', () => {
                $('#' + target + '_elements')
                .hide();

                $('#' + target + '_drop')
                .toggleClass('fa-angle-up fa-angle-down');

                label = '#' + element_container + naming_target + '_label';

                if (datum[element_target].length <= 50) {
                  $(label)
                  .text(datum[element_target]);
                } else {
                  $(label)
                  .text(datum[element_target].substring(0, 50) + ' ...');
                }

                updateListData($(label).text(), element_container, target_function);

                recent_events_dropdown_toggled = false;
              })
              .append(
                $('<p/>')
                .addClass('font_standard')
                .text(datum[element_target])
              )
            );
          }
        });

        recent_events_dropdown_created = true;
        recent_events_dropdown_toggled = true;
    }
  });

  console.log(data);
};
