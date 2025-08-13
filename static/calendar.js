document.addEventListener('DOMContentLoaded', function () {
  var el = document.getElementById('calendar');
  if (!el) return;

  var isMobile = window.matchMedia('(max-width: 768px)').matches;

  function fmtDate(d){
    return new Intl.DateTimeFormat('ar-SA', {
      weekday:'long', year:'numeric', month:'long', day:'numeric'
    }).format(d);
  }
  function fmtTime(d){
    try {
      return new Intl.DateTimeFormat('ar-SA', {
        hour:'2-digit', minute:'2-digit', hour12:true
      }).format(d);
    } catch(e){
      let hours = d.getHours();
      let ampm = hours >= 12 ? 'م' : 'ص';
      hours = hours % 12;
      hours = hours ? hours : 12; // 0 -> 12
      let minutes = d.getMinutes().toString().padStart(2,'0');
      return hours + ':' + minutes + ' ' + ampm;
    }
  }

  var calendar = new FullCalendar.Calendar(el, {
    locale: 'ar',
    initialView: 'dayGridMonth',
    height: 'auto',
    contentHeight: 'auto',
    expandRows: true,
    fixedWeekCount: true,
    dayMaxEvents: true,
    nowIndicator: true,
    eventTimeFormat: { hour: '2-digit', minute: '2-digit', meridiem: 'short' },
    eventSources: [el.getAttribute('data-events-url')],
    buttonText: { today: 'اليوم', month: 'شهر', week: 'أسبوع', day: 'يوم', list: 'قائمة' },
    headerToolbar: isMobile
      ? { left: 'prev,next today', center: 'title', right: '' }
      : { left: 'prev,next today', center: 'title', right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek' },

    // نصنع Tooltip جميل لكل حدث
    eventDidMount: function(info){
      var course = info.event.title || '';
      var trainer = info.event.extendedProps?.trainer
                 || (course.includes('—') ? course.split('—').slice(1).join('—').trim() : '');
      var day = fmtDate(info.event.start);
      var time = fmtTime(info.event.start) + ' — ' + fmtTime(info.event.end);

      var html = `
        <div dir="rtl" style="text-align:right;">
          <div>📚 <strong>الدورة:</strong> ${course}</div>
          <div>👤 <strong>المدرب:</strong> ${trainer || '—'}</div>
          <div>🗓️ <strong>اليوم:</strong> ${day}</div>
          <div>⏰ <strong>الوقت:</strong> ${time}</div>
        </div>
      `;

      // Bootstrap Tooltip
      var tip = new bootstrap.Tooltip(info.el, {
        title: html,
        html: true,
        placement: 'auto',
        container: 'body',
        sanitize: false
      });
      info.el._fcTip = tip;
    },

    eventWillUnmount: function(info){
      if (info.el._fcTip) {
        info.el._fcTip.dispose();
        delete info.el._fcTip;
      }
    }
  });

  window.addEventListener('resize', function () {
    var nowMobile = window.matchMedia('(max-width: 768px)').matches;
    calendar.setOption('headerToolbar', nowMobile
      ? { left: 'prev,next today', center: 'title', right: '' }
      : { left: 'prev,next today', center: 'title', right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek' }
    );
    calendar.updateSize();
  });

  calendar.render();
});
