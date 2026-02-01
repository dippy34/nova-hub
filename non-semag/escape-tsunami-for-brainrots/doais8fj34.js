// Utility functions
const debounce = (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};

// Constants
const CONFIG = {
    ENDPOINTS: {
        DELIVER: '/_d',
        ADULT: '/_a',
        CONTACT: '/_c',
        EVENT: '/_e',
        FALLBACK: '/_o'
    },
    AFD_SCRIPT: 'https://www.google.com/adsense/domains/caf.js?abp=1&abpgo=true',
    ERROR_MESSAGES: {
        FETCH_UNSUPPORTED: 'This browser is not supported. Please use a modern browser.',
        SERVER_ERROR: 'Error communicating with server. Please try again.',
        INITIALIZATION_ERROR: 'AD BLOCKER DETECTED. Please disable ad blockers to view this domain.',
        DOMAIN_NOT_FOUND: 'The domain has not been provisioned on our platform.',
        NO_CHANNELS: 'No valid delivery channels available for this domain.',
        DNS_MISCONFIGURED: 'Domain appears to be misconfigured. Please check the DNS settings.',
        UNDER_DEVELOPMENT: 'This domain is under development and coming soon.',
        AD_BLOCK_DETECTED: 'Ad blocker detected. Please disable ad blockers to view this page.'
    }
};

// Error Handler
class DeliveryError extends Error {
    constructor(message, code, details = {}) {
        super(message);
        this.name = 'DeliveryError';
        this.code = code;
        this.details = details;
    }
}

// UI Manager
class UIManager {
    constructor() {
        this.container = document.getElementById('container');
        this.messageEl = document.getElementById('message');
        this.headerEl = document.querySelector('header');
        this.contactHeader = document.getElementById('banner');
    }

    configureContactMessage(contact) {
        // If no contact info or it's empty, don't show any contact message
        // Also don't show if afd=1 is in URL parameters
        if (!contact || Object.keys(contact).length === 0 || 
            new URLSearchParams(window.location.search).get('afd') === '1') {
            return;
        }

        const contactEl = contact.location === 'bottom' ? 
            this.ensureContactFooter() : this.contactHeader;
        if (!contactEl) return;

        // Create contact link
        const link = document.createElement('a');
        link.href = CONFIG.ENDPOINTS.CONTACT;
        link.textContent = contact.banner_text;
        link.style.textDecoration = 'none';

        // Apply styles based on contact style
        if (contact.style === 'aggressive') {
            contactEl.style.background = '#ff6b6b';
            link.style.color = '#ffffff';
            link.style.fontWeight = 'bold';
        } else {
            contactEl.style.background = '#646464';
            link.style.color = '#eeeeee';
        }

        const p = document.createElement('p');
        p.appendChild(link);
        contactEl.innerHTML = '';
        contactEl.appendChild(p);
        contactEl.style.opacity = '1';
    }

    ensureContactFooter() {
        let contactFooter = document.getElementById('contact-footer');
        if (!contactFooter) {
            contactFooter = document.createElement('div');
            contactFooter.id = 'contact-footer';
            contactFooter.style.cssText = 'position: fixed; bottom: 0; left: 0; width: 100%; opacity: 0; transition: opacity 0.3s ease; padding: 10px 0; text-align: center;';
            document.body.appendChild(contactFooter);
        }
        return contactFooter;
    }

    showError(message) {
        if (this.messageEl) {
            this.messageEl.textContent = message;
        }
        this.showContainer();
    }

    showContainer() {
        if (this.container) {
            this.container.style.visibility = 'visible';
        }
    }

    setPageTitle(display_domain, show_title) {
        if (!this.headerEl) return;

        if (show_title) {
            document.title = display_domain;
            const titleElement = document.createElement('h1');
            titleElement.textContent = display_domain;
            this.headerEl.appendChild(titleElement);
        } else {
            const spacerElement = document.createElement('div');
            spacerElement.style.height = '2em';
            this.headerEl.appendChild(spacerElement);
        }
    }
}

// API Client
class APIClient {
    async fetchPageData() {
        try {
            // Get current redirect count from URL parameters
            const currentUrl = new URL(window.location.href);
            const redirectCount = parseInt(currentUrl.searchParams.get('rc') || '0');

            // If err=frame is present, use frame_referrer instead of document.referrer
            const referrer = currentUrl.searchParams.get('err') === 'frame' ? 
                (currentUrl.searchParams.get('frame_referrer') || document.referrer) : 
                document.referrer;

            const response = await fetch(CONFIG.ENDPOINTS.DELIVER, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: JSON.stringify({
                    referrer: referrer,
                    current_location: window.location.href,
                    redirect_count: redirectCount,
                    user_agent: navigator.userAgent,
                    window_info: {
                        href: window.location.href,
                        hostname: window.location.hostname,
                        pathname: window.location.pathname
                    }
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.debug('Error response:', errorText);
                let errorData;
                try {
                    errorData = JSON.parse(errorText);
                    console.debug('Parsed error data:', errorData);
                } catch (e) {
                    console.error('Error parsing response:', e);
                    throw new DeliveryError(CONFIG.ERROR_MESSAGES.SERVER_ERROR, 'SERVER_ERROR', {
                        status: response.status,
                        statusText: response.statusText,
                        errorText
                    });
                }

                // If we have a code and a corresponding message, use it
                if (errorData.code && CONFIG.ERROR_MESSAGES[errorData.code]) {
                    console.debug('Using error message for code:', errorData.code);
                    // Pass through all error data to make it available to the UI
                    throw new DeliveryError(CONFIG.ERROR_MESSAGES[errorData.code], errorData.code, errorData);
                }
                
                // If we get here, we didn't recognize the error code
                console.debug('Unrecognized error code:', errorData.code);
                throw new DeliveryError(CONFIG.ERROR_MESSAGES.SERVER_ERROR, 'SERVER_ERROR', {
                    status: response.status,
                    statusText: response.statusText,
                    errorText
                });
            }

            const data = await response.json();
            if (!data) throw new DeliveryError('Empty response received', 'EMPTY_RESPONSE');
            
            // Check if user is from Russia based on geo data
            if (data.geo && data.geo.country === 'RU') {
                // Get the fallback URL if available
                if (data.delivery && data.delivery.fallback_list && data.delivery.fallback_list.length > 0) {
                    window.location.href = data.delivery.fallback_list[0];
                    return null;
                }
                // If no fallback URL, redirect to fallback endpoint
                window.location.pathname = CONFIG.ENDPOINTS.FALLBACK;
                return null;
            }
            
            return data;
        } catch (error) {
            // Only log API level errors if they're not DeliveryErrors
            if (!(error instanceof DeliveryError)) {
                console.error('API Error:', error);
            }
            throw error;
        }
    }
}

// Main Application
class DeliveryApp {
    constructor() {
        this.ui = new UIManager();
        this.api = new APIClient();
        this.validateEnvironment();
        this.domain_settings = null; // Store domain settings for event logging
        this.terms = null; // Store terms for event logging
        this.fallback_urls = []; // Store fallback URLs
    }

    validateEnvironment() {
        if (!window.fetch) {
            throw new DeliveryError(CONFIG.ERROR_MESSAGES.FETCH_UNSUPPORTED, 'FETCH_UNSUPPORTED');
        }
    }

    logViewportInfo(event_type = 'initial', trigger = null) {
        this.reportEvent('metric:browser:viewport', {
            width: window.innerWidth,
            height: window.innerHeight,
            pixelRatio: window.devicePixelRatio || 1,
            isVisible: !document.hidden,
            hasFrameParent: window.top !== window.self,
            userAgent: navigator.userAgent,
            timestamp: Date.now(),
            event_type: event_type,
            screen_width: window.screen?.width,
            screen_height: window.screen?.height,
            documentHasFocus: document.hasFocus(),
            orientation: window.screen?.orientation?.type || 'unknown',
            interaction_trigger: trigger
        });
    }

    setupViewportLogging() {
        // Don't log on search results pages
        const isSearchResultPage = new URLSearchParams(window.location.search).get('afd') === '1';
        if (isSearchResultPage) return;

        let hasLogged = false;
        
        // Helper to log viewport info when we detect real user activity
        const logRealUser = (trigger) => {
            if (!hasLogged) {
                this.logViewportInfo('initial', trigger);
                hasLogged = true;
                // Clean up all listeners since we only need to log once
                cleanup();
            }
        };

        // Debounced versions of handlers
        const debouncedMouseMove = debounce(() => logRealUser('mousemove'), 150);
        const debouncedScroll = debounce(() => logRealUser('scroll'), 150);
        const clickHandler = () => logRealUser('click');
        const focusHandler = () => {
            if (document.hasFocus()) logRealUser('focus');
        };
        const keyHandler = () => logRealUser('keydown');
        const touchHandler = () => logRealUser('touch');

        // Set up multiple interaction listeners
        const setupListeners = () => {
            // Mouse movement (with debounce to avoid spam)
            document.addEventListener('mousemove', debouncedMouseMove);
            
            // Click events
            document.addEventListener('click', clickHandler);
            
            // Scroll events (with debounce)
            document.addEventListener('scroll', debouncedScroll);
            
            // Focus events
            document.addEventListener('focus', focusHandler);

            // Key events
            document.addEventListener('keydown', keyHandler);

            // Touch events for mobile
            document.addEventListener('touchstart', touchHandler);
        };

        // Cleanup function to remove all listeners once we've logged
        const cleanup = () => {
            document.removeEventListener('mousemove', debouncedMouseMove);
            document.removeEventListener('click', clickHandler);
            document.removeEventListener('scroll', debouncedScroll);
            document.removeEventListener('focus', focusHandler);
            document.removeEventListener('keydown', keyHandler);
            document.removeEventListener('touchstart', touchHandler);
        };

        // Check immediately in case document already has focus
        if (document.hasFocus()) {
            logRealUser('initial-focus');
        } else {
            // Set up interaction listeners if not focused
            setupListeners();
        }
    }

    loadAFDScript() {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = CONFIG.AFD_SCRIPT;
            script.type = 'text/javascript';
            script.onload = resolve;
            script.onerror = () => {
                console.error('Failed to load AFD script');
                // Log script load failure
                this.reportEvent('error:browser:caf:script:load_failed', {
                    script: CONFIG.AFD_SCRIPT
                });
                // Attempt fallback delivery
                // this.attemptFallbackDelivery();
                // reject(new Error('Failed to load AFD script'));
                reject(new DeliveryError(CONFIG.ERROR_MESSAGES.AD_BLOCK_DETECTED, 'AD_BLOCK_DETECTED'));
            };
            document.head.appendChild(script);
        });
    }

    // Event logging client
    reportEvent = async (eventName, context) => {
        try {
            const response = await fetch(CONFIG.ENDPOINTS.EVENT, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: JSON.stringify({
                    event: eventName,
                    event_data: {
                        context,
                        domain_settings: this.domain_settings
                    }
                })
            });

            if (!response.ok) throw new Error('Event reporting failed');
            console.debug('Event logged:', eventName);
        } catch (error) {
            console.error('Event logging error:', error);
        }
    }

    attemptFallbackDelivery = () => {
        if (this.fallback_urls && this.fallback_urls.length > 0) {
            const fallbackUrl = this.fallback_urls[0];
            console.log('Attempting fallback delivery to:', fallbackUrl);
            
            // Log the fallback attempt
            this.reportEvent('event:browser:fallback:attempt', {
                fallback_url: fallbackUrl
            });
            
            // Redirect to the fallback URL
            window.location.href = fallbackUrl;
        }
    }

    handlePageLoadedCallback = (requestAccepted, status) => {
        console.log('AFD Page Loaded:', { requestAccepted, status });
        
        if (!requestAccepted) {
            console.error('AFD request not accepted:', status);
            
            if (status.error_code) {
                console.error('AFD Error Code:', status.error_code);
                this.reportEvent('error:browser:caf:page', {
                    error_code: status.error_code,
                    status
                });
            }
            
            if (status.faillisted) {
                console.error('Domain Faillisted. Reason:', status.faillistReason);
                this.reportEvent('error:browser:caf:page:faillisted', {
                    reason: status.faillistReason,
                    status
                });
                // For non-adult failures, redirect to fallback endpoint
                window.location.pathname = CONFIG.ENDPOINTS.FALLBACK;
                return;
            }

            if (status.adult) {
                this.reportEvent('error:browser:caf:page:adult', { status });
                
                // Navigate directly to /_a for adult domain
                window.location.pathname = CONFIG.ENDPOINTS.ADULT;
                return;
            }

            
        } else {
            // Log successful page load
            this.reportEvent('event:browser:caf:page:loaded', {
                status,
                client: status.client,
                feed: status.feed,
                user_search: status.user_search,
                query: status.query
            });
        }
    }

    handleBlockLoadedCallback = (containerName, adsLoaded, isExperimentVariant, callbackOptions) => {
        console.log('AFD Block Loaded:', {
            container: containerName,
            adsLoaded,
            isExperimentVariant,
            options: callbackOptions
        });

        if (!adsLoaded) {
            console.warn('No ads loaded for container:', containerName);
            
            // Log failed block load with specific reasons if available
            if (callbackOptions?.cafStatus?.adult) {
                this.reportEvent('error:browser:caf:block:adult', {
                    container: containerName,
                    isExperimentVariant,
                    terms: this.terms,
                    callbackOptions
                });
                
                // Navigate directly to /_a for adult domain
                window.location.pathname = CONFIG.ENDPOINTS.ADULT;
                return;
            } else if (callbackOptions?.cafStatus?.faillisted) {
                this.reportEvent('error:browser:caf:block:faillisted', {
                    container: containerName,
                    isExperimentVariant,
                    terms: this.terms,
                    callbackOptions
                });
                window.location.pathname = CONFIG.ENDPOINTS.FALLBACK;
                return;
            } else {
                this.reportEvent('error:browser:caf:block:failed', {
                    container: containerName,
                    isExperimentVariant,
                    terms: this.terms,
                    callbackOptions
                });
                
                // For ads container, redirect to root with nofill error
                if (containerName === 'ads') {
                    window.location.href = '/?err=nofill';
                    return;
                }
                // For rs container, redirect to fallback URL if available
                if (containerName === 'rs' && this.fallback_urls && this.fallback_urls.length > 0) {
                    window.location.href = this.fallback_urls[0];
                    return;
                }
                // If no fallback URL available for rs, redirect to fallback endpoint
                if (containerName === 'rs') {
                    window.location.pathname = CONFIG.ENDPOINTS.FALLBACK;
                    return;
                }
            }
            
        } else {
            // Transform termPositions format and include terms in event data
            if (callbackOptions?.termPositions) {
                callbackOptions.termPositions = Object.entries(callbackOptions.termPositions)
                    .map(([term, position]) => ({ term, position }));
            }

            this.reportEvent('event:browser:caf:block:loaded', {
                container: containerName,
                isExperimentVariant,
                terms: this.terms,
                callbackOptions
            });
            
            if (containerName === 'rs') {
                this.reportEvent('event:browser:caf:rs:loaded', {
                    container: containerName,
                    isExperimentVariant,
                    terms: this.terms,
                    callbackOptions
                });
            }
        }
    }

    applyAFDStyles(colors) {
        if (!colors) {
            console.warn('No AFD colors provided');
            return;
        }
        
        console.log('Applying AFD theme colors:', colors);
        
        // Create or update AFD stylesheet
        let styleEl = document.getElementById('afd-theme');
        if (!styleEl) {
            styleEl = document.createElement('style');
            styleEl.id = 'afd-theme';
            document.head.appendChild(styleEl);
        }
        
        // Build CSS rules to match AFD's styling
        const cssRules = `
            :root {
                ${Object.entries(colors).map(([key, value]) => `${key}: ${value};`).join('\n                ')}
            }
            
            body {
                background-color: var(--main-bg-color);
                color: var(--main-text-color);
                font-family: var(--font-family);
            }
            
            a:not([class*="afd"]) {
                color: var(--link-color);
            }
            
            header h1 {
                color: var(--main-text-color);
            }
            
            #custom-text {
                color: var(--main-text-color);
            }
        `;
        
        styleEl.textContent = cssRules;
        
        console.log('Applied AFD theme', {
            bgColor: getComputedStyle(document.body).backgroundColor,
            textColor: getComputedStyle(document.body).color,
            fontFamily: getComputedStyle(document.body).fontFamily
        });
    }

    initializeAFD(data) {
        if (!data.afd || !data.afd.client_id || !data.afd.drid || !data.afd.style_id) {
            throw new DeliveryError('Missing AFD configuration', 'AFD_CONFIG_ERROR');
        }

        // Apply theme colors first so page looks consistent before AFD loads
        if (data.afd.colors) {
            this.applyAFDStyles(data.afd.colors);
        }

        console.log('Initializing AFD:', data.afd);

        // Store terms for event logging
        this.terms = data.afd.related_searches;

        // Construct base URL for results page (without AFD token and query)
        const url = new URL(window.location.href);
        url.searchParams.append('afd', '1');
        
        const pageOptions = {
            'pubId': data.afd.client_id,
            'domainRegistrant': data.afd.drid,
            'adtest': 'off',
            'adsafe': 'low',
            'channel': (() => {
                const err = new URLSearchParams(window.location.search).get('err');
                if (err === 'noquery') return 'ch1,ch2';
                if (err === 'nofill') return 'ch1,ch3';
                return 'ch1';
            })(),
            'maxTermLength': 50,
            'styleId': data.afd.style_id, // Use the predefined AFD style ID
            'resultsPageBaseUrl': url.href,
            'domainName': data.domain,
            'hl': 'en',
            'personalizedAds': false,
            'ivt': data.afd?.ivt ?? false,
            'terms': data.afd.related_searches,
            'kw': data.afd.related_searches,
            // 'kw': data.afd.related_searches ? data.afd.related_searches.split(',')[0] : '',
            'pageLoadedCallback': this.handlePageLoadedCallback,
            'clicktrackUrl': window.location.origin + '/_t?session_id=' + data.settings.session_id + 
                '&type=' + (new URLSearchParams(window.location.search).get('afd') === '1' ? 'click' : 'query') +
                (new URLSearchParams(window.location.search).get('afd') === '1' ? '&query=' + encodeURIComponent(new URLSearchParams(window.location.search).get('query') || '') : '')
        };

        console.log('AFD Page Options:', pageOptions);

        // Define shared variables
        const isSearchResultPage = new URLSearchParams(window.location.search).get('afd') === '1';
        const isSpecialUser = data.settings?.user_id === '4cd64db9-4e2a-4fbc-a46b-e463e0dcd5f0';
        const hasRelatedTerms = !!data.afd?.related_searches;
        const stage = isSearchResultPage ? 'ads' : 'rs';
        const containerId = stage === 'ads' ? 'ads' : 'rs';

        // Create containers based on user and terms status
        if (isSpecialUser && !hasRelatedTerms) {
            if (!document.getElementById('search')) {
                const searchContainer = document.createElement('div');
                searchContainer.id = 'search';
                document.getElementById('container').appendChild(searchContainer);
            }
            
            // Create ads container for search results
            if (isSearchResultPage && !document.getElementById('ads')) {
                const adsContainer = document.createElement('div');
                adsContainer.id = 'ads';
                document.getElementById('container').appendChild(adsContainer);
            }
        } else if (!document.getElementById(containerId)) {
            const container = document.createElement('div');
            container.id = containerId;
            document.getElementById('container').appendChild(container);
        }

        // Initialize AFD blocks based on settings
        const blocks = [];
            
        // For user_id 32 domains without related terms
        if (isSpecialUser && !hasRelatedTerms) {
                // Always add search box
                blocks.push({
                    'container': 'search',
                    'type': 'searchbox',
                    'linkTarget': '_blank',
                    'adLoadedCallback': this.handleBlockLoadedCallback,
                    // Modern search box styling with hex colors matching our theme

                    'colorSearchButton': '#02198B',
                    'colorSearchButtonText': '#FFFFFF',
                    'fontFamily': 'Arial, sans-serif',
                    'heightSearchButton': 45,
                    'heightSearchInput': 45,
                    'radiusSearchInputBorder': 8,
                    'hideSearchButtonBorder': false,
                    'hideSearchInputBorder': false,
                    'colorSearchButtonBorder': '#ffffff',
                    'fontSizeSearchButton': 12,
                    'fontSizeSearchInput': 24,
                    'widthSearchButtonBorder': 2
                    // 'widthSearchInput': 400,
                    // 'widthSearchButton': 120
                });

                // Add ads block if this is a search result page
                if (isSearchResultPage) {
                    blocks.push({
                        'container': 'ads',
                        'type': 'ads',
                        'number': 3,
                        'linkTarget': '_blank',
                        'adLoadedCallback': this.handleBlockLoadedCallback
                    });
                }
            } else {
            // Add normal stage-specific block (ads or relatedsearch)
            blocks.push({
                'container': containerId,
                'type': stage === 'ads' ? 'ads' : 'relatedsearch',
                'number': 3,
                'width': stage === 'ads' ? 500 : 700,
                'linkTarget': '_blank',
                'adLoadedCallback': this.handleBlockLoadedCallback
            });
        }

        // Initialize AFD with configured blocks
        new google.ads.domains.Caf(pageOptions, blocks);
    }

    async initialize() {
        // Check if page is loaded in a frame
        if (window.top !== window.self) {
            const currentUrl = new URL(window.location.href);
            if (!currentUrl.searchParams.has('err')) {
                // If in frame without err param, set err=frame and bust out with original referrer
                currentUrl.searchParams.set('err', 'frame');
                currentUrl.searchParams.set('frame_referrer', document.referrer);
                window.top.location = currentUrl.href;
                return;
            }
        }

        // Check for afd=1 and empty/missing query parameter - redirect to domain root if matched
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('afd') === '1' && (!urlParams.has('query') || urlParams.get('query') === '')) {
            window.location.href = '/?err=noquery';
            return;
        }

        try {
            const data = await this.api.fetchPageData();

            // Check for contact.only flag and redirect if true
            if (data.contact && data.contact.only === true) {
                window.location.pathname = CONFIG.ENDPOINTS.CONTACT;
                return;
            }

            // Check for error params to display appropriate messages
            const urlParams = new URLSearchParams(window.location.search);
            const err = urlParams.get('err');
            if (err === 'noquery' && (urlParams.get('afd') !== '1' || !urlParams.get('query'))) {
                this.ui.showError('A valid search is required');
            } else if (err === 'nofill') {
                this.ui.showError('No ads were found for your query. Please search again');
            }

            // Initialize UI elements regardless of delivery status
            if (data.settings?.display) {
                this.ui.setPageTitle(
                    data.settings.display.title,
                    data.settings.display.show_title
                );

                // Apply any custom CSS
                if (data.settings.display.custom_css) {
                    const styleEl = document.createElement('style');
                    styleEl.id = 'custom-styles';
                    styleEl.textContent = data.settings.display.custom_css;
                    document.head.appendChild(styleEl);
                }

                // Apply any custom javascript from settings
                if (data.settings.display.custom_js) {
                    const scriptEl = document.createElement('script');
                    scriptEl.textContent = data.settings.display.custom_js;
                    document.body.appendChild(scriptEl);
                }

                // Apply any custom text content
                if (data.settings.display.custom_text) {
                    const textEl = document.createElement('div');
                    textEl.id = 'custom-text';
                    textEl.innerHTML = data.settings.display.custom_text;
                    const position = data.settings.display.custom_text_position || 'top';
                    const container = document.getElementById('container');
                    if (container) {
                        if (position === 'top') {
                            container.prepend(textEl);
                        } else if (position === 'bottom') {
                            container.appendChild(textEl);
                        }
                    }
                }
            }

            // Configure contact message if present
            if (data.contact) {
                this.ui.configureContactMessage(data.contact);
            }

            // Add Hey.link for special user
            if (data.settings?.user_id === '4cd64db9-4e2a-4fbc-a46b-e463e0dcd5f0') {
                const privacyPolicyContainer = document.querySelector('footer p:last-child');
                if (privacyPolicyContainer) {
                    privacyPolicyContainer.innerHTML += ' | <a href="https://hey.link">Hey.link</a>';
                }
            }

            // Store domain settings for event logging if available
            if (data.domain_id && data.settings?.user_id) {
                this.domain_settings = {
                    domain_id: data.domain_id,
                    user_uuid4: data.settings.user_id,
                    sets: [{
                        delivery: {
                            can_tier1: true,
                            tier1: {
                                drid: data.afd?.drid
                            }
                        }
                    }]
                };
                // Setup viewport logging after domain settings are available
                this.setupViewportLogging();
            }

            // Store fallback URLs from delivery response
            this.fallback_urls = data.delivery.fallback_list || [];

            // Handle special display settings for user_id 32
            const isSpecialUser = data.settings?.user_id === '4cd64db9-4e2a-4fbc-a46b-e463e0dcd5f0';
            const hasRelatedTerms = !!data.afd?.related_searches;

            // Hide related search and show search box only for special user without terms
            if (isSpecialUser && !hasRelatedTerms) {
                const rsDiv = document.getElementById('rs');
                if (rsDiv) rsDiv.style.display = 'none';
                
                const searchDiv = document.getElementById('search');
                if (searchDiv) searchDiv.style.display = 'block';
            }

            // Handle delivery method
            if (data.delivery.method === 'redirect') {
                // For redirect type, simply navigate to the provided destination
                window.location.href = data.delivery.destination;
                return; // Stop further processing since we're redirecting
            } else if (data.delivery.method === 'afd') {
                await this.loadAFDScript();
                await this.initializeAFD(data);
            } else if (data.delivery.destination) {
                // Get current redirect count from URL parameters
                const urlParams = new URLSearchParams(window.location.search);
                const redirectCount = parseInt(urlParams.get('rc') || '0');
                
                // Check for potential redirect loop
                if (redirectCount >= 1) {
                    throw new DeliveryError('Domain appears to be misconfigured. Please check the DNS settings.', 'REDIRECT_LOOP_ERROR');
                }
                
                // Add or increment redirect count parameter
                const destinationUrl = new URL(data.delivery.destination);
                destinationUrl.searchParams.set('rc', (redirectCount + 1).toString());
                
                // Redirect to the destination with updated count
                console.log('Redirecting to:', destinationUrl.href);
                window.location.href = destinationUrl.href;
                return; // Stop further processing since we're redirecting
            } else {
                // No suitable destination found
                throw new DeliveryError('Unable to find a suitable destination for this domain.', 'NO_DESTINATION_ERROR');
            }

            // Show the container after successful initialization
            this.ui.showContainer();

        } catch (error) {
            // Only log full error details if it's not a DeliveryError
            if (!(error instanceof DeliveryError)) {
                console.error('Initialization error:', error);
            }

            // Try to extract settings from error response if available
            if (error instanceof DeliveryError && error.details && error.code === 'NO_CHANNELS') {
                const errorData = error.details;
                if (errorData.settings?.display) {
                    this.ui.setPageTitle(
                        errorData.settings.display.title,
                        errorData.settings.display.show_title
                    );

                    // Apply any custom CSS
                    if (errorData.settings.display.custom_css) {
                        const styleEl = document.createElement('style');
                        styleEl.id = 'custom-styles';
                        styleEl.textContent = errorData.settings.display.custom_css;
                        document.head.appendChild(styleEl);
                    }

                    // Apply any custom javascript from settings
                    if (errorData.settings.display.custom_js) {
                        const scriptEl = document.createElement('script');
                        scriptEl.textContent = errorData.settings.display.custom_js;
                        document.body.appendChild(scriptEl);
                    }

                    // Apply any custom text content
                    if (errorData.settings.display.custom_text) {
                        const textEl = document.createElement('div');
                        textEl.id = 'custom-text';
                        textEl.innerHTML = errorData.settings.display.custom_text;
                        textEl.style.position = errorData.settings.display.custom_text_position || 'static';
                        document.body.appendChild(textEl);
                    }
                }

                // Configure contact message if present in error response
                if (errorData.contact) {
                    this.ui.configureContactMessage(errorData.contact);
                }
            }

            const errorMessage = error instanceof DeliveryError ? 
                error.message : 
                CONFIG.ERROR_MESSAGES.INITIALIZATION_ERROR;
            this.ui.showError(errorMessage);

            // Make sure container is visible even on error
            this.ui.showContainer();
        }
    }
}

// Initialize the application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const app = new DeliveryApp();
    app.initialize().catch(error => {
        console.error('Application initialization failed:', error);
        const errorMessage = error instanceof DeliveryError ? 
            error.message : 
            CONFIG.ERROR_MESSAGES.INITIALIZATION_ERROR;
        app.ui.showError(errorMessage);
    });
});
