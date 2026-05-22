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
    const browserChannelSelect = document.getElementById("browserChannel");
    const browserVerificationTimeoutSecondsInput = document.getElementById("browserVerificationTimeoutSeconds");

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

    const modeBrowseBtn = document.getElementById("modeBrowseBtn");
    const modeParseBtn = document.getElementById("modeParseBtn");

    const parseBtn = document.getElementById("parseBtn");
    const urlInput = document.getElementById("urlInput");
    const emptyState = document.getElementById("emptyState");
    const previewContent = document.getElementById("previewContent");
    const logConsole = document.getElementById("logConsole");
    const cfModal = document.getElementById("cfModal");
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
    let currentBrowseVideos = [];
    let currentPlaylistItems = [];
    let currentRelatedVideos = [];
    let downloadSnapshot = { activeTasks: [], queuedTasks: [], historyTasks: [] };
    let downloadEventSource = null;
    let downloadReconnectTimer = null;
    let cfModalTimer = null;
    const selectedBrowseItems = new Map();
    let currentHomeSections = [];
    let currentHomeHero = null;
    let currentCreatorData = null; // Cache last successful creator page data
    let pageCacheLimit = 20;
    const PAGE_CACHE_STORAGE_KEY = "hanimeMediaCenter.pageCache.v1";
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

    function loadPageCache() {
        try {
            const raw = window.sessionStorage?.getItem(PAGE_CACHE_STORAGE_KEY);
            const entries = raw ? JSON.parse(raw) : [];
            if (!Array.isArray(entries)) return new Map();
            return new Map(entries.filter(entry => Array.isArray(entry) && entry.length === 2));
        } catch (_error) {
            return new Map();
        }
    }

    function persistPageCache() {
        try {
            window.sessionStorage?.setItem(PAGE_CACHE_STORAGE_KEY, JSON.stringify(Array.from(pageCache.entries())));
        } catch (_error) {
            // Cache is best-effort; ignore quota/private-mode storage failures.
        }
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
    }

    function getPageCacheEntry(key) {
        const entry = pageCache.get(key);
        if (!entry) return null;
        pageCache.delete(key);
        entry.lastUsed = Date.now();
        pageCache.set(key, entry);
        persistPageCache();
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
            window.sessionStorage?.removeItem(PAGE_CACHE_STORAGE_KEY);
        } catch (_error) {
            // Ignore storage failures; in-memory cache has already been cleared.
        }
        updatePageCacheStatus();
    }

    function updatePageCacheStatus(message = "") {
        const pageCacheStatus = document.getElementById("pageCacheStatus");
        if (!pageCacheStatus) return;
        pageCacheStatus.textContent = message || `已缓存 ${pageCache.size}/${pageCacheLimit} 个页面`;
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
        card.className = "grid-item";
        const isSelected = selectedBrowseItems.has(vid.url);
        const isPlaylist = vid.url.includes("playlist?list=") || vid.isPlaylist;

        card.innerHTML = `
            <button class="grid-select-toggle ${isSelected ? 'selected' : ''}" type="button">${isSelected ? '已选' : '选择'}</button>
            <div class="grid-thumb-container">
                <img src="${imageUrl(vid.thumbnail)}" data-src-raw="${escapeHtml(vid.thumbnail || "")}" onerror="fallbackImage(this)" loading="lazy" class="grid-thumb" alt="cover">
                ${vid.duration ? `<div class="grid-item-duration">${escapeHtml(vid.duration)}</div>` : ''}
                ${vid.videoCount ? `<div class="grid-item-playlist-badge">${escapeHtml(vid.videoCount)}</div>` : ''}
            </div>
            <div class="grid-title" title="${escapeHtml(vid.title || "")}">${escapeHtml(vid.title || "未命名视频")}</div>
        `;
        const selectButton = card.querySelector(".grid-select-toggle");
        setBrowseSelectionState(card, selectButton, isSelected);

        if (isPlaylist) {
            selectButton.style.display = "none";
        }

        selectButton.addEventListener("click", (event) => {
            event.stopPropagation();
            if (selectedBrowseItems.has(vid.url)) {
                selectedBrowseItems.delete(vid.url);
            } else {
                selectedBrowseItems.set(vid.url, {
                    title: vid.title,
                    pageUrl: vid.url,
                    thumbnail: vid.thumbnail,
                    downloadUrl: ""
                });
            }
            setBrowseSelectionState(card, selectButton, selectedBrowseItems.has(vid.url));
            updateBrowseSelectionSummary();
        });

        // Click card delegates to Parser or playlist browsing
        card.addEventListener("click", () => {
            if (isPlaylist) {
                const listId = new URL(vid.url).searchParams.get("list");
                if (listId) {
                    rememberCurrentPageScroll();
                    loadBrowseCategory("playlist:" + listId, 1, true);
                    return;
                }
            }
            rememberCurrentPageScroll();
            urlInput.value = vid.url;
            switchView("viewParser", false);
            parseBtn.click();
        });
        return card;
    }

    function createHomeVideoCard(vid) {
        const container = document.createElement("div");
        container.className = "video-item-container";
        const isSelected = selectedBrowseItems.has(vid.url);
        
        const thumbnail = imageUrl(vid.thumbnail);
        
        container.innerHTML = `
            <div class="horizontal-card">
                <button class="grid-select-toggle ${isSelected ? 'selected' : ''}" type="button" style="z-index: 10;">${isSelected ? '已选' : '选择'}</button>
                <div class="video-link">
                    <div class="thumb-container">
                        <img class="main-thumb" src="${thumbnail}" data-src-raw="${escapeHtml(vid.thumbnail || "")}" onerror="fallbackImage(this)" loading="lazy" alt="cover">
                        ${vid.duration ? `<div class="duration">${escapeHtml(vid.duration)}</div>` : ''}
                        <div class="stats-container">
                            ${vid.likes ? `<div class="stat-item"><span class="thumb-icon">👍</span> ${escapeHtml(vid.likes)}</div>` : ''}
                            ${vid.views ? `<div class="stat-item">${escapeHtml(vid.views)}</div>` : ''}
                        </div>
                    </div>
                    <div class="title" title="${escapeHtml(vid.title || "")}">
                        ${escapeHtml(vid.title || "未命名视频")}
                    </div>
                </div>
                ${vid.creator ? `
                <div class="subtitle">
                    ${escapeHtml(vid.creator)}
                </div>
                ` : ''}
            </div>
        `;
        
        const selectButton = container.querySelector(".grid-select-toggle");
        
        function setSelectionState(selected) {
            if (selected) {
                selectButton.classList.add("selected");
                selectButton.innerText = "已选";
                container.classList.add("selected-card");
            } else {
                selectButton.classList.remove("selected");
                selectButton.innerText = "选择";
                container.classList.remove("selected-card");
            }
        }
        setSelectionState(isSelected);

        selectButton.addEventListener("click", (event) => {
            event.stopPropagation();
            if (selectedBrowseItems.has(vid.url)) {
                selectedBrowseItems.delete(vid.url);
            } else {
                selectedBrowseItems.set(vid.url, {
                    title: vid.title,
                    pageUrl: vid.url,
                    thumbnail: vid.thumbnail,
                    downloadUrl: ""
                });
            }
            setSelectionState(selectedBrowseItems.has(vid.url));
            updateBrowseSelectionSummary();
        });

        const cardArea = container.querySelector(".video-link");
        cardArea.addEventListener("click", (event) => {
            if (event.target === selectButton) return;
            if (vid.url.includes("playlist?list=")) {
                const listId = new URL(vid.url).searchParams.get("list");
                if (listId) {
                    rememberCurrentPageScroll();
                    switchView("viewBrowse", false);
                    loadBrowseCategory("playlist:" + listId, 1, true);
                    return;
                }
            }
            rememberCurrentPageScroll();
            urlInput.value = vid.url;
            switchView("viewParser", false);
            parseBtn.click();
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

        videoGrid.innerHTML = "";
        browseLoader.classList.remove("hidden");
        if (restoreCachedBrowsePage(cacheKey)) {
            return;
        }

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
        const response = await fetch("/api/downloads/history/clear", {
            method: "POST"
        });
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText || "清空下载历史失败");
        }
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

    function scheduleCfModal() {
        if (cfModalTimer) {
            clearTimeout(cfModalTimer);
        }
        cfModalTimer = setTimeout(() => {
            cfModal.classList.remove("hidden");
            cfModalTimer = null;
        }, 1200);
    }

    function hideCfModal() {
        if (cfModalTimer) {
            clearTimeout(cfModalTimer);
            cfModalTimer = null;
        }
        cfModal.classList.add("hidden");
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

    // ---- Settings API ----
    settingsBtn.addEventListener("click", async () => {
        settingsModal.classList.remove("hidden");
        updatePageCacheStatus();

        // fetch available browsers dynamically
        try {
            const browserRes = await fetch("/api/browsers");
            if (browserRes.ok) {
                const browserData = await browserRes.json();
                const choices = browserData.choices || [];
                if (browserChannelSelect) {
                    browserChannelSelect.innerHTML = choices.map(choice => {
                        const label = choice.available ? choice.label : `${choice.label} (未检测到)`;
                        return `<option value="${escapeHtml(choice.channel)}">${escapeHtml(label)}</option>`;
                    }).join("");
                }
            }
        } catch (e) {
            console.error("Failed to load browsers list", e);
        }

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
            if (browserChannelSelect) {
                browserChannelSelect.value = data.browserChannel || "msedge";
            }
            if (browserVerificationTimeoutSecondsInput) {
                browserVerificationTimeoutSecondsInput.value = data.browserVerificationTimeoutSeconds || 180;
            }
        } catch (e) {
            console.error("Failed to load settings");
        }
    });

    // Clear Cache
    const clearCacheBtn = document.getElementById('clearCacheBtn');
    if (clearCacheBtn) {
        clearCacheBtn.addEventListener('click', async () => {
            if (!confirm('确定要清除浏览器本地缓存吗？这会强行关闭当前正在运行的抓取引擎（如果有的话），并清除所有验证记录。')) return;
            
            clearCacheBtn.disabled = true;
            clearCacheBtn.innerText = '🧹 正在清理...';
            
            try {
                const res = await fetch('/api/settings/clear-cache', { method: 'POST' });
                if (res.ok) {
                    alert('本地缓存清理成功！抓取引擎已重置。');
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

    const clearPageCacheBtn = document.getElementById("clearPageCacheBtn");
    if (clearPageCacheBtn) {
        clearPageCacheBtn.addEventListener("click", () => {
            clearPageCache();
            updatePageCacheStatus("页面缓存已清除");
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

        const browserChannel = browserChannelSelect?.value || "msedge";

        const browserVerificationTimeoutSeconds = Number.parseInt(browserVerificationTimeoutSecondsInput?.value || "180", 10);
        if (!Number.isInteger(browserVerificationTimeoutSeconds) || browserVerificationTimeoutSeconds < 30 || browserVerificationTimeoutSeconds > 600) {
            return alert("穿透超时时间必须在 30 到 600 秒之间");
        }

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
                    browserChannel,
                    browserVerificationTimeoutSeconds
                })
            });
            if (res.ok) {
                applyPageCacheLimit(pageCacheLimitValue);
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

        log("初始化探针引力引擎...", "info");
        log("调用本地代理规避侦测...", "info");
        
        scheduleCfModal();

        try {
            log(`目标源: ${normalizedUrl}`, "info");

            const response = await fetch("/api/parse", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url: normalizedUrl })
            });

            hideCfModal();

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
            hideCfModal();
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
            }
            if (creatorInfoCard) {
                creatorInfoCard.classList.remove("hidden");
                creatorInfoCard.onclick = () => {
                    switchView("viewBrowse", false);
                    loadBrowseCategory("user:" + data.creator.id, 1, true);
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
    }

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

        grid.innerHTML = '';
        loader.classList.remove('hidden');
        if (restoreCachedBrowsePage(cacheKey)) {
            return;
        }

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
