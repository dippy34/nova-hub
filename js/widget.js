let firstLoadWidget = 1;
let widgetOpen = 0;
document.addEventListener("DOMContentLoaded", () => {
    let button = document.createElement("button");
    button.setAttribute("id", "discord");
    document.body.appendChild(button);
    button.addEventListener("click", () => {
        if(firstLoadWidget) {
            toast({ title: "Do you want to load Discord?", message: "This may be blocked in certain schools.\nClick here to load Discord." }, loadWidget);
        }
    })
})

function loadWidget() {
    if(firstLoadWidget) {
        firstLoadWidget = 0;
        loadScript("https://cdn.jsdelivr.net/npm/@widgetbot/crate@3", loadCrate);
    }
}
function loadCrate() {
    new Crate({server: '1148719137238040606',channel: '1173731814196645909', color: "#00000000", glyph: ["data:;base64,=", "100%"]});
    crate.toggle(true);
    let element = document.querySelector('[aria-label="Discord chat embed"]');
    element.remove();
}