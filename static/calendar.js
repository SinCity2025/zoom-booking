document.addEventListener('DOMContentLoaded', function() {
  var el = document.getElementById('calendar');
  if(!el) return;
  var url = el.getAttribute('data-events-url');
  var calendar = new FullCalendar.Calendar(el, {
    initialView: 'dayGridMonth',
    locale: 'ar',
    height: 'auto',
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek'
    },
    eventSources: [ url ],
    nowIndicator: true
  });
  calendar.render();
});
