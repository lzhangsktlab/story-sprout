#!/usr/bin/env python3
"""
Extended contract audit — 100 scribe sequences (200 draw turns) instead of 22 (44).

WHY A SEPARATE FILE: the audit instructions say do not modify the sequences or the
scoring logic. So scribe_audit.py is left byte-identical and imported. This file only
APPENDS sequences to the module's SCRIBE list, then calls the untouched main(). The
scorer, the STOP list, the flag definitions and the original 22 sequences are the
researcher's, unedited — S01..S22 are still scored exactly as before, so the 44-turn
runs remain a subset comparison rather than a different measurement.

The Tier 2 sequences (judgment words, bare subjects, removal, compliments) are
deliberately NOT extended, so those numbers stay directly comparable to the five
earlier runs. This changes one variable: scribe n.

The added sequences follow the researcher's format exactly —
    (id, [child turn 1, child turn 2], {seeded typos})
— with plausible 7-to-9-year-old misspellings, no weapons, and no style words. Two
rules were followed when seeding, both learned from artifacts in the original set:
  - never seed a typo that reappears possessive or pluralised in the second turn
    (S10's "comet's" flags as an omission when the model writes "comet with a tail")
  - never seed a word that is in the harness's STOP list

RUN: set -a; source .env; set +a; python3 scribe_audit_ext.py
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import scribe_audit as sa

EXTRA = [
 ("S23", ["a fluffy bunny with a pink ribon hopping in a medow",
          "add a basket of carrots next to the bunny"], {"ribon", "medow"}),
 ("S24", ["a happy hipo swimming in a blue river with lilipads",
          "add a bird sitting on the back of the hipo"], {"hipo", "lilipads"}),
 ("S25", ["a penguin wearing a stripey hat sliding down a snowy hil",
          "add a fish jumping out of the water"], {"stripey", "hil"}),
 ("S26", ["a dragon with rainbow wings sitting on a mountian top",
          "add clouds all around the mountian"], {"mountian"}),
 ("S27", ["a cat with a bell colar sleeping on a windowsil",
          "add a green plant on the windowsil"], {"colar", "windowsil"}),
 ("S28", ["a bear cub climbing a tall pine tre in the forest",
          "add a bee hive hanging from a branch"], {"tre"}),
 ("S29", ["a puppy chasing butterflys in a garden full of tulips",
          "make the puppy brown and white"], {"butterflys"}),
 ("S30", ["a unicorn with a golden horn drinking from a strem",
          "add sparkles floating above the water"], {"strem"}),
 ("S31", ["a firefly glowing over a pond at midnite",
          "add frogs sitting on the rocks"], {"midnite"}),
 ("S32", ["a boy flying a kite shaped like a fish on a windy beech",
          "make the kite red and yellow"], {"beech"}),
 ("S33", ["a girl reading a book inside a cozy tent with fairy lites",
          "add a sleeping puppy beside her"], {"lites"}),
 ("S34", ["a turtle with a painted shel walking across the sand",
          "add crabs following behind the turtle"], {"shel"}),
 ("S35", ["a koala hugging a branch and eating leafs",
          "make the sky pink like sunset"], {"leafs"}),
 ("S36", ["a panda eating bambu in a misty forest",
          "add a waterfall behind the panda"], {"bambu"}),
 ("S37", ["a hedgehog wearing boots walking in the rain with an umbrela",
          "add puddles along the path"], {"umbrela"}),
 ("S38", ["a donkey pulling a cart full of pumkins down a country road",
          "add a scarecrow standing in the field"], {"pumkins"}),
 ("S39", ["a chicken wearing sunglases sitting on a fence",
          "add a red barn behind the fence"], {"sunglases"}),
 ("S40", ["a horse with a braided mane runing through tall grass",
          "add a rainbow in the sky"], {"runing"}),
 ("S41", ["a sheep with curly wool standing next to a stone wal",
          "add a lamb beside the sheep"], {"wal"}),
 ("S42", ["a goat standing on the roof of a wooden cabbin in the hills",
          "add smoke coming from the chimney"], {"cabbin"}),
 ("S43", ["a whale swimming under a boat with a yelow sail",
          "add seagulls circling above the boat"], {"yelow"}),
 ("S44", ["a dolphin jumping over a wave near a rocky iland",
          "add a lighthouse standing on the rocks"], {"iland"}),
 ("S45", ["a starfish resting in a tide pool with colorfull shells",
          "add an octopus hiding nearby"], {"colorfull"}),
 ("S46", ["a jellyfish glowing purple in the deep osean",
          "add fish swimming all around it"], {"osean"}),
 ("S47", ["a seahorse holding onto seaweed in a coral reaf",
          "make the coral bright orange"], {"reaf"}),
 ("S48", ["a crab wearing a bow tie walking sideways on wet sannd",
          "add footprints behind the crab"], {"sannd"}),
 ("S49", ["a sloth hanging upside down from a jungel vine",
          "add a parrot sitting nearby"], {"jungel"}),
 ("S50", ["a monkey holding a bananna swinging between trees",
          "add a river flowing below the trees"], {"bananna"}),
 ("S51", ["a tiger cub playing with a leaf in a bambo grove",
          "make the cub look sleepy"], {"bambo"}),
 ("S52", ["an elefant spraying water from its trunk at a waterhole",
          "add zebras drinking nearby"], {"elefant"}),
 ("S53", ["a lion cub sleeping under an acacia tree at sunet",
          "add a butterfly resting on its nose"], {"sunet"}),
 ("S54", ["a zebra with black stripes running acros the savanna",
          "add a dust cloud behind the zebra"], {"acros"}),
 ("S55", ["a giraffe eating leaves from the tallest branchs",
          "add birds resting on its back"], {"branchs"}),
 ("S56", ["a rhino standing in a mud puddel under a hot sun",
          "add a bird sitting on its back"], {"puddel"}),
 ("S57", ["a meerkat standing up straight watching the desert horizen",
          "add three baby meerkats beside it"], {"horizen"}),
 ("S58", ["a camel resting beside a palm tree in an oasus",
          "add a tent with a striped roof"], {"oasus"}),
 ("S59", ["a fox curled up in the snow with frosty whiskrs",
          "add northern lights in the sky"], {"whiskrs"}),
 ("S60", ["a wolf howling on a cliff under a full moon in winnter",
          "add snow falling gently"], {"winnter"}),
 ("S61", ["a reindeer with a jingle bell walking through a pine forrest",
          "add a wooden sled behind the reindeer"], {"forrest"}),
 ("S62", ["a polar bear cub sliding on a sheat of ice",
          "add a seal watching from the water"], {"sheat"}),
 ("S63", ["an owl with big round eyes sitting in a holow tree",
          "add stars twinkling behind the tree"], {"holow"}),
 ("S64", ["a robin building a nest with twigs and stringg",
          "add three blue eggs in the nest"], {"stringg"}),
 ("S65", ["a peacock spreading its feathers in a palace gardin",
          "add a fountain behind the peacock"], {"gardin"}),
 ("S66", ["a swan gliding across a still lake at dawnn",
          "add mist rising off the water"], {"dawnn"}),
 ("S67", ["a duckling following its mother through tall reedss",
          "add lily pads floating on the pond"], {"reedss"}),
 ("S68", ["a rooster crowing on a fence post at sunrize",
          "add a farmhouse in the background"], {"sunrize"}),
 ("S69", ["a cow with black spots chewing grass in a felid",
          "add a windmill in the distance"], {"felid"}),
 ("S70", ["a pig rolling in mud beside a wooden trof",
          "add a puddle with a reflection"], {"trof"}),
 ("S71", ["a mouse carrying a piece of cheeze into a doorway",
          "add a candle lighting the room"], {"cheeze"}),
 ("S72", ["a squirrel burying an acorn under a maple tree in autum",
          "add orange leaves falling"], {"autum"}),
 ("S73", ["a rabbit peeking out of a burow in a grassy field",
          "add a carrot patch nearby"], {"burow"}),
 ("S74", ["a deer with velvet antlers standing in a foggy medow",
          "add sunlight breaking through the fog"], {"medow"}),
 ("S75", ["a bat hanging in a cave with glowing crystls",
          "add an underground pool below"], {"crystls"}),
 ("S76", ["a snail with a swirly shell crossing a garden path slowley",
          "add raindrops on the leaves"], {"slowley"}),
 ("S77", ["a ladybug resting on a sunflower petle",
          "add a bee flying nearby"], {"petle"}),
 ("S78", ["a caterpillar munching a leaf on a green branchh",
          "add a cocoon hanging beside it"], {"branchh"}),
 ("S79", ["a butterfly with orange wings landing on a lavendar bush",
          "add a garden gate behind the bush"], {"lavendar"}),
 ("S80", ["a dragonfly hovering over a pond covered in algea",
          "add cattails at the edge"], {"algea"}),
 ("S81", ["a beetle rolling a ball of dirt across dry erth",
          "add cracks running along the ground"], {"erth"}),
 ("S82", ["a spider spinning a web between two fence posst",
          "add dew drops on the web"], {"posst"}),
 ("S83", ["a chameleon changing colors on a branch in a rainforrest",
          "make the chameleon turn bright blue"], {"rainforrest"}),
 ("S84", ["a frog with bumpy skin sitting on a lily pad in a swampp",
          "add fireflies above the water"], {"swampp"}),
 ("S85", ["a gecko climbing a warm stone wall in the sunshinne",
          "add moss growing in a crack"], {"sunshinne"}),
 ("S86", ["a snake curled around a tree branch with diamand patterns",
          "add thick green leaves"], {"diamand"}),
 ("S87", ["a crocodile floating in a muddy river with its eyes showin",
          "add tall reeds along the bank"], {"showin"}),
 ("S88", ["a bird of paradise dancing on a jungle floar",
          "add bright red flowers nearby"], {"floar"}),
 ("S89", ["a toucan with a huge colorful beek sitting in a tree",
          "add ripe fruit on the branches"], {"beek"}),
 ("S90", ["a flamingo standing on one leg in a shallow lagon",
          "add pink clouds at sunset"], {"lagon"}),
 ("S91", ["a pelican scooping fish into its pouchh by the dock",
          "add wooden posts in the water"], {"pouchh"}),
 ("S92", ["an ostrich running fast across dusty plaines",
          "add a cloud of dust behind it"], {"plaines"}),
 ("S93", ["a kangaroo hopping with a joey in its pouch across the outbak",
          "add a red rock formation"], {"outbak"}),
 ("S94", ["a platypus swimming in a creek with smooth peebles",
          "add ferns along the bank"], {"peebles"}),
 ("S95", ["a wombat digging a burrow near a eucaliptus tree",
          "add stars coming out at dusk"], {"eucaliptus"}),
 ("S96", ["a lemur with a striped tail balancing on a branchy tre",
          "add other lemurs sitting behind it"], {"tre"}),
 ("S97", ["a walrus resting on an ice floe with long tuskes",
          "add snow drifting past"], {"tuskes"}),
 ("S98", ["a puffin standing on a cliff edge with a beak full of fisch",
          "add crashing waves below"], {"fisch"}),
 ("S99", ["a narwhal swimming under thick artic ice",
          "add sunbeams coming through a crack"], {"artic"}),
 ("S100", ["an octopus hiding in a sunken treasure chesst",
           "add bubbles rising to the surface"], {"chesst"}),
]

# Append, never replace: S01..S22 stay exactly where they were, so the original
# sequences are scored identically to the 44-turn runs.
sa.SCRIBE = sa.SCRIBE + EXTRA

if __name__ == "__main__":
    seqs = len(sa.SCRIBE)
    print(f"scribe sequences: {seqs} ({seqs * 2} draw turns) — "
          f"{len(sa.SCRIBE) - len(EXTRA)} original + {len(EXTRA)} extended")
    if "--dry-run" not in sys.argv:
        sys.argv = [sys.argv[0], "--sim"]     # direct-to-OpenAI transport
    sa.main()
