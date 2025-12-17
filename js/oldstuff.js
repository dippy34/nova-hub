
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
if(localStorage.getItem("selenite.password") && !location.hash) {
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
		if(localStorage.getItem("selenite.password")) {
			if(passAttempt == password) {
				return false;
			}
		} else {
			localStorage.setItem("selenite.password", enc.encode(password));
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
