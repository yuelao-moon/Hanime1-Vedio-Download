document.addEventListener("DOMContentLoaded", () => {
    // ---- DOM Elements ----
    const navLogo = document.getElementById("navLogo");
    const settingsBtn = document.getElementById("settingsBtn");
    const settingsModal = document.getElementById("settingsModal");
    const closeSettingsBtn = document.getElementById("closeSettingsBtn");
    const saveSettingsBtn = document.getElementById("saveSettingsBtn");
    const downloadDirInput = document.getElementById("downloadDir");
    const maxConcurrentDownloadsInput = document.getElementById("maxConcurrentDownloads");
    const pageCacheLimitInput = document.getElementById("pageCacheLimit");
    
    // Gopeed & Browser Settings
    const gopeedHostInput = document.getElementById("gopeedHost");
    const gopeedPortInput = document.getElementById("gopeedPort");
    const gopeedTokenInput = document.getElementById("gopeedToken");
    const gopeedConnectionsInput = document.getElementById("gopeedConnections");
    const maxLocalCacheSizeGBInput = document.getElementById("maxLocalCacheSizeGB");

    const downloadCenterBtn = document.getElementById("downloadCenterBtn");
    const downloadBadge = document.getElementById("downloadBadge");
    const downloadCenterModal = document.getElementById("downloadCenterModal");
    const closeDownloadCenterBtn = document.getElementById("closeDownloadCenterBtn");
    const downloadCenterSummary = document.getElementById("downloadCenterSummary");
    const downloadLiveCount = document.getElementById("downloadLiveCount");
    const downloadHistoryCount = document.getElementById("downloadHistoryCount");
    const downloadQueueList = document.getElementById("downloadQueueList");
    const downloadHistoryList = document.getElementById("downloadHistoryList");
    const retryAllFailedBtn = document.getElementById("retryAllFailedBtn");
    const clearDownloadHistoryBtn = document.getElementById("clearDownloadHistoryBtn");
    const pauseAllDownloadsBtn = document.getElementById("pauseAllDownloadsBtn");
    const cancelAllDownloadsBtn = document.getElementById("cancelAllDownloadsBtn");
    const globalSearch = document.getElementById("globalSearch");
    const globalSearchExpandBtn = document.getElementById("globalSearchExpandBtn");
    const globalSearchTypeSelect = document.getElementById("globalSearchTypeSelect");
    const globalSearchInput = document.getElementById("globalSearchInput");
    const globalFilterBtn = document.getElementById("globalFilterBtn");
    const globalSearchSubmitBtn = document.getElementById("globalSearchSubmitBtn");
    const browseSearchToolbar = document.getElementById("browseSearchToolbar");
    const browseSearchTypeSelect = document.getElementById("browseSearchTypeSelect");
    const browseSearchTagBtn = document.getElementById("browseSearchTagBtn");
    const browseSearchSortSelect = document.getElementById("browseSearchSortSelect");
    const browseSearchDateSelect = document.getElementById("browseSearchDateSelect");
    const browseSearchDurationSelect = document.getElementById("browseSearchDurationSelect");
    const browseSearchInput = document.getElementById("browseSearchInput");
    const browseSearchSubmitBtn = document.getElementById("browseSearchSubmitBtn");
    const searchFilterModal = document.getElementById("searchFilterModal");
    const closeSearchFilterBtn = document.getElementById("closeSearchFilterBtn");
    const searchTypeSelect = document.getElementById("searchTypeSelect");
    const searchGenreSelect = document.getElementById("searchGenreSelect");
    const searchSortSelect = document.getElementById("searchSortSelect");
    const searchDateSelect = document.getElementById("searchDateSelect");
    const searchDurationSelect = document.getElementById("searchDurationSelect");
    const searchTagsPanel = document.getElementById("searchTagsPanel");
    const resetSearchFiltersBtn = document.getElementById("resetSearchFiltersBtn");
    const applySearchFiltersBtn = document.getElementById("applySearchFiltersBtn");

    const viewLanding = document.getElementById("viewLanding");
    const viewBrowse = document.getElementById("viewBrowse");
    const viewParser = document.getElementById("viewParser");
    const viewProfile = document.getElementById("viewProfile");
    const authUserBtn = document.getElementById("authUserBtn");
    const authAvatar = document.getElementById("authAvatar");
    const authName = document.getElementById("authName");
    const authHint = document.getElementById("authHint");
    const profilePageHeader = document.getElementById("profilePageHeader");
    const profileSections = document.getElementById("profileSections");
    const profileSectionDetail = document.getElementById("profileSectionDetail");
    const profileSectionGrid = document.getElementById("profileSectionGrid");
    const profileSectionTitle = document.getElementById("profileSectionTitle");
    const profileBackBtn = document.getElementById("profileBackBtn");
    const profilePrevPageBtn = document.getElementById("profilePrevPageBtn");
    const profileNextPageBtn = document.getElementById("profileNextPageBtn");
    const profilePageIndicator = document.getElementById("profilePageIndicator");
    const subscriptionCreatorStrip = document.getElementById("subscriptionCreatorStrip");
    const profilePaginationBar = document.getElementById("profilePaginationBar");

    const modeBrowseBtn = document.getElementById("modeBrowseBtn");
    const modeParseBtn = document.getElementById("modeParseBtn");

    const parseBtn = document.getElementById("parseBtn");
    const urlInput = document.getElementById("urlInput");
    const emptyState = document.getElementById("emptyState");
    const previewContent = document.getElementById("previewContent");
    const logConsole = document.getElementById("logConsole");
    const searchHeader = document.getElementById("searchHeader");
    const toggleSearchBtn = document.getElementById("toggleSearchBtn");
    const statusPanelWrapper = document.getElementById("statusPanelWrapper");
    const toggleLogBtn = document.getElementById("toggleLogBtn");

    const mainTitle = document.getElementById("mainTitle");
    const mainCover = document.getElementById("mainCover");
    const creatorInfoCard = document.getElementById("creatorInfoCard");
    const creatorAvatar = document.getElementById("creatorAvatar");
    const creatorName = document.getElementById("creatorName");
    const userProfileHeader = document.getElementById("userProfileHeader");
    const playlistContainer = document.getElementById("playlistContainer");
    const playlistCount = document.getElementById("playlistCount");
    const mediaDetailTabs = document.getElementById("mediaDetailTabs");
    const detailPanelRelated = document.getElementById("detailPanelRelated");
    const detailPanelComments = document.getElementById("detailPanelComments");
    const relatedVideoGrid = document.getElementById("relatedVideoGrid");
    const relatedVideoCount = document.getElementById("relatedVideoCount");
    const commentsList = document.getElementById("commentsList");
    const commentsCount = document.getElementById("commentsCount");
    const playlistSidebar = document.querySelector(".playlist-sidebar");
    const startDownloadBtn = document.getElementById("startDownloadBtn");
    const downloadSeriesBtn = document.getElementById("downloadSeriesBtn");
    const copyLinkBtn = document.getElementById("copyLinkBtn");
    const favoriteVideoBtn = document.getElementById("favoriteVideoBtn");
    const watchLaterBtn = document.getElementById("watchLaterBtn");
    const myListBtn = document.getElementById("myListBtn");
    const subscribeCreatorBtn = document.getElementById("subscribeCreatorBtn");
    const shortcutBackInput = document.getElementById("shortcutBack");
    const shortcutForwardInput = document.getElementById("shortcutForward");

    // Video Player Elements
    const playerWrapper = document.getElementById("playerWrapper");
    const videoPlayer = document.getElementById("videoPlayer");
    const closePlayerBtn = document.getElementById("closePlayerBtn");
    const coverWrapper = document.getElementById("coverWrapper");
    const playVideoBtn = document.getElementById("playVideoBtn");

    let currentVideoUrl = "";
    let currentRawVideoUrl = "";
    let currentProxiedVideoUrl = "";
    let currentVideoFallbackTried = false;
    let hlsInstance = null; // hls.js instance
    let currentView = 'viewLanding';
    let currentCategory = '首页';
    let currentBrowseMode = 'category';
    let currentPage = 1;
    let currentSearchState = {
        query: "",
        type: "",
        genre: "",
        tags: [],
        sort: "",
        date: "",
        duration: ""
    };
    let searchOptions = null;
    let currentVideoData = null;
    let authState = { loggedIn: false, username: "", avatarUrl: "", userId: "" };
    let shortcutBack = "Alt+ArrowLeft";
    let shortcutForward = "Alt+ArrowRight";
    let activeProfileSection = "";
    let activeProfilePage = 1;
    let activeProfileTotalPages = 1;
    let currentBrowseVideos = [];
    let currentPlaylistItems = [];
    let currentRelatedVideos = [];
    let downloadSnapshot = { activeTasks: [], queuedTasks: [], historyTasks: [] };
    let downloadEventSource = null;
    let downloadReconnectTimer = null;
    const selectedBrowseItems = new Map();
    const watchLaterCardState = new Map(); // vid.url -> boolean, tracks card-level watch-later toggles
    let currentHomeSections = [];
    let currentHomeHero = null;
    let currentCreatorData = null; // Cache last successful creator page data
    let pageCacheLimit = 20;
    const PAGE_CACHE_STORAGE_KEY = "hanimeMediaCenter.pageCache.v1";
    const LS_SUB_CREATORS_KEY = "hmc_sub_creators_v1";
    const LS_CACHE_TTL = 30 * 60 * 1000; // 30 minutes
    const PAGE_CACHE_MAX_AGE = 4 * 60 * 60 * 1000; // 4 hours — page cache TTL for localStorage

    function lsGet(key) {
        try {
            const raw = localStorage.getItem(key);
            if (!raw) return null;
            const obj = JSON.parse(raw);
            if (Date.now() - (obj.ts || 0) > LS_CACHE_TTL) return null;
            return obj.data;
        } catch { return null; }
    }
    function lsSet(key, data) {
        try { localStorage.setItem(key, JSON.stringify({ ts: Date.now(), data })); } catch {}
    }
    let pageCache = loadPageCache();
    if ("scrollRestoration" in history) {
        history.scrollRestoration = "manual";
    }

    // ---- Logging ----
    function log(message, type = "info") {
        const line = document.createElement("div");
        line.className = `log-line ${type}`;
        
        const now = new Date();
        const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
        
        line.textContent = `[${timeStr}] ${message}`;
        logConsole.appendChild(line);
        logConsole.scrollTop = logConsole.scrollHeight;
    }

    function escapeHtml(value = "") {
        return String(value).replace(/[&<>"']/g, (char) => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        }[char]));
    }

    async function postJson(url, payload = {}) {
        const response = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        if (!response.ok) {
            throw new Error(await response.text() || "请求失败");
        }
        const text = await response.text();
        return text ? JSON.parse(text) : {};
    }

    function videoIdFromUrl(url) {
        try {
            return new URL(url, window.location.href).searchParams.get("v") || "";
        } catch (_error) {
            return "";
        }
    }

    function syncAuthHeader() {
        if (!authUserBtn) return;
        authUserBtn.classList.toggle("logged-in", !!authState.loggedIn);
        if (authName) authName.textContent = authState.loggedIn ? (authState.username || "已登录") : "未登录";
        if (authHint) authHint.textContent = authState.loggedIn ? "主页" : "登录";
        if (authAvatar) {
            const avatar = authState.avatarUrl ? imageUrl(authState.avatarUrl) : "";
            authAvatar.src = avatar;
            authAvatar.style.visibility = avatar ? "visible" : "hidden";
        }
    }

    async function refreshAuthState() {
        try {
            const response = await fetch("/api/auth/me");
            if (response.ok) {
                authState = await response.json();
            }
        } catch (_error) {
            authState = { loggedIn: false, username: "", avatarUrl: "", userId: "" };
        }
        syncAuthHeader();
        updateVideoAccountActions();
        return authState;
    }

    function requireLogin() {
        if (authState.loggedIn) return true;
        openLoginModal();
        return false;
    }

    function normalizeShortcut(value, fallback) {
        return String(value || "").trim() || fallback;
    }

    function shortcutFromEvent(event) {
        const parts = [];
        if (event.ctrlKey) parts.push("Ctrl");
        if (event.altKey) parts.push("Alt");
        if (event.shiftKey) parts.push("Shift");
        if (event.metaKey) parts.push("Meta");
        parts.push(event.key);
        return parts.join("+");
    }

    function isEditableTarget(target) {
        return !!target?.closest?.("input, textarea, select, [contenteditable='true']");
    }

    function loadPageCache() {
        // 禁用页面缓存，每次都重新请求
        return new Map();
    }

    function persistPageCache() {
        // 禁用页面缓存持久化
        updatePageCacheStatus();
    }

    function enforcePageCacheLimit() {
        while (pageCache.size > pageCacheLimit) {
            let oldestKey = null;
            let oldestTime = Number.POSITIVE_INFINITY;
            for (const [entryKey, entry] of pageCache.entries()) {
                const time = Number(entry?.lastUsed || entry?.updatedAt || 0);
                if (time < oldestTime) {
                    oldestTime = time;
                    oldestKey = entryKey;
                }
            }
            if (!oldestKey) break;
            pageCache.delete(oldestKey);
        }
    }

    function applyPageCacheLimit(value) {
        const parsed = Number.parseInt(value ?? "20", 10);
        pageCacheLimit = Number.isInteger(parsed) ? Math.min(Math.max(parsed, 1), 200) : 20;
        enforcePageCacheLimit();
        persistPageCache();
        return pageCacheLimit;
    }

    function setPageCacheEntry(key, data) {
        if (!key || !data) return;
        const previous = pageCache.get(key);
        if (previous) pageCache.delete(key);
        pageCache.set(key, {
            data,
            scrollY: previous?.scrollY || 0,
            updatedAt: Date.now(),
            lastUsed: Date.now()
        });
        enforcePageCacheLimit();
        persistPageCache();
        postJson("/api/page-cache", { key, data, scrollY: previous?.scrollY || 0 }).catch(() => {});
    }

    function getPageCacheEntry(key) {
        const entry = pageCache.get(key);
        if (!entry) return null;
        pageCache.delete(key);
        entry.lastUsed = Date.now();
        pageCache.set(key, entry);
        persistPageCache();
        postJson("/api/page-cache", { key, data: entry.data, scrollY: entry.scrollY || 0 }).catch(() => {});
        return entry;
    }

    function updatePageCacheScroll(key, scrollY = window.scrollY) {
        const entry = pageCache.get(key);
        if (!entry) return;
        entry.scrollY = scrollY;
        entry.lastUsed = Date.now();
        pageCache.set(key, entry);
        persistPageCache();
    }

    function getBrowseCacheKey(category, page) {
        return `browse:${category}:${page}`;
    }

    function getSearchCacheKey(page) {
        return `search:${buildSearchParams(page).toString()}`;
    }

    function getParserCacheKey(url) {
        return `parse:${String(url || "").trim()}`;
    }

    function getCurrentPageCacheKey() {
        if (currentView !== "viewBrowse") return "";
        if (currentBrowseMode === "search") return getSearchCacheKey(currentPage);
        return getBrowseCacheKey(currentCategory, currentPage);
    }

    function rememberCurrentPageScroll() {
        updatePageCacheScroll(getCurrentPageCacheKey());
    }

    function restoreCachedBrowsePage(key) {
        const entry = getPageCacheEntry(key);
        if (!entry) return false;
        browseLoader.classList.add("hidden");
        applyBrowseResult(entry.data);
        window.requestAnimationFrame(() => {
            window.scrollTo({ top: Number(entry.scrollY || 0), behavior: "auto" });
        });
        return true;
    }

    function restoreCachedParserPage(url) {
        const entry = getPageCacheEntry(getParserCacheKey(url));
        if (!entry) return false;
        prepareParserLoading(url, false);
        renderUi(entry.data);
        window.requestAnimationFrame(() => {
            window.scrollTo({ top: 0, behavior: "auto" });
            window.setTimeout(() => window.scrollTo({ top: 0, behavior: "auto" }), 0);
        });
        return true;
    }

    function clearPageCache() {
        pageCache.clear();
        try {
            localStorage.removeItem(PAGE_CACHE_STORAGE_KEY);
        } catch (_error) {
            // Ignore storage failures; in-memory cache has already been cleared.
        }
        updatePageCacheStatus();
        fetch("/api/settings/clear-page-cache", { method: "POST" }).catch(() => {});
    }

    function updatePageCacheStatus(message = "") {
        const pageCacheStatus = document.getElementById("pageCacheStatus");
        if (!pageCacheStatus) return;
        pageCacheStatus.textContent = message || "页面缓存已禁用（每次都重新请求）";
    }

    async function updateCookieStatus(message = "") {
        const cookieStatus = document.getElementById("cookieStatus");
        if (!cookieStatus) return;
        if (message) {
            cookieStatus.textContent = message;
            return;
        }
        try {
            const response = await fetch("/api/cookies/status");
            const data = await response.json();
            cookieStatus.textContent = data.hasCfClearance
                ? `Cookie 可用，已缓存 ${data.cookieCount || 0} 个`
                : "未检测到可用 Cookie";
        } catch (_error) {
            cookieStatus.textContent = "Cookie 状态读取失败";
        }
    }

    function proxyImageUrl(url) {
        return url ? `/api/proxy/image?url=${encodeURIComponent(url)}` : "";
    }

    function imageUrl(url) {
        return proxyImageUrl(url);
    }

    function directMediaUrl(url) {
        return url || "";
    }

    function proxyVideoUrl(url) {
        return url ? `/api/proxy/video?url=${encodeURIComponent(url)}` : "";
    }

    window.fallbackImage = (img) => {
        const rawUrl = img?.dataset?.srcRaw;
        if (!img || !rawUrl || img.dataset.proxyTried === "1") return;
        img.dataset.proxyTried = "1";
        img.src = proxyImageUrl(rawUrl);
    };

    function preloadCurrentVideo() {
        if (!currentVideoUrl || currentVideoUrl.includes(".m3u8")) return;
        if (currentVideoUrl === currentRawVideoUrl) return;
        playerWrapper.classList.remove("hidden");
        playerWrapper.classList.add("preloading");
        videoPlayer.onerror = null;
        videoPlayer.preload = "metadata";
        if (videoPlayer.dataset.src !== currentVideoUrl) {
            videoPlayer.dataset.src = currentVideoUrl;
            videoPlayer.src = currentVideoUrl;
            videoPlayer.load();
        }
    }

    function normalizeSearchState(state = {}) {
        return {
            query: String(state.query || "").trim(),
            type: String(state.type || "").trim(),
            genre: String(state.genre || "").trim(),
            tags: Array.isArray(state.tags) ? state.tags.filter(Boolean) : [],
            sort: String(state.sort || "").trim(),
            date: String(state.date || "").trim(),
            duration: String(state.duration || "").trim()
        };
    }

    function hasActiveSearchFilters(state = currentSearchState) {
        const normalized = normalizeSearchState(state);
        return Boolean(normalized.type || normalized.genre || normalized.sort || normalized.date || normalized.duration || normalized.tags.length);
    }

    function hasActiveSearchState(state = currentSearchState) {
        const normalized = normalizeSearchState(state);
        return Boolean(normalized.query || hasActiveSearchFilters(normalized));
    }

    function syncGlobalSearchChrome() {
        if (!globalSearch) return;
        globalSearch.classList.toggle("has-value", Boolean(globalSearchInput?.value.trim()));
        globalSearch.classList.toggle("has-filters", hasActiveSearchFilters());
        if (!globalSearchInput?.value.trim() && !hasActiveSearchFilters() && document.activeElement !== globalSearchInput) {
            globalSearch.classList.add("collapsed");
        }
    }

    function expandGlobalSearch(focus = false) {
        if (!globalSearch) return;
        globalSearch.classList.remove("collapsed");
        if (focus && globalSearchInput) {
            globalSearchInput.focus();
        }
    }

    function collapseGlobalSearchIfIdle() {
        window.setTimeout(syncGlobalSearchChrome, 120);
    }

    function setSelectOptions(select, values = [], allLabel = "全部") {
        if (!select) return;
        const current = select.value;
        select.innerHTML = `<option value="">${allLabel}</option>` + values
            .map(value => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`)
            .join("");
        select.value = values.includes(current) ? current : "";
    }

    function syncSearchTypeControls() {
        const state = normalizeSearchState(currentSearchState);
        if (globalSearchTypeSelect) globalSearchTypeSelect.value = state.type;
        if (browseSearchTypeSelect) browseSearchTypeSelect.value = state.type;
        if (browseSearchSortSelect) browseSearchSortSelect.value = state.sort;
        if (browseSearchDateSelect) browseSearchDateSelect.value = state.date;
        if (browseSearchDurationSelect) browseSearchDurationSelect.value = state.duration;
        if (globalSearchInput && document.activeElement !== globalSearchInput) {
            globalSearchInput.value = state.query;
        }
        if (browseSearchInput && document.activeElement !== browseSearchInput) {
            browseSearchInput.value = state.query;
        }
    }

    function syncSearchControlsFromOptions(options = searchOptions || {}) {
        setSelectOptions(globalSearchTypeSelect, options.types || [], "全部类型");
        setSelectOptions(browseSearchTypeSelect, options.types || [], "全部类型");
        setSelectOptions(browseSearchSortSelect, options.sorts || [], "排序方式");
        setSelectOptions(browseSearchDateSelect, options.dates || [], "发布日期");
        setSelectOptions(browseSearchDurationSelect, options.durations || [], "时长");
        syncSearchTypeControls();
    }

    function updateSearchStateFromGlobalControls() {
        currentSearchState = normalizeSearchState({
            ...currentSearchState,
            query: globalSearchInput?.value || "",
            type: globalSearchTypeSelect?.value || ""
        });
        syncSearchTypeControls();
        syncGlobalSearchChrome();
    }

    function updateSearchStateFromBrowseControls() {
        currentSearchState = normalizeSearchState({
            ...currentSearchState,
            query: browseSearchInput?.value || "",
            type: browseSearchTypeSelect?.value || "",
            sort: browseSearchSortSelect?.value || "",
            date: browseSearchDateSelect?.value || "",
            duration: browseSearchDurationSelect?.value || ""
        });
        syncSearchTypeControls();
        syncGlobalSearchChrome();
    }

    async function loadSearchOptions() {
        if (searchOptions) {
            return searchOptions;
        }
        try {
            const response = await fetch("/api/search/options");
            if (!response.ok) {
                throw new Error(await response.text() || "筛选项载入失败");
            }
            searchOptions = await response.json();
        } catch (error) {
            console.error("搜索筛选项载入失败", error);
            searchOptions = {
                types: ["裏番", "泡麵番", "Motion Anime", "3DCG", "2.5D", "2D動畫", "AI生成", "MMD", "Cosplay"],
                genres: ["裏番", "泡麵番", "Motion Anime", "3DCG", "2.5D", "2D動畫", "AI生成", "MMD", "Cosplay"],
                sorts: ["本日排行"],
                dates: ["過去 24 小時"],
                durations: ["1 分鐘 +"],
                tagGroups: [{ name: "常用标签", tags: ["巨乳", "魅魔", "中文字幕", "中文配音"] }]
            };
        }
        syncSearchControlsFromOptions(searchOptions);
        return searchOptions;
    }

    async function openSearchFilterModal() {
        expandGlobalSearch(false);
        const options = await loadSearchOptions();
        setSelectOptions(searchTypeSelect, options.types || [], "全部类型");
        setSelectOptions(searchGenreSelect, options.genres || [], "全部分类");
        setSelectOptions(searchSortSelect, options.sorts || [], "全部排序");
        setSelectOptions(searchDateSelect, options.dates || [], "全部日期");
        setSelectOptions(searchDurationSelect, options.durations || [], "全部时长");
        syncSearchFilterControls();
        syncSearchControlsFromOptions(options);
        renderSearchTags(options.tagGroups || []);
        searchFilterModal.classList.remove("hidden");
    }

    function syncSearchFilterControls() {
        const state = normalizeSearchState(currentSearchState);
        if (searchTypeSelect) searchTypeSelect.value = state.type;
        if (searchGenreSelect) searchGenreSelect.value = state.genre;
        if (searchSortSelect) searchSortSelect.value = state.sort;
        if (searchDateSelect) searchDateSelect.value = state.date;
        if (searchDurationSelect) searchDurationSelect.value = state.duration;
        syncSearchTypeControls();
    }

    function renderSearchTags(tagGroups) {
        if (!searchTagsPanel) return;
        const groups = Array.isArray(tagGroups) ? tagGroups : [];
        if (groups.length === 0) {
            searchTagsPanel.innerHTML = `<div class="download-empty">没有可用标签</div>`;
            return;
        }
        const selected = new Set(currentSearchState.tags || []);
        searchTagsPanel.innerHTML = groups.map((group) => {
            const tags = Array.isArray(group.tags) ? group.tags : [];
            return `
                <section class="search-tag-group">
                    <h3>${escapeHtml(group.name || "标签")}</h3>
                    <div class="search-tag-list">
                        ${tags.map((tag) => `
                            <button class="search-tag-chip ${selected.has(tag) ? 'active' : ''}" type="button" data-tag="${escapeHtml(tag)}">${escapeHtml(tag)}</button>
                        `).join("")}
                    </div>
                </section>
            `;
        }).join("");
    }

    function readSearchFiltersFromModal() {
        currentSearchState = normalizeSearchState({
            ...currentSearchState,
            query: globalSearchInput?.value || currentSearchState.query,
            type: searchTypeSelect?.value || "",
            genre: searchGenreSelect?.value || "",
            sort: searchSortSelect?.value || "",
            date: searchDateSelect?.value || "",
            duration: searchDurationSelect?.value || "",
            tags: currentSearchState.tags
        });
        syncSearchTypeControls();
    }

    function buildSearchParams(page = 1) {
        const state = normalizeSearchState(currentSearchState);
        const params = new URLSearchParams();
        params.set("query", state.query);
        params.set("type", state.type);
        params.set("genre", state.genre);
        state.tags.forEach(tag => params.append("tags[]", tag));
        params.set("sort", state.sort);
        params.set("date", state.date);
        params.set("duration", state.duration);
        params.set("page", String(page));
        return params;
    }

    function buildSearchHash(page = 1) {
        return `#search?${buildSearchParams(page).toString()}`;
    }

    function searchTitle() {
        const state = normalizeSearchState(currentSearchState);
        if (state.query) {
            return `搜索：${state.query}`;
        }
        return "高级筛选结果";
    }

    function applyBrowseResult(data) {
        const totalPagesIndicatorStr = document.getElementById('totalPagesIndicatorStr');
        const paginationBar = document.getElementById('paginationBar');
        selectedBrowseItems.clear();
        updateBrowseSelectionSummary();
        browseLoader.classList.add("hidden");

        if (userProfileHeader) {
            userProfileHeader.classList.add("hidden");
        }
        if (currentCategoryTitle) currentCategoryTitle.classList.remove("hidden");
        if (browseSearchToolbar) browseSearchToolbar.classList.remove("hidden");

        if (data.isHome) {
            currentHomeSections = data.sections || [];
            currentHomeHero = data.hero || null;
            currentBrowseVideos = [];
            currentHomeSections.forEach(sec => {
                if (Array.isArray(sec.videos)) {
                    currentBrowseVideos.push(...sec.videos);
                }
            });
            videoGrid.classList.add("home-layout");
            if (browseSearchToolbar) browseSearchToolbar.classList.add("hidden");
            if (paginationBar) paginationBar.classList.add("hidden");
            renderHomeSections(currentHomeSections, currentHomeHero);
        } else if (data.isCreatorPage) {
            currentHomeSections = [];
            currentHomeHero = null;
            currentBrowseVideos = Array.isArray(data.videos) ? data.videos : [];
            videoGrid.classList.remove("home-layout");
            if (currentCategoryTitle) currentCategoryTitle.classList.add("hidden");
            if (browseSearchToolbar) browseSearchToolbar.classList.add("hidden");
            if (paginationBar) paginationBar.classList.remove("hidden");

            // Cache creator data for optimistic UI updates on subsequent tab/sort clicks
            currentCreatorData = {
                creatorAvatar: data.creatorAvatar,
                creatorName: data.creatorName,
                creatorId: data.creatorId,
                creatorStats: data.creatorStats
            };

            renderCreatorHeader(currentCategory);
            renderVideoGrid(currentBrowseVideos);
        } else if (data.isPlaylistPage) {
            currentHomeSections = [];
            currentHomeHero = null;
            currentBrowseVideos = Array.isArray(data.videos) ? data.videos : [];
            videoGrid.classList.remove("home-layout");
            if (currentCategoryTitle) currentCategoryTitle.classList.add("hidden");
            if (browseSearchToolbar) browseSearchToolbar.classList.add("hidden");
            if (paginationBar) paginationBar.classList.remove("hidden");

            if (userProfileHeader) {
                userProfileHeader.style.setProperty('--avatar-url', 'none');
                userProfileHeader.innerHTML = `
                    <div class="playlist-rows-wrapper" style="background: rgba(20, 20, 26, 0.7); backdrop-filter: blur(10px);">
                        <div class="profile-main-container">
                            <div class="profile-content-right">
                                <h1 class="profile-display-name">${escapeHtml(data.playlistTitle)}</h1>
                                <div class="profile-sub-stats">
                                    <span class="profile-sub-stats-new-line">播放清單 • 創作者: 
                                        <button class="creator-link-btn" style="background: none; border: none; color: var(--primary, #ff4b4b); cursor: pointer; padding: 0; font-weight: 600; font-size: inherit; text-decoration: underline;">
                                            ${escapeHtml(data.creatorName || "未知")}
                                        </button>
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                userProfileHeader.classList.remove("hidden");

                const backBtn = userProfileHeader.querySelector(".creator-link-btn");
                if (backBtn && data.creatorId) {
                    backBtn.onclick = () => {
                        loadBrowseCategory("user:" + data.creatorId, 1, true);
                    };
                }
            }

            renderVideoGrid(currentBrowseVideos);

            if (data.totalPages && totalPagesIndicatorStr) {
                totalPagesIndicatorStr.innerText = `/ ${data.totalPages}`;
                if (nextPageBtn) {
                    nextPageBtn.disabled = (currentPage >= data.totalPages);
                }
            } else if (totalPagesIndicatorStr) {
                totalPagesIndicatorStr.innerText = "";
                if (nextPageBtn) {
                    nextPageBtn.disabled = false;
                }
            }
        } else {
            currentHomeSections = [];
            currentHomeHero = null;
            currentBrowseVideos = Array.isArray(data.videos) ? data.videos : [];
            videoGrid.classList.remove("home-layout");
            if (browseSearchToolbar) browseSearchToolbar.classList.remove("hidden");
            if (paginationBar) paginationBar.classList.remove("hidden");
            renderVideoGrid(currentBrowseVideos);

            if (data.totalPages && totalPagesIndicatorStr) {
                totalPagesIndicatorStr.innerText = `/ ${data.totalPages}`;
                if (nextPageBtn) {
                    nextPageBtn.disabled = (currentPage >= data.totalPages);
                }
            } else if (totalPagesIndicatorStr) {
                totalPagesIndicatorStr.innerText = "";
                if (nextPageBtn) {
                    nextPageBtn.disabled = false;
                }
            }
        }
    }

    /**
     * Renders the creator profile header with tabs and sort buttons.
     * Can be called optimistically (before API response) using cached currentCreatorData,
     * or after a successful API response.
     * @param {string} category - The current user category string e.g. "user:1701564:uploaded:latest"
     */
    function renderCreatorHeader(category) {
        if (!userProfileHeader) return;
        const creator = currentCreatorData;
        if (!creator) return;

        const parts = category.split(":");
        const userId = parts[1];
        const subpage = parts[2] || "home";
        const sort = parts[3] || "latest";

        let filterHtml = "";
        if (subpage === "uploaded" || subpage === "playlists") {
            filterHtml = `
                <div class="filter-button-group">
                    <button class="filter-pill ${sort === 'latest' ? 'active' : ''}" data-sort="latest">最新</button>
                    <button class="filter-pill ${sort === 'popular' ? 'active' : ''}" data-sort="popular">熱門</button>
                    <button class="filter-pill ${sort === 'oldest' ? 'active' : ''}" data-sort="oldest">最早</button>
                </div>
            `;
        }

        userProfileHeader.style.setProperty('--avatar-url', `url('${imageUrl(creator.creatorAvatar)}')`);
        userProfileHeader.innerHTML = `
            <div class="playlist-rows-wrapper">
                <div class="profile-main-container">
                    <div class="profile-avatar-wrapper">
                        <img src="${imageUrl(creator.creatorAvatar)}" data-src-raw="${escapeHtml(creator.creatorAvatar || "")}" onerror="fallbackImage(this)" alt="avatar">
                    </div>
                    <div class="profile-content-right">
                        <h1 class="profile-display-name">${escapeHtml(creator.creatorName)}</h1>
                        <div class="profile-sub-stats">
                            <span class="profile-sub-stats-id">@ ${escapeHtml(creator.creatorId)}</span>
                            <span class="profile-sub-stats-new-line">${escapeHtml(creator.creatorStats)}</span>
                        </div>
                    </div>
                </div>
                <div class="creator-tabs-divider"></div>
                <div class="nav-tabs-scroll no-scrollbar-style">
                    <button class="yt-tab ${subpage === 'home' ? 'active' : ''}" data-tab="home">首頁</button>
                    <button class="yt-tab ${subpage === 'uploaded' ? 'active' : ''}" data-tab="uploaded">影片</button>
                    <button class="yt-tab ${subpage === 'playlists' ? 'active' : ''}" data-tab="playlists">播放清單</button>
                    <button class="yt-tab search-icon-tab" data-tab="search" title="搜索作者视频">🔍</button>
                </div>
            </div>
            ${filterHtml}
        `;
        userProfileHeader.classList.remove("hidden");

        // Bind tab clicks
        userProfileHeader.querySelectorAll(".yt-tab").forEach(btn => {
            btn.onclick = () => {
                const tab = btn.getAttribute("data-tab");
                if (tab === "search") {
                    const searchInput = document.getElementById("searchInput");
                    if (searchInput) {
                        searchInput.value = creator.creatorName;
                        const searchBtn = document.getElementById("searchBtn");
                        if (searchBtn) searchBtn.click();
                    }
                    return;
                }
                loadBrowseCategory(`user:${userId}:${tab}`, 1, true);
            };
        });

        // Bind sort clicks
        userProfileHeader.querySelectorAll(".filter-pill").forEach(btn => {
            btn.onclick = () => {
                const newSort = btn.getAttribute("data-sort");
                loadBrowseCategory(`user:${userId}:${subpage}:${newSort}`, 1, true);
            };
        });
    }

    function refreshBrowseGrid() {
        if (currentCategory === '首页' && currentBrowseMode === 'category') {
            renderHomeSections(currentHomeSections, currentHomeHero);
        } else {
            renderVideoGrid(currentBrowseVideos);
        }
    }

    function createVideoCard(vid) {
        const card = document.createElement("div");
        const isSelected = selectedBrowseItems.has(vid.url);
        const isPlaylist = vid.url.includes("playlist?list=") || vid.isPlaylist;
        card.className = "grid-item" + (isSelected ? " selected" : "");

        const statsHtml = `
            <div class="grid-stats-bar">
                ${vid.duration ? `<span class="grid-stat-pill">${escapeHtml(vid.duration)}</span>` : ''}
                ${vid.likes ? `<span class="grid-stat-pill">👍 ${escapeHtml(vid.likes)}</span>` : ''}
                ${vid.views ? `<span class="grid-stat-pill">${escapeHtml(vid.views)}</span>` : ''}
                ${!isPlaylist ? `<button class="grid-watch-later-mini" type="button">+ 稍后</button>` : ''}
            </div>`;

        card.innerHTML = `
            <div class="grid-thumb-container${isSelected ? ' selected' : ''}">
                <img src="${imageUrl(vid.thumbnail)}" data-src-raw="${escapeHtml(vid.thumbnail || "")}" onerror="fallbackImage(this)" loading="lazy" class="grid-thumb" alt="cover">
                ${vid.videoCount ? `<div class="grid-item-playlist-badge">${escapeHtml(vid.videoCount)}</div>` : ''}
                <div class="grid-select-overlay${isSelected ? ' visible' : ''}">✓ 已选</div>
            </div>
            ${statsHtml}
            <button class="grid-title-btn" title="${escapeHtml(vid.title || "")}" type="button">${escapeHtml(vid.title || "未命名视频")}</button>
        `;

        const thumbContainer = card.querySelector(".grid-thumb-container");
        const selectOverlay = card.querySelector(".grid-select-overlay");

        // Thumbnail click = toggle selection (playlist thumbnail navigates instead)
        thumbContainer.addEventListener("click", (e) => {
            e.stopPropagation();
            if (isPlaylist) {
                const listId = new URL(vid.url).searchParams.get("list");
                if (listId) { rememberCurrentPageScroll(); loadBrowseCategory("playlist:" + listId, 1, true); }
                return;
            }
            const nowSelected = !selectedBrowseItems.has(vid.url);
            if (nowSelected) {
                selectedBrowseItems.set(vid.url, { title: vid.title, pageUrl: vid.url, thumbnail: vid.thumbnail, downloadUrl: "" });
            } else {
                selectedBrowseItems.delete(vid.url);
            }
            card.classList.toggle("selected", nowSelected);
            thumbContainer.classList.toggle("selected", nowSelected);
            if (selectOverlay) selectOverlay.classList.toggle("visible", nowSelected);
            updateBrowseSelectionSummary();
        });

        // Title click = navigate to video detail
        const titleBtn = card.querySelector(".grid-title-btn");
        titleBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            if (isPlaylist) {
                const listId = new URL(vid.url).searchParams.get("list");
                if (listId) { rememberCurrentPageScroll(); loadBrowseCategory("playlist:" + listId, 1, true); }
                return;
            }
            rememberCurrentPageScroll();
            urlInput.value = vid.url;
            switchView("viewParser", false);
            parseBtn.click();
        });

        // Watch-later mini button
        card.querySelector(".grid-watch-later-mini")?.addEventListener("click", (e) => {
            e.stopPropagation();
            addCardToWatchLater(vid, e.currentTarget);
        });

        return card;
    }

    function createHomeVideoCard(vid) {
        const container = document.createElement("div");
        const isSelected = selectedBrowseItems.has(vid.url);
        container.className = "video-item-container" + (isSelected ? " selected-card" : "");

        const thumbnail = imageUrl(vid.thumbnail);
        const isPlaylist = vid.url.includes("playlist?list=");

        container.innerHTML = `
            <div class="horizontal-card">
                <div class="thumb-container${isSelected ? ' selected' : ''}">
                    <img class="main-thumb" src="${thumbnail}" data-src-raw="${escapeHtml(vid.thumbnail || "")}" onerror="fallbackImage(this)" loading="lazy" alt="cover">
                    <div class="grid-select-overlay${isSelected ? ' visible' : ''}">✓ 已选</div>
                </div>
                <div class="home-stats-bar">
                    ${vid.duration ? `<span class="grid-stat-pill">${escapeHtml(vid.duration)}</span>` : ''}
                    ${vid.likes ? `<span class="grid-stat-pill">👍 ${escapeHtml(vid.likes)}</span>` : ''}
                    ${vid.views ? `<span class="grid-stat-pill">${escapeHtml(vid.views)}</span>` : ''}
                    ${!isPlaylist ? `<button class="grid-watch-later-mini" type="button">+ 稍后</button>` : ''}
                </div>
                <button class="home-title-btn" title="${escapeHtml(vid.title || "")}" type="button">${escapeHtml(vid.title || "未命名视频")}</button>
                ${vid.creator ? `<div class="subtitle">${escapeHtml(vid.creator)}</div>` : ''}
            </div>
        `;

        const thumbContainer = container.querySelector(".thumb-container");
        const selectOverlay = container.querySelector(".grid-select-overlay");

        // Thumbnail click = toggle selection (playlist thumbnail navigates)
        thumbContainer.addEventListener("click", (e) => {
            e.stopPropagation();
            if (isPlaylist) {
                const listId = new URL(vid.url).searchParams.get("list");
                if (listId) { rememberCurrentPageScroll(); loadBrowseCategory("playlist:" + listId, 1, true); }
                return;
            }
            const nowSelected = !selectedBrowseItems.has(vid.url);
            if (nowSelected) {
                selectedBrowseItems.set(vid.url, { title: vid.title, pageUrl: vid.url, thumbnail: vid.thumbnail, downloadUrl: "" });
            } else {
                selectedBrowseItems.delete(vid.url);
            }
            container.classList.toggle("selected-card", nowSelected);
            thumbContainer.classList.toggle("selected", nowSelected);
            if (selectOverlay) selectOverlay.classList.toggle("visible", nowSelected);
            updateBrowseSelectionSummary();
        });

        // Title click = navigate
        container.querySelector(".home-title-btn")?.addEventListener("click", (e) => {
            e.stopPropagation();
            if (isPlaylist) {
                const listId = new URL(vid.url).searchParams.get("list");
                if (listId) { rememberCurrentPageScroll(); loadBrowseCategory("playlist:" + listId, 1, true); }
                return;
            }
            rememberCurrentPageScroll();
            urlInput.value = vid.url;
            switchView("viewParser", false);
            parseBtn.click();
        });

        // Watch-later mini
        container.querySelector(".grid-watch-later-mini")?.addEventListener("click", (e) => {
            e.stopPropagation();
            addCardToWatchLater(vid, e.currentTarget);
        });

        return container;
    }

    function renderHomeHero(hero) {
        if (!hero) return null;
        
        const heroDiv = document.createElement("div");
        heroDiv.className = "home-hero-banner";
        
        const heroThumb = imageUrl(hero.thumbnail);
        const tagsHtml = (hero.tags || []).map(tag => {
            return `<span class="hero-tag">${escapeHtml(tag)}</span>`;
        }).join("");
        
        heroDiv.innerHTML = `
            <div class="hero-bg-wrapper">
                <img class="hero-bg-img" src="${heroThumb}" data-src-raw="${escapeHtml(hero.thumbnail || "")}" onerror="fallbackImage(this)" alt="hero background">
                <div class="hero-overlay"></div>
            </div>
            <div class="hero-content">
                <h1 class="hero-title">${escapeHtml(hero.title)}</h1>
                <div class="hero-meta">
                    ${hero.creator ? `<span class="hero-creator">${escapeHtml(hero.creator)}</span>` : ''}
                    ${hero.views ? `<span class="hero-meta-divider">•</span><span class="hero-views">${escapeHtml(hero.views)}</span>` : ''}
                    ${hero.date ? `<span class="hero-meta-divider">•</span><span class="hero-date">${escapeHtml(hero.date)}</span>` : ''}
                </div>
                <div class="hero-tags-wrapper">
                    ${tagsHtml}
                </div>
                <div class="hero-buttons">
                    <button class="hero-btn btn-play" type="button">
                        <span class="btn-icon">▶</span>播放
                    </button>
                    <button class="hero-btn btn-info" type="button">
                        <span class="btn-icon">ℹ</span>更多资讯
                    </button>
                </div>
            </div>
        `;
        
        const playBtn = heroDiv.querySelector(".btn-play");
        const infoBtn = heroDiv.querySelector(".btn-info");
        const bgWrapper = heroDiv.querySelector(".hero-bg-wrapper");
        
        const handleHeroClick = (event) => {
            event.stopPropagation();
            if (hero.watchUrl) {
                urlInput.value = hero.watchUrl;
                switchView("viewParser", false);
                parseBtn.click();
            }
        };
        
        playBtn.addEventListener("click", handleHeroClick);
        infoBtn.addEventListener("click", handleHeroClick);
        bgWrapper.addEventListener("click", handleHeroClick);
        
        return heroDiv;
    }

    function renderHomeSections(sections, hero) {
        if ((!sections || sections.length === 0) && !hero) {
            videoGrid.innerHTML = `<div class="empty-playlist">该分类下暂无兼容排版资源或需翻页支持</div>`;
            return;
        }

        videoGrid.innerHTML = "";

        if (hero) {
            const heroElement = renderHomeHero(hero);
            if (heroElement) {
                videoGrid.appendChild(heroElement);
            }
        }

        sections.forEach(sec => {
            const sectionDiv = document.createElement("div");
            sectionDiv.className = "home-section";

            const titleDiv = document.createElement("div");
            titleDiv.className = "home-section-title";

            if (sec.sectionLink) {
                // Make the title a clickable link
                const titleBtn = document.createElement("button");
                titleBtn.type = "button";
                titleBtn.className = "home-section-title-link";
                titleBtn.textContent = sec.sectionTitle || "未分类板块";
                titleBtn.title = `点击查看全部: ${sec.sectionTitle || ""}`;
                titleBtn.addEventListener("click", () => {
                    navigateToSectionLink(sec.sectionLink, sec.sectionTitle || "");
                });
                const arrowSpan = document.createElement("span");
                arrowSpan.className = "home-section-title-arrow";
                arrowSpan.textContent = "›";
                titleDiv.appendChild(titleBtn);
                titleDiv.appendChild(arrowSpan);
            } else {
                titleDiv.textContent = sec.sectionTitle || "未分类板块";
            }

            sectionDiv.appendChild(titleDiv);

            const gridDiv = document.createElement("div");
            gridDiv.className = "home-row horizontal-row";

            const vids = Array.isArray(sec.videos) ? sec.videos : [];
            vids.forEach(vid => {
                const card = createHomeVideoCard(vid);
                gridDiv.appendChild(card);
            });

            sectionDiv.appendChild(gridDiv);
            videoGrid.appendChild(sectionDiv);
        });
    }

    /**
     * Parse a hanime1.me section URL and navigate to browse/search view.
     * Supports sort= and genre= query params from section links.
     */
    function navigateToSectionLink(link, title) {
        try {
            const url = new URL(link);
            const sort = url.searchParams.get("sort") || "";
            const genre = url.searchParams.get("genre") || "";
            const type = url.searchParams.get("type") || "";

            if (sort || genre || type) {
                // Navigate via search with the sort/genre params
                currentSearchState = normalizeSearchState({
                    query: "",
                    type: type,
                    genre: genre,
                    sort: sort,
                    date: "",
                    duration: "",
                    tags: []
                });
                syncSearchTypeControls();
                syncGlobalSearchChrome();
                if (currentCategoryTitle) currentCategoryTitle.innerText = title || "正在浏览";
                switchView("viewBrowse", false);
                // Update category list highlight
                document.querySelectorAll("#categoryList li").forEach(li => li.classList.remove("active"));
                loadSearchResults(1, true);
            } else {
                // Try matching as a category from the path
                const path = url.pathname;
                const catMatch = path.match(/\/search\/?/);
                if (catMatch) {
                    currentSearchState = normalizeSearchState({ query: "", type: "", genre: "", sort: "", date: "", duration: "", tags: [] });
                    switchView("viewBrowse", false);
                    loadSearchResults(1, true);
                }
            }
        } catch (e) {
            // Fallback: do nothing
            console.warn("navigateToSectionLink: invalid URL", link, e);
        }
    }

    async function loadSearchResults(page = 1, pushState = true) {
        currentBrowseMode = "search";
        currentPage = page;
        currentSearchState = normalizeSearchState(currentSearchState);
        const cacheKey = getSearchCacheKey(page);
        syncSearchTypeControls();
        syncGlobalSearchChrome();
        switchView("viewBrowse", false);

        const pageIndicator = document.getElementById('pageIndicator');
        if (currentCategoryTitle) currentCategoryTitle.innerText = searchTitle();
        if (pageIndicator) pageIndicator.innerText = page;
        if (pushState) {
            history.pushState({ view: "viewBrowse", search: true, page, filters: currentSearchState }, "", buildSearchHash(page));
        }

        if (restoreCachedBrowsePage(cacheKey)) {
            return;
        }

        videoGrid.innerHTML = "";
        browseLoader.classList.remove("hidden");

        try {
            const response = await fetch(`/api/search?${buildSearchParams(page).toString()}`);
            if (!response.ok) {
                throw new Error(await response.text() || "搜索失败");
            }
            const data = await response.json();
            setPageCacheEntry(cacheKey, data);
            applyBrowseResult(data);
            window.scrollTo({ top: 0, behavior: "auto" });
        } catch (error) {
            browseLoader.classList.add("hidden");
            videoGrid.innerHTML = `<div style="color:red; padding: 2rem; text-align: center;">搜索异常: ${escapeHtml(error.message)}</div>`;
        }
    }

    function normalizeSnapshot(snapshot = {}) {
        return {
            activeTasks: Array.isArray(snapshot.activeTasks) ? snapshot.activeTasks : [],
            queuedTasks: Array.isArray(snapshot.queuedTasks) ? snapshot.queuedTasks : [],
            historyTasks: Array.isArray(snapshot.historyTasks) ? snapshot.historyTasks : []
        };
    }

    function formatStatus(status) {
        const labels = {
            QUEUED: "排队中",
            PREPARING: "解析中",
            DOWNLOADING: "下载中",
            PAUSED: "已暂停",
            COMPLETED: "已完成",
            FAILED: "失败",
            CANCELLED: "已取消"
        };
        return labels[status] || status || "未知状态";
    }

    function taskActionButtons(task) {
        const actions = [];
        if (task.status === "DOWNLOADING" || task.status === "PREPARING") {
            actions.push(`<button class="download-action-btn" type="button" data-action="pause" data-task-id="${escapeHtml(task.id)}">暂停</button>`);
            actions.push(`<button class="download-action-btn danger" type="button" data-action="cancel" data-task-id="${escapeHtml(task.id)}">取消</button>`);
        } else if (task.status === "PAUSED") {
            actions.push(`<button class="download-action-btn" type="button" data-action="resume" data-task-id="${escapeHtml(task.id)}">继续</button>`);
            actions.push(`<button class="download-action-btn danger" type="button" data-action="cancel" data-task-id="${escapeHtml(task.id)}">取消</button>`);
        } else if (task.status === "QUEUED") {
            actions.push(`<button class="download-action-btn danger" type="button" data-action="cancel" data-task-id="${escapeHtml(task.id)}">取消</button>`);
        }

        if (task.status === "FAILED" || task.status === "CANCELLED") {
            actions.push(`<button class="download-action-btn" type="button" data-action="retry" data-task-id="${escapeHtml(task.id)}">重试</button>`);
        }
        return actions.join("");
    }

    function proxiedImageUrl(url) {
        return proxyImageUrl(url);
    }

    function historyCoverUrl(task) {
        if (!task || (!task.pageUrl && !task.thumbnail)) return "";
        const params = new URLSearchParams();
        params.set("url", task.pageUrl || task.thumbnail || "");
        if (task.thumbnail) {
            params.set("thumbnail", task.thumbnail);
        }
        return `/api/proxy/history-cover?${params.toString()}`;
    }

    // 封面图片横竖检测
    window.setHistoryCoverOrientation = function(img) {
        const parent = img.parentElement;
        if (!parent) return;
        const isLandscape = img.naturalWidth > img.naturalHeight;
        img.className = 'download-history-thumb' + (isLandscape ? ' landscape' : ' portrait');
        parent.className = 'download-history-cover' + (isLandscape ? ' landscape' : ' portrait');
    };

    function renderHistoryPlaceholder() {
        return `<div class="download-history-thumb placeholder">No Cover</div>`;
    }

    function updateBrowseSelectionSummary() {
        browseSelectionCount.textContent = selectedBrowseItems.size;
    }

    function renderDownloadCenter() {
        const snapshot = normalizeSnapshot(downloadSnapshot);
        const liveTasks = [...snapshot.activeTasks, ...snapshot.queuedTasks];
        downloadBadge.textContent = liveTasks.length;
        downloadLiveCount.textContent = liveTasks.length;
        downloadHistoryCount.textContent = snapshot.historyTasks.length;
        if (retryAllFailedBtn) {
            const hasFailedOrCancelled = snapshot.historyTasks.some(task => task.status !== "COMPLETED");
            retryAllFailedBtn.disabled = !hasFailedOrCancelled;
        }
        if (clearDownloadHistoryBtn) {
            clearDownloadHistoryBtn.disabled = snapshot.historyTasks.length === 0;
        }
        if (pauseAllDownloadsBtn) {
            const hasPausableTasks = liveTasks.some(task => task.status === "PREPARING" || task.status === "DOWNLOADING" || task.status === "QUEUED");
            pauseAllDownloadsBtn.disabled = !hasPausableTasks;
        }
        if (cancelAllDownloadsBtn) {
            cancelAllDownloadsBtn.disabled = liveTasks.length === 0;
        }
        downloadCenterSummary.textContent = liveTasks.length > 0
            ? `当前有 ${liveTasks.length} 个任务正在执行或排队`
            : "实时查看任务队列、进度和历史记录";

        if (liveTasks.length === 0) {
            downloadQueueList.innerHTML = `<div class="download-empty">当前没有正在执行的下载任务</div>`;
        } else {
            downloadQueueList.innerHTML = liveTasks.map((task) => {
                const percent = Number(task.progressPercent || 0);
                const meta = task.status === "FAILED"
                    ? escapeHtml(task.errorMessage || "任务执行失败")
                    : `${percent.toFixed(0)}%`;
                return `
                    <article class="download-card ${String(task.status || "").toLowerCase()}">
                        <div class="download-card-head">
                            <h4>${escapeHtml(task.title || task.fileName || "未命名任务")}</h4>
                            <span class="download-status-badge">${formatStatus(task.status)}</span>
                        </div>
                        <div class="download-meta">${escapeHtml(meta)}</div>
                        <div class="progress-track">
                            <div class="progress-bar" style="width:${Math.max(0, Math.min(100, percent))}%;"></div>
                        </div>
                        <div class="download-actions">${taskActionButtons(task)}</div>
                    </article>
                `;
            }).join("");
        }

        if (snapshot.historyTasks.length === 0) {
            downloadHistoryList.innerHTML = `<div class="download-empty">尚未产生下载历史</div>`;
            return;
        }

        downloadHistoryList.innerHTML = snapshot.historyTasks.map((task) => {
            const title = escapeHtml(task.title || task.fileName || "未命名任务");
            const meta = escapeHtml(task.filePath || task.finishedAt || "等待执行");
            const pageUrl = escapeHtml(task.pageUrl || "");
            const clickableClass = task.pageUrl ? "is-clickable" : "";
            const coverUrl = historyCoverUrl(task);
            const fallbackCoverUrl = proxiedImageUrl(task.thumbnail);
            const cover = coverUrl
                ? `<img src="${coverUrl}" class="download-history-thumb" alt="cover" loading="lazy" onerror="this.style.display='none'" onload="setHistoryCoverOrientation(this)" data-fallback-src="${escapeHtml(fallbackCoverUrl)}">`
                : (fallbackCoverUrl
                    ? `<img src="${fallbackCoverUrl}" class="download-history-thumb" alt="cover" loading="lazy" onload="setHistoryCoverOrientation(this)">`
                    : renderHistoryPlaceholder());
            return `
            <article class="download-card history ${clickableClass} ${String(task.status || "").toLowerCase()}" data-page-url="${pageUrl}" tabindex="${task.pageUrl ? '0' : '-1'}">
                <div class="download-history-cover">
                    ${cover}
                </div>
                <div class="download-history-content">
                    <div class="download-card-head">
                        <h4 title="${title}">${title}</h4>
                        ${task.status === "COMPLETED"
                            ? `<span class="download-status-badge" style="color:#4ade80">已完成</span>`
                            : `<button class="download-action-btn" type="button" title="点击重新下载" data-action="retry" data-task-id="${escapeHtml(task.id)}">下载失败 - 重新下载</button>`}
                    </div>
                    <div class="download-meta" title="${meta}">${meta}</div>
                    <div class="download-actions">${taskActionButtons(task)}</div>
                </div>
            </article>
        `;
        }).join("");
        bindHistoryCardInteractions();
        bindHistoryCoverFallbacks();
    }

    function openHistoryTask(pageUrl) {
        if (!pageUrl) {
            return;
        }
        downloadCenterModal.classList.add("hidden");
        urlInput.value = pageUrl;
        switchView("viewParser", true);
        parseBtn.click();
    }

    function bindHistoryCardInteractions() {
        downloadHistoryList.querySelectorAll(".download-card.history.is-clickable").forEach((card) => {
            card.addEventListener("click", (event) => {
                if (event.target.closest("[data-action][data-task-id]")) {
                    return;
                }
                openHistoryTask(card.dataset.pageUrl);
            });
            card.addEventListener("keydown", (event) => {
                if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    openHistoryTask(card.dataset.pageUrl);
                }
            });
        });
    }

    function bindHistoryCoverFallbacks() {
        downloadHistoryList.querySelectorAll(".download-history-thumb[data-fallback-src]").forEach((image) => {
            image.addEventListener("error", () => {
                const fallbackSrc = image.dataset.fallbackSrc;
                if (fallbackSrc && image.dataset.fallbackTried !== "true") {
                    image.dataset.fallbackTried = "true";
                    image.src = fallbackSrc;
                    return;
                }
                image.replaceWith(createHistoryPlaceholderElement());
            });
        });
    }

    function createHistoryPlaceholderElement() {
        const placeholder = document.createElement("div");
        placeholder.className = "download-history-thumb placeholder";
        placeholder.textContent = "No Cover";
        return placeholder;
    }

    let snapshotFrameId = null;
    let lastSnapshotHash = "";
    function getStructureHash(snap) {
        const all = [...snap.activeTasks, ...snap.queuedTasks, ...snap.historyTasks];
        return all.map(t => t.id + "|" + t.status).join(",");
    }
    function applyDownloadSnapshot(snapshot) {
        const normalized = normalizeSnapshot(snapshot);
        const newHash = getStructureHash(normalized);
        const oldHash = lastSnapshotHash;
        downloadSnapshot = normalized;

        if (newHash !== oldHash) {
            lastSnapshotHash = newHash;
            if (snapshotFrameId) return;
            snapshotFrameId = requestAnimationFrame(() => {
                snapshotFrameId = null;
                if (!downloadCenterModal.classList.contains("hidden")) {
                    renderDownloadCenter();
                }
            });
        } else if (oldHash !== "" && !downloadCenterModal.classList.contains("hidden")) {
            updateDownloadProgress();
        }
    }
    function updateDownloadProgress() {
        const liveTasks = [...downloadSnapshot.activeTasks, ...downloadSnapshot.queuedTasks];
        const queueCards = downloadQueueList.querySelectorAll(".download-card");
        queueCards.forEach((card, index) => {
            const task = liveTasks[index];
            if (!task) return;
            const progressBar = card.querySelector(".progress-bar");
            if (progressBar) {
                progressBar.style.width = `${Math.max(0, Math.min(100, Number(task.progressPercent || 0)))}%`;
            }
            const meta = card.querySelector(".download-meta");
            if (meta && task.status !== "FAILED") {
                const percent = Number(task.progressPercent || 0);
                meta.textContent = task.status === "DOWNLOADING" || task.status === "PREPARING"
                    ? `${percent.toFixed(0)}%`
                    : meta.textContent;
            }
            const statusBadge = card.querySelector(".download-status-badge");
            if (statusBadge) {
                const newLabel = formatStatus(task.status);
                if (statusBadge.textContent !== newLabel) {
                    statusBadge.textContent = newLabel;
                }
            }
        });
    }

    async function fetchDownloadSnapshot() {
        try {
            const response = await fetch("/api/downloads");
            if (!response.ok) {
                return;
            }
            applyDownloadSnapshot(await response.json());
        } catch (error) {
            console.error("获取下载快照失败", error);
        }
    }

    function scheduleDownloadReconnect() {
        if (downloadReconnectTimer) {
            return;
        }
        downloadReconnectTimer = setTimeout(() => {
            downloadReconnectTimer = null;
            connectDownloadStream();
        }, 2000);
    }

    function connectDownloadStream() {
        if (downloadEventSource) {
            downloadEventSource.close();
        }

        downloadEventSource = new EventSource("/api/downloads/stream");
        downloadEventSource.addEventListener("snapshot", (event) => {
            try {
                applyDownloadSnapshot(JSON.parse(event.data));
            } catch (error) {
                console.error("解析下载快照失败", error);
            }
        });
        downloadEventSource.onerror = () => {
            if (downloadEventSource) {
                downloadEventSource.close();
                downloadEventSource = null;
            }
            scheduleDownloadReconnect();
        };
    }

    async function enqueueDownloadItems(items, successMessage) {
        if (!items || items.length === 0) {
            alert("请先选择要加入下载队列的项目");
            return;
        }

        const response = await fetch("/api/downloads", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ items })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText || "加入下载队列失败");
        }

        downloadCenterModal.classList.remove("hidden");
        if (successMessage) {
            log(successMessage, "info");
        }
    }

    async function performTaskAction(taskId, action) {
        const response = await fetch(`/api/downloads/${encodeURIComponent(taskId)}/${action}`, {
            method: "POST"
        });
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText || `任务${action}失败`);
        }
        applyDownloadSnapshot(await response.json());
    }

    async function performDownloadBulkAction(action) {
        const response = await fetch(`/api/downloads/${action}`, {
            method: "POST"
        });
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText || "批量操作失败");
        }
        applyDownloadSnapshot(await response.json());
    }

    async function clearDownloadHistory() {
        const response = await fetch("/api/downloads/history/clear", { method: "POST" });
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText || "清空下载历史失败");
        }
        // Also clear local image cache
        fetch("/api/settings/clear-cache", { method: "POST" }).catch(() => {});
    }

    function buildCurrentDownloadItem() {
        return {
            title: currentVideoData?.title || mainTitle.textContent || "未命名视频",
            pageUrl: urlInput.value.trim(),
            downloadUrl: currentRawVideoUrl || "",
            thumbnail: currentVideoData?.thumbnail || ""
        };
    }

    function buildSeriesDownloadItems() {
        const items = [];
        const seenUrls = new Set();

        if (urlInput.value.trim()) {
            const currentItem = buildCurrentDownloadItem();
            items.push(currentItem);
            seenUrls.add(currentItem.pageUrl);
        }

        currentPlaylistItems.forEach((item) => {
            if (!item?.url || seenUrls.has(item.url)) {
                return;
            }
            items.push({
                title: item.title || "未命名视频",
                pageUrl: item.url,
                downloadUrl: "",
                thumbnail: item.thumbnail || ""
            });
            seenUrls.add(item.url);
        });

        return items;
    }

    function updateSeriesDownloadButton() {
        const count = buildSeriesDownloadItems().length;
        downloadSeriesBtn.disabled = count <= 1;
        downloadSeriesBtn.textContent = count > 1 ? `一键下载系列 (${count})` : "一键下载系列";
    }

    function updatePlaylistPanelLayout() {
        if (!playlistSidebar) {
            return;
        }
        if (window.innerWidth <= 1024) {
            playlistSidebar.style.removeProperty("--playlist-max-height");
            return;
        }

        const visibleCount = Math.max(currentPlaylistItems.length, 1);
        const computedHeight = 180 + (Math.min(visibleCount, 4) * 96);
        const clampedHeight = Math.min(Math.max(computedHeight, 280), 560);
        playlistSidebar.style.setProperty("--playlist-max-height", `${clampedHeight}px`);
    }

    function renderRelatedVideoGrid(videos) {
        currentRelatedVideos = Array.isArray(videos) ? videos : [];
        relatedVideoCount.textContent = currentRelatedVideos.length;

        if (currentRelatedVideos.length === 0) {
            relatedVideoGrid.innerHTML = `<div class="empty-playlist">暂无相关视频</div>`;
            return;
        }

        relatedVideoGrid.innerHTML = "";
        currentRelatedVideos.forEach((item) => {
            const card = document.createElement("div");
            card.className = "grid-item related-grid-item";
            card.innerHTML = `
                <div class="grid-thumb-container">
                    <img src="${imageUrl(item.thumbnail)}" data-src-raw="${escapeHtml(item.thumbnail || "")}" onerror="fallbackImage(this)" loading="lazy" class="grid-thumb" alt="cover">
                </div>
                <div class="grid-title" title="${escapeHtml(item.title || "")}">${escapeHtml(item.title || "未命名视频")}</div>
            `;
            card.addEventListener("click", () => {
                urlInput.value = item.url;
                parseBtn.click();
                window.scrollTo({ top: 0, behavior: "smooth" });
            });
            relatedVideoGrid.appendChild(card);
        });

    }

    function renderCommentAvatar(comment, className = "comment-avatar") {
        const userName = comment?.userName || "?";
        if (comment?.avatarUrl) {
            return `<img class="${className}" src="${imageUrl(comment.avatarUrl)}" alt="avatar" loading="lazy">`;
        }
        return `<div class="${className} placeholder">${escapeHtml(userName.slice(0, 1))}</div>`;
    }

    function renderComments(comments = []) {
        const list = Array.isArray(comments) ? comments : [];
        if (!commentsList || !commentsCount) return;
        commentsCount.textContent = list.length;

        if (list.length === 0) {
            commentsList.innerHTML = `<div class="empty-playlist">暂无评论</div>`;
            return;
        }

        commentsList.innerHTML = list.map((comment) => {
            const commentId = escapeHtml(comment.commentId || "");
            const avatar = renderCommentAvatar(comment);
            const replyCount = Number(comment.replyCount || 0);
            const canLoadReplies = comment.commentId && (comment.hasReplies || replyCount > 0);
            return `
                <article class="comment-item" data-comment-id="${commentId}">
                    ${avatar}
                    <div class="comment-body">
                        <div class="comment-head">
                            <strong>${escapeHtml(comment.userName || "匿名用户")}</strong>
                            ${comment.timeText ? `<span>${escapeHtml(comment.timeText)}</span>` : ""}
                        </div>
                        <div class="comment-content">${escapeHtml(comment.content || "")}</div>
                        <div class="comment-actions">
                            ${comment.likeCount ? `<span>${escapeHtml(comment.likeCount)} 赞</span>` : ""}
                            ${canLoadReplies ? `<button class="comment-reply-btn" type="button" data-comment-id="${commentId}">查看回复${replyCount ? ` (${replyCount})` : ""}</button>` : ""}
                        </div>
                        <div class="comment-replies" data-replies-for="${commentId}"></div>
                    </div>
                </article>
            `;
        }).join("");
    }

    function renderReplies(commentId, replies = []) {
        const repliesBox = commentsList?.querySelector(`[data-replies-for="${CSS.escape(commentId)}"]`);
        if (!repliesBox) return;
        const list = Array.isArray(replies) ? replies : [];
        if (list.length === 0) {
            repliesBox.innerHTML = `<div class="comment-reply-empty">暂无回复</div>`;
            return;
        }
        repliesBox.innerHTML = list.map((reply) => {
            const replyAvatar = renderCommentAvatar({
                userName: reply.userName,
                avatarUrl: reply.avatarUrl
            }, "comment-reply-avatar");
            return `
                <div class="comment-reply-item">
                    ${replyAvatar}
                    <div class="comment-reply-body">
                        <strong>${escapeHtml(reply.userName || "匿名用户")}</strong>
                        <span>${escapeHtml(reply.content || "")}</span>
                    </div>
                </div>
            `;
        }).join("");
    }

    async function loadComments(videoId) {
        if (!commentsList || !commentsCount) return;
        if (!videoId) {
            commentsCount.textContent = "0";
            commentsList.innerHTML = `<div class="empty-playlist">未识别到视频 ID，无法载入评论</div>`;
            return;
        }

        commentsList.innerHTML = `<div class="empty-playlist">正在载入评论...</div>`;
        try {
            const response = await fetch(`/api/comments?videoId=${encodeURIComponent(videoId)}`);
            if (!response.ok) {
                throw new Error(await response.text() || "评论载入失败");
            }
            renderComments(await response.json());
        } catch (error) {
            commentsCount.textContent = "0";
            commentsList.innerHTML = `<div class="empty-playlist">评论载入失败: ${escapeHtml(error.message)}</div>`;
        }
    }

    async function loadReplies(commentId, button) {
        if (!commentId) return;
        const repliesBox = commentsList?.querySelector(`[data-replies-for="${CSS.escape(commentId)}"]`);
        if (repliesBox) {
            repliesBox.innerHTML = `<div class="comment-reply-empty">正在载入回复...</div>`;
        }
        if (button) button.disabled = true;
        try {
            const response = await fetch(`/api/replies?commentId=${encodeURIComponent(commentId)}`);
            if (!response.ok) {
                throw new Error(await response.text() || "回复载入失败");
            }
            renderReplies(commentId, await response.json());
        } catch (error) {
            if (repliesBox) {
                repliesBox.innerHTML = `<div class="comment-reply-empty">回复载入失败: ${escapeHtml(error.message)}</div>`;
            }
        } finally {
            if (button) button.disabled = false;
        }
    }

    function updateVideoAccountActions() {
        if (!currentVideoData) {
            [favoriteVideoBtn, watchLaterBtn, myListBtn, subscribeCreatorBtn].forEach(btn => {
                if (btn) btn.disabled = true;
            });
            return;
        }
        if (favoriteVideoBtn) {
            favoriteVideoBtn.disabled = false;
            favoriteVideoBtn.classList.toggle("selected-action", !!currentVideoData.isFav);
            favoriteVideoBtn.textContent = currentVideoData.isFav ? "已喜欢" : "喜欢";
        }
        if (watchLaterBtn) {
            const isWatchLater = !!currentVideoData.myList?.isWatchLater;
            watchLaterBtn.disabled = false;
            watchLaterBtn.classList.toggle("selected-action", isWatchLater);
            watchLaterBtn.textContent = isWatchLater ? "已稍后观看" : "稍后观看";
        }
        if (myListBtn) {
            myListBtn.disabled = !(currentVideoData.myList?.items || []).length;
        }
        if (subscribeCreatorBtn) {
            const post = currentVideoData.creator?.post;
            subscribeCreatorBtn.classList.toggle("hidden", !post);
            subscribeCreatorBtn.disabled = !post;
            subscribeCreatorBtn.textContent = post?.isSubscribed ? "已关注" : "关注";
            subscribeCreatorBtn.classList.toggle("selected-action", !!post?.isSubscribed);
        }
    }

    async function addCardToWatchLater(vid, button) {
        if (!requireLogin()) {
            log("用户未登录，跳过稍后观看操作", "warning");
            return;
        }
        button.disabled = true;
        const isAdded = watchLaterCardState.get(vid.url) || false;
        const newState = !isAdded;
        const payload = {
            videoId: videoIdFromUrl(vid.url),
            pageUrl: vid.url,
            isChecked: newState
        };
        log(`稍后观看操作: videoId=${payload.videoId}, pageUrl=${payload.pageUrl}, isChecked=${newState}`, "info");
        try {
            const result = await postJson("/api/video/watch-later", payload);
            log(`稍后观看操作成功: ${JSON.stringify(result)}`, "info");
            watchLaterCardState.set(vid.url, newState);
            button.textContent = newState ? "✓ 稍后" : "+ 稍后";
            button.classList.toggle("selected-action", newState);
        } catch (error) {
            log(`稍后观看操作失败: ${error.message}`, "error");
            alert(`稍后观看操作失败: ${error.message}`);
        } finally {
            button.disabled = false;
        }
    }

    async function recordCurrentWatchHistory() {
        if (!currentVideoData) return;
        try {
            await postJson("/api/watch-history/record", {
                videoId: currentVideoData.videoId || videoIdFromUrl(urlInput.value),
                title: currentVideoData.title || mainTitle.textContent || "未命名视频",
                pageUrl: urlInput.value,
                thumbnail: currentVideoData.thumbnail || ""
            });
        } catch (_error) {
            // Watching should not be blocked by local history persistence.
        }
    }

    function createProfileItemCard(item) {
        if (item.isCreator) {
            return createCreatorProfileCard(item);
        }
        const card = document.createElement("button");
        card.className = "profile-preview-card";
        card.type = "button";
        card.innerHTML = `
            <img src="${imageUrl(item.thumbnail || item.cover || "")}" data-src-raw="${escapeHtml(item.thumbnail || item.cover || "")}" onerror="fallbackImage(this)" loading="lazy" alt="cover">
            <div>${escapeHtml(item.title || item.name || "未命名内容")}</div>
        `;
        card.addEventListener("click", () => {
            const target = item.url || item.pageUrl || item.link;
            if (!target) return;
            if (target.includes("playlist?list=")) {
                const listId = new URL(target, window.location.href).searchParams.get("list");
                if (listId) loadBrowseCategory("playlist:" + listId, 1, true);
                return;
            }
            loadParserUrl(target, true, true);
        });
        return card;
    }

    function createCreatorProfileCard(item) {
        const card = document.createElement("button");
        card.className = "profile-preview-card creator-profile-card";
        card.type = "button";
        card.dataset.creatorKey = item.searchQuery || item.name || "";
        const initial = (item.name || "?").charAt(0).toUpperCase();
        const avatarHtml = item.avatarUrl
            ? `<img class="creator-avatar-img" src="${imageUrl(item.avatarUrl)}" data-src-raw="${escapeHtml(item.avatarUrl)}" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'" loading="lazy" alt="${escapeHtml(item.name || "")}"><span class="creator-avatar-initial" style="display:none">${escapeHtml(initial)}</span>`
            : `<span class="creator-avatar-initial">${escapeHtml(initial)}</span>`;
        card.innerHTML = `
            <div class="creator-avatar-wrap">${avatarHtml}</div>
            <div class="creator-card-name">${escapeHtml(item.name || "未知作者")}</div>
        `;
        card.addEventListener("click", () => {
            // Navigate to subscription detail view with this creator pre-selected
            loadSubscriptionDetailView(true, item.searchQuery || item.name || "");
        });
        return card;
    }

    async function loadProfileSummary(pushState = true) {
        if (!requireLogin()) return;
        switchView("viewProfile", false);
        if (pushState) history.pushState({ view: "viewProfile" }, "", "#profile");
        profileSectionDetail?.classList.add("hidden");
        subscriptionCreatorStrip?.classList.add("hidden");
        profilePageHeader?.classList.remove("hidden");

        // Fetch user info
        try {
            const response = await fetch("/api/auth/me");
            if (response.ok) {
                const user = await response.json();
                if (profilePageHeader && user.username) {
                    profilePageHeader.innerHTML = `
                        <img class="profile-page-avatar" src="${imageUrl(user.avatarUrl || "")}" alt="avatar">
                        <div><h1>${escapeHtml(user.username || "个人主页")}</h1><p>稍后观看、喜欢、播放清单、订阅与观看历史</p></div>
                    `;
                }
            }
        } catch (_error) {}

        // Render section frameworks immediately
        if (profileSections) {
            profileSections.innerHTML = "";
            const sections = ["watchLater", "likes", "playlists", "subscriptions", "histories"];
            const titles = { watchLater: "稍后观看", likes: "喜欢的影片", playlists: "播放清单", subscriptions: "我的订阅", histories: "浏览记录" };
            sections.forEach(section => {
                const row = document.createElement("section");
                row.className = "profile-section-row";
                row.id = `profile-section-${section}`;
                row.innerHTML = `
                    <button class="profile-section-heading" type="button">
                        <span>${escapeHtml(titles[section])}</span>
                        <span>查看全部</span>
                    </button>
                    <div class="profile-preview-row"></div>
                `;
                row.querySelector(".profile-section-heading").addEventListener("click", () => loadProfileSection(section, 1, true));
                profileSections.appendChild(row);
                // Load each section asynchronously
                loadProfileSectionPreview(section, row.querySelector(".profile-preview-row"));
            });
        }
    }

    async function loadProfileSectionPreview(section, container) {
        container.innerHTML = `<div class="empty-playlist">正在载入...</div>`;
        try {
            const response = await fetch(`/api/profile/section/${section}?page=1`);
            if (!response.ok) throw new Error("加载失败");
            const data = await response.json();
            container.innerHTML = "";
            const items = (data.items || []).slice(0, 6);
            if (items.length === 0) {
                container.innerHTML = `<div class="empty-playlist">暂无内容</div>`;
            } else {
                items.forEach(item => container.appendChild(createProfileItemCard(item)));
                // Lazy-fetch real avatars for subscription creators
                if (section === "subscriptions") {
                    items.filter(item => item.isCreator && !item.avatarUrl).forEach(item => {
                        const key = item.searchQuery || item.name || "";
                        if (!key) return;
                        const ep = item.userId
                            ? `/api/creator/info?userId=${encodeURIComponent(item.userId)}`
                            : `/api/creator/by-name?name=${encodeURIComponent(key)}`;
                        fetch(ep).then(r => r.ok ? r.json() : null).then(info => {
                            const av = info?.avatarUrl || info?.creatorAvatar || "";
                            if (!av) return;
                            const cardEl = container.querySelector(`[data-creator-key="${CSS.escape(key)}"]`);
                            if (cardEl && !cardEl.querySelector(".creator-avatar-img")) {
                                const wrap = cardEl.querySelector(".creator-avatar-wrap");
                                const initEl = cardEl.querySelector(".creator-avatar-initial");
                                if (wrap && initEl) {
                                    const img = document.createElement("img");
                                    img.className = "creator-avatar-img";
                                    img.src = imageUrl(av);
                                    img.loading = "lazy";
                                    img.alt = item.name || "";
                                    img.onerror = function() { this.style.display = "none"; initEl.style.display = "flex"; };
                                    initEl.style.display = "none";
                                    wrap.insertBefore(img, initEl);
                                }
                            }
                        }).catch(() => {});
                    });
                }
            }
        } catch (error) {
            container.innerHTML = `<div class="empty-playlist">加载失败: ${escapeHtml(error.message)}</div>`;
        }
    }


    async function loadProfileSection(section, page = 1, pushState = true) {
        if (section === "subscriptions") {
            loadSubscriptionDetailView(pushState);
            return;
        }
        activeProfileSection = section;
        activeProfilePage = page;
        switchView("viewProfile", false);
        if (pushState) history.pushState({ view: "viewProfile", section, page }, "", `#profile-${section}-${page}`);
        profileSections?.classList.add("hidden");
        profileSectionDetail?.classList.remove("hidden");
        subscriptionCreatorStrip?.classList.add("hidden");
        profilePageHeader?.classList.add("hidden");
        if (profilePaginationBar) profilePaginationBar.classList.remove("hidden");
        if (profileSectionGrid) profileSectionGrid.innerHTML = `<div class="empty-playlist">正在载入...</div>`;
        const response = await fetch(`/api/profile/section/${encodeURIComponent(section)}?page=${page}`);
        if (!response.ok) {
            if (profileSectionGrid) profileSectionGrid.innerHTML = `<div class="empty-playlist">${escapeHtml(await response.text() || "载入失败")}</div>`;
            return;
        }
        const data = await response.json();
        activeProfileTotalPages = Number(data.totalPages || 1);
        if (profileSectionTitle) profileSectionTitle.textContent = data.title || section;
        if (profilePageIndicator) profilePageIndicator.textContent = `${page} / ${activeProfileTotalPages}`;
        if (profilePrevPageBtn) profilePrevPageBtn.disabled = page <= 1;
        if (profileNextPageBtn) profileNextPageBtn.disabled = page >= activeProfileTotalPages;
        if (profileSectionGrid) {
            profileSectionGrid.innerHTML = "";
            (data.items || []).forEach(item => profileSectionGrid.appendChild(createProfileItemCard(item)));
            if (!(data.items || []).length) profileSectionGrid.innerHTML = `<div class="empty-playlist">暂无内容</div>`;
        }
    }

    async function loadSubscriptionDetailView(pushState = true, preSelectKey = null) {
        activeProfileSection = "subscriptions";
        activeProfilePage = 1;
        switchView("viewProfile", false);
        if (pushState) history.pushState({ view: "viewProfile", section: "subscriptions", page: 1 }, "", "#profile-subscriptions-1");
        profileSections?.classList.add("hidden");
        profileSectionDetail?.classList.remove("hidden");
        profilePageHeader?.classList.add("hidden");
        if (profileSectionTitle) profileSectionTitle.textContent = "我的订阅";
        if (profilePaginationBar) profilePaginationBar.classList.add("hidden");
        if (subscriptionCreatorStrip) subscriptionCreatorStrip.classList.remove("hidden");

        // Show cached creators immediately for instant display
        const cachedCreators = lsGet(LS_SUB_CREATORS_KEY);
        if (cachedCreators && cachedCreators.length > 0) {
            renderSubscriptionCreatorStrip(cachedCreators, preSelectKey);
            const target = preSelectKey
                ? (cachedCreators.find(c => (c.searchQuery || c.name) === preSelectKey) || cachedCreators[0])
                : cachedCreators[0];
            if (profileSectionGrid) profileSectionGrid.innerHTML = `<div class="empty-playlist">请在上方选择作者查看作品</div>`;
            if (target) loadSubscriptionCreatorVideos(target);
        } else {
            if (subscriptionCreatorStrip) subscriptionCreatorStrip.innerHTML = `<div class="empty-playlist" style="width:100%">正在载入作者...</div>`;
            if (profileSectionGrid) profileSectionGrid.innerHTML = `<div class="empty-playlist">请在上方选择作者查看作品</div>`;
        }

        // Background fetch to refresh
        try {
            const resp = await fetch("/api/profile/section/subscriptions?page=1");
            if (!resp.ok) throw new Error(await resp.text() || "载入失败");
            const data = await resp.json();
            let creators = [...(data.items || [])];
            const totalPages = Number(data.totalPages || 1);

            if (totalPages > 1) {
                for (let p = 2; p <= totalPages; p++) {
                    const r = await fetch(`/api/profile/section/subscriptions?page=${p}`);
                    if (r.ok) {
                        const d = await r.json();
                        (d.items || []).forEach(c => {
                            if (!creators.some(e => (e.searchQuery || e.name) === (c.searchQuery || c.name))) {
                                creators.push(c);
                            }
                        });
                    }
                }
            }

            lsSet(LS_SUB_CREATORS_KEY, creators);

            // Only re-render if no cached version was shown; otherwise silently update avatars
            if (!cachedCreators) {
                renderSubscriptionCreatorStrip(creators, preSelectKey);
                const target = preSelectKey
                    ? (creators.find(c => (c.searchQuery || c.name) === preSelectKey) || creators[0])
                    : creators[0];
                if (target) loadSubscriptionCreatorVideos(target);
            } else {
                updateSubscriptionCreatorAvatars(creators);
            }
        } catch (err) {
            if (!cachedCreators && subscriptionCreatorStrip) {
                subscriptionCreatorStrip.innerHTML = `<div class="empty-playlist" style="width:100%">载入失败: ${escapeHtml(err.message)}</div>`;
            }
        }
    }

    function updateSubscriptionCreatorAvatars(freshCreators) {
        if (!subscriptionCreatorStrip) return;
        freshCreators.forEach(creator => {
            if (!creator.avatarUrl) return;
            const key = creator.searchQuery || creator.name || "";
            const chip = subscriptionCreatorStrip.querySelector(`[data-search-query="${CSS.escape(key)}"]`);
            if (!chip) return;
            const existing = chip.querySelector(".sub-creator-chip-avatar");
            if (existing) return; // Already has avatar image
            const initial = chip.querySelector(".sub-creator-chip-initial");
            if (!initial) return;
            const img = document.createElement("img");
            img.className = "sub-creator-chip-avatar";
            img.src = imageUrl(creator.avatarUrl);
            img.loading = "lazy";
            img.alt = escapeHtml(creator.name || "");
            img.onerror = () => { img.style.display = "none"; initial.style.display = "flex"; };
            chip.insertBefore(img, initial);
            initial.style.display = "none";
        });
    }

    function renderSubscriptionCreatorStrip(creators, selectedQuery) {
        if (!subscriptionCreatorStrip) return;
        const currentActive = selectedQuery ?? subscriptionCreatorStrip.querySelector(".sub-creator-chip.active")?.dataset.searchQuery ?? null;
        subscriptionCreatorStrip.innerHTML = "";
        creators.forEach(creator => {
            const isActive = (creator.searchQuery || creator.name) === currentActive;
            const chip = document.createElement("button");
            chip.type = "button";
            chip.className = "sub-creator-chip" + (isActive ? " active" : "");
            chip.dataset.searchQuery = creator.searchQuery || creator.name || "";
            const initial = (creator.name || "?").charAt(0).toUpperCase();
            const buildAvatarHtml = (avatarUrl) => avatarUrl
                ? `<img class="sub-creator-chip-avatar" src="${imageUrl(avatarUrl)}" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'" loading="lazy" alt="${escapeHtml(creator.name || "")}"><span class="sub-creator-chip-initial" style="display:none">${escapeHtml(initial)}</span>`
                : `<span class="sub-creator-chip-initial">${escapeHtml(initial)}</span>`;
            chip.innerHTML = `${buildAvatarHtml(creator.avatarUrl)}<span class="sub-creator-chip-name">${escapeHtml(creator.name || "未知")}</span>`;
            chip.addEventListener("click", () => loadSubscriptionCreatorVideos(creator));
            subscriptionCreatorStrip.appendChild(chip);

            // Lazily fetch avatar if not yet available
            if (!creator.avatarUrl) {
                const endpoint = creator.userId
                    ? `/api/creator/info?userId=${encodeURIComponent(creator.userId)}`
                    : `/api/creator/by-name?name=${encodeURIComponent(creator.searchQuery || creator.name || "")}`;
                fetch(endpoint)
                    .then(r => r.ok ? r.json() : null)
                    .then(info => {
                        const av = info?.avatarUrl || info?.creatorAvatar || "";
                        if (av) {
                            creator.avatarUrl = av;
                            if (info?.creatorId) creator.userId = info.creatorId;
                            _applyChipAvatar(creator.searchQuery || creator.name || "", av, creator.name || "");
                            // Persist updated avatar in localStorage cache
                            const cached = lsGet(LS_SUB_CREATORS_KEY);
                            if (cached) {
                                const key = creator.searchQuery || creator.name || "";
                                const idx = cached.findIndex(c => (c.searchQuery || c.name) === key);
                                if (idx >= 0) { cached[idx].avatarUrl = av; lsSet(LS_SUB_CREATORS_KEY, cached); }
                            }
                        }
                    })
                    .catch(() => {});
            }
        });
    }

    async function loadSubscriptionCreatorVideos(creator) {
        const creatorKey = creator.searchQuery || creator.name || "";
        subscriptionCreatorStrip?.querySelectorAll(".sub-creator-chip").forEach(c => {
            c.classList.toggle("active", c.dataset.searchQuery === creatorKey);
        });
        if (!profileSectionGrid) return;
        profileSectionGrid.innerHTML = `<div class="empty-playlist">正在载入 ${escapeHtml(creator.name || "")} 的作品...</div>`;
        try {
            const category = creator.userId
                ? `user:${creator.userId}`
                : creator.searchQuery
                    ? `query:${creator.searchQuery}`
                    : null;
            if (!category) {
                profileSectionGrid.innerHTML = `<div class="empty-playlist">无法获取该作者作品</div>`;
                return;
            }
            const resp = await fetch(`/api/browse?category=${encodeURIComponent(category)}&page=1`);
            if (!resp.ok) throw new Error(await resp.text() || "载入失败");
            const data = await resp.json();

            // Update chip avatar if browse result has creator info
            if (data.creatorAvatar && !creator.avatarUrl) {
                creator.avatarUrl = data.creatorAvatar;
                if (data.creatorId) creator.userId = data.creatorId;
                _applyChipAvatar(creatorKey, data.creatorAvatar, creator.name || "");
                // Persist updated creator list
                const cached = lsGet(LS_SUB_CREATORS_KEY);
                if (cached) {
                    const idx = cached.findIndex(c => (c.searchQuery || c.name) === creatorKey);
                    if (idx >= 0) {
                        cached[idx].avatarUrl = data.creatorAvatar;
                        if (data.creatorId) cached[idx].userId = data.creatorId;
                        lsSet(LS_SUB_CREATORS_KEY, cached);
                    }
                }
            }

            profileSectionGrid.innerHTML = "";
            profileSectionGrid.className = "profile-preview-row";
            const items = data.videos || data.items || [];
            if (!items.length) {
                profileSectionGrid.innerHTML = `<div class="empty-playlist">暂无作品</div>`;
                return;
            }
            items.forEach(item => {
                const card = document.createElement("button");
                card.className = "profile-preview-card";
                card.type = "button";
                card.innerHTML = `
                    <img src="${imageUrl(item.thumbnail || item.cover || "")}" onerror="fallbackImage(this)" loading="lazy" alt="cover">
                    <div>${escapeHtml(item.title || item.name || "未命名")}</div>
                `;
                card.addEventListener("click", () => {
                    const target = item.url || item.pageUrl || item.link;
                    if (target) loadParserUrl(target, true, true);
                });
                profileSectionGrid.appendChild(card);
            });
        } catch (err) {
            profileSectionGrid.innerHTML = `<div class="empty-playlist">载入失败: ${escapeHtml(err.message)}</div>`;
        }
    }

    function _applyChipAvatar(creatorKey, avatarUrl, name) {
        if (!subscriptionCreatorStrip || !avatarUrl) return;
        const chip = subscriptionCreatorStrip.querySelector(`[data-search-query="${CSS.escape(creatorKey)}"]`);
        if (!chip || chip.querySelector(".sub-creator-chip-avatar")) return;
        const initial = chip.querySelector(".sub-creator-chip-initial");
        if (!initial) return;
        const img = document.createElement("img");
        img.className = "sub-creator-chip-avatar";
        img.src = imageUrl(avatarUrl);
        img.loading = "lazy";
        img.alt = name;
        img.onerror = () => { img.style.display = "none"; initial.style.display = "flex"; };
        chip.insertBefore(img, initial);
        initial.style.display = "none";
    }

    function setDetailTab(tabName) {
        const activeTab = tabName === "comments" ? "comments" : "related";
        document.querySelectorAll("[data-detail-tab]").forEach((button) => {
            button.classList.toggle("active", button.dataset.detailTab === activeTab);
        });
        [detailPanelRelated, detailPanelComments].forEach((panel) => {
            if (!panel) return;
            const isActive = panel.dataset.detailPanel === activeTab;
            panel.classList.toggle("active", isActive);
            panel.classList.toggle("hidden", !isActive);
        });
    }

    // ---- Navigation / SPA Routing ----
    function switchView(viewId, pushState = true) {
        if (currentView === "viewBrowse" && viewId !== "viewBrowse") {
            rememberCurrentPageScroll();
        }
        currentView = viewId;
        viewLanding.classList.add("hidden");
        viewBrowse.classList.add("hidden");
        viewParser.classList.add("hidden");
        if (viewProfile) viewProfile.classList.add("hidden");

        document.getElementById(viewId).classList.remove("hidden");
        
        // cleanup player if switching away from parser
        if (viewId !== "viewParser" && hlsInstance) {
            hlsInstance.destroy();
            videoPlayer.pause();
        }

        if (pushState) {
            history.pushState({ view: viewId }, "", `#${viewId}`);
        }
    }

    // Handle Browser Back/Forward buttons
    window.addEventListener("popstate", (event) => {
        if (event.state) {
            handleStateRestore(event.state);
        } else {
            switchView('viewLanding', false);
        }
    });

    function handleStateRestore(state) {
        if (state.view) {
            switchView(state.view, false);
            if (state.view === "viewBrowse" && state.search) {
                currentSearchState = normalizeSearchState(state.filters || {});
                if (globalSearchInput) {
                    globalSearchInput.value = currentSearchState.query;
                }
                loadSearchResults(state.page || 1, false);
            } else if (state.view === "viewBrowse" && state.category) {
                loadBrowseCategory(state.category, state.page || 1, false);
                const liToActivate = document.querySelector(`#categoryList li[data-cat="${state.category}"]`);
                if(liToActivate) {
                    document.querySelectorAll("#categoryList li").forEach(i => i.classList.remove("active"));
                    liToActivate.classList.add("active");
                }
            } else if (state.view === "viewParser" && state.url) {
                loadParserUrl(state.url, false, true);
            } else if (state.view === "viewProfile" && state.section) {
                loadProfileSection(state.section, state.page || 1, false);
            } else if (state.view === "viewProfile") {
                loadProfileSummary(false);
            }
        }
    }

    navLogo.addEventListener("click", () => switchView("viewLanding"));
    modeBrowseBtn.addEventListener("click", () => switchView("viewBrowse"));
    modeParseBtn.addEventListener("click", () => switchView("viewParser"));
    if (globalSearchExpandBtn) {
        globalSearchExpandBtn.addEventListener("click", () => expandGlobalSearch(true));
    }
    if (globalSearchInput) {
        globalSearchInput.addEventListener("focus", () => expandGlobalSearch(false));
        globalSearchInput.addEventListener("input", syncGlobalSearchChrome);
        globalSearchInput.addEventListener("blur", collapseGlobalSearchIfIdle);
        globalSearchInput.addEventListener("keydown", (event) => {
            if (event.key === "Enter") {
                event.preventDefault();
                updateSearchStateFromGlobalControls();
                loadSearchResults(1, true);
            } else if (event.key === "Escape") {
                event.preventDefault();
                globalSearchInput.blur();
                collapseGlobalSearchIfIdle();
            }
        });
    }
    if (globalSearchTypeSelect) {
        globalSearchTypeSelect.addEventListener("focus", () => expandGlobalSearch(false));
        globalSearchTypeSelect.addEventListener("change", () => {
            updateSearchStateFromGlobalControls();
            expandGlobalSearch(false);
        });
    }
    if (globalSearchSubmitBtn) {
        globalSearchSubmitBtn.addEventListener("click", () => {
            updateSearchStateFromGlobalControls();
            loadSearchResults(1, true);
        });
    }
    if (globalFilterBtn) {
        globalFilterBtn.addEventListener("click", openSearchFilterModal);
    }
    if (browseSearchInput) {
        browseSearchInput.addEventListener("keydown", (event) => {
            if (event.key === "Enter") {
                event.preventDefault();
                updateSearchStateFromBrowseControls();
                loadSearchResults(1, true);
            }
        });
    }
    [browseSearchTypeSelect, browseSearchSortSelect, browseSearchDateSelect, browseSearchDurationSelect].forEach((control) => {
        if (!control) return;
        control.addEventListener("change", updateSearchStateFromBrowseControls);
    });
    if (browseSearchSubmitBtn) {
        browseSearchSubmitBtn.addEventListener("click", () => {
            updateSearchStateFromBrowseControls();
            loadSearchResults(1, true);
        });
    }
    if (browseSearchTagBtn) {
        browseSearchTagBtn.addEventListener("click", openSearchFilterModal);
    }
    document.addEventListener("keydown", (event) => {
        if (event.key === "/" && !event.ctrlKey && !event.metaKey && !event.altKey && !event.target.closest("input, textarea, select")) {
            event.preventDefault();
            expandGlobalSearch(true);
        }
        if (event.key === "Escape" && searchFilterModal && !searchFilterModal.classList.contains("hidden")) {
            searchFilterModal.classList.add("hidden");
        }
    });
    downloadCenterBtn.addEventListener("click", () => {
        downloadCenterModal.classList.remove("hidden");
        renderDownloadCenter();
    });
    closeDownloadCenterBtn.addEventListener("click", () => downloadCenterModal.classList.add("hidden"));
    downloadCenterModal.addEventListener("click", (event) => {
        if (event.target === downloadCenterModal) {
            downloadCenterModal.classList.add("hidden");
        }
    });
    if (closeSearchFilterBtn) {
        closeSearchFilterBtn.addEventListener("click", () => searchFilterModal.classList.add("hidden"));
    }
    if (searchFilterModal) {
        searchFilterModal.addEventListener("click", (event) => {
            if (event.target === searchFilterModal) {
                searchFilterModal.classList.add("hidden");
            }
            const tagButton = event.target.closest(".search-tag-chip[data-tag]");
            if (tagButton) {
                const tag = tagButton.dataset.tag;
                const tags = new Set(currentSearchState.tags || []);
                if (tags.has(tag)) {
                    tags.delete(tag);
                } else {
                    tags.add(tag);
                }
                currentSearchState = normalizeSearchState({ ...currentSearchState, tags: Array.from(tags) });
                tagButton.classList.toggle("active", tags.has(tag));
                syncSearchTypeControls();
                syncGlobalSearchChrome();
            }
        });
    }
    if (resetSearchFiltersBtn) {
        resetSearchFiltersBtn.addEventListener("click", () => {
            currentSearchState = normalizeSearchState({
                query: browseSearchInput?.value || globalSearchInput?.value || ""
            });
            syncSearchFilterControls();
            renderSearchTags(searchOptions?.tagGroups || []);
            syncGlobalSearchChrome();
        });
    }
    if (applySearchFiltersBtn) {
        applySearchFiltersBtn.addEventListener("click", () => {
            readSearchFiltersFromModal();
            searchFilterModal.classList.add("hidden");
            syncGlobalSearchChrome();
            loadSearchResults(1, true);
        });
    }
    downloadCenterModal.addEventListener("click", async (event) => {
        const actionButton = event.target.closest("[data-action][data-task-id]");
        if (!actionButton) {
            return;
        }
        event.preventDefault();
        event.stopPropagation();

        try {
            actionButton.disabled = true;
            await performTaskAction(actionButton.dataset.taskId, actionButton.dataset.action);
        } catch (error) {
            alert(`任务操作失败: ${error.message}`);
        } finally {
            actionButton.disabled = false;
        }
    });
    if (clearDownloadHistoryBtn) {
        clearDownloadHistoryBtn.addEventListener("click", async (event) => {
            event.preventDefault();
            event.stopPropagation();
            if (downloadSnapshot.historyTasks.length === 0) {
                return;
            }
            if (!confirm("确定要清空下载历史吗？正在进行或排队的任务不会受影响。")) {
                return;
            }

            try {
                clearDownloadHistoryBtn.disabled = true;
                await clearDownloadHistory();
            } catch (error) {
                alert(`清空历史失败: ${error.message}`);
            } finally {
                clearDownloadHistoryBtn.disabled = false;
            }
        });
    }
    if (pauseAllDownloadsBtn) {
        pauseAllDownloadsBtn.addEventListener("click", async (event) => {
            event.preventDefault();
            event.stopPropagation();
            const liveTasks = [...downloadSnapshot.activeTasks, ...downloadSnapshot.queuedTasks];
            if (liveTasks.length === 0) {
                return;
            }

            try {
                pauseAllDownloadsBtn.disabled = true;
                await performDownloadBulkAction("pause-all");
            } catch (error) {
                alert(`全部暂停失败: ${error.message}`);
            } finally {
                pauseAllDownloadsBtn.disabled = false;
                renderDownloadCenter();
            }
        });
    }
    if (cancelAllDownloadsBtn) {
        cancelAllDownloadsBtn.addEventListener("click", async (event) => {
            event.preventDefault();
            event.stopPropagation();
            const liveTasks = [...downloadSnapshot.activeTasks, ...downloadSnapshot.queuedTasks];
            if (liveTasks.length === 0) {
                return;
            }
            if (!confirm("确定要取消所有正在进行和排队的下载吗？已完成历史不会被清除。")) {
                return;
            }

            try {
                cancelAllDownloadsBtn.disabled = true;
                await performDownloadBulkAction("cancel-all");
            } catch (error) {
                alert(`全部取消失败: ${error.message}`);
            } finally {
                cancelAllDownloadsBtn.disabled = false;
                renderDownloadCenter();
            }
        });
    }
    if (retryAllFailedBtn && downloadCenterModal) {
        downloadCenterModal.addEventListener("click", async (event) => {
            const retryBtn = event.target.closest("#retryAllFailedBtn");
            if (!retryBtn) return;
            event.preventDefault();
            event.stopPropagation();
            const historyTasks = downloadSnapshot?.historyTasks || [];
            const failedTasks = historyTasks.filter(task => task.status !== "COMPLETED");
            if (failedTasks.length === 0 || !confirm(`确定要重试所有 ${failedTasks.length} 个失败或已取消的下载任务吗？`)) {
                return;
            }
            try {
                retryAllFailedBtn.disabled = true;
                await performDownloadBulkAction("retry-all-failed");
            } catch (error) {
                alert(`全部重试失败: ${error.message}`);
            } finally {
                retryAllFailedBtn.disabled = false;
                renderDownloadCenter();
            }
        });
    }
    downloadHistoryList.addEventListener("click", (event) => {
        if (event.target.closest("[data-action][data-task-id]")) {
            return;
        }
        const card = event.target.closest(".download-card.history.is-clickable");
        if (!card) {
            return;
        }
        const pageUrl = card.dataset.pageUrl;
        if (!pageUrl) {
            return;
        }
        openHistoryTask(pageUrl);
    });

    // ---- Login ----
    const loginBtn = document.getElementById("loginBtn");
    const loginModal = document.getElementById("loginModal");
    const closeLoginBtn = document.getElementById("closeLoginBtn");
    const closeLoginBtn2 = document.getElementById("closeLoginBtn2");
    const submitLoginBtn = document.getElementById("submitLoginBtn");
    const logoutBtn = document.getElementById("logoutBtn");
    const loginForm = document.getElementById("loginForm");
    const loggedInPanel = document.getElementById("loggedInPanel");
    const loginError = document.getElementById("loginError");
    const loginModalTitle = document.getElementById("loginModalTitle");

    let isLoggedIn = false;

    async function refreshLoginStatus() {
        await refreshAuthState();
        isLoggedIn = !!authState.loggedIn;
        loginBtn.title = isLoggedIn ? "已登录（点击查看）" : "登录账号";
        loginBtn.textContent = isLoggedIn ? "✅" : "👤";
    }

    function openLoginModal() {
        loginError.style.display = "none";
        loginError.textContent = "";
        if (isLoggedIn) {
            loginModalTitle.textContent = "✅ 已登录";
            loginForm.style.display = "none";
            loggedInPanel.style.display = "block";
        } else {
            loginModalTitle.textContent = "👤 登录账号";
            loginForm.style.display = "block";
            loggedInPanel.style.display = "none";
        }
        loginModal.classList.remove("hidden");
    }

    loginBtn.addEventListener("click", openLoginModal);
    authUserBtn?.addEventListener("click", () => {
        if (authState.loggedIn) {
            loadProfileSummary(true);
        } else {
            openLoginModal();
        }
    });
    closeLoginBtn.addEventListener("click", () => loginModal.classList.add("hidden"));
    closeLoginBtn2.addEventListener("click", () => loginModal.classList.add("hidden"));
    loginModal.addEventListener("click", (e) => { if (e.target === loginModal) loginModal.classList.add("hidden"); });

    submitLoginBtn.addEventListener("click", async () => {
        const email = document.getElementById("loginEmail").value.trim();
        const password = document.getElementById("loginPassword").value;
        if (!email || !password) {
            loginError.textContent = "邮箱和密码不能为空";
            loginError.style.display = "block";
            return;
        }
        submitLoginBtn.disabled = true;
        submitLoginBtn.textContent = "登录中…";
        loginError.style.display = "none";
        try {
            const res = await fetch("/api/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });
            const text = await res.text();
            if (res.ok) {
                await refreshLoginStatus();
                loginBtn.textContent = "✅";
                loginBtn.title = "已登录（点击查看）";
                loginModalTitle.textContent = "✅ 已登录";
                loginForm.style.display = "none";
                loggedInPanel.style.display = "block";
            } else {
                loginError.textContent = text || "登录失败，请检查账号和密码";
                loginError.style.display = "block";
            }
        } catch (err) {
            loginError.textContent = "网络错误：" + err.message;
            loginError.style.display = "block";
        } finally {
            submitLoginBtn.disabled = false;
            submitLoginBtn.textContent = "🔑 登录";
        }
    });

    document.getElementById("loginPassword").addEventListener("keydown", (e) => {
        if (e.key === "Enter") submitLoginBtn.click();
    });

    logoutBtn.addEventListener("click", async () => {
        logoutBtn.disabled = true;
        try {
            await fetch("/api/logout", { method: "POST" });
            await fetch("/api/auth/logout", { method: "POST" });
            authState = { loggedIn: false, username: "", avatarUrl: "", userId: "" };
            isLoggedIn = false;
            syncAuthHeader();
            loginBtn.textContent = "👤";
            loginBtn.title = "登录账号";
            loginModal.classList.add("hidden");
        } finally {
            logoutBtn.disabled = false;
        }
    });

    refreshLoginStatus();

    // Auto-collapse log panel on startup
    if (statusPanelWrapper) statusPanelWrapper.classList.add("collapsed");

    profileBackBtn?.addEventListener("click", () => {
        profileSectionDetail?.classList.add("hidden");
        subscriptionCreatorStrip?.classList.add("hidden");
        if (profilePaginationBar) profilePaginationBar.classList.remove("hidden");
        profileSections?.classList.remove("hidden");
        profilePageHeader?.classList.remove("hidden");
    });
    profilePrevPageBtn?.addEventListener("click", () => {
        if (activeProfileSection && activeProfilePage > 1) {
            loadProfileSection(activeProfileSection, activeProfilePage - 1, true);
        }
    });
    profileNextPageBtn?.addEventListener("click", () => {
        if (activeProfileSection && activeProfilePage < activeProfileTotalPages) {
            loadProfileSection(activeProfileSection, activeProfilePage + 1, true);
        }
    });

    // ---- Settings API ----
    settingsBtn.addEventListener("click", async () => {
        settingsModal.classList.remove("hidden");
        updatePageCacheStatus();
        updateCookieStatus();

        // fetch current settings
        try {
            const res = await fetch("/api/settings");
            const data = await res.json();
            downloadDirInput.value = data.downloadDirectory || "";
            if (maxConcurrentDownloadsInput) {
                maxConcurrentDownloadsInput.value = data.maxConcurrentDownloads || 3;
            }
            if (pageCacheLimitInput) {
                pageCacheLimitInput.value = applyPageCacheLimit(data.pageCacheLimit || 20);
            }
            if (gopeedHostInput) {
                gopeedHostInput.value = data.gopeedHost || "127.0.0.1";
            }
            if (gopeedPortInput) {
                gopeedPortInput.value = data.gopeedPort || 9999;
            }
            if (gopeedTokenInput) {
                gopeedTokenInput.value = data.gopeedToken || "";
            }
            if (gopeedConnectionsInput) {
                gopeedConnectionsInput.value = data.gopeedConnections || 16;
            }
            if (maxLocalCacheSizeGBInput) {
                maxLocalCacheSizeGBInput.value = data.maxLocalCacheSizeGB ?? 5;
            }
            shortcutBack = normalizeShortcut(data.shortcutBack, "Alt+ArrowLeft");
            shortcutForward = normalizeShortcut(data.shortcutForward, "Alt+ArrowRight");
            if (shortcutBackInput) shortcutBackInput.value = shortcutBack;
            if (shortcutForwardInput) shortcutForwardInput.value = shortcutForward;
        } catch (e) {
            console.error("Failed to load settings");
        }
    });

    // Clear Cache
    const clearCacheBtn = document.getElementById('clearCacheBtn');
    if (clearCacheBtn) {
        clearCacheBtn.addEventListener('click', async () => {
            if (!confirm('确定要清除本地缓存吗？这会清除页面缓存和 HTTP 抓取缓存，下载历史会保留。')) return;
            
            clearCacheBtn.disabled = true;
            clearCacheBtn.innerText = '🧹 正在清理...';
            
            try {
                const res = await fetch('/api/settings/clear-cache', { method: 'POST' });
                if (res.ok) {
                    alert('本地缓存清理成功。');
                } else {
                    const err = await res.text();
                    alert('清理失败: ' + err);
                }
            } catch (e) {
                alert('网络错误: ' + e.message);
            } finally {
                clearCacheBtn.disabled = false;
                clearCacheBtn.innerText = '🧹 清除本地缓存';
            }
        });
    }

    const refreshCookieBtn = document.getElementById("refreshCookieBtn");
    if (refreshCookieBtn) {
        refreshCookieBtn.addEventListener("click", async () => {
            refreshCookieBtn.disabled = true;
            updateCookieStatus("正在打开浏览器抓取 Cookie...");
            try {
                const response = await fetch("/api/cookies/refresh", { method: "POST" });
                if (!response.ok) {
                    throw new Error(await response.text() || "Cookie 刷新失败");
                }
                const data = await response.json();
                updateCookieStatus(data.valid ? "Cookie 已刷新并验证通过" : "Cookie 已刷新，但 HTTP 验证仍失败");
            } catch (error) {
                updateCookieStatus(`Cookie 刷新失败: ${error.message}`);
            } finally {
                refreshCookieBtn.disabled = false;
            }
        });
    }

    // 检查更新
    const checkUpdateBtn = document.getElementById("checkUpdateBtn");
    const updateResult = document.getElementById("updateResult");
    if (checkUpdateBtn && updateResult) {
        checkUpdateBtn.addEventListener("click", async () => {
            checkUpdateBtn.disabled = true;
            updateResult.textContent = "检查中...";
            updateResult.style.color = "var(--text-muted)";
            try {
                const resp = await fetch("/api/check-update");
                if (!resp.ok) {
                    updateResult.textContent = "检查失败: HTTP " + resp.status;
                    updateResult.style.color = "#ff6b6b";
                    return;
                }
                const data = await resp.json();
                if (data.error) {
                    updateResult.textContent = "检查失败: " + data.error;
                    updateResult.style.color = "#ff6b6b";
                    return;
                }
                if (data.hasUpdate) {
                    updateResult.innerHTML = "发现新版本 <b>v" + escapeHtml(data.latestVersion) + "</b>！"
                        + (data.downloadUrl
                            ? ' <a href="' + escapeHtml(data.downloadUrl) + '" target="_blank" style="color:#6bc5ff">前往下载</a>'
                            : "");
                    updateResult.style.color = "#4ade80";
                } else {
                    updateResult.innerHTML = "已是最新版本 (v" + escapeHtml(data.currentVersion) + ")";
                    updateResult.style.color = "var(--text-muted)";
                }
            } catch (err) {
                updateResult.textContent = "网络错误: " + err.message;
                updateResult.style.color = "#ff6b6b";
            } finally {
                checkUpdateBtn.disabled = false;
            }
        });
    }

    closeSettingsBtn.addEventListener("click", () => settingsModal.classList.add("hidden"));
    settingsModal.addEventListener("click", (event) => {
        if (event.target === settingsModal) {
            settingsModal.classList.add("hidden");
        }
    });

    saveSettingsBtn.addEventListener("click", async () => {
        const downloadDirectory = downloadDirInput.value.trim();
        if (!downloadDirectory) return alert("下载目录不能为空");
        
        const maxConcurrentDownloads = Number.parseInt(maxConcurrentDownloadsInput?.value || "3", 10);
        if (!Number.isInteger(maxConcurrentDownloads) || maxConcurrentDownloads < 1 || maxConcurrentDownloads > 12) {
            return alert("并行下载数量必须在 1 到 12 之间");
        }

        const pageCacheLimitValue = Number.parseInt(pageCacheLimitInput?.value || "20", 10);
        if (!Number.isInteger(pageCacheLimitValue) || pageCacheLimitValue < 1 || pageCacheLimitValue > 200) {
            return alert("页面缓存数量必须在 1 到 200 之间");
        }

        const gopeedHost = gopeedHostInput?.value.trim() || "127.0.0.1";
        if (!gopeedHost) return alert("Gopeed 主机地址不能为空");

        const gopeedPort = Number.parseInt(gopeedPortInput?.value || "9999", 10);
        if (!Number.isInteger(gopeedPort) || gopeedPort < 1 || gopeedPort > 65535) {
            return alert("Gopeed 端口必须在 1 到 65535 之间");
        }

        const gopeedToken = gopeedTokenInput?.value || "";

        const gopeedConnections = Number.parseInt(gopeedConnectionsInput?.value || "16", 10);
        if (!Number.isInteger(gopeedConnections) || gopeedConnections < 1 || gopeedConnections > 128) {
            return alert("Gopeed 最大连接数必须在 1 到 128 之间");
        }

        const maxLocalCacheSizeGB = parseFloat(maxLocalCacheSizeGBInput?.value || "5");
        if (isNaN(maxLocalCacheSizeGB) || maxLocalCacheSizeGB < 0.5 || maxLocalCacheSizeGB > 100) {
            return alert("图片缓存上限必须在 0.5 到 100 GB 之间");
        }

        const nextShortcutBack = normalizeShortcut(shortcutBackInput?.value, "Alt+ArrowLeft");
        const nextShortcutForward = normalizeShortcut(shortcutForwardInput?.value, "Alt+ArrowRight");

        try {
            const res = await fetch("/api/settings", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    downloadDirectory,
                    maxConcurrentDownloads,
                    pageCacheLimit: pageCacheLimitValue,
                    gopeedHost,
                    gopeedPort,
                    gopeedToken,
                    gopeedConnections,
                    maxLocalCacheSizeGB,
                    shortcutBack: nextShortcutBack,
                    shortcutForward: nextShortcutForward
                })
            });
            if (res.ok) {
                applyPageCacheLimit(pageCacheLimitValue);
                shortcutBack = nextShortcutBack;
                shortcutForward = nextShortcutForward;
                alert("全局设置已保存！新的配置将立即生效。");
                settingsModal.classList.add("hidden");
            } else {
                alert("保存失败!");
            }
        } catch(e) {
            console.error(e);
            alert("保存出错: " + e.message);
        }
    });

    // ---- Video Player Logic ----
    playVideoBtn.addEventListener("click", () => {
        if (!currentVideoUrl) return;
        currentVideoFallbackTried = false;
        recordCurrentWatchHistory();
        
        // Hide Cover, Show Player
        coverWrapper.classList.add("hidden");
        playerWrapper.classList.remove("hidden");
        playerWrapper.classList.remove("preloading");

        const fallbackToProxyVideo = () => {
            if (currentVideoFallbackTried || !currentProxiedVideoUrl || currentVideoUrl === currentProxiedVideoUrl) return;
            currentVideoFallbackTried = true;
            currentVideoUrl = currentProxiedVideoUrl;
            if(hlsInstance) {
                hlsInstance.destroy();
                hlsInstance = null;
            }
            videoPlayer.pause();
            videoPlayer.removeAttribute("src");
            videoPlayer.load();
            if (currentVideoUrl.includes(".m3u8") && Hls.isSupported()) {
                hlsInstance = new Hls();
                hlsInstance.loadSource(currentVideoUrl);
                hlsInstance.attachMedia(videoPlayer);
                hlsInstance.on(Hls.Events.MANIFEST_PARSED, function() {
                    videoPlayer.play();
                });
            } else {
                videoPlayer.onerror = null;
                videoPlayer.dataset.src = currentVideoUrl;
                videoPlayer.src = currentVideoUrl;
                const playPromise = videoPlayer.play();
                if (playPromise) playPromise.catch(() => {});
            }
        };

        // Use HLS.js for m3u8, native HTML5 for mp4
        if (currentVideoUrl.includes(".m3u8")) {
            if (Hls.isSupported()) {
                if(hlsInstance) hlsInstance.destroy();
                hlsInstance = new Hls();
                hlsInstance.loadSource(currentVideoUrl);
                hlsInstance.attachMedia(videoPlayer);
                hlsInstance.on(Hls.Events.MANIFEST_PARSED, function() {
                    videoPlayer.play();
                });
                hlsInstance.on(Hls.Events.ERROR, function(_event, data) {
                    if (data && data.fatal) fallbackToProxyVideo();
                });
            } else if (videoPlayer.canPlayType('application/vnd.apple.mpegurl')) {
                // For Native Safari
                videoPlayer.src = currentVideoUrl;
                videoPlayer.addEventListener('loadedmetadata', function() {
                    videoPlayer.play();
                });
            }
        } else {
            videoPlayer.onerror = fallbackToProxyVideo;
            videoPlayer.preload = "auto";
            if (videoPlayer.dataset.src !== currentVideoUrl || videoPlayer.error) {
                videoPlayer.dataset.src = currentVideoUrl;
                videoPlayer.src = currentVideoUrl;
                videoPlayer.load();
            }
            const playPromise = videoPlayer.play();
            if (playPromise) playPromise.catch(fallbackToProxyVideo);
        }
    });

    closePlayerBtn.addEventListener("click", () => {
        if(hlsInstance) {
            hlsInstance.destroy();
            hlsInstance = null;
        }
        videoPlayer.pause();
        videoPlayer.onerror = null;
        delete videoPlayer.dataset.src;
        videoPlayer.removeAttribute("src");
        videoPlayer.load();
        playerWrapper.classList.add("hidden");
        playerWrapper.classList.remove("preloading");
        coverWrapper.classList.remove("hidden");
    });

    // ---- Parse Flow ----
    function prepareParserLoading(url, resetLog = true) {
        switchView("viewParser", false);
        urlInput.value = url;
        emptyState.classList.add("hidden");
        previewContent.classList.remove("hidden");
        if (resetLog) logConsole.innerHTML = "";
        
        // reset player state
        if(hlsInstance) { hlsInstance.destroy(); hlsInstance = null; }
        videoPlayer.pause();
        videoPlayer.removeAttribute("src");
        videoPlayer.load();
        playerWrapper.classList.add("hidden");
        playerWrapper.classList.remove("preloading");
        coverWrapper.classList.remove("hidden");
        currentVideoData = null;
        currentRawVideoUrl = "";
        currentVideoUrl = "";
        currentProxiedVideoUrl = "";
        currentVideoFallbackTried = false;
        delete videoPlayer.dataset.src;
        currentPlaylistItems = [];
        currentRelatedVideos = [];
        updateVideoAccountActions();
        playlistCount.textContent = "0";
        playlistContainer.innerHTML = `<div class="empty-playlist">暂无影片序列</div>`;
        relatedVideoCount.textContent = "0";
        relatedVideoGrid.innerHTML = `<div class="empty-playlist">暂无相关视频</div>`;
        if (commentsCount) commentsCount.textContent = "0";
        if (commentsList) commentsList.innerHTML = `<div class="empty-playlist">正在等待解析结果</div>`;
        updateSeriesDownloadButton();
        updatePlaylistPanelLayout();
    }

    async function loadParserUrl(url, pushState = true, preferCache = true) {
        const normalizedUrl = String(url || "").trim();
        if (!normalizedUrl) {
            alert("请粘贴视频链接");
            return;
        }

        if (pushState) {
            history.pushState({ view: "viewParser", url: normalizedUrl }, "", `#parse?v=${encodeURIComponent(normalizedUrl)}`);
        }

        if (preferCache && restoreCachedParserPage(normalizedUrl)) {
            return;
        }

        prepareParserLoading(normalizedUrl);
        window.scrollTo({ top: 0, behavior: "auto" });

        log("初始化 HTTP 抓取请求...", "info");

        try {
            log(`目标源: ${normalizedUrl}`, "info");

            const response = await fetch("/api/parse", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url: normalizedUrl })
            });

            if (!response.ok) {
                const errText = await response.text();
                throw new Error(errText || "服务器探针断开");
            }

            const data = await response.json();
            log("✅ 侦测成功，核心资源地址锁定！", "info");

            setPageCacheEntry(getParserCacheKey(normalizedUrl), data);
            renderUi(data);
            window.scrollTo({ top: 0, behavior: "auto" });

        } catch (error) {
            log(`❌ 解析异常中断: ${error.message}`, "error");
        }
    }

    parseBtn.addEventListener("click", async () => {
        await loadParserUrl(urlInput.value, true, true);
    });

    function renderUi(data) {
        currentVideoData = data;
        currentRawVideoUrl = data.videoUrl || "";
        mainTitle.textContent = data.title || "未知标题";
        currentVideoUrl = directMediaUrl(currentRawVideoUrl);
        currentProxiedVideoUrl = proxyVideoUrl(currentRawVideoUrl);
        preloadCurrentVideo();
        
        // Handle Creator Info Card
        if (data.creator && data.creator.id && data.creator.name) {
            if (creatorName) creatorName.textContent = data.creator.name;
            if (creatorAvatar) {
                creatorAvatar.dataset.srcRaw = data.creator.avatar || "";
                creatorAvatar.dataset.proxyTried = "0";
                creatorAvatar.onerror = () => fallbackImage(creatorAvatar);
                creatorAvatar.src = data.creator.avatar
                    ? imageUrl(data.creator.avatar)
                    : "https://via.placeholder.com/48x48.png?text=Avatar";
                // Asynchronously fetch the real creator avatar (creator.avatar is the logged-in user's avatar)
                const artistId = data.creator.post?.artistId || data.creator.id;
                if (artistId) {
                    fetch(`/api/creator/info?userId=${encodeURIComponent(artistId)}`)
                        .then(r => r.ok ? r.json() : null)
                        .then(info => {
                            if (info?.avatarUrl && creatorAvatar) {
                                creatorAvatar.dataset.srcRaw = info.avatarUrl;
                                creatorAvatar.dataset.proxyTried = "0";
                                creatorAvatar.src = imageUrl(info.avatarUrl);
                            }
                        })
                        .catch(() => {});
                }
            }
            if (creatorInfoCard) {
                creatorInfoCard.classList.remove("hidden");
                creatorInfoCard.onclick = () => {
                    switchView("viewBrowse", false);
                    // post.artistId is the real creator ID from the subscribe form;
                    // creator.id is extracted from nav links and may be the logged-in user's ID
                    const creatorId = data.creator.post?.artistId || data.creator.id;
                    loadBrowseCategory("user:" + creatorId, 1, true);
                };
            }
        } else {
            if (creatorInfoCard) creatorInfoCard.classList.add("hidden");
        }

        // Image Anti-Hotlink
        if (data.thumbnail) {
            mainCover.dataset.srcRaw = data.thumbnail;
            mainCover.dataset.proxyTried = "0";
            mainCover.onerror = () => fallbackImage(mainCover);
            mainCover.src = imageUrl(data.thumbnail);
        } else {
            mainCover.src = "https://via.placeholder.com/1280x720.png?text=No+Cover";
        }

        if (currentVideoUrl) {
            const streamType = currentRawVideoUrl.includes('.m3u8') ? 'HLS 切片流' : 'MP4 直供源';
            log(`捕获原生数据: [${streamType}]`, 'info');
        } else {
            log(`该源可能被屏蔽或限权流出。`, 'warning');
        }

        // Render Sidebar Playlist
        playlistContainer.innerHTML = "";
        const list = data.playlist || [];
        currentPlaylistItems = list;
        playlistCount.textContent = list.length;
        updateSeriesDownloadButton();

        if (list.length === 0) {
            playlistContainer.innerHTML = `<div class="empty-playlist">暂无连载相关</div>`;
        } else {
            list.forEach(item => {
                const el = document.createElement("div");
                el.className = "playlist-item";
                el.innerHTML = `
                    <img src="${imageUrl(item.thumbnail)}" data-src-raw="${escapeHtml(item.thumbnail || "")}" onerror="fallbackImage(this)" loading="lazy" class="item-thumb" alt="thumb">
                    <div class="item-details">
                        <div class="item-title" title="${item.title}">${item.title}</div>
                    </div>
                `;
                el.addEventListener("click", () => {
                    urlInput.value = item.url;
                    parseBtn.click();
                    // scroll to top
                    window.scrollTo({ top: 0, behavior: "smooth" });
                });
                playlistContainer.appendChild(el);
            });
        }

        updatePlaylistPanelLayout();

        renderRelatedVideoGrid(data.relatedVideos || []);
        setDetailTab("related");
        loadComments(data.videoId || "");
        updateVideoAccountActions();
    }

    favoriteVideoBtn?.addEventListener("click", async () => {
        if (!currentVideoData || !requireLogin()) return;
        favoriteVideoBtn.disabled = true;
        try {
            await postJson("/api/video/favorite", {
                videoId: currentVideoData.videoId || videoIdFromUrl(urlInput.value),
                csrfToken: currentVideoData.csrfToken,
                currentUserId: currentVideoData.currentUserId,
                isFav: !!currentVideoData.isFav
            });
            currentVideoData.isFav = !currentVideoData.isFav;
            updateVideoAccountActions();
        } catch (error) {
            alert(`喜欢操作失败: ${error.message}`);
        } finally {
            favoriteVideoBtn.disabled = false;
        }
    });

    watchLaterBtn?.addEventListener("click", async () => {
        if (!currentVideoData || !requireLogin()) return;
        const checked = !currentVideoData.myList?.isWatchLater;
        watchLaterBtn.disabled = true;
        try {
            await postJson("/api/video/watch-later", {
                videoId: currentVideoData.videoId || videoIdFromUrl(urlInput.value),
                pageUrl: urlInput.value,
                csrfToken: currentVideoData.csrfToken,
                currentUserId: currentVideoData.currentUserId,
                listCode: currentVideoData.myList?.watchLaterCode,
                isChecked: checked
            });
            currentVideoData.myList = currentVideoData.myList || {};
            currentVideoData.myList.isWatchLater = checked;
            updateVideoAccountActions();
        } catch (error) {
            alert(`稍后观看操作失败: ${error.message}`);
        } finally {
            watchLaterBtn.disabled = false;
        }
    });

    myListBtn?.addEventListener("click", async () => {
        if (!currentVideoData || !requireLogin()) return;
        const item = (currentVideoData.myList?.items || []).find(entry => !entry.isSelected) || (currentVideoData.myList?.items || [])[0];
        if (!item?.code) return alert("未识别到可加入的播放清单");
        myListBtn.disabled = true;
        try {
            await postJson("/api/video/my-list", {
                videoId: currentVideoData.videoId || videoIdFromUrl(urlInput.value),
                csrfToken: currentVideoData.csrfToken,
                currentUserId: currentVideoData.currentUserId,
                listCode: item.code,
                isChecked: !item.isSelected
            });
            item.isSelected = !item.isSelected;
        } catch (error) {
            alert(`加入清单失败: ${error.message}`);
        } finally {
            updateVideoAccountActions();
        }
    });

    subscribeCreatorBtn?.addEventListener("click", async (event) => {
        event.stopPropagation();
        if (!currentVideoData?.creator?.post || !requireLogin()) return;
        const post = currentVideoData.creator.post;
        subscribeCreatorBtn.disabled = true;
        try {
            await postJson("/api/creator/subscribe", {
                csrfToken: currentVideoData.csrfToken,
                userId: post.userId,
                artistId: post.artistId,
                isSubscribed: !!post.isSubscribed
            });
            post.isSubscribed = !post.isSubscribed;
            updateVideoAccountActions();
        } catch (error) {
            alert(`关注作者失败: ${error.message}`);
        } finally {
            subscribeCreatorBtn.disabled = false;
        }
    });

    startDownloadBtn.addEventListener("click", async () => {
        if (!currentRawVideoUrl && !urlInput.value.trim()) {
            return alert("请先解析出可用的视频资源");
        }

        try {
            await enqueueDownloadItems([buildCurrentDownloadItem()], "已加入下载队列，下载中心正在接力处理");
        } catch (error) {
            alert(`加入下载失败: ${error.message}`);
        }
    });

    downloadSeriesBtn.addEventListener("click", async () => {
        const items = buildSeriesDownloadItems();
        if (items.length <= 1) {
            return alert("当前未识别到可批量下载的系列视频");
        }

        try {
            await enqueueDownloadItems(items, `已加入 ${items.length} 个系列下载任务`);
        } catch (error) {
            alert(`加入系列下载失败: ${error.message}`);
        }
    });

    copyLinkBtn.addEventListener("click", () => {
        if (!currentRawVideoUrl) return alert("无可用链接");
        navigator.clipboard.writeText(currentRawVideoUrl).then(() => {
            log("链接萃取复制完毕", "info");
        });
    });

    if (toggleSearchBtn && searchHeader) {
        toggleSearchBtn.addEventListener("click", () => {
            searchHeader.classList.toggle("collapsed");
        });
    }

    if (toggleLogBtn && statusPanelWrapper) {
        toggleLogBtn.addEventListener("click", () => {
            statusPanelWrapper.classList.toggle("collapsed");
        });
    }

    document.addEventListener("keydown", (event) => {
        if (isEditableTarget(event.target)) return;
        const shortcut = shortcutFromEvent(event);
        if (shortcut === shortcutBack) {
            event.preventDefault();
            history.back();
        } else if (shortcut === shortcutForward) {
            event.preventDefault();
            history.forward();
        }
    });

    if (commentsList) {
        commentsList.addEventListener("click", (event) => {
            const replyButton = event.target.closest(".comment-reply-btn[data-comment-id]");
            if (!replyButton) return;
            loadReplies(replyButton.dataset.commentId, replyButton);
        });
    }

    if (mediaDetailTabs) {
        mediaDetailTabs.addEventListener("click", (event) => {
            const tabButton = event.target.closest("[data-detail-tab]");
            if (!tabButton) return;
            setDetailTab(tabButton.dataset.detailTab);
        });
    }

    navLogo.onclick = () => switchView('viewLanding');

    // ---- Browse Classification Logic ----
    const categoryListItems = document.querySelectorAll("#categoryList li");
    const videoGrid = document.getElementById("videoGrid");
    const browseLoader = document.getElementById("browseLoader");
    const currentCategoryTitle = document.getElementById("currentCategoryTitle");
    const browseSelectionCount = document.getElementById("browseSelectionCount");
    const selectPageBtn = document.getElementById("selectPageBtn");
    const clearSelectedBtn = document.getElementById("clearSelectedBtn");
    const addSelectedToQueueBtn = document.getElementById("addSelectedToQueueBtn");

    // Fetch and display category grid
    async function loadBrowseCategory(category, page = 1, pushState = true) {
        currentBrowseMode = "category";
        currentCategory = category;
        currentPage = page;
        const cacheKey = getBrowseCacheKey(category, page);
        
        const grid = document.getElementById('videoGrid');
        const loader = document.getElementById('browseLoader');
        const title = document.getElementById('currentCategoryTitle');
        const pageIndicator = document.getElementById('pageIndicator');
        const totalPagesIndicatorStr = document.getElementById('totalPagesIndicatorStr');

        if (category.startsWith("user:")) {
            title.innerText = "正在浏览: 作者主页";
            categoryListItems.forEach(item => item.classList.remove("active"));
            // Optimistic UI update: immediately render tabs/sort buttons using cached creator data
            // so they appear instantly even before the API responds (or if it fails with 503)
            if (currentCreatorData) {
                renderCreatorHeader(category);
            }
        } else if (category.startsWith("query:")) {
            title.innerText = `正在浏览: ${category.slice(6)}`;
            categoryListItems.forEach(item => item.classList.remove("active"));
        } else if (category.startsWith("playlist:")) {
            title.innerText = "正在浏览: 播放清单";
            categoryListItems.forEach(item => item.classList.remove("active"));
        } else {
            title.innerText = `正在浏览: ${category}`;
        }
        if (pageIndicator) pageIndicator.innerText = page;

        if (pushState) {
            history.pushState({ view: 'viewBrowse', category: category, page: page }, "", `#browse-${encodeURIComponent(category)}-${page}`);
        }

        // Check cache BEFORE clearing the grid to avoid visual flash
        if (restoreCachedBrowsePage(cacheKey)) {
            return;
        }

        grid.innerHTML = '';
        loader.classList.remove('hidden');

        try {
            const resp = await fetch(`/api/browse?category=${encodeURIComponent(category)}&page=${page}`);
            if (!resp.ok) {
                const errText = await resp.text();
                throw new Error(errText || "无法获取该分类资源，可能被盾");
            }

            const data = await resp.json();
            setPageCacheEntry(cacheKey, data);
            applyBrowseResult(data);
            window.scrollTo({ top: 0, behavior: "auto" });

        } catch (err) {
            loader.classList.add("hidden");
            grid.innerHTML = `<div style="color:red; padding: 2rem; text-align: center;">获取异常: ${escapeHtml(err.message)}</div>`;
        }
    }

    // Pagination Listeners
    const prevPageBtn = document.getElementById('prevPageBtn');
    const nextPageBtn = document.getElementById('nextPageBtn');

    if (prevPageBtn) prevPageBtn.onclick = () => {
        if (currentPage > 1) {
            currentPage--;
            if (currentBrowseMode === "search") {
                loadSearchResults(currentPage, true);
            } else {
                loadBrowseCategory(currentCategory, currentPage, true);
            }
        }
    };

    if (nextPageBtn) nextPageBtn.onclick = () => {
        currentPage++;
        if (currentBrowseMode === "search") {
            loadSearchResults(currentPage, true);
        } else {
            loadBrowseCategory(currentCategory, currentPage, true);
        }
    };

    categoryListItems.forEach(li => {
        li.addEventListener("click", () => {
            // Update active state
            categoryListItems.forEach(item => item.classList.remove("active"));
            li.classList.add("active");

            const category = li.getAttribute("data-cat");
            currentBrowseMode = "category";
            loadBrowseCategory(category, 1, true);
        });
    });

    function setBrowseSelectionState(card, button, selected) {
        card.classList.toggle("selected", selected);
        button.classList.toggle("selected", selected);
        button.textContent = selected ? "已选" : "选择";
    }

    function renderVideoGrid(videos) {
        if (!videos || videos.length === 0) {
            videoGrid.innerHTML = `<div class="empty-playlist">该分类下暂无兼容排版资源或需翻页支持</div>`;
            return;
        }

        videoGrid.innerHTML = "";

        videos.forEach(vid => {
            const card = createVideoCard(vid);
            videoGrid.appendChild(card);
        });
    }

    selectPageBtn.addEventListener("click", () => {
        currentBrowseVideos.forEach((vid) => {
            selectedBrowseItems.set(vid.url, {
                title: vid.title,
                pageUrl: vid.url,
                thumbnail: vid.thumbnail,
                downloadUrl: ""
            });
        });
        updateBrowseSelectionSummary();
        refreshBrowseGrid();
    });

    clearSelectedBtn.addEventListener("click", () => {
        selectedBrowseItems.clear();
        updateBrowseSelectionSummary();
        refreshBrowseGrid();
    });

    addSelectedToQueueBtn.addEventListener("click", async () => {
        try {
            await enqueueDownloadItems(Array.from(selectedBrowseItems.values()), `已批量加入 ${selectedBrowseItems.size} 个下载任务`);
            selectedBrowseItems.clear();
            updateBrowseSelectionSummary();
            refreshBrowseGrid();
        } catch (error) {
            alert(`批量加入失败: ${error.message}`);
        }
    });

    // Trigger initial load on browse tab init
    document.getElementById("modeBrowseBtn").addEventListener("click", () => {
        if(videoGrid.children.length === 0 && browseLoader.classList.contains("hidden")) {
            // click first category softly to trigger load
            document.querySelector("#categoryList li.active").click();
        }
    });

    updateBrowseSelectionSummary();
    updateSeriesDownloadButton();
    loadSearchOptions();
    syncSearchTypeControls();
    syncGlobalSearchChrome();
    setDetailTab("related");
    updatePageCacheStatus();
    renderDownloadCenter();
    fetchDownloadSnapshot();
    connectDownloadStream();
    window.addEventListener("resize", updatePlaylistPanelLayout);

});
