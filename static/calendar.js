document.addEventListener('DOMContentLoaded', function () {
  var el = document.getElementById('calendar');
  if (!el) return;

  var isMobile = window.matchMedia('(max-width: 768px)').matches;

  function fmtDate(d){
    try {
      return new Intl.DateTimeFormat('ar-SA', {
        weekday:'long', year:'numeric', month:'long', day:'numeric'
      }).format(d);
    } catch(e){
      return d.toLocaleDateString('ar-SA');
    }
  }
  function fmtTime(d){
    try {
      return new Intl.DateTimeFormat('ar-SA', {
        hour:'2-digit', minute:'2-digit', hour12:false
      }).format(d);
    } catch(e){
      return d.getHours().toString().padStart(2,'0') + ':' + d.getMinutes().toString().padStart(2,'0');
    }
  }

  var calendar = new FullCalendar.Calendar(el, {
    locale: 'ar',
    initialView: 'dayGridMonth',        // شهر كامل حتى على الجوال
    height: 'auto',
    contentHeight: 'auto',
    expandRows: true,
    fixedWeekCount: true,
    dayMaxEvents: true,
    nowIndicator: true,
    eventTimeFormat: { hour: '2-digit', minute: '2-digit', meridiem: false },
    eventSources: [el.getAttribute('data-events-url')],
    buttonText: { today: 'اليوم', month: 'شهر', week: 'أسبوع', day: 'يوم', list: 'قائمة' },
    headerToolbar: isMobile
      ? { left: 'prev,next today', center: 'title', right: '' }
      : { left: 'prev,next today', center: 'title', right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek' },

    // نصنع Tooltip لكل حدث عند التركيب
    eventDidMount: function(info){
      var course = info.event.title || '';
      var trainer = (info.event.extendedProps && info.event.extendedProps.trainer) ? info.event.extendedProps.trainer : '';
      var day = fmtDate(info.event.start);
      var time = fmtTime(info.event.start) + ' — ' + fmtTime(info.event.end);

      var html = `
        <div dir="rtl" class="zmb-tip">
          <div class="zmb-tip-row"><span class="zmb-ico">📚</span><strong>الدورة:</strong><span>${course}</span></div>
          <div class="zmb-tip-row"><span class="zmb-ico">👤</span><strong>المدرب:</strong><span>${trainer || '—'}</span></div>
          <div class="zmb-tip-row"><span class="zmb-ico">🗓️</span><strong>اليوم:</strong><span>${day}</span></div>
          <div class="zmb-tip-row"><span class="zmb-ico">⏰</span><strong>الوقت:</strong><span>${time}</span></div>
        </div>
      `;

      var tip = new bootstrap.Tooltip(info.el, {
        title: html,
        html: true,
        placement: 'auto',
        container: 'body',
        sanitize: false
      });
      info.el._fcTip = tip;
    },

    // تنظيف التولتيب عند إزالة الحدث
    eventWillUnmount: function(info){
      if (info.el._fcTip) {
        info.el._fcTip.dispose();
        delete info.el._fcTip;
      }
    }
  });

  // تحديث شريط الأدوات والقياسات عند تغيير حجم الشاشة
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
