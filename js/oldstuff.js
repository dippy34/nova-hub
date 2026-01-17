
// if (location.hash) {
// 	let temp;
// 	if(!location.pathname.includes("gba")) {
// 		localStorage.setItem("selenite.password", location.hash.substring(1));
// 		if (JSON.parse(localStorage.getItem("selenite.passwordAtt"))) {
// 			if (JSON.parse(localStorage.getItem("selenite.passwordAtt"))[0] == true && Math.floor(Date.now() / 1000) - JSON.parse(localStorage.getItem("selenite.passwordAtt"))[1] < 600) {
// 				console.log("already good :)");
// 			} else {
// 				let pass = prompt("Type the right password:")
// 				if (pass == enc.decode(location.hash.substring(1)) || pass == "tempgbafix") {
// 					localStorage.setItem("selenite.passwordAtt", `[true,${Math.floor(Date.now() / 1000)}]`);
// 					console.log("Correct password!");
// 				} else {
// 					localStorage.setItem("selenite.passwordAtt", `[false,${Math.floor(Date.now() / 1000)}]`);
// 					location.href = "https://google.com";
// 				}
// 			}
// 		} else {
// 			let pass = prompt("Type the right password:")
// 			if (pass == enc.decode(location.hash.substring(1)) || pass == "tempgbafix") {
// 				localStorage.setItem("selenite.passwordAtt", `[true,${Math.floor(Date.now() / 1000)}]`);
// 				console.log("Correct password!");
// 			} else {
// 				localStorage.setItem("selenite.passwordAtt", `[false,${Math.floor(Date.now() / 1000)}]`);
// 				location.href = "https://google.com";
// 			}
// 		}
// 	}
// }
// Migration: check cookie first, then localStorage
let passwordFromStorage = getCookie("selenite.password");
if (!passwordFromStorage && localStorage.getItem("selenite.password")) {
	passwordFromStorage = localStorage.getItem("selenite.password");
	setCookie("selenite.password", passwordFromStorage);
	localStorage.removeItem("selenite.password");
}
if(passwordFromStorage && !location.hash) {
	alert("password, but no hash");
}
if (location.hash) {
	function isSeleniteHash(hash) {
		try {
			decodedHash = enc.decode(hash);
			JSON.parse(decodedHash);
			return true;
		} catch {
			console.error("failed :(");
			return false;
		}
	}
	function tryPass(password) {
		let passAttempt = prompt("Type your Selenite password:");
		// Migration: check cookie first, then localStorage
		let storedPassword = getCookie("selenite.password");
		if (!storedPassword && localStorage.getItem("selenite.password")) {
			storedPassword = localStorage.getItem("selenite.password");
			setCookie("selenite.password", storedPassword);
			localStorage.removeItem("selenite.password");
		}
		if(storedPassword) {
			if(passAttempt == password) {
				return false;
			}
		} else {
			setCookie("selenite.password", enc.encode(password));
			return true;
		}
	}
	if (isSeleniteHash(location.hash.substring(1))) {
		decodedHash = JSON.parse(enc.decode(location.hash.substring(1)));
		if (decodedHash["selenite"]) {
			if (decodedHash["pass"]) {
				tryPass(decodedHash["pass"]);
			}
			if (decodedHash["theme"]) {
				if (changeTheme) {
					alert("theme detected!!");
				}
			}
		}
	}
}
