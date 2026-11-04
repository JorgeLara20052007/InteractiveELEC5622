// Floating PDF windows on the tree page. Press "📄 PDF" (or drop a PDF on the page) to open a
// PDF from this computer in a small window you can drag by its title bar, resize from the
// bottom-right corner, minimise and close. Several can be open at once.
//
// The file never leaves the browser: it is shown from a local object URL by the browser's own
// PDF viewer, and nothing is uploaded to the server.
(function () {
  const MIN_W = 260;
  const MIN_H = 180;
  let topZ = 1000;
  let opened = 0;

  let picker = null;
  function getPicker() {
    if (!picker) {
      picker = document.createElement('input');
      picker.type = 'file';
      picker.accept = 'application/pdf,.pdf';
      picker.multiple = true;
      picker.style.display = 'none';
      picker.addEventListener('change', function () {
        Array.from(picker.files || []).forEach(openPdfWindow);
        picker.value = ''; // so choosing the same file again still fires "change"
      });
      document.body.appendChild(picker);
    }
    return picker;
  }

  document.addEventListener('click', function (e) {
    if (e.target && e.target.closest && e.target.closest('#btn-pdf')) getPicker().click();
  });

  // Dropping a PDF anywhere on the tree page opens it too (but not on the image drop area).
  const isPdf = (f) => f && (f.type === 'application/pdf' || /\.pdf$/i.test(f.name));
  document.addEventListener('dragover', function (e) {
    if (!document.getElementById('btn-pdf') || (e.target.closest && e.target.closest('#image-upload'))) return;
    if (Array.from(e.dataTransfer.items || []).some((i) => i.kind === 'file')) e.preventDefault();
  });
  document.addEventListener('drop', function (e) {
    if (!document.getElementById('btn-pdf') || (e.target.closest && e.target.closest('#image-upload'))) return;
    const pdfs = Array.from(e.dataTransfer.files || []).filter(isPdf);
    if (!pdfs.length) return;
    e.preventDefault();
    pdfs.forEach(openPdfWindow);
  });

  function make(tag, className, parent) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (parent) parent.appendChild(el);
    return el;
  }

  function barButton(bar, text, title, onClick) {
    const b = make('button', null, bar);
    b.type = 'button';
    b.textContent = text;
    b.title = title;
    b.addEventListener('click', onClick);
    return b;
  }

  // Keep at least part of the title bar on screen so a window can always be dragged back.
  function clamp(win) {
    const r = win.getBoundingClientRect();
    const left = Math.min(Math.max(r.left, 80 - r.width), window.innerWidth - 80);
    const top = Math.min(Math.max(r.top, 0), window.innerHeight - 30);
    win.style.left = left + 'px';
    win.style.top = top + 'px';
  }

  // Follow the mouse until the button is released. While dragging, iframes and the graph
  // must not catch the mouse, or the drag would stop as soon as the pointer crosses them.
  function track(startEvent, onMove) {
    startEvent.preventDefault();
    document.body.classList.add('pdf-dragging');
    const x0 = startEvent.clientX;
    const y0 = startEvent.clientY;
    const move = (ev) => onMove(ev.clientX - x0, ev.clientY - y0);
    const up = () => {
      document.body.classList.remove('pdf-dragging');
      document.removeEventListener('mousemove', move);
      document.removeEventListener('mouseup', up);
    };
    document.addEventListener('mousemove', move);
    document.addEventListener('mouseup', up);
  }

  function openPdfWindow(file) {
    const url = URL.createObjectURL(file);
    const offset = (opened++ % 8) * 30;

    const win = make('div', 'pdf-window', document.body);
    win.style.left = 40 + offset + 'px';
    win.style.top = 100 + offset + 'px';
    win.style.width = Math.min(480, window.innerWidth - 80) + 'px';
    win.style.height = Math.min(600, window.innerHeight - 140) + 'px';
    win.style.zIndex = ++topZ;
    win.addEventListener('mousedown', () => { win.style.zIndex = ++topZ; }, true);

    const bar = make('div', 'pdf-bar', win);
    const title = make('span', 'pdf-title', bar);
    title.textContent = file.name;
    title.title = file.name;
    barButton(bar, '↗', 'Open in a new tab', () => window.open(url, '_blank'));
    barButton(bar, '–', 'Minimise / restore (or double-click the title bar)', () => win.classList.toggle('minimized'));
    barButton(bar, '×', 'Close', () => {
      win.remove();
      URL.revokeObjectURL(url);
    });
    bar.addEventListener('dblclick', (e) => {
      if (e.target.tagName !== 'BUTTON') win.classList.toggle('minimized');
    });

    const frame = make('iframe', 'pdf-frame', win);
    frame.src = url;
    frame.title = file.name;

    const handle = make('div', 'pdf-resize', win);
    handle.title = 'Drag to resize';

    bar.addEventListener('mousedown', function (e) {
      if (e.button !== 0 || e.target.tagName === 'BUTTON') return;
      const left0 = win.offsetLeft;
      const top0 = win.offsetTop;
      track(e, (dx, dy) => {
        win.style.left = left0 + dx + 'px';
        win.style.top = top0 + dy + 'px';
        clamp(win);
      });
    });

    handle.addEventListener('mousedown', function (e) {
      if (e.button !== 0) return;
      const w0 = win.offsetWidth;
      const h0 = win.offsetHeight;
      track(e, (dx, dy) => {
        win.style.width = Math.max(MIN_W, w0 + dx) + 'px';
        win.style.height = Math.max(MIN_H, h0 + dy) + 'px';
      });
    });
  }

  window.addEventListener('resize', function () {
    document.querySelectorAll('.pdf-window').forEach(clamp);
  });
})();
