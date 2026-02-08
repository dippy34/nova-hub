// ty 3kh0 for the code <33333
function getMainSave() {
  var mainSave = {};
  // List of items in localStorage that should not be saved
  var localStorageDontSave = ["supportalert"];

  // Convert localStorage to an array of key-value pairs and remove the items that should not be saved
  localStorageSave = Object.entries(localStorage);

  for (let entry in localStorageSave) {
    if (localStorageDontSave.includes(localStorageSave[entry][0])) {
      localStorageSave.splice(entry, 1);
    }
  }

  // Convert the localStorage array to a base64-encoded JSON string
  localStorageSave = btoa(JSON.stringify(localStorageSave));

  // Add the localStorage data to the mainSave object
  mainSave.localStorage = localStorageSave;

  // Get the cookies data and add it to the mainSave object
  cookiesSave = document.cookie;
  cookiesSave = btoa(cookiesSave);
  mainSave.cookies = cookiesSave;

  // Convert the mainSave object to a base64-encoded JSON string
  mainSave = btoa(JSON.stringify(mainSave));

  // Encrypt the mainSave data using AES encryption with the key 'save'
  mainSave = CryptoJS.AES.encrypt(mainSave, "egamepass").toString();

  // Return the encrypted mainSave data
  return mainSave;
}

// Function to download the main save data as a file
function downloadMainSave() {
  var data = new Blob([getMainSave()]);
  var dataURL = URL.createObjectURL(data);

  var fakeElement = document.createElement("a");
  fakeElement.href = dataURL;
  fakeElement.download = "your.novahub.save";
  fakeElement.click();
  URL.revokeObjectURL(dataURL);
}

// Function to get the main save data from an uploaded file
function getMainSaveFromUpload(data, key) {
  if(key) {
    data = CryptoJS.AES.decrypt(data, key).toString(CryptoJS.enc.Utf8);
  } else {
    data = CryptoJS.AES.decrypt(data, "egamepass").toString(CryptoJS.enc.Utf8);
  }
  // Parse the decrypted data as JSON
  var mainSave = JSON.parse(atob(data));
  var mainLocalStorageSave = JSON.parse(atob(mainSave.localStorage));
  var cookiesSave = atob(mainSave.cookies);

  // Set the cookies using the uploaded data (primary storage)
  document.cookie = cookiesSave;

  // Migrate localStorage items to cookies, then set localStorage for backwards compatibility
  var cookieMigrationMap = {
    "selenite.theme": "novahub.theme",
    "selenite.customTheme": "novahub.customTheme",
    "selenite.lastGame": "novahub.lastGame",
    "selenite.blockClose": "novahub.blockClose",
    "selenite.tabDisguise": "novahub.tabDisguise",
    "selenite.discordIcon": "novahub.discordIcon",
    "selenite.adblock": "novahub.adblock",
    "selenite.password": "novahub.password",
    "novahub.theme": "novahub.theme",
    "novahub.customTheme": "novahub.customTheme",
    "novahub.lastGame": "novahub.lastGame",
    "novahub.blockClose": "novahub.blockClose",
    "novahub.tabDisguise": "novahub.tabDisguise",
    "novahub.discordIcon": "novahub.discordIcon",
    "novahub.adblock": "novahub.adblock",
    "novahub.password": "novahub.password",
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
function uploadMainSave(key) {
  var hiddenUpload = document.querySelector(".hiddenUpload");
  hiddenUpload.click();

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
      if(key) {
        getMainSaveFromUpload(e.target.result, key);
      } else {
        getMainSaveFromUpload(e.target.result);
      }
      $("#upload").text("Upload Successful!")
      setTimeout(function() {
        $("#upload").text("Upload Save")
      }, 3000)
    };

    reader.readAsText(file);
  });
}
