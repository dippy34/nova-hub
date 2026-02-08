
// if (location.hash) {
// 	let temp;
// 	if(!location.pathname.includes("gba")) {
// 		localStorage.setItem("novahub.password", location.hash.substring(1));
// 		if (JSON.parse(localStorage.getItem("novahub.passwordAtt"))) {
// 			if (JSON.parse(localStorage.getItem("novahub.passwordAtt"))[0] == true && Math.floor(Date.now() / 1000) - JSON.parse(localStorage.getItem("novahub.passwordAtt"))[1] < 600) {
// 				console.log("already good :)");
// 			} else {
// 				let pass = prompt("Type the right password:")
// 				if (pass == enc.decode(location.hash.substring(1)) || pass == "tempgbafix") {
// 					localStorage.setItem("novahub.passwordAtt", `[true,${Math.floor(Date.now() / 1000)}]`);
// 					console.log("Correct password!");
// 				} else {
// 					localStorage.setItem("novahub.passwordAtt", `[false,${Math.floor(Date.now() / 1000)}]`);
// 					location.href = "https://google.com";
// 				}
// 			}
// 		} else {
// 			let pass = prompt("Type the right password:")
// 			if (pass == enc.decode(location.hash.substring(1)) || pass == "tempgbafix") {
// 				localStorage.setItem("novahub.passwordAtt", `[true,${Math.floor(Date.now() / 1000)}]`);
// 				console.log("Correct password!");
// 			} else {
// 				localStorage.setItem("novahub.passwordAtt", `[false,${Math.floor(Date.now() / 1000)}]`);
// 				location.href = "https://google.com";
// 			}
// 		}
// 	}
// }
// Migration: check cookie first, then localStorage
let passwordFromStorage = getCookie("novahub.password");
if (!passwordFromStorage && localStorage.getItem("novahub.password")) {
	passwordFromStorage = localStorage.getItem("novahub.password");
	setCookie("novahub.password", passwordFromStorage);
	localStorage.removeItem("novahub.password");
}
if(passwordFromStorage && !location.hash) {
	alert("password, but no hash");
}
if (location.hash) {
	function isNovahubHash(hash) {
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
		let passAttempt = prompt("Type your Nova Hub password:");
		// Migration: check cookie first, then localStorage
		let storedPassword = getCookie("novahub.password");
		if (!storedPassword && localStorage.getItem("novahub.password")) {
			storedPassword = localStorage.getItem("novahub.password");
			setCookie("novahub.password", storedPassword);
			localStorage.removeItem("novahub.password");
		}
		if(storedPassword) {
			if(passAttempt == password) {
				return false;
			}
		} else {
			setCookie("novahub.password", enc.encode(password));
			return true;
		}
	}
	if (isNovahubHash(location.hash.substring(1))) {
		decodedHash = JSON.parse(enc.decode(location.hash.substring(1)));
		if (decodedHash["novahub"]) {
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
