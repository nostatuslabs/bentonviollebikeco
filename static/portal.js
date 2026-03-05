/**
 * Phase 4: Portal - gather content from DOM (over initial content) and POST to save-content API.
 */
(function () {
  function getFieldValue(el) {
    if (!el) return '';
    if (el.type === 'checkbox') return el.checked;
    if (el.hasAttribute('contenteditable')) return (el.textContent || '').trim();
    if (el.value !== undefined) return (el.value || '').trim();
    return (el.getAttribute('data-value') || el.getAttribute('data-current') || '').trim();
  }

  function setNested(obj, path, value) {
    var parts = path.split('.');
    if (parts.length < 1) return;
    if (parts.length === 1) { obj[parts[0]] = value; return; }
    var cur = obj;
    for (var i = 0; i < parts.length - 1;) {
      var key = parts[i];
      var nextKey = parts[i + 1];
      var nextIsNum = /^\d+$/.test(nextKey);
      if (nextIsNum) {
        cur[key] = cur[key] || [];
        cur = cur[key];
        var idx = parseInt(nextKey, 10);
        cur[idx] = cur[idx] || {};
        cur = cur[idx];
        i += 2;
      } else {
        cur[key] = cur[key] || {};
        cur = cur[key];
        i += 1;
      }
    }
    cur[parts[parts.length - 1]] = value;
  }

  function gatherContent() {
    var content = window.__INITIAL_CONTENT__
      ? JSON.parse(JSON.stringify(window.__INITIAL_CONTENT__))
      : {};

    // [data-field] text/contenteditable
    document.querySelectorAll('[data-field]').forEach(function (el) {
      var field = el.getAttribute('data-field');
      if (!field) return;
      var val = getFieldValue(el);
      setNested(content, field, val);
    });

    // [data-field][data-value] image paths
    document.querySelectorAll('[data-field][data-value]').forEach(function (el) {
      var field = el.getAttribute('data-field');
      var val = el.getAttribute('data-value') || '';
      if (field) setNested(content, field, val);
    });

    // data-field-text and data-field-href (links, buttons)
    document.querySelectorAll('[data-field-text], [data-field-href]').forEach(function (el) {
      var textField = el.getAttribute('data-field-text');
      var hrefField = el.getAttribute('data-field-href');
      var text = (el.textContent || '').trim();
      var href = (el.getAttribute && el.getAttribute('href')) || (el.href || '') || '#';
      if (textField) setNested(content, textField, text);
      if (hrefField) setNested(content, hrefField, href);
    });

    // Nav items: data-field-label and data-field-href on <a>
    document.querySelectorAll('a[data-field-label]').forEach(function (el) {
      var labelField = el.getAttribute('data-field-label');
      var hrefField = el.getAttribute('data-field-href');
      if (labelField) setNested(content, labelField, (el.textContent || '').trim());
      if (hrefField) setNested(content, hrefField, (el.getAttribute('href') || ''));
    });

    // Ensure required keys exist for backend validation
    var required = ['topbar', 'header', 'hero', 'intro', 'promo_strip', 'quick_links', 'brands', 'rental_section', 'ride_to_buy', 'visit', 'footer'];
    required.forEach(function (k) {
      if (!content[k]) content[k] = k === 'quick_links' ? [] : {};
    });
    if (!content.meta) content.meta = { title: '' };

    return content;
  }

  function showStatus(msg, isError) {
    var status = document.querySelector('.portal-save-status');
    if (!status) {
      status = document.createElement('span');
      status.className = 'portal-save-status';
      var toolbar = document.querySelector('.portal-toolbar');
      if (toolbar) toolbar.appendChild(status);
    }
    status.textContent = msg;
    status.className = 'portal-save-status ' + (isError ? 'err' : 'ok');
    setTimeout(function () { status.textContent = ''; }, 4000);
  }

  function save() {
    var payload = gatherContent();
    var btn = document.querySelector('.portal-save-btn');
    if (btn) btn.disabled = true;
    fetch('/api/save-content', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(function (r) {
        if (r.ok) {
          showStatus('Saved');
          return;
        }
        return r.json().then(function (j) { throw new Error(j.error || 'Save failed'); });
      })
      .catch(function (err) {
        showStatus(err.message || 'Save failed', true);
      })
      .finally(function () {
        if (btn) btn.disabled = false;
      });
  }

  document.querySelectorAll('.portal-save-btn').forEach(function (btn) {
    btn.addEventListener('click', save);
  });

  // Change image: file input -> upload -> set data-value and update background/src
  document.querySelectorAll('.portal-change-image').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var field = this.getAttribute('data-field');
      var input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/*';
      input.onchange = function () {
        var file = input.files && input.files[0];
        if (!file) return;
        var fd = new FormData();
        fd.append('file', file);
        fetch('/api/upload-image', { method: 'POST', body: fd })
          .then(function (r) { return r.json(); })
          .then(function (j) {
            if (j.error) throw new Error(j.error);
            var path = j.path || (j.url ? j.url.replace(/^.*\/static\//, '') : '');
            if (!path && j.url) path = 'uploads/' + j.url.split('/').pop();
            var container = document.querySelector('[data-field="' + field + '"]');
            if (!container) container = btn.previousElementSibling || btn.parentElement;
            if (container) {
              container.setAttribute('data-value', path);
              if (container.style && container.style.backgroundImage !== undefined) {
                container.style.backgroundImage = "url('" + (j.url || '/static/' + path) + "')";
              }
            }
            var img = container && container.querySelector ? container.querySelector('img') : null;
            if (img) img.src = j.url || ('/static/' + path);
          })
          .catch(function (e) { alert('Upload failed: ' + (e.message || e)); });
      };
      input.click();
    });
  });
})();
