/**
 * K-Protect SDK v4 — Production-grade behavioral biometrics + device fingerprinting engine
 *
 * Captures ALL behavioral signals needed for drift scoring:
 *   - Keystroke dynamics (10-zone model, dwell/flight, transitions, rhythm, bursts, errors)
 *   - Pointer dynamics (velocity, acceleration, curvature, idle, segments, angle histogram)
 *   - Scroll behavior (velocity, direction, bursts, reading pauses)
 *   - Touch dynamics (tap timing, swipe, pressure, contact area)
 *   - Credential field behavior (zone sequences, paste, autofill, hesitation)
 *   - Sensor data (accelerometer, gyroscope, orientation)
 *   - Device fingerprinting (canvas, audio, WebGL, fonts, speech, math, CSS, battery)
 *   - Site-wide signals (navigation flow, copy/paste, resize, network, errors, focus)
 *
 * Every batch includes:
 *   - event_classification: { type, page_class, critical_action?, committed? }
 *   - device_context: hardware, screen, network, browser, locale
 *   - device_fingerprint: async-collected fingerprint signals
 *   - All behavioral signals with real extracted features
 *
 * Privacy: No raw key content, no absolute coordinates, no PII.
 * Timing: performance.now() for all behavioral timestamps.
 */
(function () {
  'use strict';

  var PULSE_INTERVAL = 30000;
  var MIN_EVENTS_FOR_PULSE = 10;
  var KEEPALIVE_INTERVAL = 30000;
  var ENDPOINT = '/api/kp-ingest';
  var SDK_VERSION = '4.0.0';
  var NUM_ZONES = 10;

  // ═══════════════════════════════════════════════════════
  // 10-ZONE KEYBOARD MODEL (per-finger assignment, QWERTY)
  // Zone 0: Left pinky    (Q,A,Z,1,`,Tab,Caps,ShiftLeft)
  // Zone 1: Left ring     (W,S,X,2)
  // Zone 2: Left middle   (E,D,C,3)
  // Zone 3: Left index    (R,T,F,G,V,B,4,5)
  // Zone 4: Right pinky   (P,;,/,0,-,=,[,],\,',Enter,Backspace,ShiftRight)
  // Zone 5: Right index   (Y,U,H,J,N,M,6,7)
  // Zone 6: Right middle  (I,K,Comma,8)
  // Zone 7: Right ring    (O,L,Period,9)
  // Zone 8: (unused — reserved for split keyboards)
  // Zone 9: Thumbs/Modifiers (Space, Ctrl, Alt, Meta on both sides)
  // Unmapped → zone 10 conceptually (arrows, F-keys, numpad, etc.)
  // ═══════════════════════════════════════════════════════
  var ZONE_MAP = {
    // Zone 0 — left pinky
    KeyQ: 0, KeyA: 0, KeyZ: 0, Digit1: 0, Backquote: 0, Tab: 0, CapsLock: 0, ShiftLeft: 0,
    // Zone 1 — left ring
    KeyW: 1, KeyS: 1, KeyX: 1, Digit2: 1,
    // Zone 2 — left middle
    KeyE: 2, KeyD: 2, KeyC: 2, Digit3: 2,
    // Zone 3 — left index
    KeyR: 3, KeyT: 3, KeyF: 3, KeyG: 3, KeyV: 3, KeyB: 3, Digit4: 3, Digit5: 3,
    // Zone 4 — right pinky
    KeyP: 4, Semicolon: 4, Slash: 4, Digit0: 4, Minus: 4, Equal: 4,
    BracketLeft: 4, BracketRight: 4, Backslash: 4, Quote: 4,
    Enter: 4, Backspace: 4, ShiftRight: 4,
    // Zone 5 — right index
    KeyY: 5, KeyU: 5, KeyH: 5, KeyJ: 5, KeyN: 5, KeyM: 5, Digit6: 5, Digit7: 5,
    // Zone 6 — right middle
    KeyI: 6, KeyK: 6, Comma: 6, Digit8: 6,
    // Zone 7 — right ring
    KeyO: 7, KeyL: 7, Period: 7, Digit9: 7,
    // Zone 9 — thumbs: space + all modifiers
    Space: 9, ControlLeft: 9, ControlRight: 9, AltLeft: 9, AltRight: 9, MetaLeft: 9, MetaRight: 9,
  };

  // Zone 10 = arrows, F-keys, numpad, Escape, Delete, Insert, Home, End, PageUp, PageDown
  var SPECIAL_ZONE = 10;
  var SPECIAL_CODES = /^(Arrow|F\d|Numpad|Escape|Delete|Insert|Home|End|Page)/;

  function getZone(code) {
    if (!code) return -1;
    var z = ZONE_MAP[code];
    if (z !== undefined) return z;
    if (SPECIAL_CODES.test(code)) return SPECIAL_ZONE;
    return -1;
  }

  // ═══════════════════════════════════════════════════════
  // UTILITIES
  // ═══════════════════════════════════════════════════════
  function r2(v) { return Math.round(v * 100) / 100; }

  function mean(arr) {
    if (!arr.length) return 0;
    var s = 0; for (var i = 0; i < arr.length; i++) s += arr[i];
    return s / arr.length;
  }

  function stdev(arr) {
    if (arr.length < 2) return null;
    var m = mean(arr), v = 0;
    for (var i = 0; i < arr.length; i++) v += (arr[i] - m) * (arr[i] - m);
    return Math.sqrt(v / arr.length);
  }

  function percentile(sorted, p) {
    if (!sorted.length) return 0;
    var idx = Math.floor(sorted.length * p);
    return sorted[Math.min(idx, sorted.length - 1)];
  }

  function stats(arr) {
    if (!arr.length) return { mean: 0, std_dev: null, p25: 0, p50: 0, p75: 0, p95: 0, sample_count: 0 };
    var s = arr.slice().sort(function (a, b) { return a - b; });
    var sd = stdev(arr);
    return {
      mean: r2(mean(arr)), std_dev: sd !== null ? r2(sd) : null,
      p25: r2(percentile(s, 0.25)), p50: r2(percentile(s, 0.5)),
      p75: r2(percentile(s, 0.75)), p95: r2(percentile(s, 0.95)),
      sample_count: arr.length,
    };
  }

  function makeUUID() {
    try { return crypto.randomUUID(); } catch (e) { return Date.now().toString(36) + Math.random().toString(36).slice(2); }
  }

  // ═══════════════════════════════════════════════════════
  // AUDIT LOG (in-memory, tamper-evident)
  // ═══════════════════════════════════════════════════════
  var auditLog = [];
  function auditRecord(action, detail) {
    auditLog.push({ seq: auditLog.length, timestamp: new Date().toISOString(), action: action, detail: detail || null });
    if (auditLog.length > 1000) auditLog.shift();
  }

  // ═══════════════════════════════════════════════════════
  // CONSENT GATE (GDPR/CCPA)
  // ═══════════════════════════════════════════════════════
  function hasConsent() {
    try {
      var raw = localStorage.getItem('kp.consent');
      if (!raw) return true; // opt-out mode: runs unless explicitly denied
      var parsed = JSON.parse(raw);
      return parsed.state !== 'denied';
    } catch (e) { return true; }
  }

  function setConsent(granted) {
    try {
      localStorage.setItem('kp.consent', JSON.stringify({ state: granted ? 'granted' : 'denied', timestamp: Date.now() }));
    } catch (e) { /* */ }
  }

  // SHA-256 hash helper (async)
  function sha256(data) {
    try {
      var encoder = new TextEncoder();
      return crypto.subtle.digest('SHA-256', encoder.encode(data)).then(function (buf) {
        return Array.from(new Uint8Array(buf)).map(function (b) { return b.toString(16).padStart(2, '0'); }).join('');
      });
    } catch (e) {
      return Promise.resolve('unavailable');
    }
  }

  // HMAC-SHA256 helper (async)
  function hmacSha256(keyStr, message) {
    try {
      var encoder = new TextEncoder();
      return crypto.subtle.importKey('raw', encoder.encode(keyStr), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign'])
        .then(function (key) {
          return crypto.subtle.sign('HMAC', key, encoder.encode(message));
        })
        .then(function (sig) {
          return Array.from(new Uint8Array(sig)).map(function (b) { return b.toString(16).padStart(2, '0'); }).join('');
        });
    } catch (e) {
      return Promise.resolve(null);
    }
  }

  // Zero-filled 2D array helper
  function zeros2D(rows, cols) {
    var arr = [];
    for (var r = 0; r < rows; r++) {
      arr[r] = [];
      for (var c = 0; c < cols; c++) arr[r][c] = 0;
    }
    return arr;
  }

  // ═══════════════════════════════════════════════════════
  // A. DEVICE FINGERPRINTING (collected async on init)
  // ═══════════════════════════════════════════════════════
  var deviceFingerprint = {};

  function collectDeviceFingerprint() {
    var promises = [];

    // 1. Canvas 2D fingerprint
    promises.push(collectCanvasFingerprint());
    // 2. AudioContext fingerprint
    promises.push(collectAudioFingerprint());
    // 3. WebGL full parameter dump
    promises.push(collectWebGLFingerprint());
    // 4. Font detection
    promises.push(collectFontFingerprint());
    // 5. Speech synthesis voices
    promises.push(collectSpeechVoices());
    // 6. Navigator full dump (sync, wrapped in promise)
    promises.push(Promise.resolve(collectNavigatorDump()));
    // 7. Math fingerprint (sync)
    promises.push(Promise.resolve(collectMathFingerprint()));
    // 8. Date formatting fingerprint (sync)
    promises.push(Promise.resolve(collectDateFingerprint()));
    // 9. CSS feature detection (sync)
    promises.push(Promise.resolve(collectCSSFeatures()));
    // 10. Storage quota
    promises.push(collectStorageQuota());
    // 11. Battery
    promises.push(collectBattery());
    // 12. Automation detection (sync)
    promises.push(Promise.resolve(collectAutomationDetection()));
    // 13. Media queries (sync)
    promises.push(Promise.resolve(collectMediaQueries()));

    return Promise.all(promises).then(function (results) {
      deviceFingerprint.canvas = results[0];
      deviceFingerprint.audio = results[1];
      deviceFingerprint.webgl = results[2];
      deviceFingerprint.fonts = results[3];
      deviceFingerprint.speech = results[4];
      deviceFingerprint.navigator = results[5];
      deviceFingerprint.math = results[6];
      deviceFingerprint.date_format = results[7];
      deviceFingerprint.css = results[8];
      deviceFingerprint.storage = results[9];
      deviceFingerprint.battery = results[10];
      deviceFingerprint.automation = results[11];
      deviceFingerprint.media_queries = results[12];
      deviceFingerprint.collected_at = Date.now();
      return deviceFingerprint;
    }).catch(function () { return deviceFingerprint; });
  }

  // A.1 Canvas 2D fingerprint
  function collectCanvasFingerprint() {
    return new Promise(function (resolve) {
      try {
        var canvas = document.createElement('canvas');
        canvas.width = 300; canvas.height = 150;
        var ctx = canvas.getContext('2d');
        if (!ctx) { resolve(null); return; }

        // Text rendering
        ctx.font = '18px Arial';
        ctx.fillStyle = '#f60';
        ctx.fillRect(125, 1, 62, 20);
        ctx.fillStyle = '#069';
        ctx.fillText('Cwm fjord vex quiz nymph', 2, 15);
        ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
        ctx.fillText('Cwm fjord vex quiz nymph', 4, 45);

        // Emoji
        ctx.font = '16px sans-serif';
        ctx.fillText('\uD83C\uDFE0\uD83D\uDD12\uD83D\uDCB0', 2, 70);

        // Gradient rectangle
        var gradient = ctx.createLinearGradient(0, 80, 200, 130);
        gradient.addColorStop(0, 'red');
        gradient.addColorStop(0.5, 'green');
        gradient.addColorStop(1, 'blue');
        ctx.fillStyle = gradient;
        ctx.fillRect(10, 80, 200, 50);

        // Arc
        ctx.beginPath();
        ctx.arc(150, 100, 30, 0, Math.PI * 2, true);
        ctx.closePath();
        ctx.fillStyle = 'rgba(255,0,255,0.5)';
        ctx.fill();

        var dataUrl = canvas.toDataURL();
        sha256(dataUrl).then(function (hash) {
          resolve({ hash: hash });
        }).catch(function () { resolve({ hash: 'error' }); });
      } catch (e) { resolve(null); }
    });
  }

  // A.2 AudioContext fingerprint
  function collectAudioFingerprint() {
    return new Promise(function (resolve) {
      try {
        var AudioCtx = window.OfflineAudioContext || window.webkitOfflineAudioContext;
        if (!AudioCtx) { resolve(null); return; }

        var context = new AudioCtx(1, 5000, 44100);
        var oscillator = context.createOscillator();
        oscillator.type = 'triangle';
        oscillator.frequency.setValueAtTime(1000, context.currentTime);

        var compressor = context.createDynamicsCompressor();
        compressor.threshold.setValueAtTime(-50, context.currentTime);
        compressor.knee.setValueAtTime(40, context.currentTime);
        compressor.ratio.setValueAtTime(12, context.currentTime);
        compressor.attack.setValueAtTime(0, context.currentTime);
        compressor.release.setValueAtTime(0.25, context.currentTime);

        oscillator.connect(compressor);
        compressor.connect(context.destination);
        oscillator.start(0);

        context.startRendering().then(function (buffer) {
          var data = buffer.getChannelData(0);
          // Hash first 100 float samples
          var sampleStr = '';
          var len = Math.min(100, data.length);
          for (var i = 0; i < len; i++) sampleStr += data[i].toFixed(10) + ',';
          sha256(sampleStr).then(function (hash) {
            resolve({ hash: hash, sample_count: len });
          }).catch(function () { resolve({ hash: 'error' }); });
        }).catch(function () { resolve(null); });
      } catch (e) { resolve(null); }
    });
  }

  // A.3 WebGL full parameter dump
  function collectWebGLFingerprint() {
    return new Promise(function (resolve) {
      try {
        var canvas = document.createElement('canvas');
        var gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        if (!gl) { resolve(null); return; }

        var params = {};
        var paramNames = [
          'MAX_TEXTURE_SIZE', 'MAX_RENDERBUFFER_SIZE', 'MAX_VIEWPORT_DIMS',
          'MAX_VERTEX_ATTRIBS', 'MAX_VARYING_VECTORS', 'MAX_VERTEX_UNIFORM_VECTORS',
          'MAX_FRAGMENT_UNIFORM_VECTORS', 'MAX_COMBINED_TEXTURE_IMAGE_UNITS',
          'MAX_VERTEX_TEXTURE_IMAGE_UNITS', 'MAX_TEXTURE_IMAGE_UNITS',
          'MAX_CUBE_MAP_TEXTURE_SIZE', 'ALIASED_LINE_WIDTH_RANGE', 'ALIASED_POINT_SIZE_RANGE'
        ];

        for (var i = 0; i < paramNames.length; i++) {
          var name = paramNames[i];
          try {
            var val = gl.getParameter(gl[name]);
            if (val instanceof Float32Array || val instanceof Int32Array) {
              params[name] = Array.from(val);
            } else {
              params[name] = val;
            }
          } catch (e) { params[name] = null; }
        }

        // Shader precision formats
        var precisions = {};
        var shaderTypes = [
          { name: 'VERTEX_SHADER', type: gl.VERTEX_SHADER },
          { name: 'FRAGMENT_SHADER', type: gl.FRAGMENT_SHADER }
        ];
        var precisionTypes = [
          { name: 'HIGH_FLOAT', type: gl.HIGH_FLOAT },
          { name: 'MEDIUM_FLOAT', type: gl.MEDIUM_FLOAT }
        ];

        for (var s = 0; s < shaderTypes.length; s++) {
          for (var p = 0; p < precisionTypes.length; p++) {
            var key = shaderTypes[s].name + '_' + precisionTypes[p].name;
            try {
              var fmt = gl.getShaderPrecisionFormat(shaderTypes[s].type, precisionTypes[p].type);
              precisions[key] = fmt ? { rangeMin: fmt.rangeMin, rangeMax: fmt.rangeMax, precision: fmt.precision } : null;
            } catch (e) { precisions[key] = null; }
          }
        }

        // Renderer info
        var renderer = null, vendor = null;
        try {
          var ext = gl.getExtension('WEBGL_debug_renderer_info');
          if (ext) {
            renderer = gl.getParameter(ext.UNMASKED_RENDERER_WEBGL);
            vendor = gl.getParameter(ext.UNMASKED_VENDOR_WEBGL);
          }
        } catch (e) { /* */ }

        // WebGL2 check
        var gl2Support = false;
        try { gl2Support = !!canvas.getContext('webgl2'); } catch (e) { /* */ }

        // Hash the full param dump
        var paramStr = JSON.stringify({ params: params, precisions: precisions });
        sha256(paramStr).then(function (hash) {
          resolve({
            params: params,
            precisions: precisions,
            renderer: renderer,
            vendor: vendor,
            webgl2: gl2Support,
            hash: hash
          });
        }).catch(function () {
          resolve({ params: params, precisions: precisions, renderer: renderer, vendor: vendor, webgl2: gl2Support, hash: 'error' });
        });
      } catch (e) { resolve(null); }
    });
  }

  // A.4 Font detection
  function collectFontFingerprint() {
    return new Promise(function (resolve) {
      try {
        var testFonts = [
          'Arial', 'Arial Black', 'Arial Narrow', 'Book Antiqua', 'Bookman Old Style',
          'Calibri', 'Cambria', 'Century', 'Century Gothic', 'Comic Sans MS',
          'Consolas', 'Courier', 'Courier New', 'Georgia', 'Helvetica',
          'Impact', 'Lucida Console', 'Lucida Grande', 'Lucida Sans Unicode',
          'Microsoft Sans Serif', 'Monaco', 'Monotype Corsiva', 'Palatino Linotype',
          'Segoe UI', 'Tahoma', 'Times', 'Times New Roman', 'Trebuchet MS',
          'Verdana', 'Wingdings'
        ];

        var baselines = ['monospace', 'serif', 'sans-serif'];
        var testStr = 'mmmmmmmmmmlli';
        var testSize = '72px';

        var container = document.createElement('div');
        container.style.cssText = 'position:absolute;left:-9999px;top:-9999px;visibility:hidden;';
        document.body.appendChild(container);

        // Measure baseline widths
        var baseWidths = {};
        for (var b = 0; b < baselines.length; b++) {
          var span = document.createElement('span');
          span.style.cssText = 'font-size:' + testSize + ';font-family:' + baselines[b] + ';position:absolute;';
          span.textContent = testStr;
          container.appendChild(span);
          baseWidths[baselines[b]] = span.offsetWidth;
        }

        var detected = [];
        for (var f = 0; f < testFonts.length; f++) {
          var found = false;
          for (var bb = 0; bb < baselines.length; bb++) {
            var sp = document.createElement('span');
            sp.style.cssText = 'font-size:' + testSize + ';font-family:"' + testFonts[f] + '",' + baselines[bb] + ';position:absolute;';
            sp.textContent = testStr;
            container.appendChild(sp);
            if (sp.offsetWidth !== baseWidths[baselines[bb]]) {
              found = true;
            }
          }
          if (found) detected.push(testFonts[f]);
        }

        document.body.removeChild(container);
        var sorted = detected.sort();
        sha256(sorted.join(',')).then(function (hash) {
          resolve({ detected: sorted, count: sorted.length, hash: hash });
        }).catch(function () { resolve({ detected: sorted, count: sorted.length, hash: 'error' }); });
      } catch (e) { resolve(null); }
    });
  }

  // A.5 Speech synthesis voices
  function collectSpeechVoices() {
    return new Promise(function (resolve) {
      try {
        if (!window.speechSynthesis) { resolve(null); return; }

        var getVoices = function () {
          var voices = speechSynthesis.getVoices();
          if (!voices || voices.length === 0) return null;
          var voiceList = voices.map(function (v) { return v.name + '|' + v.lang + '|' + (v.localService ? '1' : '0'); }).sort();
          sha256(voiceList.join(',')).then(function (hash) {
            resolve({ count: voices.length, hash: hash });
          }).catch(function () { resolve({ count: voices.length, hash: 'error' }); });
          return true;
        };

        if (!getVoices()) {
          speechSynthesis.addEventListener('voiceschanged', function () {
            getVoices();
          }, { once: true });
          // Timeout fallback
          setTimeout(function () { if (!getVoices()) resolve(null); }, 1000);
        }
      } catch (e) { resolve(null); }
    });
  }

  // A.6 Navigator full dump
  function collectNavigatorDump() {
    try {
      var result = {
        vendor: navigator.vendor || null,
        appVersion: navigator.appVersion || null,
        product: navigator.product || null,
        globalPrivacyControl: navigator.globalPrivacyControl || null,
        userAgentData: null,
      };

      if (navigator.userAgentData) {
        result.userAgentData = {
          brands: navigator.userAgentData.brands ? navigator.userAgentData.brands.map(function (b) { return b.brand + '/' + b.version; }) : null,
          mobile: navigator.userAgentData.mobile,
          platform: navigator.userAgentData.platform || null,
        };
        // getHighEntropyValues is async but we handle it separately
        if (navigator.userAgentData.getHighEntropyValues) {
          try {
            navigator.userAgentData.getHighEntropyValues(['platformVersion', 'architecture', 'model', 'bitness']).then(function (data) {
              result.userAgentData.platformVersion = data.platformVersion || null;
              result.userAgentData.architecture = data.architecture || null;
              result.userAgentData.model = data.model || null;
              result.userAgentData.bitness = data.bitness || null;
            }).catch(function () { /* */ });
          } catch (e) { /* */ }
        }
      }

      return result;
    } catch (e) { return null; }
  }

  // A.7 Math fingerprint
  function collectMathFingerprint() {
    try {
      return {
        tan_pi_4: Math.tan(Math.PI / 4),
        log_2: Math.log(2),
        e_mod: (Math.E * 1e15) % 1,
        pow_min: Math.pow(2, -1074),
      };
    } catch (e) { return null; }
  }

  // A.8 Date formatting fingerprint
  function collectDateFingerprint() {
    try {
      var epoch = new Date(0);
      return {
        full: new Intl.DateTimeFormat('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: 'numeric', minute: 'numeric', second: 'numeric', timeZoneName: 'long' }).format(epoch),
        short: new Intl.DateTimeFormat('en-US', { dateStyle: 'short', timeStyle: 'short' }).format(epoch),
        relative_era: new Intl.DateTimeFormat('en-US', { era: 'long' }).format(epoch),
      };
    } catch (e) { return null; }
  }

  // A.9 CSS feature detection
  function collectCSSFeatures() {
    try {
      if (!window.CSS || !CSS.supports) return null;
      var features = [
        'display: grid', 'display: flex', 'display: subgrid',
        'color: oklch(0.5 0.2 240)', 'backdrop-filter: blur(1px)',
        'container-type: inline-size', 'anchor-name: --a',
        'view-transition-name: a', 'text-wrap: balance',
        'color-mix(in srgb, red, blue)', 'accent-color: red',
        'aspect-ratio: 1', 'overscroll-behavior: contain',
        'scroll-snap-type: x mandatory', 'content-visibility: auto'
      ];
      var supported = {};
      for (var i = 0; i < features.length; i++) {
        var parts = features[i].split(': ');
        try {
          supported[features[i].replace(/[^a-zA-Z0-9]/g, '_')] = CSS.supports(parts[0], parts.slice(1).join(': '));
        } catch (e) { supported[features[i].replace(/[^a-zA-Z0-9]/g, '_')] = false; }
      }
      return supported;
    } catch (e) { return null; }
  }

  // A.10 Storage quota
  function collectStorageQuota() {
    return new Promise(function (resolve) {
      try {
        if (navigator.storage && navigator.storage.estimate) {
          navigator.storage.estimate().then(function (est) {
            resolve({ quota_bytes: est.quota || null, usage_bytes: est.usage || null });
          }).catch(function () { resolve(null); });
        } else { resolve(null); }
      } catch (e) { resolve(null); }
    });
  }

  // A.11 Battery
  function collectBattery() {
    return new Promise(function (resolve) {
      try {
        if (navigator.getBattery) {
          navigator.getBattery().then(function (batt) {
            resolve({ charging: batt.charging, level: batt.level, chargingTime: batt.chargingTime, dischargingTime: batt.dischargingTime });
          }).catch(function () { resolve(null); });
        } else { resolve(null); }
      } catch (e) { resolve(null); }
    });
  }

  // A.12 Automation detection
  function collectAutomationDetection() {
    try {
      return {
        webdriver: !!navigator.webdriver,
        nightmare: !!window.__nightmare,
        phantom: !!window._phantom,
        selenium_evaluate: !!document.__selenium_evaluate,
        webdriver_evaluate: !!document.__webdriver_evaluate,
        chrome_headless: !!(window.chrome && !window.chrome.runtime),
        callPhantom: !!window.callPhantom,
        domAutomation: !!window.domAutomation,
        domAutomationController: !!window.domAutomationController,
      };
    } catch (e) { return null; }
  }

  // A.13 Media queries
  function collectMediaQueries() {
    try {
      var mq = function (q) { try { return window.matchMedia(q).matches; } catch (e) { return null; } };
      return {
        pointer_fine: mq('(pointer: fine)'),
        hover_hover: mq('(hover: hover)'),
        color_gamut_p3: mq('(color-gamut: p3)'),
        dynamic_range_high: mq('(dynamic-range: high)'),
        prefers_reduced_motion: mq('(prefers-reduced-motion: reduce)'),
        prefers_color_scheme_dark: mq('(prefers-color-scheme: dark)'),
        prefers_contrast: mq('(prefers-contrast: more)'),
        forced_colors: mq('(forced-colors: active)'),
        inverted_colors: mq('(inverted-colors: inverted)'),
      };
    } catch (e) { return null; }
  }

  // ═══════════════════════════════════════════════════════
  // DEVICE & ENVIRONMENT CONTEXT (collected once on init)
  // ═══════════════════════════════════════════════════════
  function collectDeviceContext() {
    var ctx = {
      cpu_cores: navigator.hardwareConcurrency || null,
      device_memory_gb: navigator.deviceMemory || null,
      max_touch_points: navigator.maxTouchPoints || 0,
      platform: navigator.platform || null,
      screen_width: screen.width,
      screen_height: screen.height,
      screen_avail_width: screen.availWidth,
      screen_avail_height: screen.availHeight,
      device_pixel_ratio: window.devicePixelRatio || 1,
      color_depth: screen.colorDepth,
      orientation: screen.orientation ? screen.orientation.type : null,
      viewport_width: window.innerWidth,
      viewport_height: window.innerHeight,
      language: navigator.language,
      languages: navigator.languages ? Array.from(navigator.languages) : [navigator.language],
      cookie_enabled: navigator.cookieEnabled,
      do_not_track: navigator.doNotTrack,
      pdf_viewer: navigator.pdfViewerEnabled || null,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      timezone_offset_min: new Date().getTimezoneOffset(),
      referrer_hash: null,
      network: null,
      performance_memory: null,
      webgl_renderer: null,
      webgl_vendor: null,
      features: {
        web_worker: typeof Worker !== 'undefined',
        service_worker: 'serviceWorker' in navigator,
        web_gl: false,
        web_gl2: false,
        web_audio: typeof AudioContext !== 'undefined' || typeof window.webkitAudioContext !== 'undefined',
        compression_stream: typeof CompressionStream !== 'undefined',
        crypto_subtle: !!(window.crypto && window.crypto.subtle),
        intersection_observer: typeof IntersectionObserver !== 'undefined',
        resize_observer: typeof ResizeObserver !== 'undefined',
        pointer_events: typeof PointerEvent !== 'undefined',
        touch_events: 'ontouchstart' in window,
        gamepad: 'getGamepads' in navigator,
        bluetooth: 'bluetooth' in navigator,
        usb: 'usb' in navigator,
        media_devices: !!(navigator.mediaDevices && navigator.mediaDevices.enumerateDevices),
      },
    };

    // Referrer hash
    try {
      if (document.referrer) {
        sha256(document.referrer).then(function (h) { ctx.referrer_hash = h; }).catch(function () { /* */ });
      }
    } catch (e) { /* */ }

    // Network
    try {
      var conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
      if (conn) {
        ctx.network = {
          type: conn.type || null,
          effective_type: conn.effectiveType || null,
          downlink_mbps: conn.downlink || null,
          rtt_ms: conn.rtt || null,
          save_data: conn.saveData || false,
        };
      }
    } catch (e) { /* */ }

    // Performance memory
    try {
      if (performance.memory) {
        ctx.performance_memory = {
          js_heap_size_mb: r2(performance.memory.usedJSHeapSize / 1048576),
          js_heap_limit_mb: r2(performance.memory.jsHeapSizeLimit / 1048576),
        };
      }
    } catch (e) { /* */ }

    // WebGL renderer
    try {
      var canvas = document.createElement('canvas');
      var gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      if (gl) {
        ctx.features.web_gl = true;
        var ext = gl.getExtension('WEBGL_debug_renderer_info');
        if (ext) {
          ctx.webgl_renderer = gl.getParameter(ext.UNMASKED_RENDERER_WEBGL);
          ctx.webgl_vendor = gl.getParameter(ext.UNMASKED_VENDOR_WEBGL);
        }
        try { if (canvas.getContext('webgl2')) ctx.features.web_gl2 = true; } catch (e) { /* */ }
      }
    } catch (e) { /* */ }

    // Media devices count
    try {
      if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
        navigator.mediaDevices.enumerateDevices().then(function (devices) {
          ctx.media_devices = {
            audioinput: devices.filter(function (d) { return d.kind === 'audioinput'; }).length,
            videoinput: devices.filter(function (d) { return d.kind === 'videoinput'; }).length,
            audiooutput: devices.filter(function (d) { return d.kind === 'audiooutput'; }).length,
          };
        }).catch(function () { /* */ });
      }
    } catch (e) { /* */ }

    // Page load timing
    try {
      if (performance.timing) {
        var t = performance.timing;
        ctx.page_load_ms = (t.loadEventEnd > 0 && t.navigationStart > 0) ? (t.loadEventEnd - t.navigationStart) : null;
      }
    } catch (e) { /* */ }

    return ctx;
  }

  // ═══════════════════════════════════════════════════════
  // STATE
  // ═══════════════════════════════════════════════════════
  var deviceContext = collectDeviceContext();

  var state = {
    session_id: null,
    device_uuid: null,
    user_hash: null,
    pulse: 0,
    sequence: 0,
    page_class: 'normal',
    current_action: null,
    visible: true,
    username_captured: false,
    page_entered_at: 0,
    pulse_timer: null,
    session_start_epoch: Date.now(),
    session_start_perf: performance.now(),
    origin: location.origin,
    origin_hash: null,
    liveness_status: 'stale',
    last_event_at: 0,
    consent_state: hasConsent() ? 'granted' : 'denied',
    listeners: { drift: [], alert: [], critical_action: [], session_start: [], session_end: [], username_captured: [] },
  };

  // Compute origin_hash = SHA-256(session_id + origin) once session starts
  function computeOriginHash() {
    if (!state.session_id) return Promise.resolve(null);
    return sha256(state.session_id + state.origin).then(function (hash) {
      state.origin_hash = hash;
      return hash;
    });
  }

  // Liveness tracking — updated on every raw event
  function recordEvent() {
    state.last_event_at = Date.now();
    state.liveness_status = 'alive';
  }
  setInterval(function () {
    if (state.liveness_status === 'dead') return;
    if (state.last_event_at === 0 || (Date.now() - state.last_event_at) > 30000) {
      state.liveness_status = 'stale';
    }
  }, 5000);

  // ═══════════════════════════════════════════════════════
  // RAW EVENT BUFFERS
  // ═══════════════════════════════════════════════════════
  var keyBuffer = [];
  var pointerBuffer = [];
  var scrollBuffer = [];
  var touchBuffer = [];
  var credBuffer = [];
  var stagingBuffer = [];
  var sensorBuffer = [];

  // ═══════════════════════════════════════════════════════
  // F. SITE-WIDE STATE
  // ═══════════════════════════════════════════════════════
  var siteWide = {
    // F.1 Navigation flow
    navigation_flow: [],
    current_page_entered: performance.now(),
    current_page_url: location.pathname,

    // F.2 Copy/paste/cut counts
    copy_count: 0,
    cut_count: 0,
    paste_count: 0,

    // F.3 Window resize
    resize_count: 0,
    last_viewport: { w: window.innerWidth, h: window.innerHeight },

    // F.4 Network changes
    network_changes: [],

    // F.5 JS error count
    js_error_count: 0,

    // F.7 Focus/visibility tracking
    tab_visible_start: performance.now(),
    tab_visible_duration_ms: 0,
    tab_hidden_duration_ms: 0,
    tab_hidden_start: null,
    focus_changes_count: 0,
    visibility_changes_count: 0,

    // F.8 IME/composition
    ime_active: false,
    ime_event_count: 0,
  };

  // ═══════════════════════════════════════════════════════
  // H. LOAD INDICATORS
  // ═══════════════════════════════════════════════════════
  var loadIndicators = {
    fps: null,
    event_loop_latency_ms: null,
    memory_pressure: null,
    page_load_ms: null,
  };

  // FPS measurement via rAF
  function measureFPS(callback) {
    var frameCount = 0;
    var startTime = performance.now();
    var maxFrames = 60;

    function tick() {
      frameCount++;
      if (frameCount >= maxFrames) {
        var elapsed = performance.now() - startTime;
        callback(r2((frameCount / elapsed) * 1000));
        return;
      }
      requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  // Event loop latency via setTimeout(0) overshoot
  function measureEventLoopLatency(callback) {
    var expected = performance.now();
    setTimeout(function () {
      callback(r2(performance.now() - expected));
    }, 0);
  }

  function collectLoadIndicators() {
    try {
      if (performance.memory) {
        loadIndicators.memory_pressure = {
          used_mb: r2(performance.memory.usedJSHeapSize / 1048576),
          limit_mb: r2(performance.memory.jsHeapSizeLimit / 1048576),
          ratio: r2(performance.memory.usedJSHeapSize / performance.memory.jsHeapSizeLimit),
        };
      }
    } catch (e) { /* */ }

    try {
      if (performance.timing && performance.timing.loadEventEnd > 0) {
        loadIndicators.page_load_ms = performance.timing.loadEventEnd - performance.timing.navigationStart;
      }
    } catch (e) { /* */ }

    measureFPS(function (fps) { loadIndicators.fps = fps; });
    measureEventLoopLatency(function (latency) { loadIndicators.event_loop_latency_ms = latency; });
  }

  // ═══════════════════════════════════════════════════════
  // CREDENTIAL ZONE SEQUENCES (D)
  // ═══════════════════════════════════════════════════════
  var credZoneTracking = {
    password: { events: [], active: false, firstTs: 0 },
    username: { events: [], active: false, firstTs: 0 },
  };

  function recordCredZoneEvent(fieldType, zone, ts, eventType) {
    var tracker = credZoneTracking[fieldType];
    if (!tracker) return;
    if (!tracker.active) {
      tracker.active = true;
      tracker.firstTs = ts;
      tracker.events = [];
    }
    tracker.events.push({ zone: zone, ts: ts, eventType: eventType });
  }

  function buildCredentialZoneSequence(fieldType) {
    var tracker = credZoneTracking[fieldType];
    if (!tracker || tracker.events.length < 2) return null;

    var seq = [];
    var downs = [];
    var events = tracker.events;

    for (var i = 0; i < events.length; i++) {
      var ev = events[i];
      if (ev.eventType === 'kd') {
        downs.push(ev);
      } else if (ev.eventType === 'ku' && downs.length > 0) {
        // find matching down
        var matchIdx = -1;
        for (var j = downs.length - 1; j >= 0; j--) {
          if (downs[j].zone === ev.zone) { matchIdx = j; break; }
        }
        if (matchIdx >= 0) {
          var down = downs[matchIdx];
          var dwell = ev.ts - down.ts;
          downs.splice(matchIdx, 1);

          if (seq.length > 0) {
            var prev = seq[seq.length - 1];
            seq.push({
              from_zone: prev.to_zone !== undefined ? prev.to_zone : down.zone,
              to_zone: down.zone,
              flight_ms: r2(down.ts - (prev._upTs || prev._downTs || down.ts)),
              dwell_ms: r2(dwell),
              _downTs: down.ts,
              _upTs: ev.ts,
            });
          } else {
            seq.push({
              from_zone: down.zone,
              to_zone: down.zone,
              flight_ms: 0,
              dwell_ms: r2(dwell),
              _downTs: down.ts,
              _upTs: ev.ts,
            });
          }
        }
      }
    }

    // Strip internal timestamps
    return seq.map(function (s) {
      return { from_zone: s.from_zone, to_zone: s.to_zone, flight_ms: s.flight_ms, dwell_ms: s.dwell_ms };
    });
  }

  function resetCredZoneTracking(fieldType) {
    var tracker = credZoneTracking[fieldType];
    if (tracker) {
      tracker.events = [];
      tracker.active = false;
      tracker.firstTs = 0;
    }
  }

  // ═══════════════════════════════════════════════════════
  // IDENTITY
  // ═══════════════════════════════════════════════════════
  function getOrCreateUuid(key) {
    var val; try { val = localStorage.getItem(key); } catch (e) { /* */ }
    if (val) return val;
    val = makeUUID();
    try { localStorage.setItem(key, val); } catch (e) { /* */ }
    return val;
  }

  function getOrCreateSessionId() {
    var sid; try { sid = sessionStorage.getItem('kp.sid'); } catch (e) { /* */ }
    if (sid) return sid;
    sid = makeUUID();
    try { sessionStorage.setItem('kp.sid', sid); } catch (e) { /* */ }
    return sid;
  }

  function getOrCreateUsernameSalt() {
    try {
      var stored = localStorage.getItem('kp.us');
      if (stored && stored.length === 64) {
        var bytes = new Uint8Array(32);
        for (var i = 0; i < 32; i++) bytes[i] = parseInt(stored.substr(i * 2, 2), 16);
        return bytes;
      }
    } catch (e) { /* */ }
    var salt = crypto.getRandomValues(new Uint8Array(32));
    var hex = Array.from(salt).map(function (b) { return b.toString(16).padStart(2, '0'); }).join('');
    try { localStorage.setItem('kp.us', hex); } catch (e) { /* */ }
    return salt;
  }

  function hashUsername(value) {
    try {
      var salt = getOrCreateUsernameSalt();
      var encoder = new TextEncoder();
      return crypto.subtle.importKey('raw', encoder.encode(value), 'PBKDF2', false, ['deriveBits'])
        .then(function (key) {
          return crypto.subtle.deriveBits({ name: 'PBKDF2', salt: salt.buffer, iterations: 100000, hash: 'SHA-256' }, key, 256);
        })
        .then(function (derived) {
          return Array.from(new Uint8Array(derived)).map(function (b) { return b.toString(16).padStart(2, '0'); }).join('');
        });
    } catch (e) {
      return sha256(value); // fallback
    }
  }

  // Differential privacy: add Laplace noise to 2D matrix
  function addLaplaceNoise2D(matrix, scale) {
    scale = scale || 2.0;
    return matrix.map(function (row) {
      return row.map(function (count) {
        var buf = new Uint32Array(1);
        crypto.getRandomValues(buf);
        var u = (buf[0] / 0x100000000) - 0.5;
        var noise = u === 0 ? 0 : -scale * Math.sign(u) * Math.log(1 - 2 * Math.abs(u));
        return Math.max(0, Math.round(count + noise));
      });
    });
  }

  // ═══════════════════════════════════════════════════════
  // C. KEYSTROKE FEATURE EXTRACTION (full spec)
  // ═══════════════════════════════════════════════════════
  function extractKeystroke(events) {
    if (!events.length) return null;

    // Per-key tracking
    var pendingDowns = []; // [{zone, code, ts}]
    var dwells = [], flights = [];
    var prevUpTs = -1, prevUpZone = -1;
    var backspaceCount = 0, deleteCount = 0, totalDown = 0;

    // Zone-specific dwell tracking
    var zoneDwells = []; for (var z0 = 0; z0 < NUM_ZONES; z0++) zoneDwells[z0] = [];
    var zoneHitCounts = []; for (var z1 = 0; z1 < NUM_ZONES; z1++) zoneHitCounts[z1] = 0;

    // Transition matrix: counts AND flight times for mean computation
    var transitionCounts = zeros2D(NUM_ZONES, NUM_ZONES);
    var transitionFlightSums = zeros2D(NUM_ZONES, NUM_ZONES);
    var transitionFlightSqSums = zeros2D(NUM_ZONES, NUM_ZONES);
    var lastDownZone = -1;
    var lastDownTs = -1;

    // Bigram velocity (flight times for histogram)
    var allFlightTimes = [];

    // Modifier tracking
    var shiftDownTs = null, shiftHoldTimes = [];
    var modifierBeforeKeyCount = 0, modifierHeldKeyCount = 0;

    // Rhythm: burst detection
    var keyTimestamps = [];
    var consecutiveKeyIntervals = [];

    // Error proxy
    var rapidSameZoneCount = 0;
    var prevKeyDownTs = {}; // zone → last keydown ts
    var correctionSequences = 0;
    var lastWasBackspace = false;

    for (var i = 0; i < events.length; i++) {
      var ev = events[i];
      var zone = ev.zone;

      if (ev.type === 'kd') {
        pendingDowns.push({ zone: zone, code: ev.code, ts: ev.ts });
        totalDown++;
        if (ev.code === 'Backspace') backspaceCount++;
        if (ev.code === 'Delete') deleteCount++;

        if (zone >= 0 && zone < NUM_ZONES) {
          zoneHitCounts[zone]++;
          keyTimestamps.push(ev.ts);

          // Rapid same zone detection (<50ms)
          if (prevKeyDownTs[zone] !== undefined && (ev.ts - prevKeyDownTs[zone]) < 50) {
            rapidSameZoneCount++;
          }
          prevKeyDownTs[zone] = ev.ts;

          // Zone transitions with flight times
          if (lastDownZone >= 0 && lastDownZone < NUM_ZONES && zone < NUM_ZONES) {
            transitionCounts[lastDownZone][zone]++;
            if (prevUpTs > 0) {
              var flightT = ev.ts - prevUpTs;
              transitionFlightSums[lastDownZone][zone] += flightT;
              transitionFlightSqSums[lastDownZone][zone] += flightT * flightT;
            }
          }
          lastDownZone = zone;
          lastDownTs = ev.ts;
        }

        // Modifier tracking
        if (ev.code === 'ShiftLeft' || ev.code === 'ShiftRight') {
          shiftDownTs = ev.ts;
        }
        // Check if modifier is already held when a normal key comes
        if (shiftDownTs !== null && ev.code !== 'ShiftLeft' && ev.code !== 'ShiftRight') {
          if (ev.ts - shiftDownTs < 30) modifierBeforeKeyCount++;
          else modifierHeldKeyCount++;
        }

        // Correction sequence detection (backspace followed by re-typing)
        if (ev.code === 'Backspace') {
          lastWasBackspace = true;
          lastBackspaceZone = zone;
        } else {
          if (lastWasBackspace) {
            correctionSequences++;
          }
          lastWasBackspace = false;
        }

      } else if (ev.type === 'ku') {
        // Match to pending down
        var matchIdx = -1;
        for (var p = pendingDowns.length - 1; p >= 0; p--) {
          if (pendingDowns[p].zone === zone) { matchIdx = p; break; }
        }
        if (matchIdx >= 0) {
          var dwell = ev.ts - pendingDowns[matchIdx].ts;
          dwells.push(dwell);
          if (zone >= 0 && zone < NUM_ZONES) zoneDwells[zone].push(dwell);
          pendingDowns.splice(matchIdx, 1);
        }

        if (prevUpTs > 0) {
          var flight = ev.ts - prevUpTs;
          flights.push(flight);
          allFlightTimes.push(flight);
        }
        prevUpTs = ev.ts;
        prevUpZone = zone;

        // Shift hold tracking
        if ((ev.code === 'ShiftLeft' || ev.code === 'ShiftRight') && shiftDownTs !== null) {
          shiftHoldTimes.push(ev.ts - shiftDownTs);
          shiftDownTs = null;
        }
      }
    }

    var windowMs = events.length > 1 ? events[events.length - 1].ts - events[0].ts : 0;

    // --- Zone dwell means and stdevs ---
    var zoneDwellMeans = [];
    var zoneDwellStdevs = [];
    for (var zd = 0; zd < NUM_ZONES; zd++) {
      zoneDwellMeans.push(zoneDwells[zd].length > 0 ? r2(mean(zoneDwells[zd])) : -1);
      zoneDwellStdevs.push(zoneDwells[zd].length > 1 ? r2(stdev(zoneDwells[zd])) : -1);
    }

    // --- Zone transition matrix: counts and mean flights ---
    var matrixCounts = [];
    var matrixMeanFlights = [];
    var matrixStdevFlights = [];
    for (var mr = 0; mr < NUM_ZONES; mr++) {
      matrixCounts[mr] = [];
      matrixMeanFlights[mr] = [];
      matrixStdevFlights[mr] = [];
      for (var mc = 0; mc < NUM_ZONES; mc++) {
        var cnt = transitionCounts[mr][mc];
        matrixCounts[mr][mc] = cnt;
        if (cnt > 0) {
          matrixMeanFlights[mr][mc] = r2(transitionFlightSums[mr][mc] / cnt);
          if (cnt > 1) {
            var vari = (transitionFlightSqSums[mr][mc] / cnt) - Math.pow(transitionFlightSums[mr][mc] / cnt, 2);
            matrixStdevFlights[mr][mc] = r2(Math.sqrt(Math.max(0, vari)));
          } else {
            matrixStdevFlights[mr][mc] = -1;
          }
        } else {
          matrixMeanFlights[mr][mc] = -1;
          matrixStdevFlights[mr][mc] = -1;
        }
      }
    }

    // --- Rhythm features ---
    var kpsValues = [];
    if (keyTimestamps.length > 1) {
      // Compute KPS in 1-second sliding windows
      for (var ki = 0; ki < keyTimestamps.length; ki++) {
        var windowStart = keyTimestamps[ki];
        var windowEnd = windowStart + 1000;
        var count = 0;
        for (var kj = ki; kj < keyTimestamps.length && keyTimestamps[kj] <= windowEnd; kj++) count++;
        kpsValues.push(count);
      }
    }

    // Consecutive key intervals for burst detection
    for (var ci = 1; ci < keyTimestamps.length; ci++) {
      consecutiveKeyIntervals.push(keyTimestamps[ci] - keyTimestamps[ci - 1]);
    }

    // Burst detection: >4 keys/s for >3 consecutive keys
    var bursts = [];
    var currentBurst = [];
    for (var bi = 0; bi < consecutiveKeyIntervals.length; bi++) {
      if (consecutiveKeyIntervals[bi] < 250) { // 250ms = 4 keys/s
        currentBurst.push(consecutiveKeyIntervals[bi]);
      } else {
        if (currentBurst.length >= 3) bursts.push(currentBurst.slice());
        currentBurst = [];
      }
    }
    if (currentBurst.length >= 3) bursts.push(currentBurst.slice());

    // Pause detection: pauses >500ms
    var pauseCount = 0;
    for (var pi = 0; pi < consecutiveKeyIntervals.length; pi++) {
      if (consecutiveKeyIntervals[pi] > 500) pauseCount++;
    }

    // Inter-burst gaps
    var interBurstGaps = [];
    if (bursts.length > 1) {
      // Approximate gap between end of one burst and start of next
      var burstEndIdx = 0;
      for (var bg = 0; bg < bursts.length; bg++) {
        var burstLen = bursts[bg].length;
        var nextStartIdx = burstEndIdx + burstLen + 1;
        if (bg > 0 && burstEndIdx < consecutiveKeyIntervals.length) {
          interBurstGaps.push(consecutiveKeyIntervals[burstEndIdx] || 0);
        }
        burstEndIdx = nextStartIdx;
      }
    }

    var burstLengths = bursts.map(function (b) { return b.length + 1; }); // keys in burst

    // --- Bigram velocity histogram ---
    var bigramBins = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]; // [0-25, 25-50, 50-75, 75-100, 100-150, 150-200, 200-300, 300-500, 500-1000, 1000+]
    var bigramBounds = [25, 50, 75, 100, 150, 200, 300, 500, 1000, Infinity];
    for (var bf = 0; bf < allFlightTimes.length; bf++) {
      var ft = allFlightTimes[bf];
      for (var bb = 0; bb < bigramBounds.length; bb++) {
        if (ft < bigramBounds[bb]) { bigramBins[bb]++; break; }
      }
    }

    return {
      available: true,
      zone_transition_matrix: {
        counts: addLaplaceNoise2D(matrixCounts),
        mean_flights: matrixMeanFlights,
        stdevs: matrixStdevFlights,
      },
      zone_dwell_means: zoneDwellMeans,
      zone_dwell_stdevs: zoneDwellStdevs,
      zone_hit_counts: zoneHitCounts,
      dwell_times: stats(dwells),
      flight_times: stats(flights),
      rhythm: {
        kps_mean: kpsValues.length > 0 ? r2(mean(kpsValues)) : 0,
        kps_stdev: kpsValues.length > 1 ? r2(stdev(kpsValues)) : 0,
        burst_count: bursts.length,
        burst_length_mean: burstLengths.length > 0 ? r2(mean(burstLengths)) : 0,
        burst_length_stdev: burstLengths.length > 1 ? r2(stdev(burstLengths)) : 0,
        pause_count: pauseCount,
        inter_burst_gap_mean: interBurstGaps.length > 0 ? r2(mean(interBurstGaps)) : 0,
        inter_burst_gap_stdev: interBurstGaps.length > 1 ? r2(stdev(interBurstGaps)) : 0,
      },
      error_proxy: {
        backspace_rate: totalDown > 0 ? r2(backspaceCount / totalDown) : 0,
        delete_rate: totalDown > 0 ? r2(deleteCount / totalDown) : 0,
        rapid_same_zone_count: rapidSameZoneCount,
        correction_sequences: correctionSequences,
      },
      modifier_behavior: {
        shift_hold_mean_ms: shiftHoldTimes.length > 0 ? r2(mean(shiftHoldTimes)) : 0,
        modifier_before_key: (modifierBeforeKeyCount + modifierHeldKeyCount) > 0 ?
          r2(modifierBeforeKeyCount / (modifierBeforeKeyCount + modifierHeldKeyCount)) : 0,
      },
      bigram_velocity_histogram: bigramBins,
      total_keydowns: totalDown,
      window_duration_ms: r2(windowMs),
    };
  }

  // ═══════════════════════════════════════════════════════
  // G. POINTER FEATURE EXTRACTION (enhanced)
  // ═══════════════════════════════════════════════════════
  function extractPointer(events) {
    if (!events.length) return null;

    var speeds = [], accels = [];
    var clickCount = 0, dblClickCount = 0, lastClickTs = 0;
    var dirChanges = 0, prevVx = 0, prevVy = 0, prevSpeed = 0, prevTs = 0;
    var idleTime = 0, totalTime = 0, moveCount = 0;
    var distances = [], angles = [];
    var clickDwells = [], pendingDown = null;

    // Enhanced: total displacement tracking
    var firstX = null, firstY = null, lastX = 0, lastY = 0;
    var totalDist = 0;

    // Enhanced: angle histogram (8 compass bins: N,NE,E,SE,S,SW,W,NW)
    var angleHist = [0, 0, 0, 0, 0, 0, 0, 0];

    // Enhanced: segments (continuous motion separated by >100ms pause)
    var segments = [];
    var currentSegment = { startTs: 0, endTs: 0, distance: 0, displacement: 0, startX: 0, startY: 0, endX: 0, endY: 0 };
    var segmentActive = false;

    // Enhanced: idle periods with micro-movements
    var idlePeriods = [];
    var idleMicroAmps = [];

    for (var i = 0; i < events.length; i++) {
      var ev = events[i];

      if (ev.type === 'pm') {
        var speed = Math.sqrt(ev.vx * ev.vx + ev.vy * ev.vy);
        speeds.push(speed);
        moveCount++;

        if (firstX === null) { firstX = ev.nx || 0; firstY = ev.ny || 0; }
        lastX = ev.nx || 0; lastY = ev.ny || 0;

        if (prevTs > 0) {
          var dt = ev.ts - prevTs;
          var segDist = speed * dt;
          distances.push(segDist);
          totalDist += segDist;

          // Acceleration
          if (dt > 0) accels.push(Math.abs(speed - prevSpeed) / dt * 1000);

          // Direction changes (>30 degrees)
          if (ev.vx !== 0 || ev.vy !== 0) {
            var angle = Math.atan2(ev.vy, ev.vx);
            angles.push(angle);

            // Angle histogram: map angle to 8 compass bins
            var deg = ((angle * 180 / Math.PI) + 360) % 360;
            var bin = Math.floor(((deg + 22.5) % 360) / 45);
            if (bin >= 0 && bin < 8) angleHist[bin]++;
          }

          var prevAngle = Math.atan2(prevVy, prevVx);
          var currAngle = Math.atan2(ev.vy, ev.vx);
          var angleDiff = Math.abs(currAngle - prevAngle);
          if (angleDiff > Math.PI) angleDiff = 2 * Math.PI - angleDiff;
          if (angleDiff > Math.PI / 6) dirChanges++; // >30 degrees

          // Idle detection (gap > 2s)
          if (dt > 2000) {
            idleTime += dt;
            idlePeriods.push({ duration_ms: dt });
            if (speed > 0 && speed < 0.05) idleMicroAmps.push(speed);
          } else if (dt > 100) {
            // Segment boundary (>100ms pause)
            if (segmentActive) {
              currentSegment.endTs = prevTs;
              currentSegment.endX = lastX;
              currentSegment.endY = lastY;
              var dx = currentSegment.endX - currentSegment.startX;
              var dy = currentSegment.endY - currentSegment.startY;
              currentSegment.displacement = Math.sqrt(dx * dx + dy * dy);
              segments.push(currentSegment);
            }
            segmentActive = true;
            currentSegment = { startTs: ev.ts, endTs: ev.ts, distance: 0, displacement: 0, startX: lastX, startY: lastY, endX: lastX, endY: lastY };
          }

          if (segmentActive) {
            currentSegment.distance += segDist;
            currentSegment.endTs = ev.ts;
            currentSegment.endX = lastX;
            currentSegment.endY = lastY;
          }

          totalTime += dt;
        } else {
          segmentActive = true;
          currentSegment = { startTs: ev.ts, endTs: ev.ts, distance: 0, displacement: 0, startX: lastX, startY: lastY, endX: lastX, endY: lastY };
        }
        prevVx = ev.vx; prevVy = ev.vy; prevSpeed = speed; prevTs = ev.ts;

      } else if (ev.type === 'pd') {
        pendingDown = ev.ts;
      } else if (ev.type === 'pu') {
        if (pendingDown) { clickDwells.push(ev.ts - pendingDown); pendingDown = null; }
      } else if (ev.type === 'cl') {
        clickCount++;
        if (lastClickTs > 0 && (ev.ts - lastClickTs) < 400) dblClickCount++;
        lastClickTs = ev.ts;
      }
    }

    // Close last segment
    if (segmentActive && currentSegment.distance > 0) {
      currentSegment.endTs = prevTs;
      currentSegment.endX = lastX;
      currentSegment.endY = lastY;
      var sdx = currentSegment.endX - currentSegment.startX;
      var sdy = currentSegment.endY - currentSegment.startY;
      currentSegment.displacement = Math.sqrt(sdx * sdx + sdy * sdy);
      segments.push(currentSegment);
    }

    if (events.length > 1) totalTime = Math.max(totalTime, events[events.length - 1].ts - events[0].ts);

    // Curvature
    var curvature = 0;
    if (angles.length > 1) {
      var angleChanges = [];
      for (var a = 1; a < angles.length; a++) {
        var ac = Math.abs(angles[a] - angles[a - 1]);
        if (ac > Math.PI) ac = 2 * Math.PI - ac;
        angleChanges.push(ac);
      }
      curvature = angleChanges.length > 0 ? r2(mean(angleChanges) / Math.PI) : 0;
    }

    // Path efficiency: displacement / total distance
    var displacement = 0;
    if (firstX !== null) {
      var ddx = lastX - firstX, ddy = lastY - firstY;
      displacement = Math.sqrt(ddx * ddx + ddy * ddy);
    }
    var pathEfficiency = totalDist > 0 ? r2(displacement / totalDist) : 0;

    // Velocity percentiles
    var sortedSpeeds = speeds.slice().sort(function (a, b) { return a - b; });

    // Segment stats
    var segDurations = segments.map(function (s) { return s.endTs - s.startTs; });
    var segDistances = segments.map(function (s) { return s.distance; });
    var segEfficiencies = segments.map(function (s) { return s.distance > 0 ? s.displacement / s.distance : 0; });

    return {
      available: true,
      velocity: {
        mean: speeds.length ? r2(mean(speeds)) : 0,
        max: speeds.length ? r2(Math.max.apply(null, speeds)) : 0,
        p25: r2(percentile(sortedSpeeds, 0.25)),
        p50: r2(percentile(sortedSpeeds, 0.5)),
        p75: r2(percentile(sortedSpeeds, 0.75)),
        p95: r2(percentile(sortedSpeeds, 0.95)),
        std_dev: r2(stdev(speeds)),
      },
      acceleration: {
        mean: accels.length ? r2(mean(accels)) : 0,
        std_dev: r2(stdev(accels)),
        direction_changes_per_sec: totalTime > 0 ? r2(dirChanges / (totalTime / 1000)) : 0,
      },
      path_efficiency: pathEfficiency,
      angle_histogram: angleHist,
      segments: {
        count: segments.length,
        duration_mean: segDurations.length > 0 ? r2(mean(segDurations)) : 0,
        duration_stdev: segDurations.length > 1 ? r2(stdev(segDurations)) : 0,
        distance_mean: segDistances.length > 0 ? r2(mean(segDistances)) : 0,
        distance_stdev: segDistances.length > 1 ? r2(stdev(segDistances)) : 0,
        efficiency_mean: segEfficiencies.length > 0 ? r2(mean(segEfficiencies)) : 0,
      },
      clicks: {
        count: clickCount,
        double_click_count: dblClickCount,
        mean_dwell_ms: clickDwells.length ? r2(mean(clickDwells)) : 0,
        dwell_stdev: clickDwells.length > 1 ? r2(stdev(clickDwells)) : 0,
      },
      idle: {
        count: idlePeriods.length,
        duration_mean: idlePeriods.length > 0 ? r2(mean(idlePeriods.map(function (p) { return p.duration_ms; }))) : 0,
        micro_movement_amplitude: idleMicroAmps.length > 0 ? r2(mean(idleMicroAmps)) : 0,
        micro_movement_frequency: totalTime > 0 && idleMicroAmps.length > 0 ? r2(idleMicroAmps.length / (totalTime / 1000)) : 0,
      },
      idle_fraction: totalTime > 0 ? r2(idleTime / totalTime) : 0,
      ballistic_fraction: speeds.length ? r2(speeds.filter(function (v) { return v > 1.0; }).length / speeds.length) : 0,
      micro_correction_rate: moveCount > 0 ? r2(speeds.filter(function (v) { return v > 0 && v < 0.05; }).length / moveCount) : 0,
      mean_curvature: curvature,
      total_distance: r2(totalDist),
      displacement: r2(displacement),
      move_count: moveCount,
      window_duration_ms: r2(totalTime),
    };
  }

  // ═══════════════════════════════════════════════════════
  // SCROLL FEATURE EXTRACTION
  // ═══════════════════════════════════════════════════════
  function extractScroll(events) {
    if (!events.length) return null;

    var velocities = [], deltas = [];
    var upCount = 0, downCount = 0, horzCount = 0;
    var readingPauses = 0, rapidScrolls = 0;
    var prevTs = 0, prevY = 0;
    var dirChangeCount = 0, prevDir = 0;

    // Burst detection
    var burstCount = 0, currentBurstSize = 0;
    var burstSizes = [];

    for (var i = 0; i < events.length; i++) {
      var ev = events[i];
      var deltaY = ev.scrollY - prevY;

      if (prevTs > 0) {
        var dt = ev.ts - prevTs;
        var absDelta = Math.abs(deltaY);
        deltas.push(absDelta);
        if (dt > 0) velocities.push(absDelta / dt);

        if (dt > 1000 && dt < 5000) readingPauses++;
        if (absDelta > 300) rapidScrolls++;

        if (deltaY < 0) upCount++;
        else if (deltaY > 0) downCount++;

        // Direction changes
        var dir = deltaY > 0 ? 1 : (deltaY < 0 ? -1 : 0);
        if (dir !== 0 && prevDir !== 0 && dir !== prevDir) dirChangeCount++;
        if (dir !== 0) prevDir = dir;

        // Scroll bursts (rapid succession <200ms)
        if (dt < 200) {
          currentBurstSize++;
        } else {
          if (currentBurstSize > 2) { burstCount++; burstSizes.push(currentBurstSize); }
          currentBurstSize = 0;
        }
      }
      if (ev.scrollX !== undefined) horzCount++;
      prevTs = ev.ts;
      prevY = ev.scrollY;
    }
    if (currentBurstSize > 2) { burstCount++; burstSizes.push(currentBurstSize); }

    var total = (upCount + downCount + horzCount) || 1;

    return {
      available: true,
      scroll_events: events.length,
      mean_velocity: velocities.length ? r2(mean(velocities)) : 0,
      max_velocity: velocities.length ? r2(Math.max.apply(null, velocities)) : 0,
      velocity_stdev: velocities.length > 1 ? r2(stdev(velocities)) : 0,
      total_distance: deltas.length ? r2(deltas.reduce(function (a, b) { return a + b; }, 0)) : 0,
      mean_distance_per_scroll: deltas.length ? r2(mean(deltas)) : 0,
      reading_pause_count: readingPauses,
      rapid_scroll_count: rapidScrolls,
      direction_changes: dirChangeCount,
      burst_count: burstCount,
      burst_size_mean: burstSizes.length > 0 ? r2(mean(burstSizes)) : 0,
      direction_distribution: { up: r2(upCount / total), down: r2(downCount / total), horizontal: r2(horzCount / total) },
    };
  }

  // ═══════════════════════════════════════════════════════
  // TOUCH FEATURE EXTRACTION
  // ═══════════════════════════════════════════════════════
  function extractTouch(events) {
    if (!events.length) return null;

    var tapCount = 0, tapDwells = [], tapFlights = [];
    var swipeCount = 0, pinchCount = 0;
    var areas = [], pressures = [];
    var lastTapEnd = 0, pendingStart = null;
    var swipeDurations = [];

    // Heatmap zones (3x4 = 12 grid)
    var heatmapZones = [];
    for (var hz = 0; hz < 12; hz++) heatmapZones[hz] = 0;

    for (var i = 0; i < events.length; i++) {
      var ev = events[i];
      if (ev.area > 0) areas.push(ev.area);
      if (ev.pressure > 0) pressures.push(ev.pressure);

      // Heatmap tracking (normalized coordinates)
      if (ev.nx !== undefined && ev.ny !== undefined) {
        var col = Math.min(2, Math.floor(ev.nx * 3));
        var row = Math.min(3, Math.floor(ev.ny * 4));
        var zoneIdx = row * 3 + col;
        if (zoneIdx >= 0 && zoneIdx < 12) heatmapZones[zoneIdx]++;
      }

      if (ev.type === 'ts') {
        pendingStart = ev;
        if (ev.touches > 1) pinchCount++;
        if (lastTapEnd > 0) tapFlights.push(ev.ts - lastTapEnd);
      } else if (ev.type === 'te') {
        if (pendingStart) {
          var dur = ev.ts - pendingStart.ts;
          if (dur < 300) { tapCount++; tapDwells.push(dur); }
          else {
            swipeCount++;
            swipeDurations.push(dur);
          }
        }
        lastTapEnd = ev.ts;
        pendingStart = null;
      }
    }

    // Normalize heatmap
    var totalHeat = 0;
    for (var h = 0; h < 12; h++) totalHeat += heatmapZones[h];
    if (totalHeat > 0) {
      for (var hh = 0; hh < 12; hh++) heatmapZones[hh] = r2(heatmapZones[hh] / totalHeat);
    }

    return {
      available: true,
      mean_contact_area: areas.length ? r2(mean(areas)) : 0,
      area_stdev: areas.length > 1 ? r2(stdev(areas)) : 0,
      mean_pressure: pressures.length ? r2(mean(pressures)) : 0,
      pressure_stdev: pressures.length > 1 ? r2(stdev(pressures)) : 0,
      tap: {
        count: tapCount,
        mean_dwell_ms: tapDwells.length > 0 ? r2(mean(tapDwells)) : 0,
        dwell_stdev: tapDwells.length > 1 ? r2(stdev(tapDwells)) : 0,
        mean_flight_ms: tapFlights.length > 0 ? r2(mean(tapFlights)) : 0,
        flight_stdev: tapFlights.length > 1 ? r2(stdev(tapFlights)) : 0,
      },
      swipe: {
        count: swipeCount,
        duration_mean: swipeDurations.length > 0 ? r2(mean(swipeDurations)) : 0,
        duration_stdev: swipeDurations.length > 1 ? r2(stdev(swipeDurations)) : 0,
      },
      pinch_count: pinchCount,
      heatmap_zones: heatmapZones,
      dominant_hand_hint: 'unknown',
    };
  }

  // ═══════════════════════════════════════════════════════
  // E. SENSOR FEATURE EXTRACTION
  // ═══════════════════════════════════════════════════════
  function extractSensor(events) {
    if (!events.length) return null;

    var accelX = [], accelY = [], accelZ = [];
    var gyroX = [], gyroY = [], gyroZ = [];
    var orientAlpha = [], orientBeta = [], orientGamma = [];

    for (var i = 0; i < events.length; i++) {
      var ev = events[i];
      if (ev.type === 'motion') {
        if (ev.ax != null) accelX.push(ev.ax);
        if (ev.ay != null) accelY.push(ev.ay);
        if (ev.az != null) accelZ.push(ev.az);
        if (ev.gx != null) gyroX.push(ev.gx);
        if (ev.gy != null) gyroY.push(ev.gy);
        if (ev.gz != null) gyroZ.push(ev.gz);
      } else if (ev.type === 'orientation') {
        if (ev.alpha != null) orientAlpha.push(ev.alpha);
        if (ev.beta != null) orientBeta.push(ev.beta);
        if (ev.gamma != null) orientGamma.push(ev.gamma);
      }
    }

    // Accelerometer magnitude
    var accelMag = [];
    var minLen = Math.min(accelX.length, accelY.length, accelZ.length);
    for (var m = 0; m < minLen; m++) {
      accelMag.push(Math.sqrt(accelX[m] * accelX[m] + accelY[m] * accelY[m] + accelZ[m] * accelZ[m]));
    }

    // Gyroscope magnitude
    var gyroMag = [];
    var gMinLen = Math.min(gyroX.length, gyroY.length, gyroZ.length);
    for (var gm = 0; gm < gMinLen; gm++) {
      gyroMag.push(Math.sqrt(gyroX[gm] * gyroX[gm] + gyroY[gm] * gyroY[gm] + gyroZ[gm] * gyroZ[gm]));
    }

    return {
      available: true,
      accelerometer: {
        x: { mean: r2(mean(accelX)), stdev: r2(stdev(accelX)) },
        y: { mean: r2(mean(accelY)), stdev: r2(stdev(accelY)) },
        z: { mean: r2(mean(accelZ)), stdev: r2(stdev(accelZ)) },
        magnitude: { mean: r2(mean(accelMag)), stdev: r2(stdev(accelMag)) },
      },
      gyroscope: {
        x: { mean: r2(mean(gyroX)), stdev: r2(stdev(gyroX)) },
        y: { mean: r2(mean(gyroY)), stdev: r2(stdev(gyroY)) },
        z: { mean: r2(mean(gyroZ)), stdev: r2(stdev(gyroZ)) },
        magnitude: { mean: r2(mean(gyroMag)), stdev: r2(stdev(gyroMag)) },
      },
      orientation: {
        alpha: { mean: r2(mean(orientAlpha)), stdev: r2(stdev(orientAlpha)) },
        beta: { mean: r2(mean(orientBeta)), stdev: r2(stdev(orientBeta)) },
        gamma: { mean: r2(mean(orientGamma)), stdev: r2(stdev(orientGamma)) },
      },
      sample_count: events.length,
    };
  }

  // ═══════════════════════════════════════════════════════
  // CREDENTIAL FEATURE EXTRACTION
  // ═══════════════════════════════════════════════════════
  function extractCredential(events) {
    if (!events.length) return null;

    var result = { available: true };
    var pw = events.filter(function (e) { return e.field_type === 'password'; });
    var un = events.filter(function (e) { return e.field_type === 'username'; });
    var form = events.filter(function (e) { return e.field_type === 'form'; });

    if (pw.length > 0) {
      var pwKeys = pw.filter(function (e) { return e.event === 'keystroke'; }).length;
      var pwBs = pw.filter(function (e) { return e.event === 'backspace'; }).length;
      var pwZoneSeq = buildCredentialZoneSequence('password');
      result.password_field = {
        total_keystrokes: pwKeys,
        char_count: pwKeys - pwBs,
        backspace_count: pwBs,
        paste_detected: pw.some(function (e) { return e.event === 'paste'; }),
        autofill_detected: pw.some(function (e) { return e.event === 'autofill'; }),
        typed_then_cleared: pw.some(function (e) { return e.event === 'clear_retype'; }),
        hesitation_count: pw.filter(function (e) { return e.event === 'hesitation'; }).length,
        credential_zone_sequence: pwZoneSeq,
        total_duration_ms: pw.length > 1 ? r2(pw[pw.length - 1].ts - pw[0].ts) : 0,
      };
      resetCredZoneTracking('password');
    }

    if (un.length > 0) {
      var unZoneSeq = buildCredentialZoneSequence('username');
      result.username_field = {
        total_keystrokes: un.filter(function (e) { return e.event === 'keystroke'; }).length,
        backspace_count: un.filter(function (e) { return e.event === 'backspace'; }).length,
        paste_detected: un.some(function (e) { return e.event === 'paste'; }),
        autofill_detected: un.some(function (e) { return e.event === 'autofill'; }),
        autocomplete_selected: un.some(function (e) { return e.event === 'autocomplete'; }),
        credential_zone_sequence: unZoneSeq,
        total_duration_ms: un.length > 1 ? r2(un[un.length - 1].ts - un[0].ts) : 0,
      };
      resetCredZoneTracking('username');
    }

    if (form.length > 0) {
      var submitEv = form.filter(function (e) { return e.event === 'submit'; })[0];
      result.form = {
        time_to_submit_ms: submitEv ? submitEv.time_to_submit || 0 : 0,
        tab_navigation_count: form.filter(function (e) { return e.event === 'tab'; }).length,
        submit_method: submitEv ? submitEv.method || 'unknown' : 'unknown',
        field_focus_changes: form.filter(function (e) { return e.event === 'focus_change'; }).length,
      };
    }

    return result;
  }

  // ═══════════════════════════════════════════════════════
  // BATCH ASSEMBLY
  // ═══════════════════════════════════════════════════════
  function buildEventClassification(batchType, pageContext) {
    return {
      batch_type: batchType,
      page_class: pageContext.page_class,
      is_critical_action: pageContext.page_class === 'critical_action',
      critical_action_name: pageContext.critical_action || null,
      committed: pageContext.committed !== undefined ? pageContext.committed : null,
      time_on_page_ms: pageContext.time_on_page_ms || null,
    };
  }

  function collectSiteWideSnapshot() {
    // Update visibility durations
    var now = performance.now();
    if (state.visible && siteWide.tab_visible_start) {
      siteWide.tab_visible_duration_ms += (now - siteWide.tab_visible_start);
      siteWide.tab_visible_start = now;
    }
    if (!state.visible && siteWide.tab_hidden_start) {
      siteWide.tab_hidden_duration_ms += (now - siteWide.tab_hidden_start);
      siteWide.tab_hidden_start = now;
    }

    return {
      navigation_flow: siteWide.navigation_flow.slice(),
      clipboard: {
        copy_count: siteWide.copy_count,
        cut_count: siteWide.cut_count,
        paste_count: siteWide.paste_count,
      },
      resize_count: siteWide.resize_count,
      viewport: { w: siteWide.last_viewport.w, h: siteWide.last_viewport.h },
      network_changes: siteWide.network_changes.slice(),
      js_error_count: siteWide.js_error_count,
      focus: {
        tab_visible_duration_ms: r2(siteWide.tab_visible_duration_ms),
        tab_hidden_duration_ms: r2(siteWide.tab_hidden_duration_ms),
        focus_changes_count: siteWide.focus_changes_count,
        visibility_changes_count: siteWide.visibility_changes_count,
      },
      ime: {
        active: siteWide.ime_active,
        event_count: siteWide.ime_event_count,
      },
    };
  }

  function assembleBatch(batchType, pageContext) {
    var kEvents = keyBuffer.splice(0);
    var pEvents = pointerBuffer.splice(0);
    var sEvents = scrollBuffer.splice(0);
    var tEvents = touchBuffer.splice(0);
    var cEvents = credBuffer.splice(0);
    var snEvents = sensorBuffer.splice(0);
    var allTs = [].concat(kEvents, pEvents, sEvents, tEvents, cEvents, snEvents).map(function (e) { return e.ts; });
    var eventCount = kEvents.length + pEvents.length + sEvents.length + tEvents.length + cEvents.length + snEvents.length;

    var signals = {};
    var ks = extractKeystroke(kEvents); if (ks) signals.keystroke = ks;
    var ps = extractPointer(pEvents); if (ps) signals.pointer = ps;
    var ss = extractScroll(sEvents); if (ss) signals.scroll = ss;
    var ts = extractTouch(tEvents); if (ts) signals.touch = ts;
    var cs = extractCredential(cEvents); if (cs) signals.credential = cs;
    var sns = extractSensor(snEvents); if (sns) signals.sensor = sns;

    // Collect load indicators
    collectLoadIndicators();

    state.sequence++;

    return {
      type: batchType,
      batch_id: makeUUID(),
      sent_at: Date.now(),
      session_id: state.session_id,
      pulse: state.pulse,
      pulse_interval_ms: state.page_class === 'critical_action' ? KEEPALIVE_INTERVAL : PULSE_INTERVAL,
      sequence: state.sequence,
      user_hash: state.user_hash,
      device_uuid: state.device_uuid,
      origin_hash: state.origin_hash,
      liveness_status: state.liveness_status,
      page_context: pageContext,
      event_classification: buildEventClassification(batchType, pageContext),
      window_start_ms: allTs.length ? r2(Math.min.apply(null, allTs)) : r2(performance.now()),
      window_end_ms: allTs.length ? r2(Math.max.apply(null, allTs)) : r2(performance.now()),
      event_count: eventCount,
      signals: signals,
      automation_score: (deviceFingerprint && deviceFingerprint.automation) ? deviceFingerprint.automation.score : undefined,
      device_context: deviceContext,
      device_fingerprint: deviceFingerprint,
      site_wide: collectSiteWideSnapshot(),
      load_indicators: {
        fps: loadIndicators.fps,
        event_loop_latency_ms: loadIndicators.event_loop_latency_ms,
        memory_pressure: loadIndicators.memory_pressure,
        page_load_ms: loadIndicators.page_load_ms,
      },
      sdk: { version: SDK_VERSION, platform: 'web', worker_mode: 'fallback_main_thread', environment: 'debug' },
    };
  }

  function takeSignalSnapshot() {
    var kE = keyBuffer.splice(0), pE = pointerBuffer.splice(0), sE = scrollBuffer.splice(0);
    var tE = touchBuffer.splice(0), cE = credBuffer.splice(0), snE = sensorBuffer.splice(0);
    var allTs = [].concat(kE, pE, sE, tE, cE, snE).map(function (e) { return e.ts; });
    var signals = {};
    var ks = extractKeystroke(kE); if (ks) signals.keystroke = ks;
    var ps = extractPointer(pE); if (ps) signals.pointer = ps;
    var ss = extractScroll(sE); if (ss) signals.scroll = ss;
    var ts = extractTouch(tE); if (ts) signals.touch = ts;
    var cs = extractCredential(cE); if (cs) signals.credential = cs;
    var sns = extractSensor(snE); if (sns) signals.sensor = sns;
    return {
      event_count: kE.length + pE.length + sE.length + tE.length + cE.length + snE.length,
      window_start: allTs.length ? Math.min.apply(null, allTs) : performance.now(),
      window_end: allTs.length ? Math.max.apply(null, allTs) : performance.now(),
      signals: signals,
    };
  }

  function assembleStagedBatch(batchType, pageContext) {
    var snap = takeSignalSnapshot();
    if (snap.event_count > 0) stagingBuffer.push(snap);

    var signals = {}, eventCount = 0, wStart = Infinity, wEnd = 0;
    for (var i = 0; i < stagingBuffer.length; i++) {
      var s = stagingBuffer[i];
      eventCount += s.event_count;
      if (s.window_start < wStart) wStart = s.window_start;
      if (s.window_end > wEnd) wEnd = s.window_end;
      for (var sk in s.signals) { signals[sk] = s.signals[sk]; }
    }

    collectLoadIndicators();
    state.sequence++;

    return {
      type: batchType,
      batch_id: makeUUID(),
      sent_at: Date.now(),
      session_id: state.session_id,
      pulse: state.pulse,
      pulse_interval_ms: KEEPALIVE_INTERVAL,
      sequence: state.sequence,
      user_hash: state.user_hash,
      device_uuid: state.device_uuid,
      origin_hash: state.origin_hash,
      liveness_status: state.liveness_status,
      page_context: pageContext,
      event_classification: buildEventClassification(batchType, pageContext),
      window_start_ms: wStart === Infinity ? r2(performance.now()) : r2(wStart),
      window_end_ms: wEnd === 0 ? r2(performance.now()) : r2(wEnd),
      event_count: eventCount,
      signals: signals,
      automation_score: (deviceFingerprint && deviceFingerprint.automation) ? deviceFingerprint.automation.score : undefined,
      device_context: deviceContext,
      device_fingerprint: deviceFingerprint,
      site_wide: collectSiteWideSnapshot(),
      load_indicators: {
        fps: loadIndicators.fps,
        event_loop_latency_ms: loadIndicators.event_loop_latency_ms,
        memory_pressure: loadIndicators.memory_pressure,
        page_load_ms: loadIndicators.page_load_ms,
      },
      sdk: { version: SDK_VERSION, platform: 'web', worker_mode: 'fallback_main_thread', environment: 'debug' },
    };
  }

  // ═══════════════════════════════════════════════════════
  // TRANSPORT
  // ═══════════════════════════════════════════════════════
  function sendBatch(batch, useKeepalive) {
    if (!state.user_hash) return;
    var bodyStr = JSON.stringify(batch);
    var timestamp = String(batch.sent_at || Date.now());
    var nonce = batch.batch_id || '';

    // Compute HMAC auth + SHA-256 checksum in parallel
    Promise.all([
      hmacSha256('kp_test_demo', timestamp + '.' + nonce),
      sha256(bodyStr),
      hmacSha256('kp_test_demo', nonce + '.' + timestamp + '.' + bodyStr.length),
    ]).then(function (results) {
      var authToken = results[0];
      var checksum = results[1];
      var signature = results[2];

      var headers = {
        'Content-Type': 'application/json',
        'X-KP-Key-Id': 'kp_test_demo'.substring(0, 12),
        'X-KP-Session': state.session_id || '',
        'X-KP-Device': state.device_uuid || '',
        'X-KP-Nonce': nonce,
        'X-KP-Timestamp': timestamp,
      };
      if (authToken) headers['X-KP-Auth-Token'] = authToken;
      if (checksum) headers['X-KP-Checksum'] = checksum;
      if (signature) headers['X-KP-Signature'] = signature;
      if (state.origin_hash) headers['X-KP-Origin-Hash'] = state.origin_hash;

      try {
        fetch(ENDPOINT, {
          method: 'POST',
          headers: headers,
          body: bodyStr,
          keepalive: !!useKeepalive,
        }).then(function (r) {
          if (!r.ok) { console.error('[KP] send failed: status=' + r.status + ' type=' + batch.type); return; }
          return r.json();
        }).then(function (data) {
          if (data && data.ok && data.data) {
            auditRecord('batch_sent', { batch_id: batch.batch_id, type: batch.type, checksum: checksum });
            for (var k = 0; k < state.listeners.drift.length; k++) {
              try { state.listeners.drift[k](data.data); } catch (e) { /* */ }
            }
            var sigNames = Object.keys(batch.signals || {}).join(',') || 'none';
            updateStatus('p=' + state.pulse + ' ev=' + (batch.event_count || 0) + ' sigs=[' + sigNames + '] ' + batch.type);
          }
        }).catch(function (err) { console.error('[KP] send error:', err); });
      } catch (e) { console.error('[KP] send error:', e); }
    });
  }

  // ═══════════════════════════════════════════════════════
  // PULSE LOOP
  // ═══════════════════════════════════════════════════════
  function startPulseLoop() {
    stopPulseLoop();
    var interval = state.page_class === 'critical_action' ? KEEPALIVE_INTERVAL : PULSE_INTERVAL;
    state.pulse_timer = setInterval(function () {
      if (!state.visible || !state.user_hash) return;
      state.pulse++;

      if (state.page_class === 'critical_action') {
        var snap = takeSignalSnapshot();
        if (snap.event_count > 0) stagingBuffer.push(snap);
        var keepaliveBatch = {
          type: 'keepalive', batch_id: makeUUID(), sent_at: Date.now(),
          session_id: state.session_id, pulse: state.pulse, pulse_interval_ms: KEEPALIVE_INTERVAL,
          user_hash: state.user_hash, device_uuid: state.device_uuid,
          origin_hash: state.origin_hash, liveness_status: state.liveness_status,
          page_context: { url_path: location.pathname, page_class: 'critical_action', critical_action: state.current_action || '' },
          event_classification: { batch_type: 'keepalive', page_class: 'critical_action', is_critical_action: true, critical_action_name: state.current_action, committed: null },
          site_wide: collectSiteWideSnapshot(),
          load_indicators: {
            fps: loadIndicators.fps,
            event_loop_latency_ms: loadIndicators.event_loop_latency_ms,
            memory_pressure: loadIndicators.memory_pressure,
            page_load_ms: loadIndicators.page_load_ms,
          },
          sdk: { version: SDK_VERSION, platform: 'web' },
        };
        // Only include full fingerprint on first keepalive — saves ~6KB per pulse
        if (state.pulse <= 1) {
          keepaliveBatch.device_context = deviceContext;
          keepaliveBatch.device_fingerprint = deviceFingerprint;
        }
        sendBatch(keepaliveBatch);
      } else {
        if (keyBuffer.length < MIN_EVENTS_FOR_PULSE) return;
        sendBatch(assembleBatch('behavioral', { url_path: location.pathname, page_class: 'normal' }));
      }
    }, interval);
  }

  function stopPulseLoop() {
    if (state.pulse_timer) { clearInterval(state.pulse_timer); state.pulse_timer = null; }
  }

  // ═══════════════════════════════════════════════════════
  // PAGE CLASSIFICATION + CRITICAL ACTIONS
  // ═══════════════════════════════════════════════════════
  var CRITICAL_ACTIONS = [
    { page: /\/login/, action: 'login_submit', commit: 'button[type="submit"], [data-kp-commit]' },
    { page: /\/payment/, action: 'payment_confirm', commit: 'button[type="submit"], [data-kp-commit="payment"]' },
    { page: /\/transfer/, action: 'transfer_confirm', commit: 'button[type="submit"], [data-kp-commit="transfer"]' },
  ];

  function classifyPage(path) {
    // Track navigation flow
    var now = performance.now();
    if (siteWide.current_page_url) {
      siteWide.navigation_flow.push({
        url: siteWide.current_page_url,
        entered_at: r2(siteWide.current_page_entered),
        left_at: r2(now),
        duration_ms: r2(now - siteWide.current_page_entered),
      });
    }
    siteWide.current_page_url = path;
    siteWide.current_page_entered = now;

    // Abandon check
    if (state.page_class === 'critical_action' && state.current_action && stagingBuffer.length > 0) {
      var ab = assembleStagedBatch('critical_action', {
        url_path: location.pathname, page_class: 'critical_action',
        critical_action: state.current_action, committed: false,
        time_on_page_ms: r2(performance.now() - state.page_entered_at),
      });
      sendBatch(ab);
    }
    for (var i = 0; i < CRITICAL_ACTIONS.length; i++) {
      if (CRITICAL_ACTIONS[i].page.test(path)) {
        state.page_class = 'critical_action'; state.current_action = CRITICAL_ACTIONS[i].action;
        state.page_entered_at = performance.now(); stagingBuffer = [];
        startPulseLoop(); updateStatus('critical: ' + CRITICAL_ACTIONS[i].action); return;
      }
    }
    state.page_class = 'normal'; state.current_action = null;
    startPulseLoop(); updateStatus('normal | p=' + state.pulse);
  }

  function handleCommit(action) {
    var batch = assembleStagedBatch('critical_action', {
      url_path: location.pathname, page_class: 'critical_action',
      critical_action: action, committed: true,
      time_on_page_ms: r2(performance.now() - state.page_entered_at),
    });
    sendBatch(batch); stagingBuffer = [];
    for (var k = 0; k < state.listeners.critical_action.length; k++) {
      try { state.listeners.critical_action[k](batch); } catch (e) { /* */ }
    }
  }

  function updateStatus(msg) {
    var el = document.getElementById('kp-status');
    if (el) el.textContent = 'KP: ' + msg;
  }

  // ═══════════════════════════════════════════════════════
  // EVENT LISTENERS (keyboard, pointer, scroll, touch, cred)
  // ═══════════════════════════════════════════════════════
  function setupListeners() {
    var lastPtrX = 0, lastPtrY = 0, lastPtrTs = 0;
    var formFirstTs = 0, prevPwLen = 0, lastKeydownTs = 0;

    // ---- Keyboard ----
    document.addEventListener('keydown', function (e) {
      if (state.page_class === 'opted_out') return;
      recordEvent();
      var zone = getZone(e.code);
      var field = null;
      var ts = performance.now();

      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        field = e.target.name || e.target.type || 'unknown';
        if (!formFirstTs) formFirstTs = ts;

        if (e.target.type === 'password') {
          credBuffer.push({ field_type: 'password', event: e.code === 'Backspace' ? 'backspace' : 'keystroke', ts: ts });
          recordCredZoneEvent('password', zone, ts, 'kd');
          if (e.code === 'Backspace') prevPwLen = Math.max(0, prevPwLen - 1);
          else prevPwLen++;
        } else if (e.target.name === 'email' || e.target.name === 'username' || e.target.type === 'email') {
          credBuffer.push({ field_type: 'username', event: e.code === 'Backspace' ? 'backspace' : 'keystroke', ts: ts });
          recordCredZoneEvent('username', zone, ts, 'kd');
        }
        if (e.code === 'Tab') credBuffer.push({ field_type: 'form', event: 'tab', ts: ts });
      }
      lastKeydownTs = ts;
      keyBuffer.push({ type: 'kd', zone: zone, code: e.code, ts: ts, field: field });
    }, { passive: true });

    document.addEventListener('keyup', function (e) {
      if (state.page_class === 'opted_out') return;
      var field = null;
      var ts = performance.now();
      var zone = getZone(e.code);

      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        field = e.target.name || e.target.type || 'unknown';

        if (e.target.type === 'password') {
          recordCredZoneEvent('password', zone, ts, 'ku');
        } else if (e.target.name === 'email' || e.target.name === 'username' || e.target.type === 'email') {
          recordCredZoneEvent('username', zone, ts, 'ku');
        }
      }
      keyBuffer.push({ type: 'ku', zone: zone, code: e.code, ts: ts, field: field });
    }, { passive: true });

    // ---- Pointer ----
    var PTR_THROTTLE_MS = 50; // 20Hz — plenty for behavioral features
    document.addEventListener('pointermove', function (e) {
      if (state.page_class === 'opted_out') return;
      recordEvent();
      var ts = performance.now();
      if (ts - lastPtrTs < PTR_THROTTLE_MS) return; // throttle
      var dt = ts - lastPtrTs;
      var vx = dt > 0 ? (e.clientX - lastPtrX) / dt : 0;
      var vy = dt > 0 ? (e.clientY - lastPtrY) / dt : 0;
      var nx = window.innerWidth > 0 ? e.clientX / window.innerWidth : 0;
      var ny = window.innerHeight > 0 ? e.clientY / window.innerHeight : 0;
      lastPtrX = e.clientX; lastPtrY = e.clientY; lastPtrTs = ts;
      pointerBuffer.push({ type: 'pm', ts: ts, vx: vx, vy: vy, nx: nx, ny: ny });
    }, { passive: true });

    document.addEventListener('pointerdown', function () {
      if (state.page_class === 'opted_out') return;
      pointerBuffer.push({ type: 'pd', ts: performance.now(), vx: 0, vy: 0 });
    }, { passive: true });

    document.addEventListener('pointerup', function () {
      if (state.page_class === 'opted_out') return;
      pointerBuffer.push({ type: 'pu', ts: performance.now(), vx: 0, vy: 0 });
    }, { passive: true });

    document.addEventListener('click', function (e) {
      if (state.page_class === 'opted_out') return;
      if (state.page_class === 'critical_action' && state.current_action) {
        // Walk up from e.target to find if a commit element was clicked (handles clicks on child nodes)
        var el = e.target;
        while (el && el !== document) {
          if (el instanceof Element) {
            for (var c = 0; c < CRITICAL_ACTIONS.length; c++) {
              if (CRITICAL_ACTIONS[c].action !== state.current_action) continue;
              try {
                if (el.matches(CRITICAL_ACTIONS[c].commit)) {
                  console.log('[KP] commit detected:', state.current_action, 'target:', el.tagName);
                  credBuffer.push({
                    field_type: 'form', event: 'submit', ts: performance.now(),
                    method: 'button_click', time_to_submit: formFirstTs > 0 ? r2(performance.now() - formFirstTs) : 0
                  });
                  handleCommit(state.current_action); formFirstTs = 0; prevPwLen = 0; return;
                }
              } catch (err) { /* */ }
            }
          }
          el = el.parentNode;
        }
      }
      pointerBuffer.push({ type: 'cl', ts: performance.now(), vx: 0, vy: 0 });
    }, { passive: true });

    // ---- Scroll (throttled to 100ms / 10Hz) ----
    var lastScrollTs = 0;
    document.addEventListener('scroll', function () {
      if (state.page_class === 'opted_out') return;
      var ts = performance.now();
      if (ts - lastScrollTs < 100) return;
      lastScrollTs = ts;
      scrollBuffer.push({ ts: ts, scrollY: window.scrollY, scrollX: window.scrollX });
    }, { passive: true, capture: true });

    // ---- Touch ----
    document.addEventListener('touchstart', function (e) {
      if (state.page_class === 'opted_out') return;
      var t = e.touches[0];
      var area = t && t.radiusX ? Math.min(t.radiusX / 50, 1) : 0;
      var nx = t && window.innerWidth > 0 ? t.clientX / window.innerWidth : 0;
      var ny = t && window.innerHeight > 0 ? t.clientY / window.innerHeight : 0;
      touchBuffer.push({ type: 'ts', ts: performance.now(), touches: e.touches.length, area: area, pressure: t ? (t.force || 0) : 0, nx: nx, ny: ny });
    }, { passive: true });

    document.addEventListener('touchend', function (e) {
      if (state.page_class === 'opted_out') return;
      touchBuffer.push({ type: 'te', ts: performance.now(), touches: e.changedTouches.length, area: 0, pressure: 0 });
    }, { passive: true });

    document.addEventListener('touchmove', function (e) {
      if (state.page_class === 'opted_out') return;
      var t = e.touches[0];
      var area = t && t.radiusX ? Math.min(t.radiusX / 50, 1) : 0;
      touchBuffer.push({ type: 'tm', ts: performance.now(), touches: e.touches.length, area: area, pressure: 0 });
    }, { passive: true });

    // ---- Paste detection ----
    document.addEventListener('paste', function (e) {
      siteWide.paste_count++;
      var t = e.target;
      if (t instanceof HTMLInputElement) {
        if (t.type === 'password') credBuffer.push({ field_type: 'password', event: 'paste', ts: performance.now() });
        else if (t.name === 'email' || t.name === 'username') credBuffer.push({ field_type: 'username', event: 'paste', ts: performance.now() });
      }
    }, { passive: true, capture: true });

    // ---- Copy detection (F.2) ----
    document.addEventListener('copy', function () {
      siteWide.copy_count++;
    }, { passive: true, capture: true });

    // ---- Cut detection (F.2) ----
    document.addEventListener('cut', function () {
      siteWide.cut_count++;
    }, { passive: true, capture: true });

    // ---- Autofill detection ----
    document.addEventListener('input', function (e) {
      var t = e.target;
      if (!(t instanceof HTMLInputElement)) return;
      if (performance.now() - lastKeydownTs > 100) {
        if (t.type === 'password') credBuffer.push({ field_type: 'password', event: 'autofill', ts: performance.now() });
        else if (t.name === 'email' || t.name === 'username') credBuffer.push({ field_type: 'username', event: 'autofill', ts: performance.now() });
      }
    }, { passive: true, capture: true });

    // ---- Focus change tracking for credential fields ----
    document.addEventListener('focus', function (e) {
      if (e.target instanceof HTMLInputElement) credBuffer.push({ field_type: 'form', event: 'focus_change', ts: performance.now() });
    }, { passive: true, capture: true });

    // ---- Visibility + pagehide ----
    document.addEventListener('visibilitychange', function () {
      siteWide.visibility_changes_count++;
      var now = performance.now();
      if (document.visibilityState === 'visible') {
        state.visible = true;
        // Track hidden duration
        if (siteWide.tab_hidden_start) {
          siteWide.tab_hidden_duration_ms += (now - siteWide.tab_hidden_start);
          siteWide.tab_hidden_start = null;
        }
        siteWide.tab_visible_start = now;
        startPulseLoop();
      } else {
        state.visible = false;
        // Track visible duration
        if (siteWide.tab_visible_start) {
          siteWide.tab_visible_duration_ms += (now - siteWide.tab_visible_start);
          siteWide.tab_visible_start = null;
        }
        siteWide.tab_hidden_start = now;
        stopPulseLoop();
      }
    });

    // ---- Focus/blur on window (F.7) ----
    window.addEventListener('focus', function () {
      siteWide.focus_changes_count++;
    }, { passive: true });

    window.addEventListener('blur', function () {
      siteWide.focus_changes_count++;
    }, { passive: true });

    // ---- Page hide ----
    window.addEventListener('pagehide', function (e) {
      if (!state.user_hash) return;
      if (state.page_class === 'critical_action' && state.current_action && (stagingBuffer.length > 0 || keyBuffer.length > 0)) {
        var ab = assembleStagedBatch('critical_action', {
          url_path: location.pathname, page_class: 'critical_action', critical_action: state.current_action,
          committed: false, time_on_page_ms: r2(performance.now() - state.page_entered_at),
        });
        ab.api_key_id = 'kp_test_demo'.substring(0, 12);
        var abPayload = JSON.stringify({ payload: JSON.stringify(ab), key_id: 'kp_test_demo'.substring(0, 12), timestamp: Date.now(), nonce: ab.batch_id, signature: 'beacon_presigned' });
        try { navigator.sendBeacon(ENDPOINT, abPayload); } catch (err) { /* */ }
      } else if (!e.persisted) {
        var b = assembleBatch('behavioral', { url_path: location.pathname, page_class: state.page_class });
        b.api_key_id = 'kp_test_demo'.substring(0, 12);
        var bPayload = JSON.stringify({ payload: JSON.stringify(b), key_id: 'kp_test_demo'.substring(0, 12), timestamp: Date.now(), nonce: b.batch_id, signature: 'beacon_presigned' });
        if (b.event_count > 0) try { navigator.sendBeacon(ENDPOINT, bPayload); } catch (err) { /* */ }
      }
    });

    // ---- F.3 Window resize ----
    window.addEventListener('resize', function () {
      siteWide.resize_count++;
      siteWide.last_viewport = { w: window.innerWidth, h: window.innerHeight };
    }, { passive: true });

    // ---- F.4 Network changes ----
    try {
      var conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
      if (conn) {
        conn.addEventListener('change', function () {
          siteWide.network_changes.push({
            ts: performance.now(),
            type: conn.type || null,
            effective_type: conn.effectiveType || null,
            downlink: conn.downlink || null,
            rtt: conn.rtt || null,
          });
        });
      }
    } catch (e) { /* */ }

    // ---- F.5 JS error count ----
    window.addEventListener('error', function () {
      siteWide.js_error_count++;
    }, { passive: true });

    // ---- F.8 IME/composition ----
    document.addEventListener('compositionstart', function () {
      siteWide.ime_active = true;
      siteWide.ime_event_count++;
    }, { passive: true });

    document.addEventListener('compositionend', function () {
      siteWide.ime_active = false;
      siteWide.ime_event_count++;
    }, { passive: true });
  }

  // ═══════════════════════════════════════════════════════
  // E. SENSOR COLLECTOR (DeviceMotion + DeviceOrientation)
  // ═══════════════════════════════════════════════════════
  function setupSensorListeners() {
    // DeviceMotion (accelerometer + gyroscope)
    try {
      if (window.DeviceMotionEvent) {
        window.addEventListener('devicemotion', function (e) {
          if (state.page_class === 'opted_out') return;
          var acc = e.accelerationIncludingGravity || {};
          var rot = e.rotationRate || {};
          sensorBuffer.push({
            type: 'motion',
            ts: performance.now(),
            ax: acc.x != null ? r2(acc.x) : null,
            ay: acc.y != null ? r2(acc.y) : null,
            az: acc.z != null ? r2(acc.z) : null,
            gx: rot.alpha != null ? r2(rot.alpha) : null,
            gy: rot.beta != null ? r2(rot.beta) : null,
            gz: rot.gamma != null ? r2(rot.gamma) : null,
          });
        }, { passive: true });
      }
    } catch (e) { /* */ }

    // DeviceOrientation
    try {
      if (window.DeviceOrientationEvent) {
        window.addEventListener('deviceorientation', function (e) {
          if (state.page_class === 'opted_out') return;
          sensorBuffer.push({
            type: 'orientation',
            ts: performance.now(),
            alpha: e.alpha != null ? r2(e.alpha) : null,
            beta: e.beta != null ? r2(e.beta) : null,
            gamma: e.gamma != null ? r2(e.gamma) : null,
          });
        }, { passive: true });
      }
    } catch (e) { /* */ }
  }

  // ═══════════════════════════════════════════════════════
  // USERNAME CAPTURE
  // ═══════════════════════════════════════════════════════
  function setupUsernameCapture() {
    document.addEventListener('blur', function (e) {
      if (state.username_captured) return;
      if (!(e.target instanceof HTMLInputElement)) return;
      var sel = ['input[name="username"]', 'input[name="email"]', 'input[name="phoneNumber"]', 'input[type="email"]'];
      var ok = false;
      for (var s = 0; s < sel.length; s++) {
        try { if (e.target.matches(sel[s])) { ok = true; break; } } catch (err) { /* */ }
      }
      if (!ok) return;
      var val = e.target.value.trim();
      if (!val || val.length < 3 || ['username', 'email', 'phone'].indexOf(val.toLowerCase()) >= 0) return;
      hashUsername(val).then(function (hash) {
        state.user_hash = hash; state.username_captured = true;
        try { localStorage.setItem('kp.un', val); } catch (err) { /* */ }
        auditRecord('username_captured');
        updateStatus('identity: ' + hash.slice(0, 12) + '...');
        for (var k = 0; k < state.listeners.username_captured.length; k++) {
          try { state.listeners.username_captured[k]({ user_hash: hash }); } catch (err) { /* */ }
        }
        startPulseLoop();
      });
    }, { passive: true, capture: true });

    try {
      var saved = localStorage.getItem('kp.un');
      if (saved) hashUsername(saved).then(function (h) {
        state.user_hash = h; state.username_captured = true;
        updateStatus('identity: ' + h.slice(0, 12) + '...'); startPulseLoop();
      });
    } catch (e) { /* */ }
  }

  // ═══════════════════════════════════════════════════════
  // CONSENT CHECK — block SDK if user denied consent
  // ═══════════════════════════════════════════════════════
  if (!hasConsent()) {
    updateStatus('KP: consent required');
    window.KProtect = {
      init: function () {},
      on: function () { return function () {}; },
      getLatestDrift: function () { return null; },
      getSessionState: function () { return null; },
      getDeviceFingerprint: function () { return null; },
      getSiteWideState: function () { return null; },
      getLoadIndicators: function () { return null; },
      exportAuditLog: function () { return []; },
      consent: {
        grant: function () { setConsent(true); location.reload(); },
        deny: function () { setConsent(false); },
        state: function () { try { var r = localStorage.getItem('kp.consent'); return r ? JSON.parse(r).state : 'unknown'; } catch (e) { return 'unknown'; } },
      },
      logout: function () {},
      destroy: function () {},
    };
    return; // EXIT — SDK does not start without consent
  }

  // ═══════════════════════════════════════════════════════
  // INIT
  // ═══════════════════════════════════════════════════════
  state.session_id = getOrCreateSessionId();
  state.device_uuid = getOrCreateUuid('kp.did');
  state.session_start_epoch = Date.now();
  state.session_start_perf = performance.now();
  computeOriginHash(); // Bind session to origin (Finding 11)

  setupListeners();
  setupSensorListeners();
  setupUsernameCapture();
  classifyPage(location.pathname);
  auditRecord('sdk_init', { session_id: state.session_id, device_uuid: state.device_uuid });
  updateStatus('sid=' + state.session_id.slice(0, 8) + ' | did=' + state.device_uuid.slice(0, 8));

  // Async device fingerprinting (non-blocking)
  collectDeviceFingerprint().then(function () {
    auditRecord('fingerprint_collected');
    updateStatus('fp collected | sid=' + state.session_id.slice(0, 8));
  }).catch(function () { /* */ });

  // Initial load indicator collection
  try {
    if (document.readyState === 'complete') {
      collectLoadIndicators();
    } else {
      window.addEventListener('load', function () { collectLoadIndicators(); }, { once: true });
    }
  } catch (e) { /* */ }

  // SPA route detection
  var origPush = history.pushState.bind(history);
  history.pushState = function () { origPush.apply(history, arguments); classifyPage(location.pathname); };
  window.addEventListener('popstate', function () { classifyPage(location.pathname); });

  // Global API
  window.KProtect = {
    on: function (evt, cb) {
      if (state.listeners[evt]) state.listeners[evt].push(cb);
      return function () { state.listeners[evt] = state.listeners[evt].filter(function (c) { return c !== cb; }); };
    },
    getLatestDrift: function () { return null; },
    getSessionState: function () {
      return {
        session_id: state.session_id,
        pulse: state.pulse,
        page_class: state.page_class,
        username_captured: state.username_captured,
        current_action: state.current_action,
        fingerprint_ready: !!deviceFingerprint.collected_at,
        origin_hash: state.origin_hash,
        liveness_status: state.liveness_status,
        consent_state: state.consent_state,
      };
    },
    getDeviceFingerprint: function () { return deviceFingerprint; },
    getSiteWideState: function () { return collectSiteWideSnapshot(); },
    getLoadIndicators: function () { return loadIndicators; },
    exportAuditLog: function () { return auditLog.slice(); },
    consent: {
      grant: function () { setConsent(true); auditRecord('consent_granted'); },
      deny: function () { setConsent(false); auditRecord('consent_denied'); },
      state: function () { try { var r = localStorage.getItem('kp.consent'); return r ? JSON.parse(r).state : 'unknown'; } catch (e) { return 'unknown'; } },
    },
    logout: function () {
      state.user_hash = null; state.username_captured = false;
      try { localStorage.removeItem('kp.un'); sessionStorage.removeItem('kp.sid'); } catch (e) { /* */ }
      auditRecord('logout');
      updateStatus('logged out');
    },
    destroy: function (opts) {
      stopPulseLoop(); state.user_hash = null; state.username_captured = false;
      state.liveness_status = 'dead';
      if (opts && opts.clearIdentity) {
        try { localStorage.removeItem('kp.did'); localStorage.removeItem('kp.un'); localStorage.removeItem('kp.consent'); localStorage.removeItem('kp.cfg'); sessionStorage.removeItem('kp.sid'); } catch (e) { /* */ }
      }
      auditRecord('destroy');
    },
    gdpr: {
      export: function () {
        return Promise.resolve({
          user_hash: state.user_hash,
          device_uuid: state.device_uuid,
          session_id: state.session_id,
          consent_state: state.consent_state,
          stored_keys: ['kp.sid', 'kp.un', 'kp.did', 'kp.cfg', 'kp.consent'].reduce(function (acc, k) {
            try { acc[k] = localStorage.getItem(k) || sessionStorage.getItem(k) || null; } catch (e) { acc[k] = null; }
            return acc;
          }, {}),
          exported_at: new Date().toISOString(),
        });
      },
      delete: function () {
        stopPulseLoop(); state.user_hash = null; state.username_captured = false; state.liveness_status = 'dead';
        try { ['kp.sid', 'kp.un', 'kp.did', 'kp.cfg', 'kp.consent', 'kp.k', 'kp.us'].forEach(function (k) { localStorage.removeItem(k); sessionStorage.removeItem(k); }); } catch (e) { /* */ }
        auditRecord('gdpr_delete');
        return Promise.resolve();
      },
    },
  };

})();
