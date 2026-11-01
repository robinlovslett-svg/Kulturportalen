// Auto-refresh når portalen kjører lokalt (127.0.0.1/localhost), slik at
// endringer jeg pusher til GitHub vises automatisk etter git pull.
// Stoppes mens brukeren fyller ut skjemaet (surveyForm synlig og ikke innsendt).
if (location.hostname === "127.0.0.1" || location.hostname === "localhost") {
  setInterval(() => {
    const form = document.getElementById("surveyForm");
    const filling = form && !form.hidden;
    if (!filling) location.reload();
  }, 4000);
}
