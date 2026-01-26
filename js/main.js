var interval;

// Define setTheme globally before DOMContentLoaded
function setTheme(theme) {
	// Save theme to cookie instead of localStorage
	setCookie("selenite.theme", theme);
	
	// Remove all theme classes first
	document.body.classList.remove("gaming-theme", "cyberpunk-theme", "ocean-theme", "sunset-theme", "purple-theme");
	
	// Apply theme immediately without reload
	if (theme === "ocean") {
		document.body.classList.add("ocean-theme");
		document.body.setAttribute("theme", "ocean");
	} else if (theme === "sunset") {
		document.body.classList.add("sunset-theme");
		document.body.setAttribute("theme", "sunset");
	} else if (theme === "purple") {
		document.body.classList.add("purple-theme");
		document.body.setAttribute("theme", "purple");
	} else {
		// Default to code theme (gaming-theme)
		document.body.classList.add("gaming-theme");
		document.body.removeAttribute("theme");
	}
	
	// Update theme cards if on settings page
	setTimeout(() => {
		if (document.querySelector('.theme-card')) {
			document.querySelectorAll('.theme-card').forEach(card => {
				card.classList.remove('theme-card-active');
				const badge = card.querySelector('.theme-badge');
				if (badge) badge.style.display = 'none';
			});
			
			const activeCard = document.getElementById(`theme-${theme}`);
			if (activeCard) {
				activeCard.classList.add('theme-card-active');
				const badge = activeCard.querySelector('.theme-badge');
				if (badge) badge.style.display = 'block';
			}
		}
	}, 50);
}

// Also assign to window for extra safety
window.setTheme = setTheme;

document.addEventListener("DOMContentLoaded", function () {
	// Migration: Move old localStorage theme to cookie if it exists
	if (localStorage.getItem("theme")) {
		setCookie("selenite.theme", localStorage.getItem("theme"));
		localStorage.removeItem("theme");
	}
	if (localStorage.getItem("selenite.theme")) {
		setCookie("selenite.theme", localStorage.getItem("selenite.theme"));
		localStorage.removeItem("selenite.theme");
	}
	
	// Always remove all theme classes first to ensure clean state
	document.body.classList.remove("gaming-theme", "cyberpunk-theme", "ocean-theme", "sunset-theme", "purple-theme");
	
	let savedTheme = getCookie("selenite.theme");
	if (savedTheme) {
		if (savedTheme === "code" || savedTheme === "default") {
			document.body.classList.add("gaming-theme");
			document.body.removeAttribute("theme");
		} else if (savedTheme === "ocean") {
			document.body.classList.add("ocean-theme");
			document.body.setAttribute("theme", "ocean");
		} else if (savedTheme === "sunset") {
			document.body.classList.add("sunset-theme");
			document.body.setAttribute("theme", "sunset");
		} else if (savedTheme === "purple") {
			document.body.classList.add("purple-theme");
			document.body.setAttribute("theme", "purple");
		} else {
			// Legacy theme support - default to code
			document.body.classList.add("gaming-theme");
			document.body.removeAttribute("theme");
			setCookie("selenite.theme", "code");
		}
	} else {
		// Default to code theme (gaming-theme)
		document.body.classList.add("gaming-theme");
		document.body.removeAttribute("theme");
		setCookie("selenite.theme", "code");
	}
	if (document.querySelectorAll("[id=adcontainer]")) {
		for (let i = 0; i < document.querySelectorAll("[id=adcontainer]").length; i++) {
			const adblockEnabled = getCookie("selenite.adblock") == "true";
			// Migration: check localStorage too
			if (localStorage.getItem("selenite.adblock") == "true") {
				setCookie("selenite.adblock", "true");
				localStorage.removeItem("selenite.adblock");
			}
			if (Math.random() < 0.5 || adblockEnabled) document.querySelectorAll("[id=adcontainer]")[i].innerHTML = "";
		}
	}
	const iconSetting = document.querySelector("input#discordIcon");
	const blockClose = document.querySelector("input#blockClose");
	const openBlank = document.getElementById("blank");
	const bgTheme = document.querySelector("input#bgTheme");
	// if (document.querySelector("widgetbot-crate")) {
	// 	if (localStorage.getItem("selenite.discordIcon") == "true") {
	// 		const widget = document.querySelector("widgetbot-crate");
	// 		widget.setAttribute("style", "display:none");
	// 	}
	// }
	if (document.querySelector("input#discordIcon")) {
		// Migration: check localStorage first
		if (localStorage.getItem("selenite.discordIcon") == "true") {
			setCookie("selenite.discordIcon", "true");
			localStorage.removeItem("selenite.discordIcon");
			iconSetting.checked = true;
		} else if (getCookie("selenite.discordIcon") == "true") {
			iconSetting.checked = true;
		}
		iconSetting.addEventListener("click", () => {
			setCookie("selenite.discordIcon", iconSetting.checked ? "true" : "false");
		});
	}
	if (document.querySelector("input#blockClose")) {
		// Migration: check localStorage first
		if (localStorage.getItem("selenite.blockClose") == "true") {
			setCookie("selenite.blockClose", "true");
			localStorage.removeItem("selenite.blockClose");
			blockClose.checked = true;
		} else if (getCookie("selenite.blockClose") == "true") {
			blockClose.checked = true;
		}
		blockClose.addEventListener("click", () => {
			setCookie("selenite.blockClose", blockClose.checked ? "true" : "false");
		});
	}
	const tabDisguise = document.querySelector("input#tabDisguise");
	if (tabDisguise) {
		// Migration: check localStorage first
		if (localStorage.getItem("selenite.tabDisguise") == "true") {
			setCookie("selenite.tabDisguise", "true");
			localStorage.removeItem("selenite.tabDisguise");
			tabDisguise.checked = true;
		} else if (getCookie("selenite.tabDisguise") == "true") {
			tabDisguise.checked = true;
		}
		tabDisguise.addEventListener("click", () => {
			setCookie("selenite.tabDisguise", tabDisguise.checked ? "true" : "false");
		});
	}
	if (bgTheme) {
		bgTheme.checked = true;
	}
	if (document.getElementById("blank")) {
		document.getElementById("blank").addEventListener("click", () => {
			win = window.open();
			win.document.body.style.margin = "0";
			win.document.body.style.height = "100vh";
			html = `
        <style>*{margin:0;padding:0;border:none}body,iframe{height:100vh;width:100vw}iframe{height:96vh}header{display:flex;height:4vh;justify-content:center;}button{margin-right:100px;height:100%;aspect-ratio: 1 / 1}#reload{background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' height='24' viewBox='0 -960 960 960' width='24'%3E%3Cpath d='M480-160q-134 0-227-93t-93-227q0-134 93-227t227-93q69 0 132 28.5T720-690v-110h80v280H520v-80h168q-32-56-87.5-88T480-720q-100 0-170 70t-70 170q0 100 70 170t170 70q77 0 139-44t87-116h84q-28 106-114 173t-196 67Z'/%3E%3C/svg%3E");background-size:cover;}#goBack{background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' height='24' viewBox='0 -960 960 960' width='24'%3E%3Cpath d='M240-200h120v-240h240v240h120v-360L480-740 240-560v360Zm-80 80v-480l320-240 320 240v480H520v-240h-80v240H160Zm320-350Z'/%3E%3C/svg%3E");background-size:cover;}</style><script>
        </script><header><button id=goBack></button><button id=reload></button></header><iframe id=selenite></iframe>`;
		win.document.querySelector("html").innerHTML = html;
		win.eval(`let selenite = document.getElementById("selenite");console.log(selenite);selenite.setAttribute("src", "${location.origin}");console.log(selenite);document.getElementById("goBack").addEventListener("click", function () {selenite.contentDocument.location.href = selenite.contentDocument.location.origin;});document.getElementById("reload").addEventListener("click", function () {selenite.contentDocument.location.href = selenite.contentDocument.location.href;})`);
		location.href = "https://google.com";
		close();
	});
	}
	if (typeof $ !== 'undefined' && $("#panicmode").length > 0) {
		$("#panicmode").prop({ href: panicurl });
	}
	if (typeof $ !== 'undefined' && $(".seleniteminified").length > 0) {
		$.get("https://raw.githubusercontent.com/skysthelimitt/selenite-optimized/main/build/bookmark.txt", function (data) {
			$(".seleniteminified").prop({ href: data });
		});
		$.get("https://raw.githubusercontent.com/car-axle-client/car-axle-client/v10/dist/build.js", function (data) {
			$(".caraxle").prop({ href: `javascript:${encodeURI(data)}` });
		});
	}

	// Load site banner from API (same KV as terminal text)
	fetch('/api/banner').then(function (r) { return r.json(); }).then(function (data) {
		if (!data || !data.success || !data.data || !data.data.enabled || !String(data.data.text).trim()) return;
		var el = document.getElementById('nova-site-banner');
		if (el) return;
		el = document.createElement('div');
		el.id = 'nova-site-banner';
		el.className = 'nova-site-banner';
		el.textContent = data.data.text;
		document.body.insertBefore(el, document.body.firstChild);
		document.body.classList.add('nova-site-banner-visible');
	}).catch(function () {});
});

function setPanicMode() {
	if (typeof $ === 'undefined' || $("#panic").length === 0) return;
	if (!$("#panic").val().startsWith("https")) {
		document.cookie = "panicurl=https://" + $("#panic").val();
		return;
	}
	document.cookie = "panicurl=" + $("#panic").val();
}

function copyToClipboard(text) {
	navigator.clipboard.writeText(text);
	alert("Copied text!");
}

function setCloakCookie() {
	if (typeof $ === 'undefined' || $("#panic").length === 0) return;
	if (!$("#panic").val().startsWith("https")) {
		document.cookie = "panicurl=https://" + $("#panic").val();
		return;
	}
	document.cookie = "panicurl=" + $("#panic").val();
}
function setPassword() {
	setCookie("selenite.password", enc.encode(document.getElementById("pass").value));
}
function delPassword() {
	location.hash = "";
	removeCookie("selenite.passwordAtt");
	removeCookie("selenite.password");
}

if (typeof $ !== 'undefined') {
$(document).ready(function () {
		if (!window.location.href.startsWith("about:") && $("#webicon").length > 0) {
		$("#webicon").attr("placeholder", window.location.href.replace(/\/[^\/]*$/, "/"));
	}
});
}
function loadScript(a, b) {
	var c = document.createElement("script");
	(c.type = "text/javascript"), (c.src = a), (c.onload = b), document.head.appendChild(c);
}
function toast(message, onclick) {
	const toast = document.createElement("div");
	toast.setAttribute("id", "toast");
	console.log(message.time);
	toast.innerHTML = `<div class=samerow><h1>${message.title}${message.time ? ` - ${timeAgo(new Date(message.time * 1000))}` : ""}</h1></div><p>${message.message}</p>`;
	toast.style.animation = "toastFade 6s";
	document.body.appendChild(toast);
	if (onclick) {
		toast.addEventListener("click", onclick);
		toast.style.cursor = "pointer";
	}
	setTimeout(() => {
		toast.remove();
	}, 6000);
}
function timeAgo(input) {
	const date = input instanceof Date ? input : new Date(input);
	const formatter = new Intl.RelativeTimeFormat("en");
	const ranges = {
		years: 3600 * 24 * 365,
		months: 3600 * 24 * 30,
		weeks: 3600 * 24 * 7,
		days: 3600 * 24,
		hours: 3600,
		minutes: 60,
		seconds: 1,
	};
	const secondsElapsed = (date.getTime() - Date.now()) / 1000;
	for (let key in ranges) {
		if (ranges[key] < Math.abs(secondsElapsed)) {
			const delta = secondsElapsed / ranges[key];
			return formatter.format(Math.round(delta), key);
		}
	}
}
let cookieConsentScript = document.createElement("script");
cookieConsentScript.src = "/js/cookieConsent.js";
document.head.appendChild(cookieConsentScript);
let cookieConsentStyle = document.createElement("link");
cookieConsentStyle.href = "/js/cookieConsent.css";
cookieConsentStyle.rel = "stylesheet";
document.head.appendChild(cookieConsentStyle);