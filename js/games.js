// Games base URL - use external domain for game files
const GAMES_BASE_URL = window.GAMES_BASE_URL || "https://nova-labs.pages.dev";

$.getJSON("/data/games.json", function (data) {
	if (document.readyState === "complete") {
		loadGames(data);
	} else {
		let areGamesReady = setInterval(() => {
			if (document.readyState === "complete") {
				loadGames(data);
				clearInterval(areGamesReady);
			}
		}, 50);
	}
});

function loadGames(data) {
	starredgames = getCookie("starred");
	if (!starredgames) {
		starredgames = [];
	} else {
		starredgames = JSON.parse(decodeURIComponent(getCookie("starred")));
	}
	$("#gamesearch").prop({
		placeholder: "Click here to search through our " + data.length + " games!",
	});
	data.sort(dynamicSort("name"));
	gamelist = data;
	for (let i = 0; i < data.length; i++) {
		let $element = $("<a>")
			.attr({
				class: "game",
				id: data[i].directory,
				recommended: data[i].recommended,
				// href: "loader.html#" + btoa(encodeURIComponent(JSON.stringify([data[i].directory, data[i].image, data[i].name]))),
				href: GAMES_BASE_URL + "/semag/" + data[i].directory + "/index.html",
			})
			.data("recommended", data[i].recommended)
			.append(
				$("<img>").prop({
					src: GAMES_BASE_URL + "/semag/" + data[i].directory + "/" + data[i].image,
					alt: data[i].name + " logo",
					loading: "lazy"
				})
			)
			.append($("<h1>").text(data[i].name))
			.append(
				$("<img>").prop({
					src: "img/star.svg",
					alt: "star",
					class: "star",
				})
			);

		if (starredgames.includes(data[i].directory)) {
			$element.find("img.star").attr("id", "starred");
			$element.find("img.star").attr("src", "img/star-fill.svg");
			let $pinnedelement = $element.clone();
			$("#pinned").append($pinnedelement);
			if ($("#pinnedmessage")) {
				$("#pinnedmessage").hide();
			}
		}

		$("#games").append($element);
	}
	$("#games #message").remove();

	// Apply search filter if active (using the new search function)
	if (typeof window.searchActive !== 'undefined' && window.searchActive) {
		if (typeof window.searchGames === 'function') {
			window.searchGames();
		}
	}

	// starred games
	let starred;
	$(document).on("click", "img.star", function (event) {

	});
	$(document).on("click", ".game", function (event) {
		if ($(event.target).is("img.star")) {
			event.preventDefault();
			event.stopPropagation();
			if (!$(event.target).attr("id")) {
				$(event.target).prop({ id: "starred" });
				$(event.target).prop({ src: "img/star-fill.svg" });
				starred = Cookies.get("starred");
				if (starred) {
					starred = JSON.parse(starred);
				} else {
					starred = [];
				}
				starred.push($(this).attr("id"));
				Cookies.set("starred", JSON.stringify(starred));
				$element = $(this).clone();
				$("#pinned").append($element);
				$("#pinnedmessage").hide();
				temp = $("#pinned")[0].childNodes;
				pinnedarray = [...temp];
				pinnedarray.sort(dynamicSort("id"));
				$("#pinned").empty();
				for (let i = 0; i < pinnedarray.length; i++) {
					pinnedarraynodes = pinnedarray[i].childNodes;
					pinnedarraynodes = [...pinnedarraynodes];
					let $element = $("<div>")
						.prop({
							class: "game",
							id: pinnedarray[i].id,
						})
						.append(
							$("<img>").prop({
								src: pinnedarraynodes[0].src,
								alt: pinnedarraynodes[0].alt,
								class: "gameicon",
							})
						)
						.append($("<h1>").text(pinnedarraynodes[1].innerHTML))
						.append(
							$("<img>").prop({
								src: "img/star-fill.svg",
								alt: "star",
								class: "star",
								id: "starred",
							})
						);
					$("#pinned").append($element);
				}
			} else {
				$(event.target).removeAttr("id");
				$(event.target).attr("src", "img/star.svg");
				$thisdiv = "#" + $(this).attr("id");
				$thisdiv = $thisdiv.replace(".", "\\.");
				starred = Cookies.get("starred");
				starred = JSON.parse(starred);
				ourindex = starred.indexOf($(this).attr("id"));
				starred.splice(ourindex, 1);
				Cookies.set("starred", JSON.stringify(starred));
				$("#pinned " + $thisdiv).remove();
				if ($("#pinned").is(":empty")) {
					$("#pinnedmessage").show();
				}
				$($thisdiv + " #starred").attr("src", "img/star.svg");
				$($thisdiv + " #starred").removeAttr("id");
			}
		}
	});
	$(document).on("click", "#game img .star", function (event) {
		event.stopPropagation();
		$(this).prop({ class: "material-symbols-outlined fill" });
	});
}

function redirectGame(dir) {
	window.location.href = GAMES_BASE_URL + "/semag/" + dir + "/index.html";
}
function dynamicSort(property) {
	var sortOrder = 1;

	if (property[0] === "-") {
		sortOrder = -1;
		property = property.substr(1);
	}
	return function (a, b) {
		if (sortOrder == -1) {
			return b[property].localeCompare(a[property]);
		} else {
			return a[property].localeCompare(b[property]);
		}
	};
}

function selectRandomGame() {
	if (gamelist && gamelist.length > 0) {
		const randomIndex = Math.floor(Math.random() * gamelist.length);
		redirectGame(gamelist[randomIndex].directory);
	} else {
		// Load games first if not loaded
		$.getJSON("/data/games.json", function (data) {
			gamelist = data;
			const randomIndex = Math.floor(Math.random() * gamelist.length);
			redirectGame(gamelist[randomIndex].directory);
		});
	}
}

let viewrecommended = 0;
function recommendedGames() {
	if (viewrecommended == 0) {
		$("#games .game").hide();
		$("#games .game").each(function () {
			if ($(this).attr("recommended")) {
				$(this).show();
			}
		});
		$("#recommend").text("Click to view all games again!");
		viewrecommended = 1;
	} else {
		$("#games .game").hide();
		$("#games .game").show();
		viewrecommended = 0;
		$("#recommend").text("Click to view recommended games!");
	}
}

// Category changer function - shows/hides category filter
let categoryViewOpen = false;
function categoryChanger() {
	if (!categoryViewOpen) {
		// Create category modal/overlay
		const categories = ['Action', 'Adventure', 'Puzzle', 'Racing', 'Sports', 'Strategy', 'Shooter', 'RPG'];
		let categoryHTML = '<div id="categoryModal" style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.95); z-index: 10000; display: flex; align-items: center; justify-content: center;">';
		categoryHTML += '<div style="background: rgba(0, 0, 0, 0.98); border: 1px solid rgba(0, 255, 0, 0.3); border-radius: 10px; padding: 2rem; max-width: 600px; width: 90%; box-shadow: 0 0 30px rgba(0, 255, 0, 0.3);">';
		categoryHTML += '<h2 style="color: #00ff00; margin-bottom: 1.5rem; text-align: center; text-shadow: 0 0 10px rgba(0, 255, 0, 0.5);">Game Categories</h2>';
		categoryHTML += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 1rem;">';
		
		// Add "All Games" option
		categoryHTML += '<button onclick="filterByCategory(\'\'); document.getElementById(\'categoryModal\').remove(); categoryViewOpen = false;" style="padding: 1rem; background: rgba(0, 255, 0, 0.1); border: 1px solid rgba(0, 255, 0, 0.3); color: #fff; border-radius: 8px; cursor: pointer; transition: all 0.3s;">All Games</button>';
		
		categories.forEach(cat => {
			categoryHTML += `<button onclick="filterByCategory('${cat}'); document.getElementById('categoryModal').remove(); categoryViewOpen = false;" style="padding: 1rem; background: rgba(0, 255, 0, 0.1); border: 1px solid rgba(0, 255, 0, 0.3); color: #fff; border-radius: 8px; cursor: pointer; transition: all 0.3s;" onmouseover="this.style.background='rgba(0, 255, 0, 0.2)'; this.style.boxShadow='0 0 10px rgba(0, 255, 0, 0.5)';" onmouseout="this.style.background='rgba(0, 255, 0, 0.1)'; this.style.boxShadow='none';">${cat}</button>`;
		});
		
		categoryHTML += '</div>';
		categoryHTML += '<button onclick="document.getElementById(\'categoryModal\').remove(); categoryViewOpen = false;" style="margin-top: 1.5rem; width: 100%; padding: 0.75rem; background: rgba(255, 0, 0, 0.2); border: 1px solid rgba(255, 0, 0, 0.3); color: #fff; border-radius: 8px; cursor: pointer;">Close</button>';
		categoryHTML += '</div></div>';
		
		$('body').append(categoryHTML);
		categoryViewOpen = true;
	} else {
		$('#categoryModal').remove();
		categoryViewOpen = false;
	}
}

// Filter games by category (basic implementation - can be enhanced with actual category data)
function filterByCategory(category) {
	if (!category || category === '') {
		$("#games .game").show();
		return;
	}
	
	// Simple filter based on game name keywords
	$("#games .game").each(function() {
		const gameName = $(this).find('h1').text().toLowerCase();
		const categoryLower = category.toLowerCase();
		let show = false;
		
		// Basic keyword matching (this is a simple implementation)
		if (categoryLower === 'action' && (gameName.includes('war') || gameName.includes('fight') || gameName.includes('battle'))) {
			show = true;
		} else if (categoryLower === 'puzzle' && (gameName.includes('puzzle') || gameName.includes('2048') || gameName.includes('lines'))) {
			show = true;
		} else if (categoryLower === 'racing' && (gameName.includes('race') || gameName.includes('car') || gameName.includes('drive'))) {
			show = true;
		} else if (categoryLower === 'sports' && (gameName.includes('soccer') || gameName.includes('football') || gameName.includes('basketball'))) {
			show = true;
		}
		
		if (show) {
			$(this).show();
		} else {
			$(this).hide();
		}
	});
}
