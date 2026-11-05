// T-V6-25: ESLint para el frontend vanilla (sin build). Reglas que cazan errores reales — variables
// no definidas, código inalcanzable, comparaciones raras — sin pelear con el estilo existente.
// Los helpers compartidos entre ficheros (util.js, auth.js, icons.js…) se declaran como globales.
const globals = require('globals');

const SHARED = [
  // auth.js
  'getConfig', 'getSupabase', 'getSession', 'getToken', 'getUser', 'requireAuth', 'signUpEmail', 'signInEmail',
  'signInGoogle', 'signOut', 'apiFetch', 'apiJson', 'ApiError', 'apiErrorMessage', 'errorMessage', 'bfSaveNext', 'bfTakeNext',
  // util.js
  'escapeHtml', 'toast', 'confirmModal', 'promptModal', 'alertModal', 'bandColor', 'bandHue', 'initialsFrom', 'bfAvatar',
  'bfMoney', 'bfDate', 'bfDateLong', 'BF_LOCALE', 'BF_EVENT_ICON', 'BF_ATT', 'bfIco', 'bfEventIcon', 'attText', 'attHtml',
  'bfAttendees', 'bfDialog', 'bfShare', 'bfLocalInput', 'bfFromLocalInput', 'bfDuration', 'bfSetlistInsights',
  'bfSetlistInsightsHtml', 'bfCalendar', 'bfSubscribeCalendar', 'bfShareSetlist', 'bfFinanceBySeason', 'bfSkeletonList',
  'bfErrorState', 'bfShowError', 'bfBusy', 'bfPop', '_bfModalA11y',
  // icons.js / upload.js / score_render / chord_shapes / sync_engine / metronome
  'bfIcon', 'bfEmpty', 'bfUploadImage', 'bfPickAndUploadImage', 'bfImageToDataUrl', 'bfUploadFile', 'bfRecorder',
  'renderScoreInto', 'transposeChord', 'SyncEngine', 'BfMetronome', 'bfMetronomeClick', 'bfBeatAccent', 'bfHoldRepeat',
  'chordShape', 'chordDiagramSvg', 'supabase', 'pdfjsLib',
  // bands.js (lo reusa band.js / band_tools.js)
  'loadRepertoire', 'loadCollections', 'loadBandSetlists', 'loadAgenda', 'loadVenues', 'loadFinance', 'initChat',
  'newEvent', 'newTransaction', 'newSettlement', 'newBandSetlist', 'copyFromPersonal', 'generateInvite', 'ROLE_LABEL',
  'ATT_LABEL', 'fmtDate', 'attendeesLine', 'bookingLine', 'playBandSetlist',
];

module.exports = [
  {
    files: ['static/**/*.js'],
    ignores: ['static/sw.js'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'script',
      globals: { ...globals.browser, ...Object.fromEntries(SHARED.map(n => [n, 'writable'])) },
    },
    rules: {
      'no-undef': 'error',
      'no-unreachable': 'error',
      'no-dupe-keys': 'error',
      'no-self-compare': 'error',
      'use-isnan': 'error',
      'valid-typeof': 'error',
      'no-unused-vars': 'off',
      'no-redeclare': 'off',
    },
  },
  {
    files: ['static/sw.js'],
    languageOptions: { globals: { ...globals.serviceworker } },
  },
];
