// =======================
// GitHub Image Base URL
// =======================
const GITHUB_BASE_URL = "https://raw.githubusercontent.com/moomoocowsteam/timeline_app/main/";

// =======================
// Event data
// =======================
const events = [
  {
    side: "left",
    range: "JAN 20 - JAN 29",
    title: "Tamamo Cross",
    description: `Tamamo Cross is a weird horse that has <span style="color: red;">3 different position skills</span> in her innate kit. Her unique is mainly used for longs in terms of good proc timing so she's really just an end closer/late surger so some skills are kind of wasted. <span style="color: red;">Being specialized is better than being versatile</span>, oshi horse.`,
    fills: ["fill-green"],
    image: "images/0120-left-1.png",
    iconsLeft: ["icons/pace.png", "icons/late.png", "icons/end.png"],
    iconsRight: [],
    buttonsLeft: ["LONG"],
    buttonsRight: [],
    tags: ["PACE", "LATE", "END", "LONG", "NICHE"]
  },
  {
    side: "right",
    range: "JAN 20 - JAN 29",
    title: "Nice Nature Wit & Oguri Cap Power",
    description: `A gambler banner, Nice Nature gives <span style="color: #17c571;">On Your Left</span> while Oguri gives <span style="color: #17c571;">Furious Feat</span>. Both are <span style="color: red;">gambling skills for End Closers/Late Surgers primarily</span>. Pull if you love Lates/Ends otherwise save for major banners/horses.`,
    fills: ["fill-purple"],
    image: "images/0120-right-1.png",
    iconsLeft: ["icons/late.png"],
    iconsRight: ["icons/late.png"],
    buttonsLeft: [],
    buttonsRight: [],
    tags: ["LATE", "LUXURY"]
  },
  {
    side: "left",
    range: "JAN 27 - FEB 07",
    title: "NY Haru Urara & NY T.M. Opera",
    description: `NY Urara is much better than OG Urara but she is still not very strong, yet the Urara enjoyer shall want to pull this as <span style="color: red;">this will allow more Urara wins overall.</span>
As for NY TM Opera O, <span style="color: red;">she is one of the most used parents later on and she's a solid horse that can win as well</span>. Her unique gives you 0.25 speed if you activate 7 skills (an easy task later on).`,
    fills: ["fill-purple", "fill-orange"],
    image: "images/0127-left-1.png",
    iconsLeft: ["icons/late.png"],
    iconsRight: ["icons/pace.png", "icons/late.png"],
    buttonsLeft: ["DIRT"],
    buttonsRight: ["MED", "LONG"],
    tags: ["LATE", "PACE", "DIRT", "MED", "LONG", "LUXURY", "META"]
  },
  {
    side: "right",
    range: "JAN 27 - FEB 07",
    title: "Admire Vega Power & Fukukitaru Speed",
      description: `Admire Vega Power gives <span style="color: #17c571;">daring attack</span> a solid speed skill but unfortunately the card is only usable at MLB, very expensive and power cards are less than ideal because you would rather click wit than power most of the time.<br><br>
Fukukitaru Speed is a very strong high roll card but the key word is high roll, she can <span style="color: red;">low roll very hard</span>. She's a friendship card in disguise who gives you a ton of stats. You can <span style="color: red;">pull her if you like to high roll</span> but <span style="color: #17c571;">if you rather have higher consistency pull Top Road</span>. (Or pull both if rich)`,
      fills: ["fill-purple", "fill-orange"],
    image: "images/0127-right-1.png",
    iconsLeft: ["icons/end.png"],
    iconsRight: ["icons/front.png","icons/pace.png", "icons/late.png", "icons/end.png"],
    buttonsLeft: [],
    buttonsRight: [],
    tags: ["FRONT", "PACE", "LATE", "END", "LUXURY", "META"]
  },
  {
    side: "right",
    range: "JAN 27 - FEB 07",
    title: "Meishi Doto Stamina Card",
    description: `Gives Killer Tunes on a Stamina Card, really weird, stat output, not great. <span style="color: red;">Not relevant meta wise</span>. Free Card.`,
    fills: ["fill-green"],
    image: "images/0127-right-2.png",
    iconsLeft: ["icons/late.png"],
    iconsRight: [],
    buttonsLeft: [],
    buttonsRight: [],
    tags: ["LATE", "NICHE"]
  },
  {
    side: "left",
    range: "FEB 03 - FEB 12",
    title: "Character Banner",
    description: `It's a standard banner, what do you want?`,
    fills: ["fill-purple"],
    image: "images/0203-left-1.png",
    iconsLeft: [],
    iconsRight: [],
    buttonsLeft: [],
    buttonsRight: [],
    tags: ["LUXURY"]
  },
  {
    side: "right",
    range: "FEB 03 - FEB 12",
    title: "S. Anshinzawa Friend & Tamamo Cross Guts",
    description: `Anshinzawa is a <span style="color: red;">troll card</span>, no deck ever runs her. Tamamo Cross Guts is not a particularly significant card, no race bonus inside. Easy skip banner.<center><img src="${GITHUB_BASE_URL}icons/stat-card.png" style="max-width: 100%; height: auto;"></center>`,
    fills: ["fill-green"],
    image: "images/0203-right-1.png",
    iconsLeft: [],
    iconsRight: [],
    buttonsLeft: [],
    buttonsRight: [],
    tags: ["NICHE"]
  },
  {
    side: "left",
    range: "FEB 07 - MAR 27",
    title: "New Year Paid Banner (Uma)",
    description: `Nicknamed the scam banner. You are probably getting a dupe rather than a new horse but that also depends on your number of horses owned. Pull if you want.`,
    fills: ["fill-purple"],
    image: "images/0207-left-1.png",
    iconsLeft: [],
    iconsRight: [],
    buttonsLeft: [],
    buttonsRight: [],
    tags: ["LUXURY"]
  },
  {
    side: "right",
    range: "FEB 07 - MAR 27",
    title: "New Year Paid Banner (Support Card)",
    description: `Nicknamed the scam banner. You are probably getting Air Shakur Wit or Goldship Stam rather than an important card. Pull if you want.`,
    fills: ["fill-purple"],
    image: "images/0207-right-1.png",
    iconsLeft: [],
    iconsRight: [],
    buttonsLeft: [],
    buttonsRight: [],
    tags: ["LUXURY"]
  },
  {
    side: "left",
    range: "FEB 09 - FEB 17",
    title: "Sakura Chiyono O",
    description: `A spring oriented pace/front runner, comes with speed star, spring runner and pace savvy. Nothing else particularly strong about her. <span style="color: red;">Oshi horse</span>.`,
    fills: ["fill-green"],
    image: "images/0209-left-1.png",
    iconsLeft: ["icons/pace.png"],
    iconsRight: [],
    buttonsLeft: ["MILE", "MED"],
    buttonsRight: [],
    tags: ["PACE", "NICHE", "MILE", "MEDIUM"]
  },
    {
    side: "right",
    range: "FEB 09 - FEB 17",
    title: "Tazuna Friend & Riko Kashimoto Friend",
    description: `At this point, <span style="color: red;">these cards will no longer be used</span> except for MLB SSR Riko because of her 10% race bonus but even then she will fall off after MANT as well. I wouldn't recommend going out of your way to get the MLB Riko, there's plenty of good banners to pull on. <span style="color: #17c571;">Easy Skip</span>.`,
    fills: ["fill-green"],
    image: "images/0209-right-1.png",
    iconsLeft: [],
    iconsRight: [],
    buttonsLeft: [],
    buttonsRight: [],
    tags: ["NICHE"]
  },
  {
    side: "left",
    range: "FEB 15 - FEB 27",
    title: "Val. Mihono Bourbon & Val. Eishin Flash",
    description: `Valentine Bourbon is the <span style="color: red;">EASIEST front runner to make</span>, she has groundwork + front savvy + concentration + a secret event where if you get 60000 fans before valentine's day you get early lead.  Meta now, falls off a bit, Meta when LoH starts. 
Valentine Eishin Flash is <span style="color: red;">mostly just another dominator debuffer</span>, the other skills she has and her unique aren't much to speak about. `,
    fills: ["fill-orange", "fill-green"],
    image: "images/0215-left-1.png",
    iconsLeft: ["icons/front.png"],
    iconsRight: ["icons/late.png"],
    buttonsLeft: ["MED"],
    buttonsRight: [],
    tags: ["FRONT", "LATE", "MED", "META", "NICHE"]
  },
  {
    side: "right",
    range: "FEB 15 - FEB 27",
    title: "Nishino Flower Wit & Sakura Baksuhin O Guts",
    description: `Nishino Wit is <span style="color: red;">primarily used to get the gold skill downward descent</span>, it's really niche however, not every track has an ideal downhill. 
Bakushin O guts has <span style="color: red;">groundwork on 1st event</span> and a decent sprint mid-leg gold skill. 
Both of these cards don't have race bonus, not recommended since MANT is coming.
<span style="color: #17c571;">Skip</span>.`,
    fills: ["fill-green"],
    image: "images/0215-right-1.png",
    iconsLeft: ["icons/pace.png"],
    iconsRight: [],
    buttonsLeft: [],
    buttonsRight: ["SHORT"],
    tags: ["PACE", "SHORT", "NICHE"]
  },
  {
    side: "right",
    range: "FEB 15 - FEB 27",
    title: "Tosen Jordan SSR Speed",
    description: `If your cards are horrible, this speed card is an F2P's lifesaver. If your cards are good enough, not relevant. <span style="color: red;">It has Breath of Fresh Air</span> though.`,
    fills: ["fill-green"],
    image: "images/0215-right-2.png",
    iconsLeft: [],
    iconsRight: [],
    buttonsLeft: [],
    buttonsRight: [],
    tags: ["NICHE"]
  },
  {
    side: "left",
    range: "FEB 23 - MAR 03",
    title: "Mejiro Ardan",
    description: `Primarily a pace chaser for medium, she has a unique that activates on the last straight and has race planner. <span style="color: red;">Suffers from glass legs when racing too much</span> which eats 10 extra energy when you race consecutively <span style="color: red;">which isn't great when MANT is coming</span>.
<span style="color: #17c571;">Oshi horse</span>.`,
    fills: ["fill-green"],
    image: "images/0223-left-1.png",
    iconsLeft: ["icons/pace.png"],
    iconsRight: [],
    buttonsLeft: ["MED"],
    buttonsRight: [],
    tags: ["PACE", "MED", "NICHE"]
  },
  {
    side: "right",
    range: "FEB 23 - MAR 03",
    title: "Agnes Digital  SSR Power & Ines Fujin SR Wit",
    description: `Digital is <span style="color: #17c571;">another way to hunt down Uma Stan</span> but other than that is not too important because <span style="color: red;">she is a power card</span>. Also she has 5% race bonus, and her unique effect wants you to run a highlander deck (1 of every card). We aren't in JP yet sorry.
Ines Fujin <span style="color: #17c571;">gives some decent front runner skills</span> but sadly has <span style="color: red;">5% race bonus only</span>. 
<span style="color: #17c571;">Skip</span>.`,
    fills: ["fill-green"],
    image: "images/0223-right-1.png",
    iconsLeft: ["icons/late.png"],
    iconsRight: [],
    buttonsLeft: [],
    buttonsRight: [],
    tags: ["LATE", "NICHE"]
  },
  {
    side: "left",
    range: "FEB 28 - MAR 08",
    title: "Admire Vega",
    description: `This horse has a final straight unique and some end closer skills, straightaway spurt event is RNG. The timing is really bad, however, as <span style="color: red;">Admire Vega Guts SR is coming out and it's a very strong card for the MANT scenario</span> so you can't use it with her.
<span style="color: #17c571;">Oshi horse</span>.`,
    fills: ["fill-green"],
    image: "images/0228-left-1.png",
    iconsLeft: ["icons/end.png"],
    iconsRight: [],
    buttonsLeft: ["MED"],
    buttonsRight: [],
    tags: ["END", "MED", "NICHE"]
  },
  {
    side: "right",
    range: "FEB 28 - MAR 08",
    title: "Fine Motion Wit & Kawakami Princess Speed",
    description: `Fine Motion <span style="color: #17c571;">currently has the most stat gains on wit training with a high training effectiveness</span>. Do note that this banner is <span style="color: red;">right before a scenario banner</span> (Top Road Speed), so plan your pulls carefully. But she's definitely a card you would love to have.
Kawakami Princess is actually <span style="color: red;">a solid speed card but there are much better ones</span> like Biko, Fuku or Top Road for the MANT scenario. She does give center stage which is <span style="color: #17c571;">great for team trials however</span>.`,
    fills: ["fill-orange","fill-green"],
    image: "images/0228-right-1.png",
    iconsLeft: [],
    iconsRight: [],
    buttonsLeft: [],
    buttonsRight: [],
    tags: ["META", "NICHE"]
  },
  {
    side: "left",
    range: "MAR 06 - MAR 17",
    title: "Kitasan Black & Matikanetannhauser",
    description: `Kitasan Black is <span style="color: #17c571;">a strong long front runner horse</span>, will be a very strong pick alongside a variety of long horses later on. Her unique is good, her kit is good.<br><br>

Mambo is the complete opposite, she's pretty much like Haru Urara, a horse that is cute and <span style="color: red;">doesn't have much going for her in her kit</span>. Of course, she's a 2* so you are more likely to get her. <span style="color: #17c571;">Oshi pull</span>.`,
    fills: ["fill-purple", "fill-green"],
    image: "images/0306-left-1.png",
    iconsLeft: ["icons/front.png"],
    iconsRight: ["icons/late.png"],
    buttonsLeft: ["LONG"],
    buttonsRight: ["LONG"],
    tags: ["FRONT", "LONG", "LUXURY", "NICHE"]
  },
  {
    side: "right",
    range: "MAR 06 - MAR 17",
    title: "Narita Top Road SSR Speed & Admire Vega SR Guts",
    description: `NTR is <span style="color: #17c571;">a consistently powerful speed SSR made for MANT</span> and <span style="color: red;">falls off the moment MANT ends</span>. It's because she scales off Fans which requires a lot of races. 
<br>The real prize is <span style="color: red;">admire vega guts</span>, this card is so broken that even whales will use it. <span style="color: #17c571;">15% Race bonus with 1 speed and 1 power bonus</span> is just ridiculous.
Ryan has 5% race bonus, unusable in MANT.
Bakushin has 10% race bonus and gives tail held high, actually quite ok.
<span style="color: red;">Recommended to pull for Vega, NTR is more for dolphin/whale</span>.`,
    fills: ["fill-purple", "fill-orange"],
    image: "images/0306-right-1.png",
    iconsLeft: [],
    iconsRight: [],
    buttonsLeft: [],
    buttonsRight: [],
    tags: ["META", "LUXURY"]
  },
  {
    side: "right",
    range: "MAR 06 - MAR 17",
    title: "Mejiro Bright SSR Stamina",
    description: `Mejiro Bright Stamina gives the gold skill of pressure. <span style="color: red;">Not relevant meta wise</span>. Free Card.`,
    fills: ["fill-green"],
    image: "images/0306-right-2.png",
    iconsLeft: [],
    iconsRight: [],
    buttonsLeft: [],
    buttonsRight: [],
    tags: ["NICHE"]
  },
  {
    side: "left",
    range: "MAR 13 - MAR 24",
    title: "Satono Diamond",
    description: `<span style="color: #17c571;">A long late surger horse</span>, gets significantly stronger once late surger focused cards come out but she's really just alright. <span style="color: #17c571;">Oshi pull</span>.`,
    fills: ["fill-purple"],
    image: "images/0313-left-1.png",
    iconsLeft: ["icons/late.png"],
    iconsRight: [],
    buttonsLeft: ["LONG"],
    buttonsRight: [],
    tags: ["LATE", "LONG", "LUXURY"]
  },
  {
    side: "right",
    range: "MAR 13 - MAR 24",
    title: "Marvelous Sunday SSR Guts & Curren SR Speed",
    description: ` Marvelous Sunday Guts SSR is <span style="color: red;">very bad and can be easily skipped</span>, Marvelous Sunday Power SSR is a free card that is superior to her in every way especially for MANT. 
Curren Speed SR is a very good stat stick SR, very good for people with poor speed cards. <span style="color: red;">Don't pull this banner JUST for curren</span>.
<span style="color: #17c571;">Easy Skip</span>.`,
    fills: ["fill-green", "fill-purple"],
    image: "images/0313-right-1.png",
    iconsLeft: [],
    iconsRight: [],
    buttonsLeft: [],
    buttonsRight: [],
    tags: ["NICHE", "LUXURY"]
  },
  {
    side: "left",
    range: "MAR 21 - APR 01",
    title: "Mejiro Bright",
    description: `A weird horse that <span style="color: red;">wants to have a ton of stamina for more duration on her unique</span>, this actually ends up being bad most of the time. She's never relevant for meta purposes. <span style="color: #17c571;">Oshi pull</span>.`,
    fills: ["fill-green"],
    image: "images/0321-left-1.png",
    iconsLeft: ["icons/late.png", "icons/end.png"],
    iconsRight: [],
    buttonsLeft: [],
    buttonsRight: [],
    tags: ["LATE", "END", "LONG", "NICHE"]
  },
  {
    side: "right",
    range: "MAR 21 - APR 01",
    title: "Zenno Rob Roy SSR Speed & Curren SSR Wit",
    description: `Zenno Rob Roy <span style="color: red;">falls off in MANT</span> due to no race bonus. <br><br>

Curren Wit does have 10% race bonus and gives perfect prep a good skill for sprint. <span style="color: #17c571;">She will be relevant for sprint CMs</span> which happens maybe 1-2 times a year (better off borrowing).
<span style="color: #17c571;">Recommended to skip.</span>`,
    fills: ["fill-purple"],
    image: "images/0321-right-1.png",
    iconsLeft: [],
    iconsRight: [],
    buttonsLeft: [],
    buttonsRight: [],
    tags: ["LUXURY"]
  },
  {
    side: "left",
    range: "MAR 21 - APR 12",
    title: "1st Anniversary Paid Banner (Uma)",
    description: `Nicknamed the scam banner. You are probably getting a dupe rather than a new horse but that also depends on your number of horses owned. Pull if you want.`,
    fills: ["fill-purple"],
    image: "images/0322-left-1.png",
    iconsLeft: [],
    iconsRight: [],
    buttonsLeft: [],
    buttonsRight: [],
    tags: ["LUXURY"]
  },
  {
    side: "right",
    range: "MAR 21 - APR 12",
    title: "1st Anniversary Paid Banner (Support Card)",
    description: `Nicknamed the scam banner. You are probably getting Air Shakur Wit or Goldship Stamina rather than a relevant card. Pull if you want.`,
    fills: ["fill-purple"],
    image: "images/0322-right-1.png",
    iconsLeft: [],
    iconsRight: [],
    buttonsLeft: [],
    buttonsRight: [],
    tags: ["LUXURY"]
  },
  {
    side: "left",
    range: "MAR 29 - APR 11",
    title: "Ballroom Seiun Sky & Ballroom Fuji Kiseki",
    description: `Ballroom Seiun Sky is <span style="color: #17c571;">a strong front runner horse</span> and is <span style="color: #17c571;">a relevant parent for some tracks</span> just like the OG Seiun Sky. She does not make it any easier to make a front so you will still have to do it the old fashioned way (Sparks + Cards).
<br><br>
Ballroom Fuji is <span style="color: #17c571;">a strong mile pace chaser horse</span> and she will only get stronger with the addition of evolved skills. Meta wise, <span style="color: red;">there are better milers than her so not a must have</span>.`,
    fills: ["fill-orange", "fill-purple"],
    image: "images/0329-left-1.png",
    iconsLeft: ["icons/front.png"],
    iconsRight: ["icons/late.png"],
    buttonsLeft: ["MED", "LONG"],
    buttonsRight: ["MILE"],
    tags: ["MED", "LONG", "MILE", "META","LUXURY"]
  },
  {
    side: "right",
    range: "MAR 29 - APR 11",
    title: "Symboli Rudolf SSR Stam & Sirius Symboli SSR Wit",
    description: ` Symboli Rudolf is mostly <span style="color: red;">a debuffer card</span> as she good hints and hint levels. You wouldn't go out of your way to hunt down the gold skill on this card since <span style="color: red;">the card's stat output is quite meh</span>.
<br>Sirius Symboli <span style="color: #17c571;">gives you a medium acceleration gold skill</span> but for mediums, you're usually fine with the good ol, no.1,5 or 6 position uniques + nimble nav or other accels, <span style="color: red;">so no need to hunt down this gold skill here</span>.
<span style="color: #17c571;">Easy Skip Banner</span>.`,
    fills: ["fill-green"],
    image: "images/0329-right-1.png",
    iconsLeft: [],
    iconsRight: [],
    buttonsLeft: [],
    buttonsRight: [],
    tags: ["NICHE"]
  },
  {
    side: "right",
    range: "MAR 29 - APR 11",
    title: "Air Shakur SSR Speed Card",
    description: `Usable if no other options, or if you want to hunt for calm and collected gold recovery.`,
    fills: ["fill-green"],
    image: "images/0329-right-2.png",
    iconsLeft: [],
    iconsRight: [],
    buttonsLeft: [],
    buttonsRight: [],
    tags: ["NICHE"]
  },
  {
    side: "left",
    range: "APR 07 - APR 14",
    title: "Nishino Flower",
    description: `Nishino Flower is <span style="color: red;">a Meta parent</span> and can be used for
shorts or miles as an ace.
 Usually you just inherit her since her innate skills
aren't super amazing but there will be times
where her innate skills will be more relevant.`,
    fills: ["fill-orange"],
    image: "images/0407-left-1.png",
    iconsLeft: ["icons/pace.png"],
    iconsRight: [],
    buttonsLeft: ["SHORT", "MILE"],
    buttonsRight: [],
    tags: ["SHORT", "MILE", "META"]
  },
  {
    side: "right",
    range: "APR 07 - APR 14",
    title: "Daiwa Scarlet SSR Power & Sweep Tosho Wit",
    description: `Daiwa Scarlet has 10% Race Bonus so it's actually usable for MANT and has golden Head-On for pace chasers. Bad news is <span style="color: red;">she's a power card</span>, you will find that power cards are rarely used because <span style="color: red;">you would rather click other things to train it</span>.
<br><br>
Sweep Tosho Wit has 10% Race Bonus but <span style="color: red;">there's probably some better wits cards</span> that you will want to be shoving into your deck such as <span style="color: #17c571;">Agnes Tachyon, Nice Nature or Fine Motion</span>.
<span style="color: #17c571;">Easy Skip.</span>`,
    fills: ["fill-green"],
    image: "images/0407-right-1.png",
    iconsLeft: [],
    iconsRight: [],
    buttonsLeft: [],
    buttonsRight: [],
    tags: ["NICHE"]
  }
];


// =======================
// Rendering helpers
// =======================
function renderIcons(iconList = [], align) {
  return `
    <div class="icon-row ${align || ""}">
      ${iconList
        .map(icon => {
          const isImage =
            typeof icon === "string" &&
            (icon.endsWith(".png") || icon.endsWith(".jpg") || icon.endsWith(".jpeg") || icon.endsWith(".svg") || icon.startsWith("http"));
          const iconSrc = isImage && !icon.startsWith("http") ? GITHUB_BASE_URL + icon : icon;
          return isImage
            ? `<img src="${iconSrc}" alt="icon" class="icon-img" />`
            : `<span class="icon-emoji">${icon}</span>`;
        })
        .join("")}
    </div>
  `;
}

function renderButtons(buttonList = [], align) {
  if (!buttonList.length) return "";
  return `
    <div class="button-grid ${align || ""}">
      ${buttonList.map(label => {
        const upperLabel = label.toUpperCase();
        if (['MILE', 'MED', 'LONG', 'DIRT', 'SHORT'].includes(upperLabel)) {
          return `<div class="button-box"><img src="${GITHUB_BASE_URL}icons/${upperLabel.toLowerCase()}.png" alt="${label}" class="button-icon" /></div>`;
        }
        return `<div class="button-box">${label}</div>`;
      }).join("")}
    </div>
  `;
}

function renderFill(fills = []) {
  if (!fills.length) return "";
  if (fills.length === 1) {
    return `<div class="event-fill solid ${fills[0]}"></div>`;
  }
  return `
    <div class="event-fill">
      <div class="fill-half ${fills[0]}"></div>
      <div class="fill-half ${fills[1]}"></div>
    </div>
  `;
}

// =======================
// Render timeline
// =======================
function renderTimeline(evts) {
  const timeline = document.getElementById("timeline");
  if (!timeline) return;
 
  timeline.innerHTML = '<div class="timeline-line" id="timeline-line"></div>';

  const grouped = {};
  evts.forEach(ev => {
    const key = ev.range || "Unscheduled";
    if (!grouped[key]) grouped[key] = [];
    grouped[key].push(ev);
  });

  Object.keys(grouped).forEach(range => {
    const row = document.createElement("div");
    row.className = "timeline-row";

    const leftContainer = document.createElement("div");
    leftContainer.className = "left-events";

    const dateRange = document.createElement("div");
    dateRange.className = "date-range";
    dateRange.textContent = range;

    const connector = document.createElement("div");
    connector.className = "connector";

    const rightContainer = document.createElement("div");
    rightContainer.className = "right-events";

    grouped[range].forEach(ev => {
      const box = document.createElement("div");
      box.className = ev.side === "left" ? "event-box-left" : "event-box-right";
      
      
      if (ev.tags && ev.tags.length > 0) {
        box.setAttribute('data-tags', ev.tags.join(' '));
      }
      
      box.innerHTML = `
        ${renderFill(ev.fills)}
        <div class="event-content">
          <div class="event-title">${ev.title || ""}</div>
          ${ev.image ? `<img src="${GITHUB_BASE_URL}${ev.image}" alt="${ev.title || "event image"}" class="event-img" />` : ""}
          <p class="event-description">${ev.description || ""}</p>
          ${renderIcons(ev.iconsLeft || [], "left")}
          ${renderIcons(ev.iconsRight || [], "right")}
        </div>
        ${renderButtons(ev.buttonsLeft || [], "left")}
        ${renderButtons(ev.buttonsRight || [], "right")}
      `;
      const target = ev.side === "left" ? leftContainer : rightContainer;
      target.appendChild(box);
    });

    row.appendChild(leftContainer);
    row.appendChild(dateRange);
    row.appendChild(connector);
    row.appendChild(rightContainer);
    timeline.appendChild(row);
  });

  const imgs = timeline.querySelectorAll("img");
  imgs.forEach(img => {
    img.addEventListener("load", () => {
      positionTimelineLine();
      positionConnectors();
    });
  });
}

// =======================
// Scaling + connectors
// =======================


function positionTimelineLine() {
  const line = document.getElementById("timeline-line");
  const timeline = document.querySelector(".timeline");
  const allRows = document.querySelectorAll(".timeline-row");
  
  
  const visibleRows = Array.from(allRows).filter(row => row.style.display !== 'none');
  
  if (!line || !timeline || visibleRows.length < 1) {
    if (line) line.style.height = '0px';
    return;
  }

  const tlRect = timeline.getBoundingClientRect();

  const firstDateRange = visibleRows[0].querySelector('.date-range');
  const lastDateRange = visibleRows[visibleRows.length - 1].querySelector('.date-range');
  
  if (!firstDateRange || !lastDateRange) return;

  const firstRect = firstDateRange.getBoundingClientRect();
  const lastRect = lastDateRange.getBoundingClientRect();

  const top = firstRect.top - tlRect.top;
  const bottom = lastRect.bottom - tlRect.top;
  const height = bottom - top;

  line.style.top = `${Math.max(0, top)}px`;
  line.style.left = "50%";
  line.style.height = `${Math.max(0, height)}px`;
}

function positionConnectors() {
  const rows = document.querySelectorAll(".timeline-row");
  rows.forEach(row => {
    
    if (row.style.display === 'none') return;
    
    const dateRange = row.querySelector(".date-range");
    const baseConnector = row.querySelector(".connector");
    if (!dateRange || !baseConnector) return;
  
    row.querySelectorAll(".connector.segment").forEach(seg => seg.remove());

    const rowRect = row.getBoundingClientRect();
    const dateRect = dateRange.getBoundingClientRect();
    const centerY = dateRect.top + dateRect.height / 2 - rowRect.top - 2;
    const scale = 1;

    const allLeftEvents = row.querySelectorAll(".event-box-left");
    const allRightEvents = row.querySelectorAll(".event-box-right");
    
    const leftEvents = Array.from(allLeftEvents).filter(box => box.style.display !== 'none');
    const rightEvents = Array.from(allRightEvents).filter(box => box.style.display !== 'none');

    const leftTarget = leftEvents.length
      ? leftEvents.reduce((closest, box) => {
          const rect = box.getBoundingClientRect();
          return !closest || rect.right > closest.getBoundingClientRect().right ? box : closest;
        }, null)
      : null;

    const rightTarget = rightEvents.length
      ? rightEvents.reduce((closest, box) => {
          const rect = box.getBoundingClientRect();
          return !closest || rect.left < closest.getBoundingClientRect().left ? box : closest;
        }, null)
      : null;

    function drawSegment(startX, endX) {
      const seg = document.createElement("div");
      seg.className = "connector segment";
      seg.style.top = `${centerY}px`;
      seg.style.left = `${Math.min(startX, endX)}px`;
      seg.style.width = `${Math.abs(endX - startX)}px`;
      row.appendChild(seg);
    }

    const hasLeft = !!leftTarget;
    const hasRight = !!rightTarget;

    baseConnector.style.position = "absolute";
    baseConnector.style.height = "4px";
    baseConnector.style.top = `${centerY}px`;

    if (hasLeft && hasRight) {
      baseConnector.style.display = "none";
      const leftRect = leftTarget.getBoundingClientRect();
      const rightRect = rightTarget.getBoundingClientRect();
      drawSegment(leftRect.right - rowRect.left, dateRect.left - rowRect.left);
      drawSegment(dateRect.right - rowRect.left, rightRect.left - rowRect.left);
    } else if (hasLeft) {
      baseConnector.style.display = "block";
      const leftRect = leftTarget.getBoundingClientRect();
      const startX = Math.min(leftRect.right - rowRect.left, dateRect.left - rowRect.left);
      const endX = Math.max(leftRect.right - rowRect.left, dateRect.left - rowRect.left);
      baseConnector.style.left = `${startX}px`;
      baseConnector.style.width = `${endX - startX}px`;
    } else if (hasRight) {
      baseConnector.style.display = "block";
      const rightRect = rightTarget.getBoundingClientRect();
      const startX = Math.min(dateRect.right - rowRect.left, rightRect.left - rowRect.left);
      const endX = Math.max(dateRect.right - rowRect.left, rightRect.left - rowRect.left);
      baseConnector.style.left = `${startX}px`;
      baseConnector.style.width = `${endX - startX}px`;
    } else {
      baseConnector.style.display = "block";
      baseConnector.style.width = "0px";
      baseConnector.style.left = `${dateRect.left - rowRect.left}px`;
    }
  });
}

// =======================
// Bootstrapping
// =======================
function updateTimeline() {
  renderTimeline(events);
  requestAnimationFrame(() => {
    positionTimelineLine();
    positionConnectors();
  });
}

let resizeTimer = null;
function onResize() {
  if (resizeTimer) clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    requestAnimationFrame(() => {
      positionTimelineLine();
      positionConnectors();
    });
  }, 50);
}

function observeMutations() {
  const timeline = document.querySelector(".timeline");
  if (!timeline) return;
  const observer = new MutationObserver(() => {
    requestAnimationFrame(() => {
      positionTimelineLine();
      positionConnectors();
    });
  });
  observer.observe(timeline, { childList: true, subtree: true });
}

function setEvents(newEvents) {
  while (events.length) events.pop();
  newEvents.forEach(e => events.push(e));
  updateTimeline();
}

function addEvent(ev) {
  events.push(ev);
  updateTimeline();
}

window.addEventListener("load", () => {
  updateTimeline();
  observeMutations();
});
window.addEventListener("resize", onResize);

// =======================
// Search
// =======================


function matchesQuery(ev, query) {
  const q = query.toLowerCase();
  return (
    (ev.title && ev.title.toLowerCase().includes(q)) ||
    (ev.description && ev.description.toLowerCase().includes(q)) ||
    (ev.range && ev.range.toLowerCase().includes(q))
  );
}

function highlightTextInElement(el, query) {
  if (!query) return;
  const regex = new RegExp(`(${query})`, "gi");
  el.innerHTML = el.textContent.replace(regex, `<span class="highlight">$1</span>`);
}

function searchTimeline(query) {
  if (!query) {
    updateTimeline(); // show all
    return;
  }

  const filtered = events.filter(ev => matchesQuery(ev, query));

  renderTimeline(filtered);
  requestAnimationFrame(() => {
    positionTimelineLine();
    positionConnectors();

    const titles = document.querySelectorAll(".event-title");
    const descs = document.querySelectorAll(".event-description");
    const ranges = document.querySelectorAll(".date-range");
    [...titles, ...descs, ...ranges].forEach(el => highlightTextInElement(el, query));
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("timeline-search-input");
  if (searchInput) {
    searchInput.addEventListener("input", e => {
      searchTimeline(e.target.value);
    });
  }
});

// =======================
// Back to top
// =======================

document.addEventListener("DOMContentLoaded", () => {
  const backToTop = document.getElementById("back-to-top");

  window.addEventListener("scroll", () => {
    if (window.scrollY > 200) {
      backToTop.classList.add("show");
    } else {
      backToTop.classList.remove("show");
    }
  });

  backToTop.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
});


// =======================
// Legend toggle + Back to Top + Legend positioning
// =======================


const legendCard = document.getElementById("legend");
const legendToggle = document.getElementById("legend-toggle");
if (legendToggle && legendCard) {
  const headerIcon = legendToggle.querySelector(".header-icon");
  legendToggle.addEventListener("click", () => {
    legendCard.classList.toggle("collapsed");
    if (headerIcon) {
      headerIcon.textContent = legendCard.classList.contains("collapsed") ? "▶" : "▼";
    }
    requestAnimationFrame(placeLegendNoOverlap);
  });
}

const backToTopBtn = document.getElementById("back-to-top");
if (backToTopBtn) {
  window.addEventListener("scroll", () => {
    backToTopBtn.classList.toggle("show", window.scrollY > 300);
  }, { passive: true });
  backToTopBtn.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
}

function getAbsRect(el) {
  const r = el.getBoundingClientRect();
  return {
    top: r.top + window.scrollY,
    bottom: r.bottom + window.scrollY,
    height: r.height
  };
}

function placeLegendNoOverlap() {
  const legend = document.getElementById("legend");
  const allRanges = document.querySelectorAll(".date-range");
  
  const ranges = Array.from(allRanges).filter(range => {
    const row = range.closest('.timeline-row');
    return !row || row.style.display !== 'none';
  });
  
  if (!legend || !ranges.length) return;

  legend.style.position = "fixed";
  
  const firstRange = ranges[0];
  const firstRect = firstRange.getBoundingClientRect();
  const centerX = firstRect.left + firstRect.width / 2;
  
  legend.style.left = `${centerX}px`;
  legend.style.transform = "translateX(-50%)";

  const legendHeight = legend.offsetHeight;

  const firstAbs = getAbsRect(ranges[0]);
  const minTopViewport = firstAbs.bottom - window.scrollY + 10;

  let desiredTopViewport = 10;

  for (const dr of ranges) {
    const abs = getAbsRect(dr);
    const desiredTopDoc = desiredTopViewport + window.scrollY;
    const desiredBottomDoc = desiredTopDoc + legendHeight;

    const overlaps = desiredTopDoc < abs.bottom && desiredBottomDoc > abs.top;
    if (overlaps) {
      desiredTopViewport = abs.bottom - window.scrollY + 10;
    }
  }

  if (desiredTopViewport < minTopViewport) {
    desiredTopViewport = minTopViewport;
  }

  legend.style.top = `${Math.round(desiredTopViewport)}px`;
}

window.addEventListener("load", () => {
  placeLegendNoOverlap();
  window.addEventListener("scroll", placeLegendNoOverlap, { passive: true });
  window.addEventListener("resize", placeLegendNoOverlap);
});

document.addEventListener("DOMContentLoaded", placeLegendNoOverlap);

const searchInput = document.getElementById("timeline-search-input");
if (searchInput) {
  searchInput.addEventListener("input", () => {
    requestAnimationFrame(placeLegendNoOverlap);
  });
}

document.addEventListener("load", () => {
  requestAnimationFrame(placeLegendNoOverlap);
}, true);

// =======================
// Filter Box Functionality
// =======================
const activeFilters = new Set();

document.querySelectorAll('.filter-box').forEach(filterBox => {
  filterBox.addEventListener('click', () => {
    const tag = filterBox.getAttribute('data-tag');
    
    if (activeFilters.has(tag)) {
      activeFilters.delete(tag);
      filterBox.style.backgroundColor = '#ece7e4';
      filterBox.style.color = '#794016';
      filterBox.style.fontWeight = 'normal';
    } else {
      activeFilters.add(tag);
      filterBox.style.backgroundColor = '#8cd33f';
      filterBox.style.color = '#fff';
      filterBox.style.fontWeight = 'bold';
    }
    
    applyFilters();
  });
});

function applyFilters() {
  const eventBoxes = document.querySelectorAll('.event-box-left, .event-box-right');
  
  eventBoxes.forEach(box => {
    if (activeFilters.size === 0) {
      box.style.display = '';
    } else {
      const boxTags = (box.getAttribute('data-tags') || '').split(' ');
      const hasMatch = [...activeFilters].every(filter => boxTags.includes(filter));
      
      box.style.display = hasMatch ? '' : 'none';
    }
  });
  
  document.querySelectorAll('.timeline-row').forEach(row => {
    const leftBoxes = row.querySelectorAll('.event-box-left');
    const rightBoxes = row.querySelectorAll('.event-box-right');
    const hasVisibleLeft = Array.from(leftBoxes).some(box => box.style.display !== 'none');
    const hasVisibleRight = Array.from(rightBoxes).some(box => box.style.display !== 'none');
    
    if (!hasVisibleLeft && !hasVisibleRight) {
      row.style.display = 'none';
    } else {
      row.style.display = '';
    }
  });
  
  requestAnimationFrame(() => {
    positionTimelineLine();
    positionConnectors();
    placeLegendNoOverlap();
  });
}
