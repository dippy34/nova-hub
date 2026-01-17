var s = document.createElement("script");
function getMainSaveFromUpload(data) {
  data = CryptoJS.AES.decrypt(data, "egamepass").toString(CryptoJS.enc.Utf8);

  // Parse the decrypted data as JSON
  var mainSave = JSON.parse(atob(data));
  var mainLocalStorageSave = JSON.parse(atob(mainSave.localStorage));
  var cookiesSave = atob(mainSave.cookies);

  // Set the cookies using the uploaded data (primary storage)
  document.cookie = cookiesSave;

  // Migrate localStorage items to cookies, then set localStorage for backwards compatibility
  var cookieMigrationMap = {
    "selenite.theme": "selenite.theme",
    "selenite.customTheme": "selenite.customTheme",
    "selenite.lastGame": "selenite.lastGame",
    "selenite.blockClose": "selenite.blockClose",
    "selenite.tabDisguise": "selenite.tabDisguise",
    "selenite.discordIcon": "selenite.discordIcon",
    "selenite.adblock": "selenite.adblock",
    "selenite.password": "selenite.password",
    "novahub.panicUrl": "novahub.panicUrl",
    "novahub.panicEnabled": "novahub.panicEnabled",
    "fps": "fps"
  };

  for (let item of mainLocalStorageSave) {
    const key = item[0];
    const value = item[1];
    
    // If this localStorage item should be migrated to a cookie, do so
    if (cookieMigrationMap[key]) {
      // Use setCookie if available, otherwise set cookie directly
      if (typeof setCookie === 'function') {
        setCookie(cookieMigrationMap[key], value);
      } else {
        const d = new Date();
        d.setTime(d.getTime() + (365 * 24 * 60 * 60 * 1000));
        const expires = "expires=" + d.toUTCString();
        document.cookie = cookieMigrationMap[key] + "=" + value + ";" + expires + ";path=/";
      }
    }
    
    // Also set in localStorage for backwards compatibility
    localStorage.setItem(key, value);
  }
}

// Function to handle the file upload
function uploadMainSave() {
  document.body.innerHTML +=
    '<input class="hiddenUpload" type="file" accept=".save"/>';
  var hiddenUpload = document.querySelector(".hiddenUpload");

  // Listen for the change event on the file input element
  hiddenUpload.addEventListener("change", function (e) {
    var files = e.target.files;
    var file = files[0];
    if (!file) {
      return;
    }

    // Read the contents of the uploaded file as text and call getMainSaveFromUpload with the result
    var reader = new FileReader();

    reader.onload = function (e) {
      getMainSaveFromUpload(e.target.result);
    };

    reader.readAsText(file);
  });
}
(s.src =
  "https://cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/crypto-js.min.js"),
  document.head.appendChild(s);
s.onload = function () {
  uploadMainSave();
};