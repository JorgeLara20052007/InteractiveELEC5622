// Browser-side helpers that Dash callbacks cannot do: keyboard shortcuts, pasting images,
// and opening a picture full size. Dash loads every file in assets/ automatically.
(function () {
  // Ctrl+Z undoes and Ctrl+Y (or Ctrl+Shift+Z) redoes a tree change by clicking the toolbar
  // buttons. Inside a text field Ctrl+Z keeps its normal meaning (undo typing).
  document.addEventListener('keydown', function (e) {
    if (!(e.ctrlKey || e.metaKey) || e.altKey) return;
    const target = e.target;
    if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable)) return;
    const key = e.key.toLowerCase();
    let buttonId = null;
    if (key === 'z' && !e.shiftKey) buttonId = 'btn-undo';
    else if (key === 'y' || (key === 'z' && e.shiftKey)) buttonId = 'btn-redo';
    if (!buttonId) return;
    e.preventDefault();
    const button = document.getElementById(buttonId);
    if (button && !button.disabled) button.click();
  });

  // Study page: Space flips the card, → / Y = "I knew it", ← / N = "I didn't".
  document.addEventListener('keydown', function (e) {
    if (!document.getElementById('study-card') || e.ctrlKey || e.metaKey || e.altKey) return;
    const target = e.target;
    if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA')) return;
    const visible = (id) => {
      const el = document.getElementById(id);
      return el && el.offsetParent !== null ? el : null;
    };
    let el = null;
    if (e.key === ' ' || e.key === 'Enter') el = visible('study-card');
    else if (e.key === 'ArrowRight' || e.key.toLowerCase() === 'y') el = visible('btn-right');
    else if (e.key === 'ArrowLeft' || e.key.toLowerCase() === 'n') el = visible('btn-wrong');
    if (!el) return;
    e.preventDefault();
    el.click();
  });

  // Drag the bar between the tree and the side panel to resize the panel. The width is a CSS
  // variable on <html> (React never touches it) and is remembered in this browser.
  // Double-click the bar to go back to the default width.
  const PANEL_KEY = 'panel-width';
  const MIN_PANEL = 280;
  const MIN_GRAPH = 200;
  const setPanelWidth = (px) => {
    if (px === null) {
      document.documentElement.style.removeProperty('--panel-width');
    } else {
      const max = Math.max(MIN_PANEL, window.innerWidth - MIN_GRAPH);
      document.documentElement.style.setProperty('--panel-width', Math.min(max, Math.max(MIN_PANEL, px)) + 'px');
    }
    const el = document.getElementById('cy');
    if (el && el._cyreg && el._cyreg.cy) el._cyreg.cy.resize(); // keep the graph's canvas in step
  };
  try {
    const saved = parseInt(localStorage.getItem(PANEL_KEY), 10);
    if (saved) setPanelWidth(saved);
  } catch (err) { /* storage unavailable: use the default width */ }

  document.addEventListener('mousedown', function (e) {
    if (!e.target || e.target.id !== 'splitter' || e.button !== 0) return;
    e.preventDefault();
    document.body.classList.add('resizing-panel');
    const move = (ev) => setPanelWidth(window.innerWidth - ev.clientX);
    const up = () => {
      document.body.classList.remove('resizing-panel');
      document.removeEventListener('mousemove', move);
      document.removeEventListener('mouseup', up);
      const panel = document.getElementById('side-panel');
      try {
        if (panel) localStorage.setItem(PANEL_KEY, String(Math.round(panel.getBoundingClientRect().width)));
      } catch (err) { /* not remembered, still resized */ }
    };
    document.addEventListener('mousemove', move);
    document.addEventListener('mouseup', up);
  });

  document.addEventListener('dblclick', function (e) {
    if (!e.target || e.target.id !== 'splitter') return;
    try { localStorage.removeItem(PANEL_KEY); } catch (err) { /* ignore */ }
    setPanelWidth(null);
  });

  // Pasting a screenshot or copied picture into the definition box uploads it and inserts
  // the Markdown for it at the cursor.
  document.addEventListener('paste', async function (e) {
    const area = e.target;
    if (!area || area.id !== 'form-definition') return;
    const items = Array.from((e.clipboardData && e.clipboardData.items) || []);
    const item = items.find((i) => i.kind === 'file' && i.type.startsWith('image/'));
    if (!item) return;
    e.preventDefault();
    const blob = item.getAsFile();
    try {
      const reply = await fetch('/upload-image', {
        method: 'POST',
        body: blob,
        headers: { 'Content-Type': blob.type },
      });
      const result = await reply.json();
      if (!reply.ok) throw new Error(result.error || 'upload failed');
      insertAtCursor(area, '![pasted image](' + result.url + ')');
    } catch (err) {
      alert('Could not add the image: ' + err.message);
    }
  });

  function insertAtCursor(area, text) {
    const before = area.value.slice(0, area.selectionStart);
    const after = area.value.slice(area.selectionEnd);
    const spacer = before && !before.endsWith('\n\n') ? (before.endsWith('\n') ? '\n' : '\n\n') : '';
    const inserted = spacer + text + '\n';
    // Set the value the way a user edit would, so React (Dash) notices the change.
    const setValue = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
    setValue.call(area, before + inserted + after);
    area.dispatchEvent(new Event('input', { bubbles: true }));
    const cursor = (before + inserted).length;
    area.setSelectionRange(cursor, cursor);
  }

  // Click a picture in a definition to open it full size in a new tab.
  document.addEventListener('click', function (e) {
    const img = e.target;
    if (img && img.tagName === 'IMG' && img.closest('#definition')) window.open(img.src, '_blank');
  });
})();
