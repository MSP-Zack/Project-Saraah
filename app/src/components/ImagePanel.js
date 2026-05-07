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
exports.default = ImagePanel;
var react_1 = require("react");
var card_1 = require("@/components/ui/card");
var button_1 = require("@/components/ui/button");
var input_1 = require("@/components/ui/input");
var scroll_area_1 = require("@/components/ui/scroll-area");
var badge_1 = require("@/components/ui/badge");
var textarea_1 = require("@/components/ui/textarea");
var lucide_react_1 = require("lucide-react");
function ImagePanel() {
    var _this = this;
    var _a = (0, react_1.useState)('search'), activeTab = _a[0], setActiveTab = _a[1];
    var _b = (0, react_1.useState)('cute robot'), query = _b[0], setQuery = _b[1];
    var _c = (0, react_1.useState)('A futuristic anime-style companion robot with soft lighting'), prompt = _c[0], setPrompt = _c[1];
    var _d = (0, react_1.useState)('bing'), source = _d[0], setSource = _d[1];
    var _e = (0, react_1.useState)([]), results = _e[0], setResults = _e[1];
    var _f = (0, react_1.useState)([]), savedImages = _f[0], setSavedImages = _f[1];
    var _g = (0, react_1.useState)([]), history = _g[0], setHistory = _g[1];
    var _h = (0, react_1.useState)(false), loading = _h[0], setLoading = _h[1];
    var _j = (0, react_1.useState)(''), status = _j[0], setStatus = _j[1];
    var _k = (0, react_1.useState)(null), selectedImage = _k[0], setSelectedImage = _k[1];
    var _l = (0, react_1.useState)([]), providers = _l[0], setProviders = _l[1];
    var _m = (0, react_1.useState)([]), models = _m[0], setModels = _m[1];
    var _o = (0, react_1.useState)('huggingface'), selectedProvider = _o[0], setSelectedProvider = _o[1];
    var _p = (0, react_1.useState)('FLUX_DEV'), selectedModel = _p[0], setSelectedModel = _p[1];
    var _q = (0, react_1.useState)(true), saveImages = _q[0], setSaveImages = _q[1];
    var _r = (0, react_1.useState)(true), sfwOnly = _r[0], setSfwOnly = _r[1];
    var _s = (0, react_1.useState)(null), imageUpload = _s[0], setImageUpload = _s[1];
    var _t = (0, react_1.useState)(''), imagePreviewUrl = _t[0], setImagePreviewUrl = _t[1];
    var _u = (0, react_1.useState)('photorealistic'), promptStyle = _u[0], setPromptStyle = _u[1];
    (0, react_1.useEffect)(function () {
        loadSavedImages();
        loadHistory();
        loadImageSettings();
    }, []);
    var loadImageSettings = function () { return __awaiter(_this, void 0, void 0, function () {
        var res, data, error_1;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 3, , 4]);
                    return [4 /*yield*/, fetch('/api/images/settings')];
                case 1:
                    res = _a.sent();
                    return [4 /*yield*/, res.json()];
                case 2:
                    data = _a.sent();
                    if (data.provider) {
                        setSelectedProvider(data.provider);
                    }
                    if (data.model) {
                        setSelectedModel(data.model);
                    }
                    if (typeof data.save_images === 'boolean') {
                        setSaveImages(data.save_images);
                    }
                    if (typeof data.sfw_only === 'boolean') {
                        setSfwOnly(data.sfw_only);
                    }
                    if (Array.isArray(data.available_providers)) {
                        setProviders(data.available_providers);
                    }
                    if (Array.isArray(data.available_models)) {
                        setModels(data.available_models);
                    }
                    return [3 /*break*/, 4];
                case 3:
                    error_1 = _a.sent();
                    console.error('Failed to load image settings:', error_1);
                    return [3 /*break*/, 4];
                case 4: return [2 /*return*/];
            }
        });
    }); };
    var loadSavedImages = function () { return __awaiter(_this, void 0, void 0, function () {
        var res, data, error_2;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 3, , 4]);
                    return [4 /*yield*/, fetch('/api/images/list')];
                case 1:
                    res = _a.sent();
                    return [4 /*yield*/, res.json()];
                case 2:
                    data = _a.sent();
                    if (data.images) {
                        setSavedImages(data.images);
                    }
                    return [3 /*break*/, 4];
                case 3:
                    error_2 = _a.sent();
                    console.error('Failed to load saved images:', error_2);
                    return [3 /*break*/, 4];
                case 4: return [2 /*return*/];
            }
        });
    }); };
    var loadHistory = function () { return __awaiter(_this, void 0, void 0, function () {
        var res, data, error_3;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 3, , 4]);
                    return [4 /*yield*/, fetch('/api/images/history')];
                case 1:
                    res = _a.sent();
                    return [4 /*yield*/, res.json()];
                case 2:
                    data = _a.sent();
                    if (data.history) {
                        setHistory(data.history);
                    }
                    return [3 /*break*/, 4];
                case 3:
                    error_3 = _a.sent();
                    console.error('Failed to load image history:', error_3);
                    return [3 /*break*/, 4];
                case 4: return [2 /*return*/];
            }
        });
    }); };
    var searchImages = function () { return __awaiter(_this, void 0, void 0, function () {
        var res, data, error_4;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    if (!query.trim())
                        return [2 /*return*/];
                    setLoading(true);
                    setStatus('Searching images...');
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, 4, 5, 6]);
                    return [4 /*yield*/, fetch("/api/images/search?query=".concat(encodeURIComponent(query), "&source=").concat(encodeURIComponent(source), "&limit=18"))];
                case 2:
                    res = _a.sent();
                    return [4 /*yield*/, res.json()];
                case 3:
                    data = _a.sent();
                    if (data.success) {
                        setResults(data.results || []);
                    }
                    else {
                        setStatus(data.error || 'Search failed');
                    }
                    return [3 /*break*/, 6];
                case 4:
                    error_4 = _a.sent();
                    console.error('Image search failed:', error_4);
                    setStatus('Search failed. Try again.');
                    return [3 /*break*/, 6];
                case 5:
                    setLoading(false);
                    return [7 /*endfinally*/];
                case 6: return [2 /*return*/];
            }
        });
    }); };
    var generateImage = function () { return __awaiter(_this, void 0, void 0, function () {
        var payload, reader_1, imageBase64, res, data_1, error_5;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    if (!prompt.trim())
                        return [2 /*return*/];
                    setLoading(true);
                    setStatus('Generating image...');
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, 6, 7, 8]);
                    payload = {
                        prompt: prompt,
                        style: promptStyle,
                        count: 1,
                        provider: selectedProvider,
                        model: selectedModel,
                        save_images: saveImages,
                        sfw_only: sfwOnly,
                    };
                    if (!imageUpload) return [3 /*break*/, 3];
                    reader_1 = new FileReader();
                    return [4 /*yield*/, new Promise(function (resolve, reject) {
                            reader_1.onload = function () {
                                if (typeof reader_1.result === 'string') {
                                    resolve(reader_1.result.split(',')[1]);
                                }
                                else {
                                    reject(new Error('Failed to read image file'));
                                }
                            };
                            reader_1.onerror = reject;
                            reader_1.readAsDataURL(imageUpload);
                        })];
                case 2:
                    imageBase64 = _a.sent();
                    payload.image_input = imageBase64;
                    _a.label = 3;
                case 3: return [4 /*yield*/, fetch('/api/images/generate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    })];
                case 4:
                    res = _a.sent();
                    return [4 /*yield*/, res.json()];
                case 5:
                    data_1 = _a.sent();
                    if (data_1.success && Array.isArray(data_1.images)) {
                        setSavedImages(function (prev) { return __spreadArray(__spreadArray([], data_1.images, true), prev, true); });
                        setHistory(function (prev) { return __spreadArray([{
                                id: Date.now().toString(),
                                type: imageUpload ? 'image_to_image' : 'generate',
                                prompt: prompt,
                                images: data_1.images,
                                timestamp: new Date().toISOString(),
                            }], prev, true); });
                        setStatus('Image generated successfully.');
                        setImageUpload(null);
                        setImagePreviewUrl('');
                    }
                    else {
                        setStatus(data_1.error || 'Generation failed');
                    }
                    return [3 /*break*/, 8];
                case 6:
                    error_5 = _a.sent();
                    console.error('Image generation failed:', error_5);
                    setStatus('Image generation failed.');
                    return [3 /*break*/, 8];
                case 7:
                    setLoading(false);
                    return [7 /*endfinally*/];
                case 8: return [2 /*return*/];
            }
        });
    }); };
    var downloadImage = function (imageUrl) { return __awaiter(_this, void 0, void 0, function () {
        var res, data_2, error_6;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    setLoading(true);
                    setStatus('Downloading image...');
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, 4, 5, 6]);
                    return [4 /*yield*/, fetch('/api/images/download', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ url: imageUrl })
                        })];
                case 2:
                    res = _a.sent();
                    return [4 /*yield*/, res.json()];
                case 3:
                    data_2 = _a.sent();
                    if (data_2.success && data_2.url) {
                        setSavedImages(function (prev) { return __spreadArray([data_2.url], prev, true); });
                        setStatus('Image downloaded.');
                    }
                    else {
                        setStatus(data_2.error || 'Download failed');
                    }
                    return [3 /*break*/, 6];
                case 4:
                    error_6 = _a.sent();
                    console.error('Download failed:', error_6);
                    setStatus('Download failed.');
                    return [3 /*break*/, 6];
                case 5:
                    setLoading(false);
                    return [7 /*endfinally*/];
                case 6: return [2 /*return*/];
            }
        });
    }); };
    var renderImageCard = function (image) { return (<card_1.Card key={image.id} className="bg-white/5 border-white/10 cursor-pointer overflow-hidden transition hover:border-cyan-400/40" onClick={function () { return setSelectedImage(image); }}>
      <div className="relative overflow-hidden rounded-xl bg-slate-950/20">
        <img src={image.thumbnail || image.url} alt={image.title} className="h-40 w-full object-cover"/>
      </div>
      <div className="p-3 space-y-2">
        <div className="flex items-center justify-between gap-2">
          <p className="text-sm font-semibold text-white truncate">{image.title || 'Image result'}</p>
          <badge_1.Badge className="text-[10px] bg-white/10 text-white/70 border-white/10 uppercase">{image.source}</badge_1.Badge>
        </div>
        <p className="text-xs text-white/40 line-clamp-2">{image.url}</p>
      </div>
    </card_1.Card>); };
    return (<scroll_area_1.ScrollArea className="h-full px-4 py-4">
      <div className="space-y-4">
        <div className="flex items-center gap-2 mb-3">
          <lucide_react_1.Sparkles className="w-5 h-5 text-cyan-400"/>
          <h2 className="text-lg font-semibold text-white">Image Studio</h2>
        </div>

        <div className="flex flex-wrap gap-2">
          {['search', 'generate', 'saved', 'history'].map(function (tab) { return (<button_1.Button key={tab} size="sm" variant={activeTab === tab ? 'secondary' : 'ghost'} className={activeTab === tab ? 'bg-cyan-500/20 text-white' : 'bg-white/5 text-white/70'} onClick={function () { return setActiveTab(tab); }}>
              {tab === 'search' && 'Search'}
              {tab === 'generate' && 'Generate'}
              {tab === 'saved' && 'Saved'}
              {tab === 'history' && 'History'}
            </button_1.Button>); })}
        </div>

        <card_1.Card className="bg-white/5 border-white/10 p-4 space-y-4">
          {activeTab === 'search' && (<div className="space-y-4">
              <div className="grid gap-3 md:grid-cols-[1fr_140px]">
                <input_1.Input value={query} onChange={function (e) { return setQuery(e.target.value); }} placeholder="Search for images..."/>
                <button_1.Button onClick={searchImages} disabled={loading}>
                  {loading ? <lucide_react_1.Loader2 className="w-4 h-4 animate-spin"/> : <><lucide_react_1.Search className="w-4 h-4 mr-2"/> Search</>}
                </button_1.Button>
              </div>
              <div className="flex flex-wrap gap-2 text-xs text-white/50">
                <button_1.Button variant="ghost" onClick={function () { return setSource('bing'); }} className={source === 'bing' ? 'bg-cyan-500/20' : ''}>Bing</button_1.Button>
                <button_1.Button variant="ghost" onClick={function () { return setSource('unsplash'); }} className={source === 'unsplash' ? 'bg-cyan-500/20' : ''}>Unsplash</button_1.Button>
                <button_1.Button variant="ghost" onClick={function () { return setSource('pexels'); }} className={source === 'pexels' ? 'bg-cyan-500/20' : ''}>Pexels</button_1.Button>
              </div>
            </div>)}

          {activeTab === 'generate' && (<div className="space-y-4">
              <textarea_1.Textarea value={prompt} onChange={function (e) { return setPrompt(e.target.value); }} placeholder="Describe the image to generate..." className="min-h-[140px] bg-white/5 border-white/10 text-white placeholder:text-white/30"/>
              <div className="grid gap-3 md:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-xs uppercase text-white/60">Provider</label>
                  <select value={selectedProvider} onChange={function (e) { return setSelectedProvider(e.target.value); }} className="w-full rounded-lg border border-white/10 bg-slate-950/70 px-3 py-2 text-sm text-white">
                    {providers.map(function (provider) { return (<option key={provider} value={provider}>{provider}</option>); })}
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-xs uppercase text-white/60">Model</label>
                  <select value={selectedModel} onChange={function (e) { return setSelectedModel(e.target.value); }} className="w-full rounded-lg border border-white/10 bg-slate-950/70 px-3 py-2 text-sm text-white">
                    {models.map(function (model) { return (<option key={model} value={model}>{model}</option>); })}
                  </select>
                </div>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-xs uppercase text-white/60">Style</label>
                  <input value={promptStyle} onChange={function (e) { return setPromptStyle(e.target.value); }} placeholder="photorealistic" className="w-full rounded-lg border border-white/10 bg-slate-950/70 px-3 py-2 text-sm text-white"/>
                </div>
                <div className="space-y-2">
                  <label className="text-xs uppercase text-white/60">Upload image</label>
                  <input type="file" accept="image/*" onChange={function (e) {
                var _a, _b;
                var file = (_b = (_a = e.target.files) === null || _a === void 0 ? void 0 : _a[0]) !== null && _b !== void 0 ? _b : null;
                setImageUpload(file);
                if (file) {
                    setImagePreviewUrl(URL.createObjectURL(file));
                }
                else {
                    setImagePreviewUrl('');
                }
            }} className="w-full rounded-lg border border-white/10 bg-slate-950/70 px-3 py-2 text-sm text-white"/>
                </div>
              </div>
              {imagePreviewUrl && (<div className="rounded-xl border border-white/10 overflow-hidden bg-slate-950/80">
                  <img src={imagePreviewUrl} alt="Upload preview" className="h-44 w-full object-cover"/>
                </div>)}
              <div className="flex flex-wrap gap-2 items-center">
                <button_1.Button onClick={generateImage} disabled={loading}>
                  {loading ? <lucide_react_1.Loader2 className="w-4 h-4 animate-spin"/> : <><lucide_react_1.Sparkles className="w-4 h-4 mr-2"/> Generate</>}
                </button_1.Button>
                <button_1.Button variant={saveImages ? 'secondary' : 'ghost'} onClick={function () { return setSaveImages(function (prev) { return !prev; }); }} size="sm">
                  {saveImages ? 'Saving Enabled' : 'Preview Only'}
                </button_1.Button>
                <button_1.Button variant={sfwOnly ? 'secondary' : 'ghost'} onClick={function () { return setSfwOnly(function (prev) { return !prev; }); }} size="sm">
                  {sfwOnly ? 'SFW Mode' : 'NSFW Allowed'}
                </button_1.Button>
              </div>
              <p className="text-xs text-white/40">Create premium-quality images with smart defaults and optional image-to-image transformation.</p>
            </div>)}

          {activeTab === 'saved' && (<div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-white">Saved Images</h3>
                  <p className="text-xs text-white/50">Images Sarah generated or downloaded.</p>
                </div>
                <button_1.Button size="sm" variant="outline" onClick={loadSavedImages}>Refresh</button_1.Button>
              </div>
              {savedImages.length === 0 ? (<p className="text-sm text-white/50">No saved images yet. Generate or download one to get started.</p>) : (<div className="grid gap-3 md:grid-cols-2">
                  {savedImages.map(function (url) { return (<card_1.Card key={url} className="bg-white/5 border-white/10 overflow-hidden">
                      <img src={url} alt="Saved asset" className="h-40 w-full object-cover"/>
                      <div className="p-3 flex items-center justify-between gap-2">
                        <span className="text-xs text-white/60 truncate">{url.replace('/images/', '')}</span>
                        <button_1.Button size="sm" variant="ghost" onClick={function () { return window.open(url, '_blank'); }}>View</button_1.Button>
                      </div>
                    </card_1.Card>); })}
                </div>)}
            </div>)}

          {activeTab === 'history' && (<div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-white">History</h3>
                  <p className="text-xs text-white/50">Recent image searches and generations.</p>
                </div>
                <button_1.Button size="sm" variant="outline" onClick={loadHistory}>Refresh</button_1.Button>
              </div>
              {history.length === 0 ? (<p className="text-sm text-white/50">No image history yet.</p>) : (<div className="space-y-3">
                  {history.map(function (entry) { return (<card_1.Card key={entry.id} className="bg-white/5 border-white/10 p-3">
                      <div className="flex items-center justify-between gap-2">
                        <div>
                          <p className="text-xs text-white/70 uppercase tracking-[0.2em]">{entry.type}</p>
                          <p className="text-sm text-white">{entry.prompt || entry.query || entry.url || 'Image operation'}</p>
                        </div>
                        <badge_1.Badge className="bg-white/10 text-white/70 border-white/10 text-xs">{new Date(entry.timestamp).toLocaleString()}</badge_1.Badge>
                      </div>
                      {entry.images && entry.images.length > 0 && (<div className="mt-2 grid gap-2 sm:grid-cols-2">
                          {entry.images.map(function (imageUrl) { return (<img key={imageUrl} src={imageUrl} alt="History" className="h-24 w-full rounded-md object-cover"/>); })}
                        </div>)}
                    </card_1.Card>); })}
                </div>)}
            </div>)}

          {status && (<div className="rounded-xl border border-white/10 bg-black/40 p-3 text-sm text-white/70">{status}</div>)}
        </card_1.Card>

        {activeTab === 'search' && results.length > 0 && (<div className="space-y-3">
            <div className="flex items-center gap-2 text-xs text-white/50">
              <lucide_react_1.Search className="w-4 h-4"/>
              <span>Search results</span>
            </div>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {results.map(renderImageCard)}
            </div>
          </div>)}

        {selectedImage && (<card_1.Card className="bg-white/5 border-white/10 p-4 space-y-3">
            <div className="flex items-center justify-between gap-2">
              <div>
                <h3 className="text-sm font-semibold text-white">Preview</h3>
                <p className="text-xs text-white/40">Click download to save the selected image.</p>
              </div>
              <badge_1.Badge className="bg-white/10 text-white/70 border-white/10">{selectedImage.source}</badge_1.Badge>
            </div>
            <img src={selectedImage.thumbnail || selectedImage.url} alt={selectedImage.title} className="h-72 w-full rounded-xl object-cover"/>
            <div className="flex flex-wrap gap-2">
              <button_1.Button onClick={function () { return downloadImage(selectedImage.url); }} disabled={loading}>
                <lucide_react_1.Download className="w-4 h-4 mr-2"/> Save Image
              </button_1.Button>
              <button_1.Button variant="secondary" onClick={function () { return setSelectedImage(null); }}>
                Close
              </button_1.Button>
            </div>
          </card_1.Card>)}
      </div>
    </scroll_area_1.ScrollArea>);
}
