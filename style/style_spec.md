# Not Yet: style spec

Checkpoint C1 (brief, "Checkpoints"): palette hex values for the six colour roles, materials (glass, frost, felt,
steel), lighting, and one test frame of the glass room in the hall. `config/look.json` holds every number here;
change this file first, then the config.

**Sources.** This project has no reference videos. The look comes from three places. The brief supplies the set,
the colour roles, the rules and the texture pass. The drafting chat's style notes add "keep it soft", "no jump
scares, no glitches and no red", and "avoid the look of well-known bedtime picture books"
(`docs/drafting_chat/drafting_chat.md`, message 28). Sandbox Rhapsody's style spec supplies the series'
conventions: Eevee, AgX, Fresnel glass, the probe and the kit. Where this video departs from Sandbox Rhapsody,
the departure is stated below.

## The look in one line

A dark, cold museum hall with one warm glass room glowing in it. Everything outside the glass is cold blue;
everything inside is cream. Only three things carry any other colour: a green glint in the crib, an amber window
on the hill and a tungsten slit under the floor. Nothing is saturated except those three, and nothing is red.

## Frame rate and format

- **60 fps**, as in Sandbox Rhapsody.
  - The video is one slow, continuous push past steel mullions and glass edges (the texture pass's arc). At 30 fps,
    thin verticals sliding slowly across the frame step visibly.
  - It snaps MIDI onsets to 8.3 ms, which matters for the comb plucks and star births.
  - It matches the series.
- **Cost:** 246.36 s of song is 14,782 frames, plus the black, the CRT line and the cards (2D, cheap). At 720p and 64
  samples on this GTX 970, a frame of the full set takes about 21 s including the build; most of that is the build,
  which a sequence render pays once.
  - The 4K final runs on the RTX 5090. Budget from Sandbox Rhapsody's figures there: 8.5 s per 4K test frame.
  - If the 4K budget is too long, 30 fps with Eevee motion blur halves it, at some risk of judder on the mullions. This is a C1 question for the human.
- **Format:** 3840×2160 (16:9) for the main video; drafts at 1280×720 (`config/render_profiles.json`, `draft720`).
  The vertical cut (N23 to N41) reframes a wider render, set at C4.

## Palette (`config/look.json` → `palette`)

### The six colour roles (brief, "The set → Color roles")

| Role | Key | Hex | Where |
| --- | --- | --- | --- |
| The house and its glass | `house` | `#5f86c4` | hall light, glass reflections, frost tint, the hall's spot and rim lights (`key` `#8fb0e0` and `rim` `#bcd4ff` are its lit and edge tints) |
| Comfort | `comfort` | `#ffe3b0` | the night-light, the projected stars, the nursery's fill, porch lights, the music box's comb glow |
| The crib probe | `standby` | `#5fe39a` | its LED (a glint until N38), the baby monitor's pip; nothing else |
| Another house's child | `amber` | `#ffa21f` | the neighbor's window only (and every amber window in N27). It is Sandbox Rhapsody's agent amber, exactly |
| The maintainer | `tungsten` | `#ffd27a` | the basement desk lamp; the slit of light under the plinth (N28) |
| Commerce | `commerce` | `#eef4f1` | the shop window: flat, slightly green-white fluorescent, no warmth |

- **Amber is Sandbox Rhapsody's own value.** The neighbor's kid is that lab's kind of probe, so the colour matches,
  and the brief's "same make, different house, different light" holds.
- **Tungsten against amber and comfort.** Tungsten is yellower than amber (hue 41° against 35°) and more saturated
  than comfort. It never shares a frame with amber up close, since the basement and the hill are never in the same shot.

### Supporting surfaces

| Surface | Key | Hex |
| --- | --- | --- |
| Surround (zenith, horizon) | `void`, `horizon` | `#04060b`, `#0c1424` |
| Hall floor, walls | `floor`, `hall_wall` | `#0a0d13`, `#121823` |
| Plinth | `plinth` | `#1a2130` |
| Fill (shadows) | `fill` | `#22314f`: shadows stay blue, not Sandbox Rhapsody's violet |
| Moon, night sky, hill | `moon`, `sky`, `hill` | `#cfdcf5`, `#13254a`, `#05080e` |
| Frost | `frost` | `#dfe9f7` |
| Steel frame | `steel` | `#8d97a6` |
| Vault door paint | `pastel` | `#c8c0e4`: lavender. Not pink, so it can't be read as red, and not mint, which would collide with the probe's green |
| Crib and nursery paint | `crib` | `#ece5d8` |
| Chair wood | `wood` | `#9a7a5c` |
| Felt (blanket, mobile, rug) | `felt_blue`, `felt_cream`, `felt_grey`, `rug` | `#9fb3cf`, `#e9dcc4`, `#b9b4ad`, `#d8cdb8` |
| Sticky note | `note` | `#f2d64b`, Sandbox Rhapsody's |
| Pencil (growth chart) | `pencil` | `#3a3d44` |

**Rules**
- **No red anywhere.** That includes the dial's markings, tags and screens. The real pages at N33, N34 and N43 are
  recorded as they are; the composite keeps them small enough on the display that a red link or logo can't dominate.
  This gets checked at C5.
- **Amber is reserved.** It appears only in the neighbor's window and the far amber windows. Sandbox Rhapsody's kit
  pieces that glow amber (the music box's comb tips and crank knob, the flag) are recoloured when imported: comb tips
  cream, knob and flag felt blue. The probe's LED takes `standby` through `led_role`.
- **The glass room is the warmest thing in the hall.** Outside it, only the three accents may be warm.

## Materials (`materials`)

| Material | Settings | Notes |
| --- | --- | --- |
| Glass (walls, roof, door bay, shop window) | Sandbox Rhapsody's `mat_glass`: tinted transparency plus a Fresnel-weighted reflection (0.55; shop 0.35) of a procedural environment, blended | Proven in Sandbox Rhapsody; real reflections of the hall (the texture pass's foreshadowing) are a C4/C5 item, through planar light probes on the four walls |
| Frost | Principled, `frost` colour, roughness 0.55, emission 0.08, alpha from ragged noise (scale 38) on a 0.45 m strip inside each pane; `room["frost"]` 1 → 0 lowers the edge to nothing | Thins over the song (brief); C1 shows 0.45 |
| Felt (blanket, mobile, rug, chair blanket) | roughness 1.0, specular 0.2, sheen 0.7 tinted `comfort` | The sheen catches the night-light on edges, so wool reads without texture |
| Steel (frame, mullions, plinth band, window) | metallic 1, roughness 0.32 | Brushed, not chrome: the frame shouldn't sparkle |
| Paint (crib, door, dresser) | no coat, roughness 0.42–0.5 | |
| Chrome (door rim, bolts, dial ring, knobs, probe) | Sandbox Rhapsody's (metallic 1, roughness 0.05) | The probe imports unchanged at C2 |
| Stone (hall floor, plinth, walls) | roughness 0.28 floor, 0.6 plinth, 0.85 walls | The floor holds soft reflections of the glass room and the shop |

- **Texture:** none painted. Text (the sticky note, the price tag) is the only "texture", rendered from fonts, as in
  Sandbox Rhapsody.
- **Fonts:** the sticky note is Instrument Serif Italic, Sandbox Rhapsody's `NO INTERNET :)` hand. The tag is Inter.
- **Legibility:** Sandbox Rhapsody's rule applies. Every sign must read in the widest shot whose anchor needs it:
  the note at N07, and the tag at N31 and N32.

## Lighting (`lights`)

| Light | Value | Role |
| --- | --- | --- |
| Hall spots | two 420 W spots from the ceiling (8.6 m) onto the plinth, cone 32° | `key` |
| Moon | sun 1.6, through the tall window from behind and above | `moon` |
| Door key | 60 W soft area from the front | `moon`: lets the pastel read as pastel |
| Rims | two 300 W areas behind the room, specular 0.25 | `rim`: they draw the steel frame against the dark |
| Night-light | 30 W point inside the projector dome | `comfort` |
| Nursery fill | 70 W area under the roof, specular 0.2 | `comfort` |
| Shop | 220 W area, plus tube emitters (6) | `commerce` |
| Tungsten slit | emitter 6 | `tungsten` |
| Haze | volume density 0.004 through the hall | the moonlight and the projector read as beams |
| Bloom | threshold 1.5, size 0.45, strength 0.55 | softer than Sandbox Rhapsody's (4.0, 0.3): stars, porch lights and the glint glow |

- **AgX, Base Contrast**, not Sandbox Rhapsody's Punchy: the lullaby wants soft shoulders, not snap.
- **Practicals do the moving.** The night-light, the stars, the glint, the comb glow and the neighbor's window are the
  lights that change, each driven by notes or the timing map. The hall's lights stay constant, apart from the moon's
  slow travel (the moonlight clock).
- **The moonlight clock.** The sun's direction is keyed so the window's patch starts at the window's base at N02 and
  reaches the crib at N38 (texture pass). C1 shows it mid-song.

## The set as built for C1

- **Hall:** 22 × 26 m, 9 m high. The tall window (3.2 × 7 m, 4 × 8 panes) is in the back wall. A taped hall window
  is behind the camera's start (N09). The shop window is in the right wall.
- **Plinth:** 5.6 m square, 0.4 m high, steel edge band, and the tungsten slit at its front base.
- **Glass room:** 4 m square, 2.8 m high, one pane per metre on a steel frame, glass roof on ribs, and frost inside the bottom edge.
- **The door:** Sandbox Rhapsody's vault door (chrome rim, ten bolts, handwheel, untouched black dial), scaled to
  1.84 m across and repainted lavender. It sits in a glass bay with a heavy pastel ring frame, hinged at the left,
  with `open` up to 12°. The sticky note reads `NOT FOR THE PUBLIC :)`. A solid pastel surround was tried first and
  hid the nursery, so the bay is glass.
- **Nursery:** rug; crib with a breathing blanket and a glint under its head-end lip; the mobile (bank, globe, cloud,
  flag) on a mast; the star projector on a side table; the rocking chair, with a blanket over its arm; a dresser with
  Sandbox Rhapsody's music box (recoloured) and the baby monitor; and the growth chart leaning on the back glass.
- **Stars:** 320 seeded directions (seed 41) from the projector, cast onto the glass walls and roof as 5-point
  stars. C1 shows 85%, 242 placed. The projector's rotation and the per-chorus additions come at C3/C4.
- **Street:** a night sky, the moon and a 21 m hill of thirteen houses with porch lights. The neighbor's house is
  placed so the tall window frames its upstairs amber window from the wide camera.
- **Shop window:** a fluorescent display box with an identical crib, the glint, `COMING SOON` on the rail, a dark
  screen for verse 4, and the baby monitor's receiver. The twin probe and its mittens come at C2.
- **Basement:** not built for C1. Only the slit shows it.

## Camera

- **One continuous move from N03 to N38** (brief), on a spline that arcs round the glass room (texture pass), at
  constant speed. It eases in once at N03 and out once at N38, with no speed changes in between. Its speed comes
  from path length over time at C4: about 35 m over about 215 s, roughly 0.16 m/s. That is slower than any of
  Sandbox Rhapsody's moves, as a lullaby should be.
- **Lenses:** 27–35 mm. Depth of field around f/5.6–8 in the hall. Focus pulls happen on downbeats only (texture pass).
- **No shake, no handheld drift, no cuts until the outro's black** (brief).

## Captions

Lyric captions in Inter, cream (`comfort`), bottom centre. Each word brightens from 40% to full as it is sung, with
no pop or overshoot (unlike Ghost in the Machine and Sandbox Rhapsody), and lines fade out. Verse 4's thinner voice
is set in Inter's lighter weight. The N34 check marks are drawn in a different hand (Instrument Serif Italic,
in `paper`; green is the probe's alone).

## Open for C1 review

- 60 fps against 30 fps with motion blur (cost above).
- The pastel: lavender `#c8c0e4`.
- The glint isn't visible in either test frame. The close frame's angle hides the crib's head end. It is easy to
  show and isn't a colour question; it gets checked with the probe at C2.
