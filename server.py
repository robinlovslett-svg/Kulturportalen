#!/usr/bin/env python3
"""Kulturportal - måling og utvikling av bedriftskultur.

Webapp bygget på masteroppgaven "Lederens rolle som kulturarkitekt"
(transformasjonsledelse og forbedringskultur). Kun stdlib + SQLite.
"""
import json
import sqlite3
import statistics
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

BASE = Path(__file__).parent
STATIC = BASE / "static"
DB_PATH = BASE / "data" / "kulturportal.db"

# --- Spørreskjema definert etter oppgaven (Tabell 3 og 4) ---
SURVEY = {
    "tl": {
        "title": "Lederskap",
        "instruction": "Tenk på din(e) nærmeste leder(e) som har myndighet og ressurser til å påvirke din arbeidshverdag.",
        "dimensions": {
            "idealisert_inflytelse": {"label": "Idealisert innflytelse", "items": [
                "Ledelsen setter fellesskapet foran egne behov.",
                "Ledelsen er et godt forbilde for hvordan vi bør opptre i organisasjonen."]},
            "inspirerende_motivasjon": {"label": "Inspirerende motivasjon", "items": [
                "Ledelsen formidler en tydelig og motiverende visjon.",
                "Ledelsen skaper engasjement på min arbeidsplass slik at arbeidet føles meningsfullt."]},
            "intellektuell_stimulering": {"label": "Intellektuell stimulering", "items": [
                "Ledelsen oppmuntrer oss til å tenke nytt.",
                "Når ting ikke går som planlagt, ser ledelsen muligheter for læring."]},
            "individuell_oppfølging": {"label": "Individuell oppfølging", "items": [
                "Ledelsen viser interesse for mitt arbeid og min utvikling.",
                "Ledelsen gir konstruktive tilbakemeldinger som hjelper meg videre."]},
        },
    },
    "fk": {
        "title": "Samarbeid og arbeidspraksis",
        "instruction": "Ta stilling til følgende påstander om hvordan du opplever samarbeid, kultur og forbedringsarbeid på din arbeidsplass.",
        "dimensions": {
            "psykologisk_trygghet": {"label": "Psykologisk trygghet", "items": [
                "Det er trygt å si fra hvis jeg er uenig, også med ledelsen.",
                "Jeg opplever at mine synspunkter blir lyttet til."]},
            "organisasjonens_verdier": {"label": "Organisasjonens verdier", "items": [
                "Våre nedskrevne verdier blir etterlevd på min arbeidsplass.",
                "Hos oss er det viktig å samarbeide for å lykkes som et lag."]},
            "støttende_ledelse": {"label": "Støttende ledelse", "items": [
                "Ledelsen tilrettelegger for at jeg skal gjøre en god jobb.",
                "Ledelsen gir meg handlingsrom for å prøve nye måter å jobbe på."]},
            "engasjement_empowerment": {"label": "Engasjement og empowerment", "items": [
                "Jeg har frihet til å tilpasse hvordan jeg utfører mine arbeidsoppgaver.",
                "Jeg engasjerer meg aktivt i måten vi jobber på."]},
            "lærende_organisasjon": {"label": "Lærende organisasjon", "items": [
                "Når ting ikke går som planlagt, setter vi av tid til å finne den underliggende årsaken.",
                "Der jeg jobber lærer vi av hverandre ved å aktivt dele erfaringer."]},
            "prosesstenkning_forbedring": {"label": "Prosesstenkning og kontinuerlig forbedring", "items": [
                "I vår organisasjon jobber vi systematisk med å forbedre våre arbeidsprosesser.",
                "Vi bruker faktabasert informasjon naar vi tar beslutninger på min arbeidsplass."]},
        },
    },
}

ITEM_INDEX = {}
_n = 0
for group in ("tl", "fk"):
    for dim, d in SURVEY[group]["dimensions"].items():
        for item in d["items"]:
            _n += 1
            ITEM_INDEX[_n] = (group, dim)
N_ITEMS = _n


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS responses (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            gender TEXT,
            tenure TEXT,
            leadership_role TEXT,
            avdeling TEXT,
            tl_score REAL,
            fk_score REAL,
            payload TEXT NOT NULL
        )
    """)
    cols = [r[1] for r in con.execute("PRAGMA table_info(responses)").fetchall()]
    if "avdeling" not in cols:
        con.execute("ALTER TABLE responses ADD COLUMN avdeling TEXT")
    con.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            response_id TEXT NOT NULL,
            item INTEGER NOT NULL,
            value INTEGER NOT NULL,
            PRIMARY KEY (response_id, item)
        )
    """)
    con.commit()
    con.close()


def score(payload_answers):
    group_scores = {"tl": [], "fk": []}
    dim_scores = {g: {d: [] for d in SURVEY[g]["dimensions"]} for g in ("tl", "fk")}
    for item_str, value in payload_answers.items():
        item = int(item_str)
        group, dim = ITEM_INDEX[item]
        group_scores[group].append(value)
        dim_scores[group][dim].append(value)
    tl = sum(group_scores["tl"]) / len(group_scores["tl"]) if group_scores["tl"] else None
    fk = sum(group_scores["fk"]) / len(group_scores["fk"]) if group_scores["fk"] else None
    dims = {
        g: {d: (sum(v) / len(v) if v else None) for d, v in dd.items()}
        for g, dd in dim_scores.items()
    }
    return tl, fk, dims


def fetch_all():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT * FROM responses ORDER BY created_at").fetchall()
    con.close()
    return [dict(r) for r in rows]


class Handler(BaseHTTPRequestHandler):
    server_version = "Kulturportal/1.0"

    def log_message(self, fmt, *args):
        pass

    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path, content_type):
        try:
            body = path.read_bytes()
        except FileNotFoundError:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        path = url.path
        if path == "/" or path == "/survey":
            self._send_file(STATIC / "survey.html", "text/html; charset=utf-8")
        elif path == "/admin":
            self._send_file(STATIC / "admin.html", "text/html; charset=utf-8")
        elif path == "/result":
            self._send_file(STATIC / "result.html", "text/html; charset=utf-8")
        elif path == "/static/survey.js":
            self._send_file(STATIC / "survey.js", "application/javascript; charset=utf-8")
        elif path == "/static/admin.js":
            self._send_file(STATIC / "admin.js", "application/javascript; charset=utf-8")
        elif path == "/static/style.css":
            self._send_file(STATIC / "style.css", "text/css; charset=utf-8")
        elif path == "/api/survey":
            self._send_json(SURVEY)
        elif path == "/api/stats":
            self._send_json(self._stats(parse_qs(url.query)))
        elif path == "/api/result":
            rid = parse_qs(url.query).get("id", [None])[0]
            self._send_json(self._result(rid))
        elif path == "/api/demo":
            self._send_json(self._seed_demo())
        elif path == "/api/export.csv":
            self._export_csv()
        else:
            self.send_error(404)

    def do_POST(self):
        url = urlparse(self.path)
        if url.path != "/api/submit":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json({"error": "Ugyldig forespørsel"}, 400)
            return
        answers = data.get("answers", {})
        if not isinstance(answers, dict) or len(answers) != N_ITEMS:
            self._send_json({"error": f"Alle {N_ITEMS} påstander må besvares"}, 400)
            return
        clean = {}
        try:
            for k, v in answers.items():
                item = int(k)
                val = int(v)
                if item not in ITEM_INDEX or not (1 <= val <= 5):
                    raise ValueError
                clean[str(item)] = val
        except (ValueError, TypeError):
            self._send_json({"error": "Ugyldige svarverdier"}, 400)
            return

        rid = uuid.uuid4().hex
        tl, fk, dims = score(clean)
        payload = {
            "gender": data.get("gender"),
            "tenure": data.get("tenure"),
            "leadership_role": data.get("leadership_role"),
            "avdeling": data.get("avdeling"),
            "comment": (data.get("comment") or "")[:2000],
        }
        con = sqlite3.connect(DB_PATH)
        con.execute(
            "INSERT INTO responses (id, created_at, gender, tenure, leadership_role, avdeling, tl_score, fk_score, payload) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (rid, datetime.now(timezone.utc).isoformat(), payload["gender"], payload["tenure"],
             payload["leadership_role"], payload["avdeling"], tl, fk, json.dumps({"answers": clean, **payload}, ensure_ascii=False)),
        )
        for item, val in clean.items():
            con.execute("INSERT INTO answers (response_id, item, value) VALUES (?,?,?)", (rid, int(item), val))
        con.commit()
        con.close()
        self._send_json({"id": rid, "tl": round(tl, 2), "fk": round(fk, 2), "dimensions": dims})

    def _result(self, rid):
        if not rid:
            return {"error": "Mangler id"}
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        row = con.execute("SELECT * FROM responses WHERE id = ?", (rid,)).fetchone()
        ans = con.execute("SELECT item, value FROM answers WHERE response_id = ?", (rid,)).fetchall()
        con.close()
        if not row:
            return {"error": "Fant ikke resultat"}
        payload = json.loads(row["payload"])
        tl, fk, dims = score({str(a["item"]): a["value"] for a in ans})
        return {
            "id": rid, "created_at": row["created_at"], "tl": round(tl, 2), "fk": round(fk, 2),
            "dimensions": dims, "survey": SURVEY,
        }

    def _stats(self, query):
        rows = fetch_all()
        group_filter = query.get("group", [None])[0]  # gender | tenure | leadership_role
        if not rows:
            return {"count": 0}
        tls = [r["tl_score"] for r in rows if r["tl_score"] is not None]
        fks = [r["fk_score"] for r in rows if r["fk_score"] is not None]

        dim_agg = {g: {d: [] for d in SURVEY[g]["dimensions"]} for g in ("tl", "fk")}
        con = sqlite3.connect(DB_PATH)
        all_answers = con.execute(
            "SELECT a.item, a.value, r.gender, r.tenure, r.leadership_role, r.created_at FROM answers a "
            "JOIN responses r ON r.id = a.response_id"
        ).fetchall()
        con.close()
        for item, value, gender, tenure, role, created in all_answers:
            g, d = ITEM_INDEX[item]
            dim_agg[g][d].append({"value": value, "gender": gender, "tenure": tenure,
                                  "role": role, "created": created})

        def summarize(vals):
            vals = [v for v in vals if v is not None]
            if not vals:
                return None
            return {"mean": round(statistics.mean(vals), 2), "n": len(vals),
                    "sd": round(statistics.stdev(vals), 2) if len(vals) > 1 else 0.0,
                    "min": min(vals), "max": max(vals)}

        dims_out = {
            g: {d: summarize([x["value"] for x in lst]) for d, lst in dd.items()}
            for g, dd in dim_agg.items()
        }

        # Trend per måned
        months = {}
        for r in rows:
            m = r["created_at"][:7]
            months.setdefault(m, {"tl": [], "fk": []})
            if r["tl_score"] is not None:
                months[m]["tl"].append(r["tl_score"])
                months[m]["fk"].append(r["fk_score"])
        trend = [{"month": m, "tl": round(statistics.mean(v["tl"]), 2) if v["tl"] else None,
                  "fk": round(statistics.mean(v["fk"]), 2) if v["fk"] else None, "n": len(v["tl"])}
                 for m, v in sorted(months.items())]

        # Gruppesammenligning
        groups = None
        if group_filter in ("gender", "tenure", "leadership_role"):
            key = {"gender": "gender", "tenure": "tenure", "leadership_role": "role"}[group_filter]
            agg = {}
            for r in rows:
                gval = {"gender": r["gender"], "tenure": r["tenure"], "leadership_role": r["leadership_role"]}[group_filter]
                if not gval:
                    continue
                a = agg.setdefault(gval, {"tl": [], "fk": []})
                if r["tl_score"] is not None:
                    a["tl"].append(r["tl_score"])
                    a["fk"].append(r["fk_score"])
            groups = {k: {"tl": round(statistics.mean(v["tl"]), 2) if v["tl"] else None,
                          "fk": round(statistics.mean(v["fk"]), 2) if v["fk"] else None,
                          "n": len(v["tl"])} for k, v in sorted(agg.items())}

        # Avdelingsoversikt
        avd = {}
        for r in rows:
            a = r["avdeling"] or "Ukjent"
            avd.setdefault(a, {"tl": [], "fk": []})
            if r["tl_score"] is not None:
                avd[a]["tl"].append(r["tl_score"])
                avd[a]["fk"].append(r["fk_score"])
        # psykologisk trygghet per avdeling (P9-P10)
        con2 = sqlite3.connect(DB_PATH)
        pt_rows = con2.execute(
            "SELECT r.avdeling, a.value FROM answers a JOIN responses r ON r.id=a.response_id WHERE a.item IN (9,10)"
        ).fetchall()
        con2.close()
        pt = {}
        for a, v in pt_rows:
            pt.setdefault(a or "Ukjent", []).append(v)
        avdelinger = {
            a: {
                "tl": round(statistics.mean(v["tl"]), 2) if v["tl"] else None,
                "fk": round(statistics.mean(v["fk"]), 2) if v["fk"] else None,
                "trygghet": round(statistics.mean(pt.get(a, [])), 2) if pt.get(a) else None,
                "n": len(v["tl"]),
            } for a, v in sorted(avd.items())
        }

        # Gap ledere vs medarbeidere per dimensjon
        con3 = sqlite3.connect(DB_PATH)
        all_rows = con3.execute(
            "SELECT a.item, a.value, r.leadership_role FROM answers a JOIN responses r ON r.id=a.response_id"
        ).fetchall()
        con3.close()
        ledere = {i: [] for i in range(1, N_ITEMS + 1)}
        med = {i: [] for i in range(1, N_ITEMS + 1)}
        for item, value, role in all_rows:
            (ledere if role == "Ja" else med)[item].append(value)
        gap = []
        for item in range(1, N_ITEMS + 1):
            g, d = ITEM_INDEX[item]
            l = statistics.mean(ledere[item]) if ledere[item] else None
            m = statistics.mean(med[item]) if med[item] else None
            if l is not None and m is not None:
                gap.append({"dim": SURVEY[g]["dimensions"][d]["label"], "gap": round(l - m, 2)})
        gap.sort(key=lambda x: -abs(x["gap"]))

        # kommentarer (anonymiserte, kun fra payload)
        kommentarer = [json.loads(r["payload"]).get("comment", "") for r in rows]
        kommentarer = [k.strip() for k in kommentarer if k and k.strip()]

        # Korrelasjon TL vs FK (Pearsons r)
        pairs = [(r["tl_score"], r["fk_score"]) for r in rows
                 if r["tl_score"] is not None and r["fk_score"] is not None]
        r_corr = None
        if len(pairs) > 2:
            xs = [p[0] for p in pairs]
            ys = [p[1] for p in pairs]
            mx, my = statistics.mean(xs), statistics.mean(ys)
            num = sum((x - mx) * (y - my) for x, y in pairs)
            den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
            r_corr = round(num / den, 3) if den else None

        return {
            "count": len(rows),
            "tl": summarize(tls),
            "fk": summarize(fks),
            "dimensions": dims_out,
            "trend": trend,
            "groups": groups,
            "group_filter": group_filter,
            "correlation_tl_fk": r_corr,
            "avdelinger": avdelinger,
            "gap": gap,
            "kommentarer": kommentarer,
        }

    def _seed_demo(self):
        import random
        rnd = random.Random(20260926)
        avdelinger = ["Produksjon", "Vedlikehold", "Administrasjon"]
        def normal(mu, sigma):
            u = max(rnd.random(), 1e-9); v = rnd.random()
            return mu + sigma * ( (-2 * __import__("math").log(u)) ** 0.5 ) * __import__("math").cos(2 * 3.14159265 * v)
        added = 0
        for i in range(118):
            r = rnd.random()
            avd = "Produksjon" if r < 0.45 else "Vedlikehold" if r < 0.75 else "Administrasjon"
            leder = rnd.random() < 0.18
            ans = "Under 2 år" if rnd.random() < 0.3 else ("2–10 år" if rnd.random() < 0.6 else "Over 10 år")
            answers = {}
            for item in range(1, N_ITEMS + 1):
                g, d = ITEM_INDEX[item]
                dim_label = SURVEY[g]["dimensions"][d]["label"]
                mu = 3.35
                if leder: mu += 0.45 if g == "tl" else 0.3
                if avd == "Vedlikehold":
                    if dim_label == "Psykologisk trygghet": mu -= 0.95
                    if dim_label == "Lærende organisasjon": mu -= 0.5
                    if dim_label == "Prosesstenkning og kontinuerlig forbedring": mu -= 0.3
                    if g == "tl": mu -= 0.25
                if avd == "Produksjon":
                    if dim_label == "Psykologisk trygghet": mu -= 0.3
                    if dim_label == "Engasjement og empowerment": mu += 0.1
                if avd == "Administrasjon": mu += 0.3
                answers[str(item)] = min(5, max(1, round(normal(mu, 0.85))))
            payload = {"gender": "Mann", "tenure": ans, "leadership_role": "Ja" if leder else "Nei",
                       "avdeling": avd, "comment": ""}
            rid = uuid.uuid4().hex
            tl, fk, _ = score(answers)
            con = sqlite3.connect(DB_PATH)
            con.execute(
                "INSERT OR IGNORE INTO responses (id, created_at, gender, tenure, leadership_role, avdeling, tl_score, fk_score, payload) VALUES (?,?,?,?,?,?,?,?,?)",
                (rid, datetime.now(timezone.utc).isoformat(), payload["gender"], payload["tenure"],
                 payload["leadership_role"], avd, tl, fk, json.dumps({"answers": answers, **payload}, ensure_ascii=False)))
            for item, val in answers.items():
                con.execute("INSERT OR IGNORE INTO answers (response_id, item, value) VALUES (?,?,?)", (rid, int(item), val))
            con.commit(); con.close()
            added += 1
        return {"added": added}

    def _export_csv(self):
        rows = fetch_all()
        con = sqlite3.connect(DB_PATH)
        lines = ["id,created_at,gender,tenure,leadership_role,tl_score,fk_score," +
                 ",".join(f"P{i}" for i in range(1, N_ITEMS + 1))]
        for r in rows:
            ans = con.execute("SELECT item, value FROM answers WHERE response_id=? ORDER BY item",
                              (r["id"],)).fetchall()
            vals = {a[0]: a[1] for a in ans}
            lines.append(",".join([
                r["id"], r["created_at"], r["gender"] or "", r["tenure"] or "",
                r["leadership_role"] or "", str(r["tl_score"]), str(r["fk_score"]),
                *[str(vals.get(i, "")) for i in range(1, N_ITEMS + 1)],
            ]))
        con.close()
        body = ("\n".join(lines)).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", 'attachment; filename="kulturportal_export.csv"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    init_db()
    port = 8000
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Kulturportal kjører på http://127.0.0.1:{port}  (survey: /  admin: /admin)")
    server.serve_forever()


if __name__ == "__main__":
    main()
