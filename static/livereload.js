// Auto-refresh når portalen kjører lokalt (127.0.0.1/localhost), slik at
// endringer jeg pusher til GitHub vises automatisk etter git pull.
if (location.hostname === "127.0.0.1" || location.hostname === "localhost") {
  setInterval(() => location.reload(), 4000);
}
