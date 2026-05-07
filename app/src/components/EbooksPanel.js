"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
var __spreadArray = (this && this.__spreadArray) || function (to, from, pack) {
    if (pack || arguments.length === 2) for (var i = 0, l = from.length, ar; i < l; i++) {
        if (ar || !(i in from)) {
            if (!ar) ar = Array.prototype.slice.call(from, 0, i);
            ar[i] = from[i];
        }
    }
    return to.concat(ar || Array.prototype.slice.call(from));
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.default = EbooksPanel;
var react_1 = require("react");
var scroll_area_1 = require("@/components/ui/scroll-area");
var input_1 = require("@/components/ui/input");
var button_1 = require("@/components/ui/button");
var card_1 = require("@/components/ui/card");
var useStore_1 = require("@/hooks/useStore");
var lucide_react_1 = require("lucide-react");
var select_1 = require("@/components/ui/select");
var textarea_1 = require("@/components/ui/textarea");
var switch_1 = require("@/components/ui/switch");
var label_1 = require("@/components/ui/label");
var tabs_1 = require("@/components/ui/tabs");
function EbooksPanel() {
    var _this = this;
    var store = (0, useStore_1.useStore)();
    var _a = (0, react_1.useState)({}), ebooks = _a[0], setEbooks = _a[1];
    var _b = (0, react_1.useState)(null), selected = _b[0], setSelected = _b[1];
    var _c = (0, react_1.useState)(null), meta = _c[0], setMeta = _c[1];
    var _d = (0, react_1.useState)(1), startPage = _d[0], setStartPage = _d[1];
    var _e = (0, react_1.useState)(1), endPage = _e[0], setEndPage = _e[1];
    var _f = (0, react_1.useState)(''), textPreview = _f[0], setTextPreview = _f[1];
    var _g = (0, react_1.useState)(false), uploading = _g[0], setUploading = _g[1];
    var fileRef = (0, react_1.useRef)(null);
    var previewRef = (0, react_1.useRef)(null);
    var _h = (0, react_1.useState)({}), profiles = _h[0], setProfiles = _h[1];
    var _j = (0, react_1.useState)({}), voices = _j[0], setVoices = _j[1];
    var _k = (0, react_1.useState)(null), selectedProfile = _k[0], setSelectedProfile = _k[1];
    var _l = (0, react_1.useState)(1.0), speed = _l[0], setSpeed = _l[1];
    var _m = (0, react_1.useState)(false), generating = _m[0], setGenerating = _m[1];
    var _o = (0, react_1.useState)([]), audioUrls = _o[0], setAudioUrls = _o[1];
    var audioRef = (0, react_1.useRef)(null);
    var currentIndex = (0, react_1.useRef)(0);
    // Premium features
    var _p = (0, react_1.useState)({}), ebookSettings = _p[0], setEbookSettings = _p[1];
    var _q = (0, react_1.useState)([]), bookmarks = _q[0], setBookmarks = _q[1];
    var _r = (0, react_1.useState)([]), notes = _r[0], setNotes = _r[1];
    var _s = (0, react_1.useState)(''), searchQuery = _s[0], setSearchQuery = _s[1];
    var _t = (0, react_1.useState)([]), searchResults = _t[0], setSearchResults = _t[1];
    var _u = (0, react_1.useState)({}), readingStats = _u[0], setReadingStats = _u[1];
    var _v = (0, react_1.useState)(true), sarahNarration = _v[0], setSarahNarration = _v[1];
    var _w = (0, react_1.useState)(''), newBookmarkTitle = _w[0], setNewBookmarkTitle = _w[1];
    var _x = (0, react_1.useState)(''), newNoteContent = _x[0], setNewNoteContent = _x[1];
    (0, react_1.useEffect)(function () {
        fetchList();
        fetchVoices();
        fetchEbookSettings();
    }, []);
    var fetchVoices = function () { return __awaiter(_this, void 0, void 0, function () {
        var res, data, e_1;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 3, , 4]);
                    return [4 /*yield*/, fetch('/api/tts/voices')];
                case 1:
                    res = _a.sent();
                    return [4 /*yield*/, res.json()];
                case 2:
                    data = _a.sent();
                    if (data) {
                        setProfiles(data.profiles || {});
                        setVoices(data.voices || {});
                    }
                    return [3 /*break*/, 4];
                case 3:
                    e_1 = _a.sent();
                    return [3 /*break*/, 4];
                case 4: return [2 /*return*/];
            }
        });
    }); };
    var fetchEbookSettings = function () { return __awaiter(_this, void 0, void 0, function () {
        var res, data, e_2;
        var _a;
        return __generator(this, function (_b) {
            switch (_b.label) {
                case 0:
                    _b.trys.push([0, 3, , 4]);
                    return [4 /*yield*/, fetch('/api/ebooks/settings')];
                case 1:
                    res = _b.sent();
                    return [4 /*yield*/, res.json()];
                case 2:
                    data = _b.sent();
                    if (data.success) {
                        setEbookSettings(data);
                        setSarahNarration((_a = data.sarah_narration_enabled) !== null && _a !== void 0 ? _a : true);
                    }
                    return [3 /*break*/, 4];
                case 3:
                    e_2 = _b.sent();
                    console.error('Failed to fetch ebook settings', e_2);
                    return [3 /*break*/, 4];
                case 4: return [2 /*return*/];
            }
        });
    }); };
    var updateEbookSettings = function (updates) { return __awaiter(_this, void 0, void 0, function () {
        var res, data, e_3;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 3, , 4]);
                    return [4 /*yield*/, fetch('/api/ebooks/settings', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(updates),
                        })];
                case 1:
                    res = _a.sent();
                    return [4 /*yield*/, res.json()];
                case 2:
                    data = _a.sent();
                    if (data.success) {
                        setEbookSettings(data);
                    }
                    return [3 /*break*/, 4];
                case 3:
                    e_3 = _a.sent();
                    console.error('Failed to update ebook settings', e_3);
                    return [3 /*break*/, 4];
                case 4: return [2 /*return*/];
            }
        });
    }); };
    var searchEbook = function () { return __awaiter(_this, void 0, void 0, function () {
        var res, data, e_4;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    if (!selected || !searchQuery)
                        return [2 /*return*/];
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, 4, , 5]);
                    return [4 /*yield*/, fetch("/api/ebooks/search/".concat(selected, "?query=").concat(encodeURIComponent(searchQuery)))];
                case 2:
                    res = _a.sent();
                    return [4 /*yield*/, res.json()];
                case 3:
                    data = _a.sent();
                    if (data.success) {
                        setSearchResults(data.results || []);
                    }
                    return [3 /*break*/, 5];
                case 4:
                    e_4 = _a.sent();
                    console.error('Search failed', e_4);
                    return [3 /*break*/, 5];
                case 5: return [2 /*return*/];
            }
        });
    }); };
    var addBookmark = function () { return __awaiter(_this, void 0, void 0, function () {
        var form, res, data, e_5;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    if (!selected || !startPage)
                        return [2 /*return*/];
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, 4, , 5]);
                    form = new FormData();
                    form.append('ebook_id', selected);
                    form.append('page', String(startPage));
                    if (newBookmarkTitle)
                        form.append('title', newBookmarkTitle);
                    return [4 /*yield*/, fetch('/api/ebooks/bookmark', { method: 'POST', body: form })];
                case 2:
                    res = _a.sent();
                    return [4 /*yield*/, res.json()];
                case 3:
                    data = _a.sent();
                    if (data.success) {
                        setBookmarks(__spreadArray(__spreadArray([], bookmarks, true), [data.bookmark], false));
                        setNewBookmarkTitle('');
                        alert('Bookmark added!');
                    }
                    return [3 /*break*/, 5];
                case 4:
                    e_5 = _a.sent();
                    console.error('Failed to add bookmark', e_5);
                    return [3 /*break*/, 5];
                case 5: return [2 /*return*/];
            }
        });
    }); };
    var addNote = function () { return __awaiter(_this, void 0, void 0, function () {
        var form, res, data, e_6;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    if (!selected || !startPage || !newNoteContent)
                        return [2 /*return*/];
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, 4, , 5]);
                    form = new FormData();
                    form.append('ebook_id', selected);
                    form.append('page', String(startPage));
                    form.append('content', newNoteContent);
                    return [4 /*yield*/, fetch('/api/ebooks/note', { method: 'POST', body: form })];
                case 2:
                    res = _a.sent();
                    return [4 /*yield*/, res.json()];
                case 3:
                    data = _a.sent();
                    if (data.success) {
                        setNotes(__spreadArray(__spreadArray([], notes, true), [data.note], false));
                        setNewNoteContent('');
                        alert('Note added!');
                    }
                    return [3 /*break*/, 5];
                case 4:
                    e_6 = _a.sent();
                    console.error('Failed to add note', e_6);
                    return [3 /*break*/, 5];
                case 5: return [2 /*return*/];
            }
        });
    }); };
    var startReadingSession = function () { return __awaiter(_this, void 0, void 0, function () {
        var form, e_7;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    if (!selected)
                        return [2 /*return*/];
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, 3, , 4]);
                    form = new FormData();
                    form.append('ebook_id', selected);
                    form.append('start_page', String(startPage || 1));
                    return [4 /*yield*/, fetch('/api/ebooks/start_session', { method: 'POST', body: form })];
                case 2:
                    _a.sent();
                    return [3 /*break*/, 4];
                case 3:
                    e_7 = _a.sent();
                    console.error('Failed to start session', e_7);
                    return [3 /*break*/, 4];
                case 4: return [2 /*return*/];
            }
        });
    }); };
    var endReadingSession = function () { return __awaiter(_this, void 0, void 0, function () {
        var e_8;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 2, , 3]);
                    return [4 /*yield*/, fetch('/api/ebooks/end_session', { method: 'POST' })];
                case 1:
                    _a.sent();
                    return [3 /*break*/, 3];
                case 2:
                    e_8 = _a.sent();
                    console.error('Failed to end session', e_8);
                    return [3 /*break*/, 3];
                case 3: return [2 /*return*/];
            }
        });
    }); };
    var sarahRead = function () { return __awaiter(_this, void 0, void 0, function () {
        var form, res, data, ws, e_9;
        var _a;
        return __generator(this, function (_b) {
            switch (_b.label) {
                case 0:
                    if (!selected)
                        return [2 /*return*/, alert('Select an ebook')];
                    setGenerating(true);
                    _b.label = 1;
                case 1:
                    _b.trys.push([1, 4, , 5]);
                    form = new FormData();
                    form.append('ebook_id', selected);
                    form.append('start_page', String(startPage || 1));
                    form.append('end_page', String(endPage || startPage || 1));
                    if (selectedProfile)
                        form.append('voice_profile', selectedProfile);
                    return [4 /*yield*/, fetch('/api/ebooks/sarah_read', { method: 'POST', body: form })];
                case 2:
                    res = _b.sent();
                    return [4 /*yield*/, res.json()];
                case 3:
                    data = _b.sent();
                    if (data.success && data.audio_urls) {
                        setAudioUrls(data.audio_urls);
                        currentIndex.current = 0;
                        // Trigger VRM reading animation
                        if ((_a = data.metadata) === null || _a === void 0 ? void 0 : _a.animations) {
                            ws = window.ws;
                            if (ws) {
                                ws.send(JSON.stringify({
                                    type: 'vrm_action',
                                    action: 'read_book',
                                    metadata: data.metadata
                                }));
                            }
                        }
                    }
                    else
                        alert('Sarah read failed: ' + (data.error || ''));
                    return [3 /*break*/, 5];
                case 4:
                    e_9 = _b.sent();
                    console.error(e_9);
                    alert('Error generating Sarah narration');
                    return [3 /*break*/, 5];
                case 5:
                    setGenerating(false);
                    return [2 /*return*/];
            }
        });
    }); };
    var fetchList = function () { return __awaiter(_this, void 0, void 0, function () {
        var res, data, e_10;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 3, , 4]);
                    return [4 /*yield*/, fetch('/api/ebooks/list')];
                case 1:
                    res = _a.sent();
                    return [4 /*yield*/, res.json()];
                case 2:
                    data = _a.sent();
                    setEbooks(data.ebooks || {});
                    return [3 /*break*/, 4];
                case 3:
                    e_10 = _a.sent();
                    console.error('Failed to list ebooks', e_10);
                    return [3 /*break*/, 4];
                case 4: return [2 /*return*/];
            }
        });
    }); };
    var handleUpload = function () { return __awaiter(_this, void 0, void 0, function () {
        var f, form, res, data, e_11;
        var _a, _b;
        return __generator(this, function (_c) {
            switch (_c.label) {
                case 0:
                    if (!((_b = (_a = fileRef.current) === null || _a === void 0 ? void 0 : _a.files) === null || _b === void 0 ? void 0 : _b.length))
                        return [2 /*return*/, alert('Choose a file')];
                    setUploading(true);
                    _c.label = 1;
                case 1:
                    _c.trys.push([1, 4, , 5]);
                    f = fileRef.current.files[0];
                    form = new FormData();
                    form.append('file', f);
                    return [4 /*yield*/, fetch('/api/ebooks/upload', { method: 'POST', body: form })];
                case 2:
                    res = _c.sent();
                    return [4 /*yield*/, res.json()];
                case 3:
                    data = _c.sent();
                    if (data.success) {
                        alert('Uploaded');
                        fetchList();
                    }
                    else
                        alert('Upload failed: ' + (data.error || ''));
                    return [3 /*break*/, 5];
                case 4:
                    e_11 = _c.sent();
                    console.error(e_11);
                    alert('Upload error');
                    return [3 /*break*/, 5];
                case 5:
                    setUploading(false);
                    if (fileRef.current)
                        fileRef.current.value = '';
                    return [2 /*return*/];
            }
        });
    }); };
    var selectEbook = function (id) { return __awaiter(_this, void 0, void 0, function () {
        var res, data, e_12;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    setSelected(id);
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, 4, , 5]);
                    return [4 /*yield*/, fetch("/api/ebooks/meta/".concat(id))];
                case 2:
                    res = _a.sent();
                    return [4 /*yield*/, res.json()];
                case 3:
                    data = _a.sent();
                    if (data.success) {
                        setMeta(data.meta);
                        setStartPage(1);
                        setEndPage(data.meta.pages || data.meta.chapters || 1);
                        setBookmarks(data.meta.bookmarks || []);
                        setNotes(data.meta.notes || []);
                        setReadingStats(data.meta);
                    }
                    return [3 /*break*/, 5];
                case 4:
                    e_12 = _a.sent();
                    console.error('meta fetch failed', e_12);
                    return [3 /*break*/, 5];
                case 5: return [2 /*return*/];
            }
        });
    }); };
    var previewText = function () { return __awaiter(_this, void 0, void 0, function () {
        var res, data, e_13;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    if (!selected)
                        return [2 /*return*/];
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, 4, , 5]);
                    return [4 /*yield*/, fetch("/api/ebooks/text/".concat(selected, "?start_page=").concat(startPage || 1, "&end_page=").concat(endPage || startPage || 1))];
                case 2:
                    res = _a.sent();
                    return [4 /*yield*/, res.json()];
                case 3:
                    data = _a.sent();
                    if (data.success)
                        setTextPreview(data.text || '');
                    else
                        alert('Preview failed: ' + (data.error || ''));
                    return [3 /*break*/, 5];
                case 4:
                    e_13 = _a.sent();
                    console.error(e_13);
                    return [3 /*break*/, 5];
                case 5: return [2 /*return*/];
            }
        });
    }); };
    var setStartFromSelection = function () {
        if (!previewRef.current)
            return alert('No preview available');
        var ta = previewRef.current;
        var selStart = ta.selectionStart || 0;
        if (!meta)
            return alert('No metadata to map selection to pages');
        try {
            var totalChars = (textPreview || '').length || 1;
            var pages = meta.pages || meta.chapters || 1;
            var charsPerPage = Math.max(1, Math.floor(totalChars / pages));
            var page = Math.max(1, Math.floor(selStart / charsPerPage) + 1);
            setStartPage(page);
            alert("Start page set to ".concat(page, " (from selection)"));
        }
        catch (e) {
            console.error(e);
            alert('Failed to set start from selection');
        }
    };
    var readNow = function () { return __awaiter(_this, void 0, void 0, function () {
        var form, pct, rateStr, res, data, e_14;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    if (!selected)
                        return [2 /*return*/, alert('Select an ebook')];
                    setGenerating(true);
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, 4, , 5]);
                    form = new FormData();
                    form.append('ebook_id', selected);
                    form.append('start_page', String(startPage || 1));
                    form.append('end_page', String(endPage || startPage || 1));
                    // use selected profile if present, otherwise fallback to store profile
                    form.append('profile', selectedProfile || store.voiceProfile || 'default');
                    pct = Math.round((speed - 1.0) * 100);
                    rateStr = "".concat(pct >= 0 ? '+' : '').concat(pct, "%");
                    form.append('rate', rateStr);
                    return [4 /*yield*/, fetch('/api/ebooks/read', { method: 'POST', body: form })];
                case 2:
                    res = _a.sent();
                    return [4 /*yield*/, res.json()];
                case 3:
                    data = _a.sent();
                    if (data.success && data.audio_urls) {
                        setAudioUrls(data.audio_urls);
                        currentIndex.current = 0;
                        setTimeout(function () { return playIndex(0); }, 100);
                    }
                    else
                        alert('Read failed: ' + (data.error || ''));
                    return [3 /*break*/, 5];
                case 4:
                    e_14 = _a.sent();
                    console.error(e_14);
                    alert('Error generating audio');
                    return [3 /*break*/, 5];
                case 5:
                    setGenerating(false);
                    return [2 /*return*/];
            }
        });
    }); };
    var playIndex = function (idx) {
        if (!audioRef.current)
            audioRef.current = document.createElement('audio');
        if (!audioUrls || audioUrls.length === 0)
            return;
        if (idx < 0 || idx >= audioUrls.length)
            return;
        currentIndex.current = idx;
        audioRef.current.src = audioUrls[idx] + '?t=' + Date.now();
        audioRef.current.onended = function () {
            if (currentIndex.current + 1 < audioUrls.length)
                playIndex(currentIndex.current + 1);
        };
        audioRef.current.play().catch(function () { });
    };
    var pause = function () { var _a; return (_a = audioRef.current) === null || _a === void 0 ? void 0 : _a.pause(); };
    var stop = function () { if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
    } };
    return (<scroll_area_1.ScrollArea className="h-full px-4 py-4">
      <div className="space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <lucide_react_1.FileText className="w-5 h-5 text-emerald-400"/>
          <h2 className="text-lg font-semibold text-white">E‑Books</h2>
        </div>

        <card_1.Card className="bg-white/5 border-white/10 p-3">
          <div className="flex gap-2 items-center">
            <input ref={fileRef} type="file" accept=".pdf,.epub,.txt" className="hidden"/>
            <button_1.Button onClick={function () { var _a; return (_a = fileRef.current) === null || _a === void 0 ? void 0 : _a.click(); }} size="sm" className="flex items-center gap-2"><lucide_react_1.UploadCloud className="w-4 h-4"/> Choose</button_1.Button>
            <button_1.Button onClick={handleUpload} size="sm">{uploading ? 'Uploading...' : 'Upload'}</button_1.Button>
            <div className="ml-auto text-xs text-white/40">Supported: PDF, EPUB, TXT</div>
          </div>
        </card_1.Card>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <card_1.Card className="bg-white/5 border-white/10 p-3">
            <h3 className="text-sm text-white mb-2">Library</h3>
            <div className="space-y-2 max-h-96 overflow-auto">
              {Object.keys(ebooks).length === 0 && <div className="text-xs text-white/40">No ebooks uploaded</div>}
              {Object.entries(ebooks).map(function (_a) {
            var _b;
            var id = _a[0], e = _a[1];
            return (<div key={id} className={"p-2 rounded-md cursor-pointer hover:bg-white/5 ".concat(selected === id ? 'ring-1 ring-emerald-400' : '')} onClick={function () { return selectEbook(id); }}>
                  <div className="text-sm text-white font-medium">{e.filename || e.stored_name || id}</div>
                  <div className="text-xs text-white/50">{(_b = e.ext) === null || _b === void 0 ? void 0 : _b.toUpperCase()} • {Math.round((e.size || 0) / 1024)} KB</div>
                </div>);
        })}
            </div>
          </card_1.Card>

          <card_1.Card className="bg-white/5 border-white/10 p-3">
            <h3 className="text-sm text-white mb-2">Details</h3>
            {meta ? (<div className="space-y-2 text-xs text-white/60">
                <div><strong className="text-white">{meta.title || meta.filename || meta.stored_name}</strong></div>
                <div>Author: {meta.author || 'Unknown'}</div>
                <div>Pages: {meta.pages || meta.chapters || '—'}</div>
                <div>Uploaded: {new Date(meta.uploaded_at || Date.now()).toLocaleString()}</div>
                <div className="mt-2 grid grid-cols-2 gap-2">
                  <input_1.Input value={String(startPage || '')} onChange={function (e) { return setStartPage(Number(e.target.value || 1)); }}/>
                  <input_1.Input value={String(endPage || '')} onChange={function (e) { return setEndPage(Number(e.target.value || startPage || 1)); }}/>
                </div>
                <div className="flex gap-2 mt-2">
                  <button_1.Button onClick={previewText} size="sm">Preview Text</button_1.Button>
                  <button_1.Button onClick={readNow} size="sm" className="bg-emerald-500/20 hover:bg-emerald-500/30">{generating ? 'Generating...' : 'Read'}</button_1.Button>
                </div>
              </div>) : (<div className="text-xs text-white/40">Select an ebook to see details</div>)}
          </card_1.Card>

          <card_1.Card className="bg-white/5 border-white/10 p-3">
            <h3 className="text-sm text-white mb-2">Player</h3>
            <div className="text-xs text-white/60 mb-2">Voice / Speed</div>
            <div className="flex items-center gap-2 mb-3">
              <div className="flex-1">
                <select_1.Select value={selectedProfile || store.voiceProfile} onValueChange={function (v) { return setSelectedProfile(v); }}>
                  <select_1.SelectTrigger className="bg-white/5 border-white/10 text-white w-full h-8">
                    <select_1.SelectValue placeholder="Select voice/profile"/>
                  </select_1.SelectTrigger>
                  <select_1.SelectContent className="bg-gray-900 border-white/20">
                    <select_1.SelectGroup>
                      <select_1.SelectLabel>Profiles</select_1.SelectLabel>
                      {Object.keys(profiles).length > 0 ? (Object.keys(profiles).map(function (p) { return <select_1.SelectItem key={p} value={p}>{p}</select_1.SelectItem>; })) : (<select_1.SelectItem value="default">default</select_1.SelectItem>)}
                    </select_1.SelectGroup>
                    <select_1.SelectSeparator />
                    <select_1.SelectGroup>
                      <select_1.SelectLabel>Voices</select_1.SelectLabel>
                      {Object.keys(voices).length > 0 ? (Object.keys(voices).map(function (v) { return <select_1.SelectItem key={v} value={v}>{v}</select_1.SelectItem>; })) : null}
                    </select_1.SelectGroup>
                  </select_1.SelectContent>
                </select_1.Select>
              </div>

              <div className="w-36">
                <div className="text-xs text-white/50 mb-1">Speed: {speed}x</div>
                <input type="range" min={0.5} max={2.0} step={0.05} value={speed} onChange={function (e) { return setSpeed(Number(e.target.value)); }}/>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <button_1.Button onClick={function () { return playIndex(currentIndex.current); }} size="sm"><lucide_react_1.Play className="w-4 h-4"/></button_1.Button>
                <button_1.Button onClick={pause} size="sm"><lucide_react_1.Pause className="w-4 h-4"/></button_1.Button>
                <button_1.Button onClick={stop} size="sm"><lucide_react_1.StopCircle className="w-4 h-4"/></button_1.Button>
              </div>

              <div className="text-xs text-white/50">{audioUrls.length} audio segment(s) ready</div>
              <div className="space-y-1">
                {audioUrls.map(function (u, i) { return (<div key={u} className="flex items-center justify-between text-xs text-white/60">
                    <div>Segment {i + 1}</div>
                    <div className="flex items-center gap-2">
                      <a href={u} target="_blank" rel="noreferrer" className="text-white/60 hover:text-white"><lucide_react_1.DownloadCloud className="w-4 h-4"/></a>
                      <button_1.Button size="sm" onClick={function () { return playIndex(i); }}>Play</button_1.Button>
                    </div>
                  </div>); })}
              </div>
            </div>
          </card_1.Card>
        </div>

        <card_1.Card className="bg-white/5 border-white/10 p-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm text-white mb-2">Preview</h3>
            <div className="flex items-center gap-2">
              <button_1.Button size="sm" onClick={setStartFromSelection}>Set start from selection</button_1.Button>
              <button_1.Button size="sm" onClick={function () { setTextPreview(''); }}>Clear</button_1.Button>
            </div>
          </div>
          <textarea ref={previewRef} value={textPreview} onChange={function (e) { return setTextPreview(e.target.value); }} className="min-h-[160px] w-full bg-transparent border border-white/10 rounded-md p-2 text-sm text-white placeholder:text-white/50"/>
        </card_1.Card>

        {/* Premium Features */}
        {selected && (<card_1.Card className="bg-white/5 border-white/10 p-3">
            <tabs_1.Tabs defaultValue="bookmarks" className="w-full">
              <tabs_1.TabsList className="grid w-full grid-cols-4">
                <tabs_1.TabsTrigger value="bookmarks">Bookmarks</tabs_1.TabsTrigger>
                <tabs_1.TabsTrigger value="notes">Notes</tabs_1.TabsTrigger>
                <tabs_1.TabsTrigger value="search">Search</tabs_1.TabsTrigger>
                <tabs_1.TabsTrigger value="settings">Settings</tabs_1.TabsTrigger>
              </tabs_1.TabsList>

              <tabs_1.TabsContent value="bookmarks" className="space-y-2">
                <div className="flex gap-2">
                  <input_1.Input placeholder="Bookmark title..." value={newBookmarkTitle} onChange={function (e) { return setNewBookmarkTitle(e.target.value); }} className="bg-white/5 border-white/10 text-white text-sm h-8"/>
                  <button_1.Button onClick={addBookmark} size="sm" className="h-8">
                    <lucide_react_1.Bookmark className="w-4 h-4 mr-1"/>
                    Add
                  </button_1.Button>
                </div>
                <div className="space-y-1 max-h-32 overflow-auto">
                  {bookmarks.map(function (bookmark) { return (<div key={bookmark.id} className="text-xs text-white/60 p-2 bg-white/5 rounded">
                      <div className="font-medium">{bookmark.title || "Page ".concat(bookmark.page)}</div>
                      <div className="text-white/40">Page {bookmark.page}</div>
                    </div>); })}
                </div>
              </tabs_1.TabsContent>

              <tabs_1.TabsContent value="notes" className="space-y-2">
                <textarea_1.Textarea placeholder="Add a note..." value={newNoteContent} onChange={function (e) { return setNewNoteContent(e.target.value); }} className="bg-white/5 border-white/10 text-white text-sm min-h-[60px]"/>
                <button_1.Button onClick={addNote} size="sm">
                  Add Note
                </button_1.Button>
                <div className="space-y-1 max-h-32 overflow-auto">
                  {notes.map(function (note) { return (<div key={note.id} className="text-xs text-white/60 p-2 bg-white/5 rounded">
                      <div className="font-medium">{note.content}</div>
                      <div className="text-white/40">Page {note.page} • {new Date(note.timestamp).toLocaleDateString()}</div>
                    </div>); })}
                </div>
              </tabs_1.TabsContent>

              <tabs_1.TabsContent value="search" className="space-y-2">
                <div className="flex gap-2">
                  <input_1.Input placeholder="Search in ebook..." value={searchQuery} onChange={function (e) { return setSearchQuery(e.target.value); }} onKeyDown={function (e) { return e.key === 'Enter' && searchEbook(); }} className="bg-white/5 border-white/10 text-white text-sm h-8"/>
                  <button_1.Button onClick={searchEbook} size="sm" className="h-8">
                    <lucide_react_1.Search className="w-4 h-4 mr-1"/>
                    Search
                  </button_1.Button>
                </div>
                <div className="space-y-1 max-h-32 overflow-auto">
                  {searchResults.map(function (result, idx) { return (<div key={idx} className="text-xs text-white/60 p-2 bg-white/5 rounded">
                      <div className="font-medium">Page {result.page}</div>
                      <div className="text-white/40 line-clamp-2">{result.text}</div>
                    </div>); })}
                </div>
              </tabs_1.TabsContent>

              <tabs_1.TabsContent value="settings" className="space-y-3">
                <div className="flex items-center justify-between">
                  <label_1.Label htmlFor="sarah-narration" className="text-sm text-white">Sarah Narration</label_1.Label>
                  <switch_1.Switch id="sarah-narration" checked={sarahNarration} onCheckedChange={function (checked) {
                setSarahNarration(checked);
                updateEbookSettings({ sarah_narration_enabled: checked });
            }}/>
                </div>
                <div className="text-xs text-white/40">
                  When enabled, Sarah will narrate the ebook with her voice and lip sync animations.
                </div>
                <button_1.Button onClick={sarahRead} disabled={!sarahNarration} className="w-full">
                  <lucide_react_1.BookOpen className="w-4 h-4 mr-2"/>
                  {generating ? 'Sarah is reading...' : 'Let Sarah Read'}
                </button_1.Button>
                {readingStats && (<div className="text-xs text-white/40 space-y-1">
                    <div>Reading sessions: {readingStats.sessions || 0}</div>
                    <div>Total time: {Math.round((readingStats.total_time || 0) / 60)} min</div>
                    <div>Pages read: {readingStats.pages_read || 0}</div>
                  </div>)}
              </tabs_1.TabsContent>
            </tabs_1.Tabs>
          </card_1.Card>)}
      </div>
    </scroll_area_1.ScrollArea>);
}
