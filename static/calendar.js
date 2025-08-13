document.addEventListener('DOMContentLoaded', function () {
  var el = document.getElementById('calendar');
  if (!el) return;

  // كشف الجوال (<= 768px)
  var isMobile = window.matchMedia('(max-width: 768px)').matches;

  // تكوينات مشتركة
  var baseOptions = {
    locale: 'ar',
    height: 'auto',
    expandRows: true,
    navLinks: false,
    nowIndicator: true,
    eventTimeFormat: { hour: '2-digit', minute: '2-digit', meridiem: false },
    dayMaxEvents: true,              // طيّ الزيادة مع "+X المزيد"
    eventDisplay: 'block',           // يسهل القراءة في الجوال
    eventSources: [el.getAttribute('data-events-url')],
    buttonText: {
      today: 'اليوم',
      month: 'شهر',
      week:  'أسبوع',
      day:   'يوم',
      list:  'قائمة'
    }
  };

  // شاشات صغيرة: واجهة أخف + عرض قائمة أسبوعية
  var mobileOptions = {
    initialView: 'listWeek',
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'listWeek,timeGridDay'
    },
    // يقلل كثافة العرض ويمنع التمرير الأفقي
    slotMinTime: '07:00:00',
    slotMaxTime: '22:00:00'
  };

  // شاشات أكبر: العرض الشهري الافتراضي
  var desktopOptions = {
    initialView: 'dayGridMonth',
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek'
    }
  };

  var calendar = new FullCalendar.Calendar(
    el,
    Object.assign({}, baseOptions, isMobile ? mobileOptions : desktopOptions)
  );

  // تبديل حيّ أثناء تغيير حجم الشاشة
  window.addEventListener('resize', function () {
    var nowMobile = window.matchMedia('(max-width: 768px)').matches;
    var view = calendar.view.type;
    if (nowMobile && view !== 'listWeek') {
      calendar.changeView('listWeek');
    } else if (!nowMobile && view === 'listWeek') {
      calendar.changeView('dayGridMonth');
    }
  });

  calendar.render();
});
