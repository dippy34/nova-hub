let backup_icon;
let backup_name;
let socket;
if (location.origin.includes("https")) {
	socket = new WebSocket(`wss://${location.host}/socket`);
} else {
	socket = new WebSocket(`ws://${location.host}/socket`);
}
socket.addEventListener("open", (event) => {
	let cookies = document.cookie.split("; ");
	for (let i = 0; i < cookies.length; i++) {
		if (cookies[i].trim().startsWith("token=")) {
			socket.send(cookies[i].trim());
		}
	}
});
socket.addEventListener("message", (event) => {
	if (event.data == "ping") {
		socket.send(`pong${location.pathname.includes("/semag/") ? location.pathname.split("/")[2] : ""}`);
		return;
	}
	if (event.data.startsWith("announce.")) {
		let styles = document.createElement("style");
		styles.innerHTML = `@import url("https://fonts.googleapis.com/css2?family=Prompt:wght@300&display=swap");.announce {font-family: "Prompt", sans-serif;position: absolute;margin-left: auto;margin-right: auto;top: 10px;z-index: 10000000;background-color: #a53026;padding: 10px;width: max-content;border-radius: 10px;left:0;right:0;border-color: #f74f40;border-width: 5px;border-radius: 10px;border-style: solid;max-width: 60%;font-size: 16px;color: white;}@keyframes FadeIn {0% {opacity: 0;}100% {opacity: 1;}}@keyframes FadeOut {0% {opacity: 1;}100% {opacity: 0;}}`;
		let announcement = document.createElement("div");
		announcement.innerText = event.data.substring(9);
		announcement.setAttribute("class", "announce");
		announcement.style.opacity = "0";
		announcement.style.animation = "FadeIn 1s ease-in-out forwards";
		document.head.appendChild(styles);
		document.body.appendChild(announcement);
		setTimeout(() => {
			announcement.style.animation = "FadeOut 1s ease-in-out forwards";
			setTimeout(() => {
				announcement.remove();
				styles.remove();
			}, 1000);
		}, 14000);
	}
});

let cloakIconElement = null;
let cloakTitleBackup = null;

function setCloak(name, icon) {
	// Cache title backup once
	if (!cloakTitleBackup) {
		cloakTitleBackup = document.title;
	}
	
	// Set title immediately (fast operation)
	if (name) {
		document.title = name;
	} else {
		var tabname = getCookie("tabname");
		if (tabname) {
			document.title = tabname;
		}
	}

	// Handle icon efficiently
	var targetIcon = icon || getCookie("tabicon");
	if (targetIcon) {
		// Use cached element or create once
		if (!cloakIconElement) {
			// Remove existing icon links efficiently
			const existingIcons = document.querySelectorAll("link[rel~='icon'], link[rel~='shortcut icon']");
			if (existingIcons.length > 0 && !backup_icon) {
				backup_icon = existingIcons[0].cloneNode(true);
			}
			existingIcons.forEach(el => el.remove());
			
			// Create single icon element
			cloakIconElement = document.createElement("link");
			cloakIconElement.rel = "icon";
			document.head.appendChild(cloakIconElement);
		}
		// Update href (fast operation)
		cloakIconElement.href = targetIcon;
	}

	panicMode();
}
if (getCookie("debugging") == 1) {
	const debugscript = document.createElement("script");
	debugscript.setAttribute("src", "/js/debug.js");
	document.head.append(debugscript);
}
function getCookie(cname) {
	let name = cname + "=";
	let decodedCookie = decodeURIComponent(document.cookie);
	let ca = decodedCookie.split(";");
	for (let i = 0; i < ca.length; i++) {
		let c = ca[i];
		while (c.charAt(0) == " ") {
			c = c.substring(1);
		}
		if (c.indexOf(name) == 0) {
			return c.substring(name.length, c.length);
		}
	}
	return "";
}
let listofchars = "";
document.addEventListener("keydown", (e) => {
	listofchars = listofchars + e.key;
	if (listofchars.length > 20) {
		listofchars = listofchars.substring(e.key.length);
	}
	if (listofchars.includes("safemode")) {
		window.location.href = panicurl;
		listofchars = "";
	} else if (listofchars.includes("debugplz")) {
		if (getCookie("debugging") == 1) {
			document.cookie = "debugging=0;";
			alert("debugging off!");
		} else {
			document.cookie = "debugging=1";
			alert("debugging on!");
		}
		listofchars = "";
	}
});
function panicMode() {
	panicurl = getCookie("panicurl");
	if (panicurl == "") {
		panicurl = "https://google.com";
	}
}
document.addEventListener(
	"DOMContentLoaded",
	() => {
		// Set initial backups before applying cloak
		cloakTitleBackup = document.title;
		const existingIcon = document.querySelector("link[rel~='icon'], link[rel~='shortcut icon']");
		if (existingIcon && !backup_icon) {
			backup_icon = existingIcon.cloneNode(true);
		}
		setCloak();
		let plausible = document.createElement("script");
		plausible.setAttribute("event-domain", location.host)
		plausible.setAttribute("defer", "");
		plausible.setAttribute("src", "/js/analytics.js");
		plausible.setAttribute("data-domain", "selenite.cc");
		document.head.appendChild(plausible);
	},
	false
);
if (location.pathname.substring(1).includes("semag") && localStorage.getItem("selenite.blockClose") == "true") {
	window.onbeforeunload = function () {
		return "";
	};
}
let visibilityTimeout = null;
addEventListener("visibilitychange", (e) => {
	if (localStorage.getItem("selenite.tabDisguise") == "true") {
		// Clear any pending timeout
		if (visibilityTimeout) {
			clearTimeout(visibilityTimeout);
		}
		
		// Use requestAnimationFrame for better performance on mobile
		requestAnimationFrame(() => {
			if (document.visibilityState === "hidden") {
				setCloak("Google", "https://www.google.com/favicon.ico");
			} else {
				// Restore original icon efficiently
				if (cloakIconElement) {
					if (backup_icon) {
						cloakIconElement.href = backup_icon.href;
					} else {
						cloakIconElement.href = location.origin + "/nova-favicon.ico";
					}
				}
				// Restore original title
				if (cloakTitleBackup) {
					document.title = cloakTitleBackup;
				} else if (backup_name) {
					document.title = backup_name;
				}
			}
		});
	}
});
var polyfillScript = document.createElement("script");
polyfillScript.src = "https://cdnjs.cloudflare.com/polyfill/v3/polyfill.min.js?version=4.8.0";
document.head.appendChild(polyfillScript);
function fps() {
	var script = document.createElement("script");
	script.onload = function () {
		var stats = new Stats();
		document.body.appendChild(stats.dom);
		requestAnimationFrame(function loop() {
			stats.update();
			requestAnimationFrame(loop);
		});

		localStorage.setItem("fps", true);
	};
	script.src = "https://cdn.jsdelivr.net/gh/mrdoob/stats.js@master/build/stats.min.js";
	document.head.appendChild(script);
}

if (localStorage.getItem("fps")) {
	fps();
}
