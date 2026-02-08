function customTheme() {
	setCookie("novahub.theme", "custom");
	document.body.classList.remove("gaming-theme");
	document.body.setAttribute("theme", "custom");
	if (document.getElementById("customMenu")) {
		document.getElementById("customMenu").style.display = "block";
	}
	loadTheme();
	// Don't reload here - user needs to interact with custom menu
}
document.addEventListener("DOMContentLoaded", () => {
	loadTheme();
	// Migration: check localStorage first
	if (localStorage.getItem("novahub.theme") == "custom") {
		setCookie("novahub.theme", "custom");
		localStorage.removeItem("novahub.theme");
	}
    if(getCookie("novahub.theme") == "custom"){
        const customMenu = document.getElementById("customMenu");
        if (customMenu) {
            customMenu.style.display = "block";
            const inputbg = document.getElementById("inputbg");
            const uibg = document.getElementById("uibg");
            const textcolor = document.getElementById("textcolor");
            const bg = document.getElementById("bg");
            const bgimg = document.getElementById("bgimg");
            if (inputbg) inputbg.value = getComputedStyle(document.body).getPropertyValue("--inputbg");
            if (uibg) uibg.value = getComputedStyle(document.body).getPropertyValue("--uibg");
            if (textcolor) textcolor.value = getComputedStyle(document.body).getPropertyValue("--textcolor");
            if (bg) {
                if(getComputedStyle(document.body).getPropertyValue("--bg").includes("url")){
                    if (bgimg) bgimg.value = getComputedStyle(document.body).getPropertyValue("--bg").replace("url(", "").replace(")", "");
                    bg.value = "#000000";
                } else {
                    bg.value = getComputedStyle(document.body).getPropertyValue("--bg");
                }
            }
        }
    }
	if(location.pathname.includes("/settings")) {
		const inputbg = document.getElementById("inputbg");
		const inputborder = document.getElementById("inputborder");
		const uibg = document.getElementById("uibg");
		const textcolor = document.getElementById("textcolor");
		const bg = document.getElementById("bg");
		const bgimg = document.getElementById("bgimg");
		if (inputbg) {
			inputbg.addEventListener("change", (e) => {
				changeTheme("inputbg", e.target.value);
			});
		}
		if (inputborder) {
			inputborder.addEventListener("change", (e) => {
				changeTheme("inputborder", e.target.value);
			});
		}
		if (uibg) {
			uibg.addEventListener("change", (e) => {
				changeTheme("uibg", e.target.value);
			});
		}
		if (textcolor) {
			textcolor.addEventListener("change", (e) => {
				changeTheme("textcolor", e.target.value);
			});
		}
		if (bg) {
			bg.addEventListener("change", (e) => {
				changeTheme("bg", e.target.value);
			});
		}
		if (bgimg) {
			bgimg.addEventListener("keydown", (e) => {
				if (e.key == "Enter") {
					changeTheme("bg", e.target.value);
				}
			});
		}
	}
});
function loadTheme() {
	// Migration: check localStorage first
	if (localStorage.getItem("novahub.theme") == "custom" || getCookie("novahub.theme") == "custom") {
		let theme = getCookie("novahub.customTheme");
		// Migration: check localStorage
		if (!theme && localStorage.getItem("novahub.customTheme")) {
			theme = localStorage.getItem("novahub.customTheme");
			setCookie("novahub.customTheme", theme);
			localStorage.removeItem("novahub.customTheme");
		}
		if (theme) {
			try {
				theme = JSON.parse(theme);
			} catch (e) {
				// If parsing fails, try decodeURIComponent
				try {
					theme = JSON.parse(decodeURIComponent(theme));
				} catch (e2) {
					return;
				}
			}
			for (let i = 0; i < Object.keys(theme).length; i++) {
				document.body.style.setProperty(`--${Object.keys(theme)[i]}`, eval(`theme.${Object.keys(theme)[i]}   `));
			}
		}
	}
}

function changeTheme(name, value) {
    if(isValidHttpUrl(value)){
        value = `url(${value})`;
    }
	// Migration: check localStorage first
	ogStyle = getCookie("novahub.customTheme");
	if (!ogStyle && localStorage.getItem("novahub.customTheme")) {
		ogStyle = localStorage.getItem("novahub.customTheme");
		setCookie("novahub.customTheme", ogStyle);
		localStorage.removeItem("novahub.customTheme");
	}
	if (ogStyle) {
		try {
			ogStyle = JSON.parse(decodeURIComponent(ogStyle));
		} catch (e) {
			try {
				ogStyle = JSON.parse(ogStyle);
			} catch (e2) {
				ogStyle = {};
			}
		}
		ogStyle[name] = value;
		setCookie("novahub.customTheme", encodeURIComponent(JSON.stringify(ogStyle)));
		loadTheme();
	} else {
		ogStyle = {};
		ogStyle[name] = value;
		setCookie("novahub.customTheme", encodeURIComponent(JSON.stringify(ogStyle)));
		loadTheme();
	}
}

// https://stackoverflow.com/a/43467144
function isValidHttpUrl(string) {
    let url;
    
    try {
      url = new URL(string);
    } catch (_) {
      return false;  
    }
  
    return url.protocol === "http:" || url.protocol === "https:";
  }