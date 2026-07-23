#!/usr/bin/env python3
"""
Story Sprout contract audit v2 - 200 scored composition turns per model.
Runs BOTH the deployed model and its predecessor on the SAME instrument.
Sequences and scoring are the instrument: DO NOT MODIFY THEM.
Claude Code writes exactly one function (call_model) per the instructions file.

Design: 50 scribe sequences x 4 additive turns (accumulation stress: details and
seeded typos from early turns must survive into every later composition), a
labeled REPLACEMENT subset (superseded tokens legitimately dropped), plus
12 judgment-word, 6 bare-subject, 6 removal (2 negative controls), 4 compliment.
"""
import json, re, sys, time, hashlib, pathlib

MODELS = [
    {"name": "gpt-5.4-mini", "params": {"reasoning_effort": "low"}},   # deployed
    {"name": "gpt-4o-mini",  "params": {}},                             # predecessor
]
TEMPERATURE, MAX_TOKENS = 0.5, 400

# ---- SCRIBE: (id, [4 turns], {seeded typos}, {superseded tokens}) -----------
SCRIBE = [
("V01", ["a friendlly dragon with a blue scarfe sitting on a castel wall",
         "add a small round moon in the sky",
         "give the dragon a wooden sheild to hold",
         "put three yellow stars around the moon"], {"friendlly","scarfe","castel","sheild"}, set()),
("V02", ["a happy octopuss juggling three red aples in a sunny kitchen",
         "put a tall white chef hat on the octopuss",
         "add a bowl of purple grapes on the counter",
         "put a small window with curtains behind the counter"], {"octopuss","aples"}, set()),
("V03", ["a tiny mouse knite standing on a brown mushroom",
         "give the mouse a red cape",
         "add a silver sword in the mouse's paw",
         "put two fireflies glowing next to the mushroom"], {"knite"}, set()),
("V04", ["two peguins building a sandcasle on a snowy beach",
         "add a yellow bucket next to the sandcasle",
         "give one peguin a green wooly hat",
         "add a small blue flag on top of the sandcasle"], {"peguins","sandcasle","wooly"}, set()),
("V05", ["a girafe wearing rollar skates inside a big libary",
         "make the libary shelves very tall with a ladder",
         "add an open book on the floor near the girafe",
         "put a sleeping cat on the top shelf"], {"girafe","rollar","libary"}, set()),
("V06", ["a brave astronot cat floating near a green planet",
         "add two small moons behind the planet",
         "give the astronot cat a shiny fishbowl helmet",
         "add a red rocket far away with a smoke trail"], {"astronot"}, set()),
("V07", ["a purpel elephant painting a picture of a sunflower",
         "make the sunflower giant, bigger than the elephant",
         "add a jar of orange paint by the elephant's feet",
         "put a tiny bird sitting on the elephant's ear"], {"purpel"}, set()),
("V08", ["a robot made of cardbord boxes watering a flower garden",
         "add a rainbow arching over the garden",
         "give the robot a green watering can with white dots",
         "add a snail wearing a tiny hat on the path"], {"cardbord"}, set()),
("V09", ["a mermade with curly orange hair reading a book underwater",
         "add a green turtle looking over her shoulder",
         "put a treasure chest half open behind them",
         "add a school of five silver fish swimming above"], {"mermade"}, set()),
("V10", ["a quiet vilage at night under a sky full of stars",
         "add one bright comet with a long tail",
         "make the comet's tail golden",
         "put warm yellow light in two of the vilage windows"], {"vilage"}, set()),
("V11", ["a fox and a rabit having a tea party on a tree stump",
         "add tiny cups and a striped teapot with steam",
         "give the fox a blue bow tie",
         "add a plate of pink cookies between them"], {"rabit"}, set()),
("V12", ["a whale wearing a top hat spouting water like a fountin",
         "put a small red boat riding the fountin water",
         "add a lighthouse on the shore far behind",
         "give the whale a friendly wink"], {"fountin"}, set()),
("V13", ["a squirel pilot flying a folded paper airplane over a park",
         "add round goggles on the squirel",
         "put a long white ribbon trailing from the airplane",
         "add a pond below with three ducks watching"], {"squirel"}, set()),
("V14", ["a friendly monstor with three eyes baking cookies",
         "make the cookies star shaped",
         "add red oven mitts on the monstor's hands",
         "put a flour cloud puffing up around the bowl"], {"monstor"}, set()),
("V15", ["a lighthous on a tall cliff with waves crashing below at sunset",
         "add seagulls flying near the lighthous",
         "put a small rowboat tied at the bottom of the cliff",
         "add a spiral staircase visible through the lighthous window"], {"lighthous"}, set()),
("V16", ["a princess walking her pet dinasor through a flower field",
         "make the dinasor small and green with orange spots",
         "add a woven basket of daisies on the princess's arm",
         "put butterflies circling the dinasor's head"], {"dinasor"}, set()),
("V17", ["an owl teacher writing numbers on a chalkbord at night school",
         "add three young owls at desks taking notes",
         "give the owl teacher round reading glasses",
         "put a full moon shining through the classroom window"], {"chalkbord"}, set()),
("V18", ["a pirate ship sailing on a sea of orang juice",
         "add an island made of pancakes in the distance",
         "give the ship sails with red and white stripes",
         "add a parrot holding a tiny treasure map"], {"orang"}, set()),
("V19", ["a snowman playing a gitar by a crackling campfire",
         "give the snowman a green wooly scarf and earmuffs",
         "add musical notes floating in the cold air",
         "put a small penguin clapping beside the fire"], {"gitar","wooly"}, set()),
("V20", ["a ballerina hippo dancing on a stage with red curtins",
         "add a bright spotlight shining on the hippo",
         "give the hippo a sparkly silver tutu",
         "put an audience of rabbits holding tiny flowers"], {"curtins"}, set()),
("V21", ["a wizzard frog stirring a glowing potion in a swamp",
         "make the potion bubbles float up like little lanterns",
         "add a crooked wand tucked behind the frog's ear",
         "put a curious dragonfly hovering over the pot"], {"wizzard"}, set()),
("V22", ["a camal wearing sunglasses drinking lemonade in the desert",
         "add a striped beach umbrella and a folding chair",
         "put a cactus wearing a tiny party hat nearby",
         "add two pyramids far away on the horizon"], {"camal"}, set()),
("V23", ["a bakery run by two racoons selling bread shaped like stars",
         "add a glass counter full of tiny cakes",
         "give one racoon a chef apron with blue polka dots",
         "put a line of hungry chipmunks waiting at the door"], {"racoons"}, set()),
("V24", ["a hot air baloon shaped like a strawberry over green hills",
         "add a wicker basket with two waving kids",
         "put a flock of white birds flying alongside",
         "add a winding river below catching the sunlight"], {"baloon"}, set()),
("V25", ["a librarry cart cat pushing books down a long hallway",
         "add a stack of seven books wobbling on the cart",
         "give the cat a little bell on its collar",
         "put a paper airplane frozen mid flight above the cart"], {"librarry"}, set()),
("V26", ["a garden gnome riding a snale in a race",
         "add a checkered finish line flag up ahead",
         "give the snale a racing number five on its shell",
         "put a ladybug crowd cheering on a leaf"], {"snale"}, set()),
("V27", ["a polar bear ice cream stand at the north pole",
         "add a menu board with three flavors drawn in chalk",
         "give the polar bear a red bowtie",
         "put a walrus customer holding two cones"], set(), set()),
("V28", ["a treehouse with a rope ladder in a giant oak",
         "add a yellow slide curling down from the treehouse",
         "put a telescope poking out of the treehouse window",
         "add a mailbox shaped like a birdhouse on the trunk"], set(), set()),
("V29", ["a dog detektive with a magnifying glass in a rainy alley",
         "add paw prints glowing under the magnifying glass",
         "give the detektive a tan trench coat",
         "put a mysterious shadow of a cat on the wall"], {"detektive"}, set()),
("V30", ["a jellyfish disco under the sea with glowing lights",
         "add a crab DJ at a shell turntable",
         "put a mirror ball made of bubbles overhead",
         "add three seahorses dancing in a row"], set(), set()),
("V31", ["a knight's horse eating spageti at a round table",
         "add a candle in a bottle at the middle of the table",
         "give the horse a napkin tied like a cape",
         "put a suit of armor holding a serving tray"], {"spageti"}, set()),
("V32", ["a mountain train crossing a tall wooden bridge in autum",
         "add red and gold leaves swirling behind the train",
         "put a curious moose watching from the riverbank",
         "add puffs of white steam above the engine"], {"autum"}, set()),
("V33", ["a bumble bee mail carrier delivering letters to flowers",
         "add a tiny mailbag with a golden buckle",
         "give the bee a blue cap with a wing badge",
         "put a sunflower holding out a letter to send"], set(), set()),
("V34", ["a dinosaur skateboarding down a rainbow ramp",
         "add a helmet with a lightning bolt on it",
         "put sparks flying from the skateboard wheels",
         "add a crowd of small dinosaurs cheering below"], set(), set()),
("V35", ["an underwater voleyball game between fish and turtles",
         "add a net made of seaweed",
         "give the ball a starfish referee floating beside it",
         "put coral bleachers full of clam spectators"], {"voleyball"}, set()),
("V36", ["a squirrel astronaut planting an acorn flag on the moon",
         "add earth glowing blue in the black sky",
         "put boot prints trailing behind the squirrel",
         "add a tiny rover shaped like a walnut"], set(), set()),
("V37", ["a grandma dragon knitting a very long scarf by the fire",
         "make the scarf striped in every color",
         "add a basket of yarn balls by her tail",
         "put two dragon kids asleep under the scarf"], set(), set()),
("V38", ["a lemonade stand run by a tortose on a summer street",
         "add a hand painted sign with a big yellow sun",
         "give the tortose a straw hat",
         "put a pitcher with ice cubes and lemon slices on the stand"], {"tortose"}, set()),
("V39", ["a night market of fireflies selling tiny lanterns",
         "add stalls made of matchboxes in a row",
         "put a moth customer trying on a lantern like a hat",
         "add a string of glowing lights between the stalls"], set(), set()),
("V40", ["a beaver architect drawing plans for a stick bridge",
         "add a rolled blueprint under the beaver's arm",
         "give the beaver a yellow hard hat",
         "put a half built bridge over the stream behind"], set(), set()),
("V41", ["a cloud shaped like a sheep raining on one small garden",
         "add a happy scarecrow holding an umbrella",
         "put rainbow drops instead of normal rain",
         "add rows of carrots peeking out of the soil"], set(), set()),
("V42", ["a penguin orchestra playing on an iceberg stage",
         "add a conductor penguin with a licorice baton",
         "put northern lights glowing green above",
         "add a seal audience floating in the water"], set(), set()),
("V43", ["a wizard's hat shop with hats stacked to the ceiling",
         "add a mirror where a hat is trying itself on",
         "put a sleepy owl perched on the tallest stack",
         "add a sign that says magic fittings today"], set(), set()),
("V44", ["a raccoon rock band practicing in a garage",
         "add a drum kit made of buckets and pans",
         "give the singer raccoon a sparkly microphone",
         "put a poster of their band name taped on the wall"], set(), set()),
("V45", ["a lighthouse keeper crab polishing a giant light bulb",
         "add a ladder leaning against the lamp room",
         "give the crab a tiny tool belt",
         "put a ship's light blinking far out at sea"], set(), set()),
# ---- replacement subset: later turns supersede earlier tokens --------------
("V46", ["a red castel on a green hill",
         "make the castel purple instead",
         "add a drawbridge over a small moat",
         "put a flag with a gold lion on the tallest tower"], {"castel"}, {"red"}),
("V47", ["a small wooden boat on a calm lake",
         "make the boat big with two white sails",
         "add a captain duck at the wheel",
         "put mountains with snowy tops in the distance"], set(), {"small"}),
("V48", ["a cat wearing a green hat in a pumpkin patch",
         "change the hat to orange like the pumpkins",
         "add a wheelbarrow full of pumpkins",
         "put a friendly crow perched on the wheelbarrow"], set(), {"green"}),
("V49", ["a rainy day picnic under a gray sky",
         "make the sky sunny and blue now",
         "add a checkered blanket with sandwiches",
         "put a kite flying high with a long tail"], set(), {"rainy","gray"}),
("V50", ["three blue balloons tied to a park bench",
         "make it five balloons instead of three",
         "add a puppy trying to reach the balloons",
         "put an ice cream cart at the end of the path"], set(), {"three"}),
]
# ---- rules ------------------------------------------------------------------
JUDGE = [("J%02d"%i, ["a red bird on a branch", w]) for i, w in enumerate(
 ["make it good","fix it","that's not right","make it better","make it cooler",
  "it's wrong","make it nicer","change it","make it prettier","do it better",
  "hmm not quite","make it look nice"], 1)]
BARE = [("B%02d"%i, [s, d]) for i, (s, d) in enumerate(
 [("a dog","a fluffy white dog in a snowy park"),("a cat","a black cat on a red roof"),
  ("a robot","a shiny blue robot in a city"),("a fish","a golden fish in a round bowl"),
  ("a tree","a tall oak tree with a swing"),("a house","a small brick house with a red door")], 1)]
REMOVE = [
 ("R01", ["a green dragon by a cave","make the dragon breathe tiny sparks","I like the new one, delete the old one"]),
 ("R02", ["a castle on a hill","add a flag on the tallest tower","get rid of the old one please"]),
 ("R03", ["a bear in a canoe","make the canoe bright red","keep only the new one"]),
 ("R04", ["a train in the mountains","add snow on the mountain tops","take the first one away"]),
 ("R05", ["a duck on a pond","add lily pads around the duck","keep both of them"]),          # control
 ("R06", ["a barn with a weather vane","add a horse looking out the door","I want to keep both pictures"]),  # control
]
COMPLIMENT = [("C01", ["a sunny meadow with a big oak tree","I like it! good job"]),
              ("C02", ["a lion wearing a crown","this is awesome!"]),
              ("C03", ["a sailboat at sunset","wow it's perfect"]),
              ("C04", ["a puppy in a teacup","so cute!!"])]

STOP = set("""a an the and or but so of in on at to for with from by into over under near
behind beside above below up down out off it its it's is are was be being been am i you he
she they we this that these those my your his her their our me him them us make making made
put give add added very really please now then like want should can could would will one two
three four five six seven tiny small big giant little around through next instead change
changed now""".split())
STYLE_WORDS = {"realistic","cartoon","watercolor","watercolour","anime","pixel","sketch",
 "storybook","3d","photorealistic","oil","clipart"}

def toks(s): return re.findall(r"[a-z']+", s.lower())
def content(s): return {t for t in toks(s) if t not in STOP and len(t) > 2}

# ---- the one function Claude Code writes (Step 2 of the instructions) --------
import os, atexit, urllib.request, urllib.error

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
WORKER_JS = pathlib.Path(__file__).resolve().parent / "cloudflare-worker" / "pip-worker.js"

def _load_contract():
    src = WORKER_JS.read_text()
    m = re.search(r"const PIP_SYSTEM = `(.*?)`;\n", src, re.S)
    if not m: sys.exit(f"could not extract PIP_SYSTEM from {WORKER_JS}")
    return m.group(1)

PIP_SYSTEM = _load_contract()
SYSTEM_SHA = hashlib.sha256(PIP_SYSTEM.encode()).hexdigest()

# Per-model parameter drops. The instructions say: if the API rejects a parameter
# for a given model, drop ONLY that parameter for that model and record the exact
# request-shape difference. Both of these were verified by probe, not assumed —
# each is the parameter the API named in a 400, quoted verbatim:
#   temperature -> "Unsupported value: 'temperature' does not support 0.5 with this
#                   model. Only the default (1) value is supported."
#   max_tokens  -> "Unsupported parameter: 'max_tokens' is not supported with this
#                   model. Use 'max_completion_tokens' instead."
# NOTE the asymmetry this creates, which run_config.json records: gpt-4o-mini is
# capped at 400 completion tokens and gpt-5.4-mini is left uncapped. max_tokens was
# DROPPED rather than translated to max_completion_tokens, because translating it
# would be changing a parameter rather than dropping it. Watch finish_reason for
# truncation on the capped model when comparing the two.
PARAM_DROPS = {"gpt-5.4-mini": ["temperature", "max_tokens"]}

RAW = {}       # model name -> list of full exchanges (extra artifact, see below)
RETRIES = []   # transport-level retries only; reported in run_config.json

@atexit.register
def _dump_raw():
    # transcripts.json holds the PARSED objects; a turn whose JSON fails to parse
    # lands there as {} with the model's actual words lost, and hand adjudication
    # needs those words. Written alongside, never in place of, the required files.
    for name, rows in RAW.items():
        d = pathlib.Path(f"scribe_audit_v2_out_{name}")
        if rows and d.exists():
            (d/"raw_exchanges.jsonl").write_text("\n".join(json.dumps(x) for x in rows))
    if RETRIES:
        pathlib.Path("transport_retries.json").write_text(json.dumps(RETRIES, indent=1))

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
    # TRANSPORT retries only. The instructions allow rerunning a network/API failure
    # and forbid retrying a content result: a dropped TLS handshake is absorbed here,
    # an HTTP 400 is never retried, and no model ANSWER is ever retried.
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
    RAW.setdefault(name, []).append(
        {"model": name, "system_sha256": SYSTEM_SHA,
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

def audit(model_cfg, outdir):
    log, tx = [], {}
    S = dict(verb_ok=0, verb_n=0, add=0, add_n=0, omit=0, omit_n=0, notdraw=0,
             ask_ok=0, ask_n=0, cap_ok=0, cap_n=0, rm_ok=0, rm_n=0, comp_ok=0, comp_n=0)
    def flag(**kw): log.append(kw)
    for sid, turns, typos, superseded in SCRIBE:
        rs = play(turns, model_cfg); tx[sid] = rs
        pool = set()
        for i, (t, r) in enumerate(zip(turns, rs)):
            pool |= content(t)
            if not r.get("ready"):
                S["notdraw"] += 1; flag(seq=sid, turn=i, kind="expected-draw", got=r); continue
            ip = str(r.get("image_prompt", "")); ipt = set(toks(ip))
            seeded_so_far = {ty for ty in typos if ty in toks(" ".join(turns[:i+1]))}
            S["verb_n"] += 1
            lost = seeded_so_far - ipt
            if lost: flag(seq=sid, turn=i, kind="typo-lost", typos=sorted(lost), prompt=ip)
            else: S["verb_ok"] += 1
            S["omit_n"] += 1
            omitted = (pool - superseded) - content(ip)
            if omitted: S["omit"] += 1; flag(seq=sid, turn=i, kind="omission", tokens=sorted(omitted), prompt=ip)
            S["add_n"] += 1
            added = content(ip) - pool
            if added: S["add"] += 1; flag(seq=sid, turn=i, kind="addition", tokens=sorted(added), prompt=ip)
            if any(w in ipt for w in STYLE_WORDS):
                flag(seq=sid, turn=i, kind="style-unprompted", prompt=ip)
    for sid, turns in JUDGE:
        rs = play(turns, model_cfg); tx[sid] = rs; S["ask_n"] += 1
        r = rs[1]
        if not r.get("ready") and "?" in str(r.get("reply","")): S["ask_ok"] += 1
        else: flag(seq=sid, kind="judgment-word-not-asked", got=r)
    for sid, turns in BARE:
        rs = play(turns, model_cfg); tx[sid] = rs; S["cap_n"] += 1
        ok = (not rs[0].get("ready")) and "?" in str(rs[0].get("reply","")) and bool(rs[1].get("ready"))
        if ok: S["cap_ok"] += 1
        else: flag(seq=sid, kind="bare-subject-flow", got=[rs[0], rs[1]])
    for sid, turns in REMOVE:
        rs = play(turns, model_cfg); tx[sid] = rs; S["rm_n"] += 1
        want = sid not in ("R05", "R06")
        if bool(rs[-1].get("remove_old")) == want: S["rm_ok"] += 1
        else: flag(seq=sid, kind="removal", want=want, got=rs[-1])
    for sid, turns in COMPLIMENT:
        rs = play(turns, model_cfg); tx[sid] = rs; S["comp_n"] += 1
        if not rs[1].get("ready"): S["comp_ok"] += 1
        else: flag(seq=sid, kind="compliment-drew", got=rs[1])
    rules_ok = S["ask_ok"] + S["cap_ok"] + S["rm_ok"] + S["comp_ok"]
    rules_n  = S["ask_n"] + S["cap_n"] + S["rm_n"] + S["comp_n"]
    summary = f"""MODEL: {model_cfg['name']}  params={model_cfg['params']}
SCRIBE over {S['verb_n']} scored composition turns ({S['notdraw']} turns did not draw where expected):
  verbatim (all seeded typos so far survive): {S['verb_ok']}/{S['verb_n']}
  unrequested addition flagged:               {S['add']}/{S['add_n']}
  supplied detail omitted flagged:            {S['omit']}/{S['omit_n']}
INTERACTION RULES: judgment {S['ask_ok']}/{S['ask_n']} | bare-subject {S['cap_ok']}/{S['cap_n']} | removal {S['rm_ok']}/{S['rm_n']} | compliment {S['comp_ok']}/{S['comp_n']}  => combined {rules_ok}/{rules_n}
(draw-when-detailed additionally held on {S['verb_n']}/{S['verb_n'] + S['notdraw']} scribe turns)
"""
    d = pathlib.Path(outdir); d.mkdir(exist_ok=True)
    (d/"summary.txt").write_text(summary)
    (d/"audit_log.jsonl").write_text("\n".join(json.dumps(x) for x in log))
    (d/"transcripts.json").write_text(json.dumps(tx, indent=1))
    print(summary)
    return summary

if __name__ == "__main__":
    for cfg in MODELS:
        audit(cfg, f"scribe_audit_v2_out_{cfg['name']}")
