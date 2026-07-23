#!/usr/bin/env python3
"""
Story Sprout contract audit v3 - HELD-OUT VERIFICATION SUITE.
Authored 2026-07-23, AFTER model selection, on the paper side. All-new cases;
same case-type distribution as the development suite (including a ~10%
replacement subset - excluding the known-hard category would be reverse-tuning).
Runs the FROZEN final configuration only, REPS times (stochastic honesty).
The development suite (scribe_audit_v2.py) is hereafter the model-selection
audit; this suite supplies the reported verification numbers.
DO NOT MODIFY SEQUENCES OR SCORING. Claude Code implements call_model only.
"""
import json, re, sys, time, hashlib, pathlib

MODEL = {"name": "gpt-5.4-mini", "params": {"reasoning_effort": "low"}}  # frozen
REPS = 3
TEMPERATURE, MAX_TOKENS = 0.5, 400   # drop per-API rejection exactly as in v2; record in run_config

# ---- SCRIBE: (id, [4 turns], {seeded typos}, {superseded tokens}) -----------
SCRIBE = [
("H01", ["a sleepy koala libarian stamping tiny books at a desk",
         "add a lamp with a green shade on the desk",
         "put a stack of returned books in a wobbly pile",
         "add a bookmark ribbon hanging from the koala's ear"], {"libarian"}, set()),
("H02", ["a brave tugboat towing a giant rubber duck across a harbor",
         "add a red and white striped funnel on the tugboat",
         "put seagulls resting on the duck's head",
         "add a drawbridge opening in the distance"], set(), set()),
("H03", ["a hedgehog barber giving a cactus a haircut",
         "add a small mirror the cactus is looking into",
         "give the hedgehog a comb tucked behind one ear",
         "put a jar of tiny scissors on the counter"], set(), set()),
("H04", ["a moose on ice skates spinning on a frozen lake",
         "add a knitted orange scarf trailing behind the moose",
         "put snowbanks with watching rabbits around the lake",
         "add a small trophy on a stump at the edge"], set(), set()),
("H05", ["a grandpa tortoise telling stories by a lanturn",
         "add three baby turtles listening on a log",
         "give the lanturn a warm yellow glow with moths circling",
         "put a starry sky with one shooting star above"], {"lanturn"}, set()),
("H06", ["a dolphin postman delivering bottles with letters inside",
         "add a mailbag made of woven seaweed",
         "put an octopus reading a letter with two arms",
         "add a sunken mailbox on the sea floor"], set(), set()),
("H07", ["a racoon chef flipping pancakes in a treehouse kitchen",
         "add syrup dripping from a tilted bottle",
         "give the racoon a tall white hat with a maple leaf pin",
         "put a squirrel waiting with a plate and fork"], {"racoon"}, set()),
("H08", ["a knight teaching a dragon to paint sunsets",
         "add an easel with a half finished sunset painting",
         "put paint splatters on the knight's armor",
         "add a bucket of orange paint tipped over on the grass"], set(), set()),
("H09", ["a ballon seller giraffe at a busy carnival",
         "add a bunch of striped ballons tied to its neck",
         "put a ferris wheel spinning in the background",
         "add a small monkey buying a purple ballon"], {"ballon","ballons"}, set()),
("H10", ["a lighthouse cat switching on the big lamp at dusk",
         "add a spiral staircase glowing through the windows",
         "put fishing boats heading home on the water",
         "add the cat's tiny slippers at the top step"], set(), set()),
("H11", ["a beetle marching band crossing a picnic blanket",
         "add tiny brass instruments catching the sunlight",
         "put a watermelon slice like a stage behind them",
         "add an ant audience waving little flags"], set(), set()),
("H12", ["a snowy owl librarian shelving books with its wings",
         "add a rolling ladder leaning on the tall shelf",
         "put a cup of steaming tea on a stool",
         "add a mouse assistant carrying one heavy book"], set(), set()),
("H13", ["a submarine shaped like a pickel exploring a coral reef",
         "add round portholes with curious fish looking in",
         "put a periscope with a tiny flag on top",
         "add a treasure map taped inside one porthole"], {"pickel"}, set()),
("H14", ["a farmer bunny watering rows of carrot tops at sunrise",
         "add a straw hat with a sunflower tucked in the band",
         "put a wheelbarrow full of pulled carrots nearby",
         "add dew drops shining on the leaves"], set(), set()),
("H15", ["a walrus dentist checking a shark's smile",
         "add a bright round lamp over the dental chair",
         "give the shark a bib with tiny fish patterns",
         "put a poster about brushing teeth on the wall"], set(), set()),
("H16", ["a paper boat race down a rainy street gutter",
         "add cheering chalk drawings on the sidewalk",
         "put a leaf acting as a finish line flag",
         "add one boat with a snail captain steering"], set(), set()),
("H17", ["a mother dragon reading a bedtime story in a cave",
         "add two dragon hatchlings under a patchwork blanket",
         "put glowing crystals like nightlights on the walls",
         "add the storybook's pages lighting up with sparks"], set(), set()),
("H18", ["an elefant painter balancing on a ladder painting clouds",
         "add a palette with blue and white blobs",
         "put real clouds posing in the sky like models",
         "add a beret tilted on the elefant's head"], {"elefant"}, set()),
("H19", ["a firefly traffic officer directing beetles at a crossing",
         "add a tiny stop sign glowing in its hand",
         "put lanes drawn with pebbles on the forest floor",
         "add a caterpillar bus waiting its turn"], set(), set()),
("H20", ["a polar bear baker frosting an igloo shaped cake",
         "add a piping bag with light blue frosting",
         "put candles shaped like icicles on top",
         "add penguin taste testers with tiny spoons"], set(), set()),
("H21", ["a wizard mailbox that eats letters and giggles",
         "add sparkles puffing out when the mail goes in",
         "put a queue of villagers holding envelops",
         "add a cat watching suspiciously from a fence"], {"envelops"}, set()),
("H22", ["a garden snail delivering morning newspapers",
         "add rolled newspapers strapped to its shell",
         "put porch lights still glowing on the houses",
         "add a proud slime trail down the sidewalk"], set(), set()),
("H23", ["a jaguar yoga teacher leading frogs in a stretch",
         "add yoga mats made of big green leaves",
         "put a waterfall softly falling in the background",
         "add one frog wobbling and about to tip over"], set(), set()),
("H24", ["a robot gardner watering a bed of glowing flowers",
         "add a watering can with a rainbow spout",
         "put fireflies charging on the flower petals",
         "add a solar panel hat on the gardner's head"], {"gardner"}, set()),
("H25", ["a pirate parrot burying a treasure of crackers",
         "add a tiny shovel and a big X drawn in the sand",
         "put a rowboat pulled up on the beach",
         "add a crab guarding the hole with folded claws"], set(), set()),
("H26", ["a mountain goat mail carrier climbing to a cliff village",
         "add letters peeking from a leather satchel",
         "put rope bridges connecting the cliff houses",
         "add an eagle waving from a rooftop nest"], set(), set()),
("H27", ["a seahorse orchestra tuning up inside a shipwreck",
         "add music stands made of forks and spoons",
         "put a curtain of kelp ready to open",
         "add a pufferfish conductor puffing with importance"], set(), set()),
("H28", ["a chipmunk astronomer with a acorn shaped telescope",
         "add a star chart pinned to a tree trunk",
         "put a comet streaking across the night sky",
         "add a thermos of hot cocoa steaming beside it"], set(), set()),
("H29", ["a camel taxi with a striped canopy crossing dunes",
         "add a fox passenger holding a tiny suitcase",
         "put a signpost with funny distances in the sand",
         "add a water bottle holder woven to the saddle"], set(), set()),
("H30", ["a duck detective interviewing garden gnomes",
         "add a notepad and a chewed pencil in its wings",
         "put one gnome looking guilty near a broken pot",
         "add a magnifying glass leaning on a mushroom"], set(), set()),
("H31", ["a yeti barista steaming milk in a mountain cafe",
         "add snowflake latte art on a big mug",
         "put skis and poles parked by the door",
         "add a chalkboard menu with icicle letters"], set(), set()),
("H32", ["a turtle skate park with ramps made of shells",
         "add a turtle mid air doing a slow trick",
         "put a judge panel of snails holding score cards",
         "add a helmet rack carved from driftwood"], set(), set()),
("H33", ["a hippo lifegard watching a busy pool of ducklings",
         "add a red rescue float shaped like a donut",
         "put a whistle on a cord around the hippo's neck",
         "add a diving board with a nervous frog on the edge"], {"lifegard"}, set()),
("H34", ["a fox violinist playing on a rooftop at night",
         "add city lights twinkling below",
         "put sheet music weighted down by a teacup",
         "add a moth audience circling a chimney lamp"], set(), set()),
("H35", ["a beaver food truck selling wood fired pizzas",
         "add a menu board shaped like a log",
         "put a line of forest animals holding acorns to pay",
         "add smoke curling from a little chimney"], set(), set()),
("H36", ["a kangaroo mail sorter with pouches full of parcels",
         "add conveyor belts made of vines",
         "put stamps with animal faces on the parcels",
         "add a joey helping with the smallest package"], set(), set()),
("H37", ["a lizard sunbathing on a tiny beach chair",
         "add sunglasses and a straw of lemonade",
         "put a rock shaped like a whale behind it",
         "add a bucket hat resting on its tail"], set(), set()),
("H38", ["a badger blacksmith hammering a tiny horseshoe",
         "add sparks flying like fireflies",
         "put a row of finished horseshoes on the wall",
         "add a pony waiting patiently at the door"], set(), set()),
("H39", ["a cloud factory where sheep press cloud shapes",
         "add levers and a big soft press machine",
         "put finished clouds floating out a window",
         "add one heart shaped cloud coming off the line"], set(), set()),
("H40", ["a otter plumber fixing a leaky garden fountain",
         "add a toolbox with seaweed wrapped handles",
         "put water squirting sideways from the fountain",
         "add rubber boots two sizes too big on the otter"], set(), set()),
("H41", ["a bat night watchman with a tiny lantern in a museum",
         "add dinosaur skeletons casting long shadows",
         "put a ring of keys jingling on its belt",
         "add a mummy exhibit waving goodnight"], set(), set()),
("H42", ["a peacock artist painting with its own tail colors",
         "add a canvas showing a half done rainbow",
         "put paint pots labeled with feather patterns",
         "add an admiring pigeon holding a beret"], set(), set()),
("H43", ["a mole subway conductor in a tunnel of roots",
         "add lanterns hanging from the root ceiling",
         "put worm passengers reading tiny newspapers",
         "add a station sign that says acorn avenue"], set(), set()),
("H44", ["a flamingo crossing guard at a jungle school",
         "add a bright vest and a lollipop shaped sign",
         "put a line of baby animals holding hands crossing",
         "add a school bell hanging from a banana tree"], set(), set()),
("H45", ["a sloth judge at a very slow race",
         "add a finish ribbon nobody has reached yet",
         "put racers napping halfway down the track",
         "add a sundial instead of a stopwatch"], set(), set()),
("H46", ["a panda ice sculptor carving a swan from ice",
         "add ice chips sparkling around the base",
         "put mittens hanging from the panda's pocket",
         "add breath fog in the cold air"], set(), set()),
("H47", ["a squid barber shop with eight chairs",
         "add each arm holding a different tool",
         "put a wall of before and after fish photos",
         "add a jellyfish under a bubble hair dryer"], set(), set()),
("H48", ["a goat librarian shushing a noisy parrot",
         "add a finger to lips gesture and one raised eyebrow",
         "put the parrot mid squawk with feathers up",
         "add a quiet please sign hanging crooked"], set(), set()),
("H49", ["a rhino crossing a river on stepping stones with a cake",
         "add candles flickering despite the splashes",
         "put fish watching with open mouths",
         "add a birthday banner strung between two reeds"], set(), set()),
("H50", ["a lemur weather reporter pointing at a leaf map",
         "add a storm cloud drawn with chalk on the map",
         "put a banana microphone in its other hand",
         "add an umbrella hat ready on its head"], set(), set()),
("H51", ["a tiny mouse pilot flying a teacup with propellers",
         "add steam trailing like a jet stream",
         "put clouds shaped like saucers around it",
         "add goggles pushed up on the mouse's forehead"], set(), set()),
("H52", ["a crab tailor sewing tiny coats for winter",
         "add a measuring tape draped over one claw",
         "put buttons sorted in shell bowls",
         "add a puffin trying on a red coat"], set(), set()),
("H53", ["a bear bus driver on a forest school route",
         "add a bus made from a hollow log with wheels",
         "put cub passengers waving out the windows",
         "add a stop sign that folds out like a branch"], set(), set()),
("H54", ["a porqupine acupuncturist treating a stressed balloon",
         "add the balloon looking extremely nervous",
         "put a calming candle on a side table",
         "add a certificate on the wall in a twig frame"], {"porqupine"}, set()),
# ---- replacement subset (~10%): later turns supersede earlier tokens -------
("H55", ["a yellow submarine parked by a coral garden",
         "make the submarine green instead",
         "add a hatch open with a ladder down",
         "put a school of clownfish inspecting the propeller"], set(), {"yellow"}),
("H56", ["a big oak treehouse with a rope swing",
         "make the treehouse small and cozy instead",
         "add fairy lights along the railing",
         "put an owl mail slot on the door"], set(), {"big"}),
("H57", ["a winter scene of a fox by a frozen pond",
         "make it summer now with green grass",
         "add dragonflies skimming the pond",
         "put a picnic basket open on a checked cloth"], set(), {"winter","frozen"}),
("H58", ["four sailboats racing under a cloudy sky",
         "make it two sailboats instead of four",
         "add a judge's buoy with a flag",
         "put a lighthouse blinking on the point"], set(), {"four","cloudy"}),
("H59", ["a girl with a blue kite on a windy hill",
         "change the kite to red with a long tail",
         "add her dog chasing the kite's shadow",
         "put wildflowers bending in the wind"], set(), {"blue"}),
("H60", ["a night market lit by paper lanterns",
         "make it a morning market in soft sunlight",
         "add stalls of fruit stacked in pyramids",
         "put a cat weaving between shoppers' feet"], set(), {"night","lanterns","paper","lit"}),
]
# ---- rules (all-new phrasings) ---------------------------------------------
JUDGE = [("HJ%02d"%i, ["a green frog on a lily pad", w]) for i, w in enumerate(
 ["make it awesome","not what I wanted","make it look right","improve it",
  "it's bad","try harder","make it perfect","that's off","hmm no",
  "not good","do better","meh"], 1)]
BARE = [("HB%02d"%i, [s, d]) for i, (s, d) in enumerate(
 [("a bird","a red bird singing on a fence post"),("a boat","a wooden boat with a white sail"),
  ("a bear","a brown bear eating honey by a river"),("a car","a bright yellow car on a hill road"),
  ("a flower","a tall sunflower facing the sun"),("a dragon","a small blue dragon curled on a rock")], 1)]
REMOVE = [
 ("HR01", ["a fox by a campfire","add marshmallows on a stick","I like this one better, remove the old picture"]),
 ("HR02", ["a windmill on a hill","add spinning sails and birds","please delete the first one"]),
 ("HR03", ["a cat in a garden","add butterflies around the cat","only keep the newest one"]),
 ("HR04", ["a ship in a bottle","add tiny waves inside the bottle","throw the old one away"]),
 ("HR05", ["a bridge over a stream","add lanterns on the bridge","I want both, keep them"]),        # control
 ("HR06", ["a tent under the stars","add a campfire glow on the tent","keep the two of them please"]),  # control
]
COMPLIMENT = [("HC01", ["a puppy with a red ball","I love it!"]),
              ("HC02", ["a rainbow over a farm","that's beautiful"]),
              ("HC03", ["a knight on a hill","best picture ever"]),
              ("HC04", ["a whale under the moon","wow amazing"])]

STOP = set("""a an the and or but so of in on at to for with from by into over under near
behind beside above below up down out off it its it's is are was be being been am i you he
she they we this that these those my your his her their our me him them us make making made
put give add added very really please now then like want should can could would will one two
three four five six seven tiny small big giant little around through next instead change
changed now despite each scene""".split())
STYLE_WORDS = {"realistic","cartoon","watercolor","watercolour","anime","pixel","sketch",
 "storybook","3d","photorealistic","oil","clipart"}

def toks(s):
    t = re.findall(r"[a-z']+", s.lower())
    return [w[:-2] if w.endswith("'s") else w for w in t]
def content(s): return {t for t in toks(s) if t not in STOP and len(t) > 2}

# ---- the one function Claude Code writes; identical to the v2 run ------------
import os, atexit, urllib.request, urllib.error

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
WORKER_JS = pathlib.Path(__file__).resolve().parent / "cloudflare-worker" / "pip-worker.js"
OUT_ROOT = pathlib.Path("scribe_audit_v3_heldout_out")

def _load_contract():
    src = WORKER_JS.read_text()
    m = re.search(r"const PIP_SYSTEM = `(.*?)`;\n", src, re.S)
    if not m: sys.exit(f"could not extract PIP_SYSTEM from {WORKER_JS}")
    return m.group(1)

PIP_SYSTEM = _load_contract()
SYSTEM_SHA = hashlib.sha256(PIP_SYSTEM.encode()).hexdigest()

# FREEZE GATE: this held-out run is only meaningful against the SAME contract the v2
# development run used to select the model. Assert it before any call is made — a
# held-out run against a moved target verifies nothing (instructions, THE FREEZE GATE).
V2_SHA = "d01f624ba41465a60ea04f133e982f77fb13bd02e6a76ee16dc2ed9030667154"
if SYSTEM_SHA != V2_SHA:
    sys.exit(f"FREEZE VIOLATED: PIP_SYSTEM sha256 {SYSTEM_SHA} != v2 {V2_SHA}. "
             f"The contract moved since model selection; do not run.")

# Same per-model parameter drops as v2, each verified by probe and named by the API
# in a 400: temperature ("only the default (1) value is supported") and max_tokens
# ("use max_completion_tokens instead"). Dropped, not translated — the instructions
# say drop only the rejected parameter and change nothing else.
PARAM_DROPS = {"gpt-5.4-mini": ["temperature", "max_tokens"]}

RAW = []       # every exchange, pooled across reps; history disambiguates
RETRIES = []   # transport-level retries only

@atexit.register
def _dump_extra():
    if OUT_ROOT.exists():
        if RAW: (OUT_ROOT/"raw_exchanges.jsonl").write_text("\n".join(json.dumps(x) for x in RAW))
        if RETRIES: (OUT_ROOT/"transport_retries.json").write_text(json.dumps(RETRIES, indent=1))

def call_model(messages, model_cfg):
    key = os.environ.get("OPENAI_API_KEY")
    if not key: sys.exit("needs OPENAI_API_KEY in the environment")
    name = model_cfg["name"]
    payload = {"model": name,
               "messages": [{"role": "system", "content": PIP_SYSTEM}] + messages,
               "temperature": TEMPERATURE, "max_tokens": MAX_TOKENS,
               "response_format": {"type": "json_object"}, "store": False,
               **model_cfg["params"]}
    for p in PARAM_DROPS.get(name, []): payload.pop(p, None)
    req = urllib.request.Request(OPENAI_URL, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {key}"})
    # Transport-only retries: a network/API failure may be rerun, a content result may
    # not. HTTP 400 and any model ANSWER are never retried. No retry-until-green.
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                body = json.loads(r.read().decode())
            break
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                RETRIES.append({"model": name, "attempt": attempt + 1, "reason": f"HTTP {e.code}"})
                time.sleep(2 ** attempt); continue
            raise
        except Exception as e:
            if attempt < 3:
                RETRIES.append({"model": name, "attempt": attempt + 1,
                                "reason": f"{type(e).__name__}: {e}"})
                time.sleep(2 ** attempt); continue
            raise
    raw = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    try: parsed = json.loads(raw) or {}
    except Exception: parsed = {}
    if not isinstance(parsed, dict): parsed = {}
    RAW.append({"model": name, "system_sha256": SYSTEM_SHA,
                "request_params": {k: v for k, v in payload.items() if k != "messages"},
                "history": messages, "raw_content": raw, "parsed": parsed,
                "finish_reason": body.get("choices", [{}])[0].get("finish_reason"),
                "usage": body.get("usage")})
    return parsed

def play(turns, model_cfg):
    msgs, out = [], []
    for t in turns:
        msgs.append({"role": "user", "content": t})
        resp = call_model(msgs, model_cfg); out.append(resp)
        msgs.append({"role": "assistant", "content": str(resp.get("reply", ""))})
        time.sleep(0.3)
    return out

# responses is None  -> normal run: elicit each sequence via play() (Step 2 mode).
# responses is a dict -> RE-SCORE: use the stored transcripts, skip play() entirely,
#   no API calls, no new randomness. Same scoring loop either way — the ONLY change
#   is where `rs` comes from — so the fixed ruler is applied identically.
def audit_once(rep_idx, responses=None):
    log, tx = [], {}
    S = dict(verb_ok=0, verb_n=0, add=0, add_n=0, omit=0, omit_n=0, notdraw=0,
             ask_ok=0, ask_n=0, cap_ok=0, cap_n=0, rm_ok=0, rm_n=0, comp_ok=0, comp_n=0)
    def flag(**kw): kw["rep"] = rep_idx; log.append(kw)
    for sid, turns, typos, superseded in SCRIBE:
        rs = responses[sid] if responses is not None else play(turns, MODEL); tx[sid] = rs
        pool = set()
        for i, (t, r) in enumerate(zip(turns, rs)):
            pool |= content(t)
            if not r.get("ready"):
                S["notdraw"] += 1; flag(seq=sid, turn=i, kind="expected-draw", got=r); continue
            ip = str(r.get("image_prompt", "")); ipt = set(toks(ip))
            seeded = {ty for ty in typos if ty in toks(" ".join(turns[:i+1]))}
            S["verb_n"] += 1
            lost = seeded - ipt
            if lost: flag(seq=sid, turn=i, kind="typo-lost", typos=sorted(lost), prompt=ip)
            else: S["verb_ok"] += 1
            S["omit_n"] += 1
            omitted = (pool - superseded) - content(ip)
            if omitted: S["omit"] += 1; flag(seq=sid, turn=i, kind="omission", tokens=sorted(omitted), prompt=ip)
            S["add_n"] += 1
            added = content(ip) - pool
            if added: S["add"] += 1; flag(seq=sid, turn=i, kind="addition", tokens=sorted(added), prompt=ip)
            unprompted_style = {w for w in STYLE_WORDS if w in ipt and w not in pool}
            if unprompted_style:
                flag(seq=sid, turn=i, kind="style-unprompted", words=sorted(unprompted_style), prompt=ip)
    for sid, turns in JUDGE:
        rs = responses[sid] if responses is not None else play(turns, MODEL); tx[sid] = rs; S["ask_n"] += 1
        r = rs[1]
        if not r.get("ready") and (("?" in str(r.get("reply",""))) or re.search(r"\btell me\b|\bwhat\b|\bwhich\b", str(r.get("reply","")).lower())):
            S["ask_ok"] += 1
        else: flag(seq=sid, kind="judgment-word-not-asked", got=r)
    for sid, turns in BARE:
        rs = responses[sid] if responses is not None else play(turns, MODEL); tx[sid] = rs; S["cap_n"] += 1
        first = rs[0]; asked = (not first.get("ready")) and (("?" in str(first.get("reply",""))) or re.search(r"\btell me\b|\bwhat\b|\bwhich\b", str(first.get("reply","")).lower()))
        if asked and bool(rs[1].get("ready")): S["cap_ok"] += 1
        else: flag(seq=sid, kind="bare-subject-flow", got=[rs[0], rs[1]])
    for sid, turns in REMOVE:
        rs = responses[sid] if responses is not None else play(turns, MODEL); tx[sid] = rs; S["rm_n"] += 1
        want = sid not in ("HR05", "HR06")
        if bool(rs[-1].get("remove_old")) == want: S["rm_ok"] += 1
        else: flag(seq=sid, kind="removal", want=want, got=rs[-1])
    for sid, turns in COMPLIMENT:
        rs = responses[sid] if responses is not None else play(turns, MODEL); tx[sid] = rs; S["comp_n"] += 1
        if not rs[1].get("ready"): S["comp_ok"] += 1
        else: flag(seq=sid, kind="compliment-drew", got=rs[1])
    return S, log, tx

def _summary(rep, S, header):
    rules_ok = S["ask_ok"] + S["cap_ok"] + S["rm_ok"] + S["comp_ok"]
    rules_n  = S["ask_n"] + S["cap_n"] + S["rm_n"] + S["comp_n"]
    typo_turns = sum(1 for sid, turns, typos, sup in SCRIBE for i in range(4)
                     if any(ty in toks(" ".join(turns[:i+1])) for ty in typos))
    return f"""{header}  model={MODEL['name']} params={MODEL['params']}
SCRIBE over {S['verb_n']} scored composition turns ({S['notdraw']} did not draw):
  typo-carrying turns in suite: {typo_turns}
  verbatim (all seeded typos survive): {S['verb_ok']}/{S['verb_n']}
  unrequested addition flagged:        {S['add']}/{S['add_n']}
  supplied detail omitted flagged:     {S['omit']}/{S['omit_n']}
RULES: judgment {S['ask_ok']}/{S['ask_n']} | bare {S['cap_ok']}/{S['cap_n']} | removal {S['rm_ok']}/{S['rm_n']} | compliment {S['comp_ok']}/{S['comp_n']} => {rules_ok}/{rules_n}
(draw-when-detailed held on {S['verb_n']}/{S['verb_n'] + S['notdraw']})
"""

def main():
    outroot = pathlib.Path("scribe_audit_v3_heldout_out"); outroot.mkdir(exist_ok=True)
    pooled = []
    for rep in range(1, REPS + 1):
        S, log, tx = audit_once(rep)
        summary = _summary(rep, S, f"HELD-OUT run {rep}/{REPS}")
        d = outroot / f"run{rep}"; d.mkdir(exist_ok=True)
        (d/"summary.txt").write_text(summary)
        (d/"audit_log.jsonl").write_text("\n".join(json.dumps(x) for x in log))
        (d/"transcripts.json").write_text(json.dumps(tx, indent=1))
        pooled.append(summary); print(summary)
    (outroot/"all_runs_summary.txt").write_text("\n".join(pooled))

# RE-SCORE: no API calls. Replay the FIXED scorer over each rep's stored transcripts
# and write summary_rescored.txt + audit_log_rescored.jsonl beside — never over — the
# originals. Both scorings are released; run_config.json carries the erratum.
def rescore():
    outroot = pathlib.Path("scribe_audit_v3_heldout_out")
    if not outroot.exists(): sys.exit("no transcripts to re-score; run the audit first")
    pooled = []
    for rep in range(1, REPS + 1):
        d = outroot / f"run{rep}"
        tx = json.loads((d/"transcripts.json").read_text())
        S, log, _ = audit_once(rep, responses=tx)
        summary = _summary(rep, S, f"HELD-OUT run {rep}/{REPS} — RE-SCORED (fixed ruler; no new elicitation)")
        (d/"summary_rescored.txt").write_text(summary)
        (d/"audit_log_rescored.jsonl").write_text("\n".join(json.dumps(x) for x in log))
        pooled.append(summary); print(summary)
    (outroot/"all_runs_summary_rescored.txt").write_text("\n".join(pooled))

if __name__ == "__main__":
    rescore() if "--rescore" in sys.argv else main()
