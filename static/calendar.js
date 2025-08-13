document.addEventListener('DOMContentLoaded', function () {
  var el = document.getElementById('calendar');
  if (!el) return;

  var isMobile = window.matchMedia('(max-width: 768px)').matches;

  var calendar = new FullCalendar.Calendar(el, {
    locale: 'ar',
    initialView: 'dayGridMonth',        // شهر كامل حتى على الجوال
    height: 'auto',
    contentHeight: 'auto',
    expandRows: true,                    // يمد الصفوف لتجنّب التمرير
    fixedWeekCount: true,                // دائمًا 6 أسابيع لثبات الواجهة
    dayMaxEvents: true,                  // طيّ الأحداث الزائدة + رابط "المزيد"
    eventDisplay: 'block',
    nowIndicator: true,
    eventTimeFormat: { hour: '2-digit', minute: '2-digit', meridiem: false },
    eventSources: [el.getAttribute('data-events-url')],
    buttonText: { today: 'اليوم', month: 'شهر', week: 'أسبوع', day: 'يوم', list: 'قائمة' },

    // شريط أدوات مخصص حسب حجم الشاشة
    headerToolbar: isMobile
      ? { left: 'prev,next today', center: 'title', right: '' }
      : { left: 'prev,next today', center: 'title', right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek' },

    // يجعل خلايا الأيام لا تنضغط زيادة عند كثرة الأحداث
    moreLinkClick: 'popover'
  });

  // إذا تحوّل الجهاز من عرض صغير لكبير (أو العكس) نحافظ على الشهر
  window.addEventListener('resize', function () {
    var nowMobile = window.matchMedia('(max-width: 768px)').matches;
    // إعادة تهيئة شريط الأدوات على الطاير
    calendar.setOption('headerToolbar', nowMobile
      ? { left: 'prev,next today', center: 'title', right: '' }
      : { left: 'prev,next today', center: 'title', right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek' }
    );
    // يضمن إعادة حساب الارتفاعات
    calendar.updateSize();
  });

  calendar.render();
});
