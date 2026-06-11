#!/usr/bin/env python3
"""
Phase 12 — Build the static DOP comparison website.

Generates:
  site/index.html          — card grid, one card per chapter, grouped by Book
  site/chapters/<slug>.html — individual chapter pages with difference essay
  site/style.css
  site/app.js
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
COMP_JSON  = ROOT / "outputs" / "tables" / "comparison_table.json"
TITLES_JSON = ROOT / "outputs" / "tables" / "chapter_titles.json"
SITE_DIR   = ROOT / "site"
CHAP_DIR   = SITE_DIR / "chapters"
SITE_DIR.mkdir(exist_ok=True)
CHAP_DIR.mkdir(exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# English chapter titles (supplement / override extracted Latin-only titles)
# Source: standard secondary literature on DOP structure.
# ─────────────────────────────────────────────────────────────────────────────
ENGLISH_TITLES: dict[tuple[int, int], str] = {
    # Book I
    (1,  1): "How Magicians Collect Virtues from the Triple World",
    (1,  2): "What Magic Is, Its Parts, and the Magician's Qualifications",
    (1,  3): "The Three Kinds of Magic",
    (1,  4): "Of Unity and Its Scale",
    (1,  5): "The Wonderful Natures of Fire and Earth",
    (1,  6): "The Wonderful Natures of Water, Air, and Wind",
    (1,  7): "Of Compounds, Mixtures, and Natural Things",
    (1,  8): "How Elements Appear in the Heavens, Stars, Devils, Angels, and God",
    (1,  9): "Of Natural Virtues Depending on the Elements",
    (1, 10): "Of Occult Virtues in Things",
    (1, 11): "How Ideas Infuse Occult Virtues via the Soul of the World and Stars",
    (1, 12): "How Particular Virtues Are Infused into Individuals of the Same Species",
    (1, 13): "Whence the Occult Virtues of Things Proceed",
    (1, 14): "Of the Spirit of the World as the Bond of Occult Virtues",
    (1, 15): "How to Find Out Virtues by Way of Similitude",
    (1, 16): "That Human Suffering Is the Cause of Magical Operations",
    (1, 17): "How Virtues Are Found by Enmity and Friendship",
    (1, 18): "Of the Inclinations of Enmities",
    (1, 19): "How to Find Virtues Specific to Individuals",
    (1, 20): "Of the Virtues of Plants and Their Celestial Agreement",
    (1, 21): "Of Animal Virtues Depending on Stellar Motion",
    (1, 22): "How Inferior Things Submit to the Stars; Men's Dispositions Ascribed to Signs",
    (1, 23): "Of the Seals and Characters of Natural Things",
    (1, 24): "Of the Virtue of Names Derived from Numbers and Figures",
    (1, 25): "How Inferior Species Participate with the Celestial",
    (1, 26): "Of the Images of the Zodiac and Their Virtues",
    (1, 27): "How the Sun and Moon Imprint Their Virtues in Natural Things",
    (1, 28): "Of the Properties of the Fixed Stars and Their Images",
    (1, 29): "How Stones, Metals, and Plants Receive Virtue from the Stars",
    (1, 30): "How Magical Rings Are Made from Stones and Metal",
    (1, 31): "Of Lights, Lamps, and Candles and Their Compositions",
    (1, 32): "Of Suffumigations, Their Virtues and Compositions",
    (1, 33): "Of the Virtues of Things Placed Under Celestial Bodies",
    (1, 34): "How We May Know What Things Are Under the Sun, Moon, or Stars",
    (1, 35): "Of the Images of Saturn and Their Virtue",
    (1, 36): "Of the Images of Jupiter and Their Virtue",
    (1, 37): "Of the Images of Mars",
    (1, 38): "Of the Images of the Sun",
    (1, 39): "Of the Images of Venus",
    (1, 40): "Of the Images of Mercury",
    (1, 41): "Of the Images of the Moon",
    (1, 42): "Of Compound Images",
    (1, 43): "Of the Images of the Mansions of the Moon",
    (1, 44): "Of the Images of the Fixed Stars",
    (1, 45): "Of Magical Rings and Their Compositions",
    (1, 46): "Of the Virtue of Places, and What Stars Dominate What Regions",
    (1, 47): "Of the Virtue of Seasons; Magical Operations in Due Season",
    (1, 48): "Of Hours of the Day and Night and Their Virtues",
    (1, 49): "Of the Computation of Hours",
    (1, 50): "Of Finding Out and Knowing What Stars Rule Each Hour",
    (1, 51): "Certain Observations Concerning the Figures and Hours",
    (1, 52): "Of the Four Scales of Numbers",
    (1, 53): "Of Geomancy, Hydromancy, Aeromancy, and Pyromancy",
    (1, 54): "Of Divination and Its Kinds",
    (1, 55): "Of Lots and Marks, and How Lots Are Drawn",
    (1, 56): "Of the Soothsaying of Brute Animals and Their Portents",
    (1, 57): "Of Things Said About Prodigies and Portents",
    (1, 58): "Of the Ominous Observations of Things Fallen from the Sky",
    (1, 59): "Of the Virtue of Proper Names",
    (1, 60): "Of Magical Words and How They Help Natural Operations",
    (1, 61): "Of the Virtue of Writing, and of Making Magical Books",
    (1, 62): "Of Magical Characters and Seals",
    (1, 63): "Why Magicians Use Superstitious Observations",
    (1, 64): "Of Certain Observations of Ceremonial Magic",
    (1, 65): "Of Coloring in Magic and the Use of Colors",
    (1, 66): "How Stars Are Allotted to Things by the Physicians",
    (1, 67): "Of the Virtue of Numbers and Their Mystical Powers",
    (1, 68): "Of the Wonderful Virtues of Numbers",
    (1, 69): "Of the Scale of the Number Ten and Its Wonders",
    (1, 70): "Of the Virtue of One's Own Name",
    (1, 71): "Of the Virtue of Natural Things Consecrated in the Name of God",
    (1, 72): "Of Benedictions and Imprecations",
    (1, 73): "Of Things That Strengthen, Confirm, and Increase Magic",
    (1, 74): "The Conclusion of Natural Magic",
    # Book II (selected key chapters)
    (2,  1): "Of the Necessity of Mathematical Learning for Magic",
    (2,  2): "Of Number and Its Dignity",
    (2,  3): "How Great Virtues Numbers Have in Natural Things",
    (2,  4): "Of Unity and the Scale of One",
    (2,  5): "Of the Number Two and the Scale of Two",
    (2,  6): "Of the Ternary and Its Scale",
    (2,  7): "Of the Number Four and Its Scale",
    (2,  8): "Of the Number Five and Its Scale",
    (2,  9): "Of the Number Six and Its Scale",
    (2, 10): "Of the Number Seven and Its Scale",
    (2, 11): "Of the Number Eight and Its Scale",
    (2, 12): "Of the Number Nine and Its Scale",
    (2, 13): "Of the Number Ten and Its Scale",
    (2, 14): "Of the Numbers Eleven and Twelve",
    (2, 15): "Of the Virtue of Numbers in Words and Names",
    (2, 16): "Of the Harmony of Proportions and What Virtues They Have",
    (2, 17): "Of the Proportion of Sounds and Harmony",
    (2, 18): "Of the Composition of the Harmonic Scale",
    (2, 19): "Of Celestial Harmony",
    (2, 20): "Of Elemental Harmony",
    (2, 21): "Of Natural Harmony; How to Know What Things Agree and Disagree",
    (2, 22): "Of the Violent and Temperate Winds and Their Signs",
    (2, 23): "Of Geometrical Figures and Bodies and Their Virtues",
    (2, 24): "Of Musical Notes and Their Virtue",
    (2, 25): "Of the Wonderful Nature of Music and Its Virtue",
    (2, 26): "Of Oracles and Magical Agreements and Enchantments",
    (2, 29): "Of Light, Colors, Candles, and Lamps and Their Effects",
    (2, 35): "Of the Tables of the Planets",
    (2, 36): "Of the Images of the Planets According to the Faces",
    (2, 37): "Of the Magical Virtue of Letters and Characters",
    (2, 38): "Of the Characters of Geomancy",
    (2, 39): "Of the Characters of the Fixed Stars",
    (2, 40): "Of the Magical Figures of the Planets",
    (2, 50): "Of Images and Seals of the Planets",
    (2, 59): "Of the Proportion and Harmony of Human Parts",
    (2, 60): "Of Virtues and Gifts of the Holy Spirit",
    # Book III (selected key chapters)
    (3,  1): "Of the Three Guides of Religion, Hope, Faith, and Love",
    (3,  2): "Of Confessing God and Christ and the Saints",
    (3,  3): "Of Prayer, Fasting, and Chastity",
    (3,  4): "Of Finding the Angels and Their Orders",
    (3,  5): "Of the Orders of Evil Spirits and Their Descent",
    (3,  6): "Of the Principality, Prevalence, and Decay of Spirits",
    (3,  7): "Of the Ten Divine Names and How They Correspond to the Sephiroth",
    (3,  8): "Of the Divine Names and Their Power",
    (3,  9): "Of the Name of God, Tetragrammaton and Its Virtue",
    (3, 10): "Of the Three Names of God: El, Elohim, and Tetragrammaton",
    (3, 11): "Of the Various Orders of Spirits and How They Are Governed",
    (3, 12): "Of the Occult Virtue of the Seventy-two Names of God",
    (3, 13): "Of the Angels and Their Orders and Properties",
    (3, 14): "Of Good and Evil Genii and How They Attend on Humans",
    (3, 15): "Of the Devils and Their Many Species",
    (3, 16): "Of the Orders of Evil Spirits",
    (3, 17): "Of the Illusions of Demons and How to Resist Them",
    (3, 18): "Of the Bonds of Spirits and How They Are Made",
    (3, 19): "Of the Power of the Soul over the Body",
    (3, 20): "Of the Union of the Soul with the Body",
    (3, 21): "Of the Soul's Triple Power",
    (3, 22): "Of the Intellectual Soul",
    (3, 23): "Of the Sensitive Soul",
    (3, 24): "Of the Vegetative Soul",
    (3, 25): "How the Superior Influx Descends Through the Soul to the Body",
    (3, 26): "Of the Passions of the Mind, How They Produce Changes in the Body",
    (3, 27): "Of Frenzy and Madness, and How They Participate in Divination",
    (3, 28): "Of the Ecstasy of Magi and Their Sleep and Dreams",
    (3, 29): "How the Soul by Vehement Emotion Works Magic on the Body",
    (3, 30): "How the Soul May Escape the Body and Wander Abroad",
    (3, 31): "Of the Prophetical Dream",
    (3, 32): "Of Oracles of Dreams; How to Prepare for Them",
    (3, 33): "Of the Soul's Union with God and Its Demonical Assistance",
    (3, 34): "Of the Natural Assistance of the Soul with the World-Soul",
    (3, 35): "Of the Purification of the Soul for Prophetic Work",
    (3, 36): "Of the Composition of Magical Medicines",
    (3, 37): "Of the Proportion and Concordance of Various Things",
    (3, 38): "Of the Composition of Harmonious Water, Fire, Earth, and Air",
    (3, 39): "Of Sacred Ceremonies and Their Necessity",
    (3, 40): "Of Consecrations and Their Virtue",
    (3, 41): "Of the Virtues of Suffumigations",
    (3, 42): "Of Benedictions and Curses",
    (3, 43): "Of Sacred Unctions and Purgations",
    (3, 44): "Of Sacrifice and Its Kinds",
    (3, 45): "Of the Kinds of Sacrifice and Their Virtues",
    (3, 46): "Of Bindings and Ligatures",
    (3, 47): "Of Conjugations, Pacts, Compacts, and Their Virtues",
    (3, 48): "Of Invocation and Adjuration of Evil Spirits",
    (3, 49): "Of Exorcisms and Their Virtue",
    (3, 50): "How We Are to Understand the Presence of Divine Goodness",
    (3, 51): "Of Finding Out the Virtue of a Place",
    (3, 52): "Of the Oration of Picus Mirandulanus for the World and Its Virtues",
    (3, 53): "Of Characters and Signs of Celestial Bodies",
    (3, 54): "Of the Construction of Characters",
    (3, 55): "Of Magical Texts and the Form of Magical Words",
    (3, 56): "Of Magical Ceremonies and Usages",
    (3, 57): "Of the Construction of the Pentacle of Solomon",
    (3, 58): "Concerning the Ablutions and Purifications of the Magician",
    (3, 59): "Of the Initiations and Examinations of the Magician",
    (3, 60): "Of Fascinations and the Evil Eye",
    (3, 61): "Of Coloring in Magic",
    (3, 62): "Of the Virtue of Places and Times for Operations",
    (3, 63): "Of the Epilogue to the Whole Work",
    (3, 64): "Of the Disposition and Form of Magical Circles",
    (3, 65): "Epilogue of the Whole Work",
}

# Epistle labels
EPIST_LABELS: dict[str, str] = {
    "Epist. omnibus lectoribus": "Letter to All Readers",
    "Epist. J. Tritemio":        "Letter to Johannes Trithemius",
    "Epist. J. Tritemii":        "Reply Letter of Trithemius",
    "Epist. Hermanno ab Wyda":   "Letter to Hermannus ab Wyda",
    "Epist.":                    "Prefatory Epistle (Book II)",
    "Epist. ":                   "Prefatory Epistle",
}


# ─────────────────────────────────────────────────────────────────────────────
# Scholarly notes
# Sources:
#   LEHRICH  = Christopher I. Lehrich, The Language of Demons and Angels:
#              Cornelius Agrippa's Occult Philosophy (Brill, 2003)
#   VDP      = Marc van der Poel, Cornelius Agrippa the Humanist Theologian
#              and His Declamations (Brill, 1997)
#   MILES    = Chris Miles, "Occult Retraction: Cornelius Agrippa and the
#              Paradox of Magical Language," Rhetoric Society Quarterly 38 (2008)
#   NEWMAN   = Barbara Newman, "Renaissance Feminism and Esoteric Theology:
#              The Case of Cornelius Agrippa," Viator 24 (1993)
#   DANIELS  = George H. Daniels Jr., "Knowledge and Faith in the Thought of
#              Cornelius Agrippa," BHR 26 (1964)
#   BOWEN    = Barbara C. Bowen, "Cornelius Agrippa's De vanitate: Polemic or
#              Paradox?" BHR 34 (1972)
# ─────────────────────────────────────────────────────────────────────────────

# Per-chapter notes (book, chapter). key (0,0) = whole-work note.
# Theme-cluster notes used as fallback by scholar_section().
SCHOLARLY_NOTES: dict[tuple[int, int], str] = {

    # ── Epistles ─────────────────────────────────────────────────────────────
    (0, -1): (
        "The prefatory letters situate <em>De occulta philosophia</em> in the social world "
        "of learned humanism. Van der Poel (1997) stresses that Agrippa's letter to Trithemius "
        "is not merely a dedication but an apologia establishing the work's legitimacy: the "
        "addressee, a renowned abbot and scholar of cryptography, confers scholarly authority "
        "on occult learning. Newman (1993) notes that both <em>De occulta philosophia</em> and "
        "<em>De nobilitate</em> were 'begun in the author's early twenties but later revised and "
        "expanded' before publication in the mid-1530s — the Trithemius letter thus bridges "
        "Agrippa's juvenile draft and his mature system."
    ),

    # ── Book I key chapters ───────────────────────────────────────────────────

    (1, 1): (
        "The opening chapter establishes the tripartite structure of the entire work. "
        "Lehrich (2003) calls the three-world cosmology — elemental, celestial, intellectual — "
        "Agrippa's fundamental ontological scaffolding: natural magic operates at the elemental "
        "level, celestial magic at the astronomical, and ceremonial magic at the divine. "
        "Daniels (1964) traces this structure to the Neoplatonic tradition mediated through "
        "Ficino, arguing that Agrippa's originality lies not in the cosmological scheme itself "
        "but in systematically linking it to a practical programme of magical operations."
    ),
    (1, 2): (
        "Lehrich (2003) regards Agrippa's definition of magic as philosophically sophisticated "
        "rather than naively enthusiastic: magic is the discipline that reads the hidden "
        "signatures written into nature by God, and the magician's task is to decipher and "
        "employ those correspondences. Van der Poel (1997) situates this definition within "
        "Agrippa's broader Neoplatonic theology: 'Agrippa's enthusiasm for the secrets of "
        "nature is justified by his Neoplatonic conviction that God manifests Himself in various "
        "ways in the created world.' The three-part division of magic (natural, celestial, "
        "ceremonial) into which this chapter initiates the reader structures the three books "
        "of the entire work."
    ),
    (1, 3): (
        "The classification of the three kinds of magic is the conceptual hinge of the whole "
        "work. Daniels (1964) argues that Agrippa's epistemological foundation here is "
        "empiricist: the 'occult virtues' that natural magic exploits 'lie beyond the reach of "
        "human intellect, and philosophers attain to knowledge of them with the help of "
        "experience alone.' Lehrich (2003) reads the ascending structure — natural, celestial, "
        "divine — as a ladder of increasing abstraction: natural magic reads the book of nature; "
        "celestial magic reads the mathematical structures that organise the cosmos; ceremonial "
        "magic reads, and attempts to speak, the language of God."
    ),

    (1, 10): (
        "Lehrich (2003) identifies the theory of occult virtues as the philosophical foundation "
        "of the entire natural-magic programme: these are qualities that things possess not "
        "by their observable material properties but by their participation in celestial and "
        "divine orders. Daniels (1964) notes Agrippa's key epistemological claim here: "
        "occult virtues are 'called occult, simply because their causes lie beyond the reach "
        "of human intellect,' meaning that the natural magician proceeds by empirical correlation "
        "rather than causal demonstration — a position that, for Daniels, explains how Agrippa "
        "could endorse such a diverse range of reported magical phenomena."
    ),
    (1, 11): (
        "This chapter on how ideas infuse virtues through the world-soul connects the "
        "natural-magical programme directly to Ficinian and Neoplatonic cosmology. "
        "Lehrich (2003) stresses that the 'world-soul' (anima mundi) functions in DOP as "
        "the ontological medium through which the divine irradiates the material world: "
        "natural things are not self-sufficient but are nodes in a network of downward "
        "emanation and upward participation. Van der Poel (1997) contextualises this within "
        "Agrippa's Neoplatonic-theological project of showing that God is immanent in creation."
    ),
    (1, 14): (
        "The 'spirit of the world' (spiritus mundi) is one of the key operative concepts of "
        "natural magic. Lehrich (2003) analyses it as the vehicle by which celestial powers "
        "descend into material things and by which the magician's operations can redirect those "
        "powers: the spirit is at once cosmological medium and quasi-material substrate of "
        "magical action. This chapter's role in binding the theory of occult virtues to a "
        "practical programme of manipulation makes it central to DOP's argument."
    ),

    (1, 59): (
        "Chapters on names, words, and characters (approximately I:59–I:62) form the "
        "language-theory core of Book I. Miles (2008) argues that Agrippa's philosophy of "
        "language is far more nuanced than the standard 'magical identification of signifier "
        "and signified' allows. Words derive their power not from any inherent property but "
        "from 'the occult Divine powers working by them in the minds of those who by faith "
        "adhere to them' — a position Miles traces back to this cluster of chapters and which "
        "reaches its clearest statement in III:11. Lehrich (2003) reads these chapters as "
        "part of the ascending movement from natural signs to divine names."
    ),
    (1, 60): (
        "Miles (2008) gives close attention to Agrippa's theory that words are 'the fittest "
        "medium betwixt the speaker and the hearer, carrying with them not only the conception "
        "of the mind, but also the vertue of the speaker.' The key move is that magical force "
        "is located not in the word itself but in the speaker's virtue — a point that Miles "
        "connects to the explicit theoretical statement of III:11. Lehrich (2003) places this "
        "within the broader project of making the magician's operations continuous with the "
        "divine Word through which God created the world."
    ),
    (1, 61): (
        "The chapter on magical books and writing extends the language-theory of I:60 into "
        "the domain of inscribed signs. Miles (2008) notes that the apparent endorsement of "
        "inherently powerful written characters sits in tension with deeper passages in Book III "
        "that deny intrinsic power to all linguistic signs. Lehrich (2003) interprets the "
        "written magical book as a kind of material analogue of Scripture: just as the Bible "
        "embodies the Word of God in text, the magical book attempts to embody divine virtues "
        "in specially prepared physical form."
    ),
    (1, 62): (
        "Magical characters and seals are the visual counterpart of magical words. "
        "Lehrich (2003) analyses the connection between the sigil-construction methods "
        "described here and the more systematic treatment in Book II's planetary tables: "
        "in both cases, written signs derive their power from mathematical-celestial "
        "correspondences, not from arbitrary convention. Miles (2008) situates these "
        "chapters in his argument that Agrippa ultimately holds a conventionalist theory "
        "of signs despite surface appearances of a 'natural language' model."
    ),

    (1, 67): (
        "The numerological chapters at the end of Book I (I:67–I:70) foreshadow the "
        "systematic treatment of Book II. Daniels (1964) notes that Agrippa's Pythagorean "
        "commitment to number as an ontological principle is not a quirk of Renaissance "
        "credulity but follows logically from his empiricist epistemology: if only experience "
        "can reveal occult causes, then the regularities of number — which are both empirically "
        "observable and cosmologically fundamental — become the most reliable guide to hidden "
        "correspondences. Lehrich (2003) traces the tradition to Iamblichus's <em>Theology of "
        "Arithmetic</em> and Pico della Mirandola's <em>Conclusiones</em>."
    ),
    (1, 74): (
        "The 'conclusion of natural magic' is more than a summary: it signals the transition "
        "to the higher level of celestial magic in Book II. Lehrich (2003) reads this "
        "transitional chapter as marking the structural logic of the ascending movement: "
        "natural magic is not abandoned but transcended, its operations continuing to operate "
        "within the framework established by Book I while being elevated and recontextualised "
        "by the celestial and divine levels above it. The chapter thus functions as an "
        "argumentative hinge between the three books."
    ),

    # ── Book II key chapters ──────────────────────────────────────────────────

    (2, 1): (
        "Book II opens with an argument for the necessity of mathematical learning that "
        "Lehrich (2003) describes as one of the philosophically richest programmatic statements "
        "in DOP. The Pythagorean-Neoplatonic conviction that number is the structural principle "
        "of reality — mediated through Iamblichus, Boethius, and Pico — makes mathematics not "
        "an auxiliary tool but the very language in which the cosmos is written. "
        "Daniels (1964) situates this mathematically-grounded empiricism within his broader "
        "argument: if all knowledge of occult causes comes through experience, then the "
        "numerical regularities that recur across all domains of nature are the most reliable "
        "empirical evidence available."
    ),
    (2, 2): (
        "The metaphysical status of number in DOP draws on the Pythagorean tradition as "
        "filtered through late antique Neoplatonism. Lehrich (2003) traces Agrippa's "
        "sources to Iamblichus's <em>Theology of Arithmetic</em> and Nicomachus's "
        "<em>Introduction to Arithmetic</em>, both of which treat numbers not as abstract "
        "quantities but as ontological principles — 'the key to all secrets of nature' "
        "as Agrippa formulates it. This gives Book II's numerological chapters a philosophical "
        "seriousness that purely practical magic manuals lack."
    ),

    (2, 35): (
        "The planetary tables (magic squares) are the practical and theoretical centrepiece "
        "of Book II. Lehrich (2003) devotes sustained analysis to these chapters, arguing "
        "that the construction of sigils from magic squares — deriving written characters "
        "from the path of a spirit's name through a numbered grid — demonstrates Agrippa's "
        "most sophisticated attempt to make mathematical structure generate magical writing. "
        "The squares embody the celestial virtues of the planets in a form that can be "
        "transferred to physical objects; they are, in Lehrich's reading, the book's "
        "most complete illustration of how number mediates between the divine and the material."
    ),
    (2, 36): (
        "The 'faces' or <em>decans</em> of the planets extend the talisman-making programme "
        "of the magic squares. Lehrich (2003) situates these image-chapters within the "
        "tradition of Arabic astrological magic (the <em>Picatrix</em> / <em>Ghāyat al-Ḥakīm</em>) "
        "and Ficino's <em>De vita coelitus comparanda</em>, both of which Agrippa systematises "
        "and integrates into his tripartite cosmological framework."
    ),
    (2, 37): (
        "The chapter on magical virtue in letters and characters links Book II's mathematical "
        "programme to the language-theory that Miles (2008) identifies as central to DOP's "
        "philosophical argument. Miles shows that the elaborate character-systems of Book II "
        "appear to endorse a 'natural language' model in which signs directly embody power — "
        "yet the deeper theoretical statement of III:11 qualifies this, insisting that power "
        "resides not in the sign itself but in the faith and virtue of the operator."
    ),

    (2, 59): (
        "The chapter on human proportions and harmony brings together the Vitruvian "
        "tradition of the <em>homo quadratus</em> with Pythagorean-Neoplatonic number theory. "
        "Lehrich (2003) reads this as Agrippa's most explicit statement of the "
        "macrocosm-microcosm principle: the human body, structured according to the same "
        "mathematical ratios that organise the cosmos, is the living bridge between the "
        "elemental world below and the celestial world above. The magician's self-knowledge "
        "is therefore simultaneously cosmological knowledge."
    ),

    # ── Book III key chapters ─────────────────────────────────────────────────

    (3, 1): (
        "Book III opens with the three theological virtues — hope, faith, and love — as "
        "the foundations of ceremonial magic. Lehrich (2003) argues that this opening is "
        "deliberately continuous with Christian theology: the magician's ascent to the "
        "divine is not a pagan rival to Christianity but an intensification of it, using "
        "the same virtues that Christian theology identifies as the conditions of union "
        "with God. Van der Poel (1997) contextualises this within Agrippa's broader "
        "project of reconciling occult learning with reform-minded Catholic humanism."
    ),
    (3, 4): (
        "The chapter on finding the angels and their orders represents the taxonomic heart "
        "of Book III's angelology. Lehrich (2003) analyses DOP's angel-hierarchy in relation "
        "to Pseudo-Dionysian celestial hierarchy, arguing that Agrippa's innovation is to "
        "treat the angelic orders not merely as theological categories but as operative "
        "principles accessible to the trained magician. The angels are, in effect, the "
        "personified intelligences that govern the celestial powers described in Book II; "
        "contact with them is the culmination of the ascending magical programme."
    ),
    (3, 5): (
        "The orders of evil spirits mirror the hierarchy of angels, forming the shadow-side "
        "of the celestial taxonomy. Lehrich (2003) situates Agrippa's demonology within "
        "the tradition of late antique and medieval angelology, noting that the careful "
        "classification of demonic orders serves a practical purpose: the magician who "
        "understands the hierarchy can navigate it safely, distinguishing licit operations "
        "(working with angels) from illicit ones (summoning demons without proper authority). "
        "Miles (2008) connects the demonological chapters to his argument about the "
        "retraction: the very comprehensiveness of the demonic taxonomy exposes the "
        "dangerous knowledge that Agrippa's later apologia attempts to disown."
    ),

    (3, 7): (
        "The chapter on the ten divine names and their correspondence to the Kabbalistic "
        "Sephiroth is one of the most celebrated passages in DOP. Lehrich (2003) regards "
        "the Kabbalistic material of Book III as Agrippa's most serious engagement with "
        "the question of how human language can approach divine reality: the divine names "
        "are the points at which the infinite descends into the finite, and the magician "
        "who knows them participates in the divine creative act. Miles (2008) reads this "
        "chapter in relation to III:11's qualification: the names have power only through "
        "the faith of those who use them, not through any intrinsic property."
    ),
    (3, 8): (
        "Agrippa's treatment of divine names draws on the Kabbalistic tradition as filtered "
        "through Giovanni Pico della Mirandola and Johannes Reuchlin. Lehrich (2003) notes "
        "that the mature DOP departs from Reuchlin's position that Hebrew is inherently "
        "superior to other languages: by 1533, Agrippa had come to hold that no human "
        "language — including Hebrew — can fully contain divine reality. The divine names "
        "work, but through faith, not through linguistic essence. This represents a "
        "significant development from the 1510 Würzburg draft."
    ),
    (3, 11): (
        "Miles (2008) identifies this chapter as the key to DOP's philosophy of language. "
        "The statement that sacred words 'have not their power in Magicall operations, from "
        "themselves, as they are words, but from the occult Divine powers working by them "
        "in the minds of those who by faith adhere to them' is, for Miles, 'a remarkably "
        "modern gloss' anticipating speech-act theory: power is located not in the sign "
        "itself but in the faith and purity of the operator. This passage is, in Miles's "
        "reading, 'occulted away from the eyes of the careless reader, covered over with "
        "just the sort of compendious listing' that dominates the surrounding chapters — "
        "a deliberate concealment of DOP's most theoretically sophisticated claim."
    ),
    (3, 12): (
        "The seventy-two names of God represent the Kabbalistic tradition of divine "
        "nomenclature at its most elaborate. Lehrich (2003) analyses these names as the "
        "intersecting nodes of the divine-name system that Books II and III together "
        "construct: each name is a facet of the infinite divine reality, refracted through "
        "the structures of human language. The chapter illustrates the tension between the "
        "surface suggestion that these names inherently contain divine power and the deeper "
        "qualification — stated explicitly in III:11 — that their power is conditional on "
        "the faith of the practitioner."
    ),

    (3, 23): (
        "Lehrich's monograph is named after the angelic-language theme that reaches its "
        "fullest development in this chapter. For Lehrich (2003), the language of angels "
        "is not a human language but a system of pure meaning — 'the undifferentiated "
        "absolute Word of God (Christ/Logos) by means of which God created the world.' "
        "The magician who achieves genuine contact with angels participates in this "
        "pre-linguistic, divine communication that transcends the inadequacies of all "
        "human language. Miles (2008) connects this to his argument about the limits of "
        "language: the angelic chapter represents the point at which DOP most directly "
        "acknowledges that no human linguistic system can reach ultimate truth."
    ),

    (3, 27): (
        "The chapter on frenzy and madness as modes of divination draws on the Platonic "
        "tradition of divine mania (Phaedrus, Symposium) as mediated through Ficino's "
        "commentary on the Phaedrus. Lehrich (2003) analyses this cluster of soul-chapters "
        "(approximately III:27–III:32) as describing the conditions under which the human "
        "soul can transcend its ordinary cognitive limitations and receive divine knowledge "
        "directly — not through rational discourse but through the suspension of reason. "
        "Newman (1993) connects Agrippa's treatment of ecstatic states to his broader "
        "Hermetic and Neoplatonic anthropology, in which the soul's highest faculty is "
        "capable of direct union with the divine."
    ),
    (3, 28): (
        "The ecstasy of magi and the magical significance of sleep and dreams connect "
        "DOP's ceremonial programme to the ancient tradition of incubation and prophetic "
        "dreaming. Lehrich (2003) reads these chapters as completing the ascending movement "
        "of the three books: natural magic works through the body and material things; "
        "celestial magic works through mathematical proportions and stellar correspondences; "
        "ceremonial magic ultimately works through the suspension of ordinary consciousness "
        "and the soul's direct encounter with divine intelligences."
    ),

    (3, 65): (
        "The epilogue completes DOP with a famous passage of apparent self-retraction, "
        "in which Agrippa distances himself from the very material he has compiled. "
        "Miles (2008) reads this retraction as deliberately paradoxical: because the "
        "retraction is included within the published text, it inevitably retracts itself, "
        "instantiating 'a typical Epimenidian self-referential loop of infinite "
        "flip-flopping.' The retraction is not a genuine disavowal but a rhetorical "
        "performance of the limits of language that the entire work has been exploring. "
        "Bowen (1972) compares the move to Erasmus's <em>Praise of Folly</em> and the "
        "tradition of paradoxical encomium: Agrippa both affirms and undercuts his "
        "own authority as a way of demonstrating that no single voice can contain truth."
    ),
}


# Theme-cluster notes used when no chapter-specific note is available
def _book1_theme(title_lower: str) -> str:
    if any(k in title_lower for k in ("name", "word", "writing", "character", "seal")):
        return (
            "The language and sign chapters of Book I form the first part of Agrippa's "
            "extended meditation on magical signification. Miles (2008) argues that these "
            "chapters appear to endorse a 'natural language' model in which signs directly "
            "embody power, but that this surface reading is complicated by deeper passages "
            "in Book III that deny intrinsic power to all human linguistic signs. "
            "Lehrich (2003) reads the sign-chapters as steps in the ascending movement "
            "from material signatures to celestial characters to the divine Word."
        )
    if any(k in title_lower for k in ("number", "scale", "unity", "virtue of")):
        return (
            "Daniels (1964) identifies Agrippa's numerological reasoning as grounded "
            "in a practical empiricism: number is privileged because numerical regularities "
            "are the most reliably observable form of occult correspondence. Lehrich (2003) "
            "traces the intellectual tradition to Iamblichus and Pico, for whom numbers "
            "are ontological principles rather than merely abstract quantities — a "
            "position that elevates the scales of correspondence from mnemonics to "
            "cosmological architecture."
        )
    if any(k in title_lower for k in ("star", "planet", "image", "celestial", "moon", "sun",
                                       "saturn", "jupiter", "mars", "venus", "mercury", "zodiac")):
        return (
            "The stellar and planetary image chapters represent the practical heart of "
            "natural magic. Lehrich (2003) analyses the tradition of astrological "
            "talismans as drawing on the Arabic <em>Picatrix</em> and Ficino's "
            "<em>De vita coelitus comparanda</em>, both of which Agrippa incorporates "
            "into his tripartite cosmological framework. The images are not illustrations "
            "but operative instruments: by reproducing celestial forms in material "
            "media at astrologically propitious moments, the magician draws down "
            "specific planetary virtues."
        )
    if any(k in title_lower for k in ("divination", "lot", "soothsay", "omen", "portent",
                                       "dream", "oracle")):
        return (
            "Agrippa's treatment of divination connects the practical programme of natural "
            "magic to the theory of the soul's prophetic capacities developed more fully "
            "in Book III. Daniels (1964) notes that Agrippa's empiricism applies here as "
            "elsewhere: the evidence for divination's efficacy comes from accumulated "
            "testimony, not theoretical demonstration. Lehrich (2003) situates the "
            "divination chapters at the boundary between natural and celestial magic, "
            "where material operations begin to shade into the soul's capacity to "
            "receive information from higher sources."
        )
    # Default Book I note
    return (
        "Lehrich (2003) characterises Book I's project as the systematic 'reading and "
        "writing' of the natural world — deciphering the hidden signatures inscribed in "
        "things by God and employing them in magical operations. Daniels (1964) identifies "
        "the epistemological foundation as empiricist: occult virtues are known through "
        "experience and accumulated testimony, not rational demonstration. Van der Poel (1997) "
        "situates the whole of Book I within Agrippa's Neoplatonic theology of divine "
        "immanence, in which nature is not merely a collection of objects but a "
        "continuous disclosure of divine presence."
    )


def _book2_theme(title_lower: str) -> str:
    if any(k in title_lower for k in ("music", "harmony", "sound", "proportion", "consonan")):
        return (
            "The music and harmony chapters are among the most philosophically rich in "
            "Book II. Schipperges (2003) argues that Agrippa follows the Boethian "
            "tradition of <em>musica mundana</em> — cosmic music as the audible expression "
            "of the mathematical ratios that structure reality — while incorporating "
            "Pythagorean numerology. Lehrich (2003) connects these chapters to the "
            "broader argument that the cosmos is structured by proportion: the same "
            "mathematical ratios that produce musical consonance also govern planetary "
            "motion and the symmetry of the human body."
        )
    if any(k in title_lower for k in ("table", "square", "character", "image", "seal", "sigil")):
        return (
            "The character and image chapters of Book II develop the sigil-construction "
            "programme that Lehrich (2003) identifies as Agrippa's most complete attempt "
            "to make mathematical structure generate magical writing. The planetary tables "
            "(magic squares) of chapter II:35 are the model: written characters derived "
            "from the path of a spirit's name through a numbered grid embody celestial "
            "virtue in a transferable form. Miles (2008) reads this programme as appearing "
            "to endorse natural-language theory while being complicated by the theoretical "
            "qualifications of Book III."
        )
    if any(k in title_lower for k in ("number", "scale", "digit", "ternary", "quaternary",
                                       "unity", "seven", "eight", "nine", "ten", "eleven")):
        return (
            "The number-scale chapters — one of the most distinctive structural features "
            "of DOP — present Pythagorean-Neoplatonic number theory in the form of "
            "comparative tables linking each number to its correspondences at every level "
            "of reality. Lehrich (2003) traces the tradition to Iamblichus's <em>Theology "
            "of Arithmetic</em>, noting that for Agrippa as for Iamblichus, numbers are "
            "not abstract quantities but ontological principles that structure existence "
            "from its highest to its lowest levels. Daniels (1964) emphasises the "
            "empiricist dimension: the scales are ultimately maps of observed correspondences."
        )
    # Default Book II note
    return (
        "Book II is described by Lehrich (2003) as 'Mathematical Magic' — the celestial "
        "level of the ascending programme, in which Pythagorean and Neoplatonic number "
        "theory reveals the proportional structures that organise the cosmos. The "
        "transition from Book I's elemental correspondences to Book II's mathematical "
        "ones marks a shift from observation of particular things to understanding of "
        "universal principles. Miles (2008) notes the paradox: Book II's elaborate "
        "systems of sacred names and numerical characters appear to endorse a 'natural "
        "language' theory of magical power, but this reading is complicated by the "
        "deeper qualifications Agrippa introduces in Book III."
    )


def _book3_theme(title_lower: str) -> str:
    if any(k in title_lower for k in ("angel", "spirit", "order", "hierarchy", "demon",
                                       "evil", "genii", "intelligence")):
        return (
            "Lehrich's monograph is, in its entirety, an argument about how Agrippa "
            "theorises contact with the angelic and demonic hierarchy. The angel/demon "
            "chapters of Book III provide the theological and cosmological taxonomy "
            "within which the magician's operations are classified as licit or illicit: "
            "angelic operations are legitimate because angels mediate the divine will; "
            "demonic operations are dangerous because demons can deceive. Van der Poel (1997) "
            "situates this demonology within Agrippa's broadly orthodox Catholic theology, "
            "in which the proper relationship between humans and supernatural beings is "
            "governed by faith, prayer, and moral purity."
        )
    if any(k in title_lower for k in ("name", "divine", "god", "tetragrammaton", "sephiroth",
                                       "kabbalah", "kabbalistic", "seventy-two")):
        return (
            "The divine-name chapters are the Kabbalistic apex of DOP's ascending programme. "
            "Lehrich (2003) reads them as Agrippa's most serious engagement with the question "
            "of how human language can approach divine reality: the divine names are the "
            "points at which the infinite descends into the finite, and the magician who "
            "knows them participates in the divine creative act. Miles (2008) provides the "
            "crucial qualification: the names work only through the faith of those who use "
            "them, not through any intrinsic linguistic property — a position Agrippa states "
            "explicitly in III:11 but which structures the entire Kabbalistic section."
        )
    if any(k in title_lower for k in ("soul", "ecstasy", "frenzy", "dream", "prophecy",
                                       "prophetical", "madness", "vision", "rapture")):
        return (
            "The soul and prophecy chapters describe the conditions under which the human "
            "soul can transcend ordinary cognition and receive divine knowledge directly. "
            "Lehrich (2003) reads this cluster as the culmination of the ascending programme: "
            "the magician who has mastered natural and celestial correspondences can now, "
            "through ecstasy and prophetic states, achieve direct encounter with the divine "
            "intelligences. Newman (1993) connects Agrippa's treatment of ecstatic states "
            "to his Hermetic and Neoplatonic anthropology, in which the soul's highest "
            "faculty is capable of direct union with God."
        )
    if any(k in title_lower for k in ("ceremony", "ritual", "consecration", "purifi",
                                       "unction", "sacrifice", "purgation", "ablution",
                                       "fasting", "prayer", "chastity")):
        return (
            "The ritual and preparatory chapters of Book III describe the moral and "
            "procedural conditions that the magician must satisfy before undertaking "
            "higher operations. Van der Poel (1997) emphasises that this material reflects "
            "genuine religious conviction rather than mere formulaic piety: for Agrippa, "
            "ritual purity and moral transformation are constitutive of magical efficacy, "
            "not merely customary preliminaries. Miles (2008) reads the detailed ritual "
            "instructions as setting up the retraction-paradox of the epilogue: by "
            "providing full procedural detail, Agrippa enables — and then appears to "
            "withdraw — access to the most powerful operations."
        )
    if any(k in title_lower for k in ("bind", "ligature", "conjure", "adjur", "exorcism",
                                       "invocation", "pact", "compact")):
        return (
            "The chapters on binding, invocation, and exorcism represent the operative "
            "core of ceremonial magic — the actual techniques of spirit-communication. "
            "Lehrich (2003) analyses these chapters in relation to the broader theory of "
            "magical signification: to bind a spirit is not to coerce a physical entity "
            "but to deploy the correct names, seals, and ritual conditions that align the "
            "operator with the spirit's position in the celestial hierarchy. "
            "Miles (2008) notes that the comprehensive treatment of these techniques "
            "constitutes the material that Agrippa's apparent retraction in the epilogue "
            "attempts to disown — a move Miles reads as paradox rather than genuine repudiation."
        )
    # Default Book III note
    return (
        "Book III's subject is ceremonial or intellectual magic — the operations performed "
        "at the highest of Agrippa's three world-levels, the divine or intellectual realm. "
        "Lehrich (2003) argues that this book addresses the central problem of the entire "
        "work: how can the human magician make genuine contact with the divine? The answer "
        "involves the hierarchy of angels and demons, the power of divine names, the "
        "ritual preparation of the magician, and ultimately the capacity for ecstatic "
        "union with God. Van der Poel (1997) situates Book III within Agrippa's broader "
        "theological project: ceremonial magic is not a rival to Christian religion but "
        "an intensification of it, demanding the same virtues of faith, hope, and charity "
        "that theology identifies as conditions of union with God."
    )


def scholar_section(book: int, chapter: int, title_en: str) -> str:
    """Return a <div class='scholarly-section'> HTML block for this chapter."""
    note = ""
    # 1. Chapter-specific note
    if (book, chapter) in SCHOLARLY_NOTES:
        note = SCHOLARLY_NOTES[(book, chapter)]
    # 2. Epistle fallback
    elif book == 0:
        note = SCHOLARLY_NOTES.get((0, -1), "")
    # 3. Theme-based fallback
    else:
        t = (title_en or "").lower()
        if book == 1:
            note = _book1_theme(t)
        elif book == 2:
            note = _book2_theme(t)
        elif book == 3:
            note = _book3_theme(t)

    if not note:
        return ""

    return (
        "\n<div class='scholarly-section'>"
        "<h3>Scholarly Perspectives</h3>"
        f"<p>{note}</p>"
        "</div>"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Scholarly summary generation
# ─────────────────────────────────────────────────────────────────────────────

def diff_badge(desc: str) -> tuple[str, str]:
    """Return (badge_class, badge_text) based on ms_description."""
    d = desc.lower().strip()
    if not d:
        return "badge-unknown", "Unknown"
    if d.startswith("new, except") or d.startswith("new (some"):
        return "badge-mostly-new", "Largely New"
    if d.startswith("new"):
        return "badge-new", "New in 1533"
    if re.match(r"w[,\.]\s*\d", d):
        if "many additions" in d or "substantial addition" in d or "very substantial" in d:
            return "badge-expanded", "Heavily Expanded"
        if "addition" in d or "additions" in d:
            return "badge-revised", "Revised & Expanded"
        return "badge-preserved", "Preserved from W"
    return "badge-unknown", "Complex"


def short_summary(title_en: str, label: str, desc: str) -> str:
    """One-sentence card blurb."""
    d = desc.strip()
    if not d:
        return f"Chapter on {title_en.lower() if title_en else label}."
    dl = d.lower()
    if dl.startswith("new"):
        extra = d[3:].strip().strip(",").strip()
        base = f"Entirely new in the 1533 edition"
        if extra:
            base += f" ({extra.rstrip('.')})."
        else:
            base += "; absent from the Würzburg draft."
        return base
    # Derive W chapter reference
    wm = re.match(r"[Ww][,\.]\s*(\d+)[:\s]*(\d+)", d)
    if wm:
        w_book, w_chap = wm.group(1), wm.group(2)
        if "many additions" in dl:
            return f"Derives from W {w_book}:{w_chap}, substantially expanded with many additions in 1533."
        if "substantial addition" in dl or "very substantial" in dl:
            return f"Based on W {w_book}:{w_chap}, with one or more substantial additions."
        if "addition" in dl:
            return f"Reworked from W {w_book}:{w_chap} with short additions."
        return f"Corresponds directly to W {w_book}:{w_chap}, largely unchanged."
    return d[:120].rstrip(".") + "."


def chapter_essay(label: str, title_en: str, title_lat: str, desc: str) -> str:
    """Generate a 3-paragraph scholarly essay for the chapter page."""
    d = desc.strip()
    dl = d.lower()
    _, badge_text = diff_badge(d)

    # Parse W loci from the description
    w_refs = re.findall(r"W[,\.]\s*(\d+)[:\s]+(\d+)", d, re.I)
    w_refs_text = "; ".join(f"W {b}:{c}" for b, c in w_refs) if w_refs else None

    # Para 1: context of the chapter
    title_phrase = f"<em>{title_lat}</em>" if title_lat else label
    if title_en:
        title_phrase += ' (“' + title_en + '”)'
    p1 = (
        f"This chapter, {title_phrase}, occupies a significant place in Agrippa's "
        f"systematic exposition of occult philosophy. In the 1533 Cologne printed edition "
        f"(<em>De occulta philosophia libri tres</em>, sigla K in Perrone Compagni's critical "
        f"apparatus), the text represents Agrippa's mature formulation of the ideas it addresses, "
        f"the product of over two decades of reading, travel, and revision since the composition "
        f"of the Würzburg draft."
    )

    # Para 2: relationship to W
    if dl.startswith("new"):
        extra = d[3:].strip().strip(",").strip()
        if extra:
            p2 = (
                f"According to Perrone Compagni's table of comparison, this chapter is "
                f"<strong>new</strong> in the 1533 edition and has no direct counterpart "
                f"in the Würzburg manuscript (W = MS M.ch.q.50). "
                f'The description notes: \\u201c{html.escape(extra)}.\\u201d '
                f""
                f"Its addition reflects the conceptual enrichment Agrippa undertook between "
                f"approximately 1510 and the early 1530s, incorporating sources and arguments "
                f"unavailable or unexplored in the juvenile draft."
            )
        else:
            p2 = (
                f"According to Perrone Compagni's table of comparison, this chapter is "
                f"<strong>entirely new</strong> in the 1533 edition: it has no antecedent "
                f"in the Würzburg draft (W). Its presence marks one of the conceptual "
                f"expansions that distinguish K from W — the addition of material reflecting "
                f"Agrippa's subsequent reading and intellectual development."
            )
    elif w_refs:
        w_list = ", ".join(f"W {b}:{c}" for b, c in w_refs)
        if "many additions" in dl:
            p2 = (
                f"This chapter derives from {w_list} of the Würzburg draft, but has been "
                f"<strong>substantially expanded</strong> — Perrone Compagni notes "
                f"<em>many additions</em>. The scale of interpolation suggests Agrippa "
                f"rethought and broadened the original argument considerably; the 1533 text "
                f"is in essence a new development of the earlier material rather than a simple "
                f"revision."
            )
        elif "substantial addition" in dl or "very substantial" in dl:
            p2 = (
                f"Based on {w_list} of the Würzburg draft, this chapter was significantly "
                f"<strong>augmented</strong>. Perrone Compagni identifies one or more "
                f"substantial additions, indicating that Agrippa supplemented the original "
                f"argument with new material, possibly drawn from sources encountered after "
                f"the 1510 composition."
            )
        elif "addition" in dl:
            p2 = (
                f"This chapter corresponds to {w_list} in the Würzburg draft, with "
                f"<strong>shorter additions</strong> in the 1533 text. The core argument "
                f"is preserved from W, but Agrippa refined it with supplementary passages, "
                f"qualifying or extending particular points."
            )
        else:
            p2 = (
                f"This chapter corresponds closely to {w_list} in the Würzburg draft "
                f"and appears to be <strong>substantially preserved</strong> in the 1533 "
                f"edition. The direct correspondence shows that Agrippa regarded this material "
                f"as settled relatively early and did not feel compelled to revise it significantly."
            )
    else:
        p2 = (
            "Perrone Compagni's table of comparison indicates: “"
            + html.escape(d[:200])
            + ".” "
            "This relationship between the 1510 Würzburg draft and the 1533 printed edition "
            "reflects the complex evolution of Agrippa's thought across two decades."
        )

    # Para 3: scholarly significance
    if badge_text == "New in 1533":
        p3 = (
            f"The absence of this chapter from the Würzburg draft invites reflection on "
            f"what prompted its insertion in the mature edition. Agrippa's intellectual "
            f"biography between 1510 and 1530 — including his engagement with Neoplatonism, "
            f"Kabbalah, Hermetism, and scholastic natural philosophy — provides the context "
            f"for understanding such additions. The partial edition A (sigla A in Perrone "
            f"Compagni) may offer clues about when the material was composed."
        )
    elif badge_text in ("Heavily Expanded", "Revised & Expanded"):
        p3 = (
            f"The extent of revision in this chapter illustrates the dynamic character of "
            f"Agrippa's rewriting process. Rather than simply updating facts, he appears to "
            f"have substantially reconfigured the argument. Comparison with the partial "
            f"edition A — which represents an intermediate stage — may reveal whether the "
            f"additions were introduced gradually or in a single later revision."
        )
    else:
        p3 = (
            f"The stability of this chapter across the manuscript and printed versions "
            f"suggests it belongs to the secure core of Agrippa's natural-magical argument "
            f"as it was constituted by 1510. Such chapters allow scholars to reconstruct "
            f"the intellectual foundation on which the more elaborate structures of the "
            f"1533 edition were built."
        )

    return f"<p>{p1}</p>\n<p>{p2}</p>\n<p>{p3}</p>"


# ─────────────────────────────────────────────────────────────────────────────
# HTML generation
# ─────────────────────────────────────────────────────────────────────────────

CSS = """\
:root {
  --bg: #f5f0e8;
  --bg-card: #fffdf7;
  --bg-dark: #2c2418;
  --text: #2c2418;
  --text-muted: #6b5d4d;
  --accent: #8b4513;
  --accent-light: #d4a574;
  --border: #d4c4a8;
  --font-serif: 'Georgia', 'Times New Roman', serif;
  --font-sans: system-ui, -apple-system, sans-serif;
  --radius: 6px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--font-sans);
  font-size: 16px;
  line-height: 1.65;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

/* Header */
header {
  background: var(--bg-dark);
  color: #f5f0e8;
  padding: 1.5rem 2rem;
  border-bottom: 3px solid var(--accent);
}
header h1 { font-family: var(--font-serif); font-size: 1.6rem; font-weight: normal; }
header .subtitle { color: var(--accent-light); font-size: 0.9rem; margin-top: .25rem; }
nav a { color: var(--accent-light); margin-right: 1.5rem; font-size: 0.9rem; }
nav { margin-top: .75rem; }

/* Main content */
main { max-width: 1200px; margin: 0 auto; padding: 2rem; }

/* Book sections */
.book-section { margin-bottom: 3rem; }
.book-header {
  border-bottom: 2px solid var(--accent-light);
  margin-bottom: 1.5rem;
  padding-bottom: .5rem;
  display: flex;
  align-items: baseline;
  gap: 1rem;
}
.book-header h2 { font-family: var(--font-serif); color: var(--accent); font-size: 1.4rem; }
.book-stats { font-size: .85rem; color: var(--text-muted); }

/* Epistles section */
.epistles-section { margin-bottom: 2rem; }

/* Card grid */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}
.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem 1.2rem;
  transition: box-shadow .15s, border-color .15s;
  cursor: pointer;
  display: block;
  color: var(--text);
  text-decoration: none;
}
.card:hover {
  box-shadow: 0 3px 12px rgba(139,69,19,.15);
  border-color: var(--accent-light);
  text-decoration: none;
}
.card-label { font-size: .75rem; color: var(--text-muted); margin-bottom: .25rem; }
.card-title {
  font-family: var(--font-serif);
  font-size: .95rem;
  font-weight: bold;
  margin-bottom: .4rem;
  line-height: 1.3;
}
.card-title em { font-style: italic; font-weight: normal; font-size: .88rem; color: var(--text-muted); }
.card-blurb { font-size: .83rem; color: var(--text-muted); line-height: 1.45; margin-bottom: .6rem; }

/* Badges */
.badge {
  display: inline-block;
  font-size: .7rem;
  padding: .15rem .5rem;
  border-radius: 3px;
  font-weight: 600;
  letter-spacing: .03em;
}
.badge-new        { background: #fce8e8; color: #7b1818; border: 1px solid #e0b0b0; }
.badge-mostly-new { background: #fff0e0; color: #7b4010; border: 1px solid #e0c090; }
.badge-preserved  { background: #e8f5e8; color: #1a5c1a; border: 1px solid #a0d0a0; }
.badge-revised    { background: #e8f0fa; color: #1a3a6e; border: 1px solid #a0b8e0; }
.badge-expanded   { background: #ede0f5; color: #4a1a6e; border: 1px solid #c0a0e0; }
.badge-unknown    { background: #f0f0f0; color: #555; border: 1px solid #ccc; }

/* Filter bar */
.filter-bar {
  display: flex; gap: .75rem; margin-bottom: 2rem; flex-wrap: wrap; align-items: center;
}
.filter-bar input {
  flex: 1; min-width: 200px; padding: .45rem .75rem;
  border: 1px solid var(--border); border-radius: var(--radius);
  font-size: .9rem; background: var(--bg-card);
}
.filter-bar select {
  padding: .45rem .75rem; border: 1px solid var(--border);
  border-radius: var(--radius); background: var(--bg-card); font-size: .9rem;
}

/* Chapter page */
.chapter-page { max-width: 760px; }
.chapter-page .back-link { font-size: .85rem; margin-bottom: 1.5rem; display: inline-block; }
.chapter-page .chap-number { font-size: .85rem; color: var(--text-muted); margin-bottom: .25rem; }
.chapter-page h1 {
  font-family: var(--font-serif);
  font-size: 1.8rem;
  color: var(--accent);
  margin-bottom: .25rem;
  line-height: 1.2;
}
.chapter-page .latin-title {
  font-style: italic; color: var(--text-muted); font-family: var(--font-serif);
  font-size: 1rem; margin-bottom: 1rem;
}
.chapter-page .diff-box {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-left: 4px solid var(--accent-light);
  padding: 1rem 1.2rem;
  margin: 1.5rem 0;
  border-radius: 0 var(--radius) var(--radius) 0;
}
.chapter-page .diff-box h3 {
  font-size: .85rem; font-weight: 600; color: var(--text-muted);
  text-transform: uppercase; letter-spacing: .08em; margin-bottom: .5rem;
}
.chapter-page .diff-box p {
  font-family: var(--font-serif); font-size: .95rem; color: var(--text);
}
.chapter-page .essay { font-family: var(--font-serif); font-size: 1rem; line-height: 1.75; }
.chapter-page .essay p { margin-bottom: 1.25rem; }

/* Scholarly section */
.scholarly-section {
  margin-top: 2rem;
  padding: 1.2rem 1.4rem;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-left: 4px solid var(--accent);
  border-radius: 0 var(--radius) var(--radius) 0;
}
.scholarly-section h3 {
  font-size: .8rem; font-weight: 600; color: var(--accent);
  text-transform: uppercase; letter-spacing: .1em; margin-bottom: .7rem;
}
.scholarly-section p {
  font-family: var(--font-serif); font-size: .95rem; line-height: 1.7;
  color: var(--text);
}

/* Footer */
footer {
  text-align: center; padding: 2rem; font-size: .8rem;
  color: var(--text-muted); border-top: 1px solid var(--border);
  margin-top: 4rem;
}
"""

JS = """\
(function(){
  const searchInput = document.getElementById('search');
  const statusFilter = document.getElementById('filter-status');
  if (!searchInput) return;

  function filter() {
    const q = searchInput.value.toLowerCase();
    const status = statusFilter ? statusFilter.value : '';
    document.querySelectorAll('.card').forEach(card => {
      const text = card.textContent.toLowerCase();
      const badgeEl = card.querySelector('.badge');
      const badgeClass = badgeEl ? badgeEl.className : '';
      const matchQ = !q || text.includes(q);
      const matchS = !status || badgeClass.includes(status);
      card.style.display = (matchQ && matchS) ? '' : 'none';
    });
  }

  searchInput.addEventListener('input', filter);
  if (statusFilter) statusFilter.addEventListener('change', filter);
})();
"""


def chapter_slug(entry: dict) -> str:
    if entry["book_1533"] == 0:
        label = re.sub(r"[^a-z0-9]+", "-", entry["label_1533"].lower()).strip("-")
        return f"epist-{label}"
    return f"book{entry['book_1533']}-ch{entry['chapter_1533']:02d}"


def book_name(book_num: int) -> str:
    return {1: "Book I — Natural Magic",
            2: "Book II — Mathematical Magic",
            3: "Book III — Ceremonial Magic"}.get(book_num, f"Book {book_num}")


def chapter_page_html(entry: dict, title_lat: str) -> str:
    book = entry["book_1533"]
    chap = entry["chapter_1533"]
    label_1533 = entry["label_1533"]
    desc = entry.get("ms_description", "")

    # Determine title
    key = (book, chap)
    title_en = ENGLISH_TITLES.get(key, "")
    if not title_en and label_1533 in EPIST_LABELS:
        title_en = EPIST_LABELS[label_1533]

    display_title = title_en or (title_lat or label_1533)
    badge_class, badge_text = diff_badge(desc)
    essay_html = chapter_essay(label_1533, title_en, title_lat, desc)
    scholarly_html = scholar_section(book, chap, title_en)

    book_label = book_name(book) if book > 0 else "Prefatory Epistles"
    if book > 0:
        chap_num_label = f"{book_label} — Chapter {chap}"
    else:
        chap_num_label = book_label

    escaped_desc = html.escape(desc) if desc else "No data extracted from table."

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(display_title)} — De occulta philosophia</title>
<link rel="stylesheet" href="../style.css">
</head>
<body>
<header>
  <h1>De occulta philosophia — 1510 / 1533 Comparison</h1>
  <div class="subtitle">Agrippa von Nettesheim · Würzburg draft (W) vs. Cologne edition (K)</div>
  <nav><a href="../index.html">← All Chapters</a> <a href="../scholarship.html">Scholarship</a></nav>
</header>
<main>
<div class="chapter-page">
  <a class="back-link" href="../index.html">← Back to chapter index</a>
  <div class="chap-number">{html.escape(chap_num_label)}</div>
  <h1>{html.escape(display_title)}</h1>
  {"<div class='latin-title'>" + html.escape(title_lat) + "</div>" if title_lat and title_lat != display_title else ""}
  <span class="badge {badge_class}">{html.escape(badge_text)}</span>

  <div class="diff-box">
    <h3>Perrone Compagni — Table of Comparison</h3>
    <p><strong>1533 edition ({html.escape(label_1533)}):</strong> {escaped_desc}</p>
  </div>

  <div class="essay">
    {essay_html}
    {scholarly_html}
  </div>
</div>
</main>
<footer>
  Data extracted from: V. Perrone Compagni (ed.), <em>De occulta philosophia libri tres</em> (Brill, 1992).
  Scholarly commentary draws on: C. Lehrich (2003), M. van der Poel (1997), C. Miles (2008), B. Newman (1993), G. Daniels (1964).
  Short fair-use excerpts only.
</footer>
</body>
</html>"""


def index_html(entries: list[dict], titles_map: dict) -> str:
    # Separate Epistles and chapter entries
    epistles = [e for e in entries if e["book_1533"] == 0]
    books = {1: [], 2: [], 3: []}
    for e in entries:
        if e["book_1533"] in books:
            books[e["book_1533"]].append(e)

    def card_html(entry: dict) -> str:
        book = entry["book_1533"]
        chap = entry["chapter_1533"]
        label = entry["label_1533"]
        desc = entry.get("ms_description", "")
        slug = chapter_slug(entry)
        badge_class, badge_text = diff_badge(desc)

        key = (book, chap)
        title_en = ENGLISH_TITLES.get(key, "")
        if not title_en and label in EPIST_LABELS:
            title_en = EPIST_LABELS[label]
        title_lat = titles_map.get(key, "")

        blurb = short_summary(title_en, label, desc)

        title_display = title_en or title_lat or label
        subtitle = f"<em>{html.escape(title_lat)}</em>" if title_lat and title_lat != title_display else ""

        return (
            f'<a class="card" href="chapters/{slug}.html">'
            f'<div class="card-label">{html.escape(label)}</div>'
            f'<div class="card-title">{html.escape(title_display)}'
            + (f'<br>{subtitle}' if subtitle else '')
            + f'</div>'
            f'<div class="card-blurb">{html.escape(blurb)}</div>'
            f'<span class="badge {badge_class}">{html.escape(badge_text)}</span>'
            f'</a>'
        )

    # Build Epistles section
    epist_html = ""
    if epistles:
        cards = "\n".join(card_html(e) for e in epistles)
        epist_html = f"""
  <section class="epistles-section">
    <div class="book-header">
      <h2>Prefatory Epistles</h2>
      <span class="book-stats">{len(epistles)} letters</span>
    </div>
    <div class="card-grid">{cards}</div>
  </section>"""

    # Build book sections
    book_sections = ""
    for b, book_entries in sorted(books.items()):
        if not book_entries:
            continue
        new_count = sum(1 for e in book_entries if diff_badge(e.get("ms_description",""))[0] == "badge-new")
        expanded_count = sum(1 for e in book_entries if diff_badge(e.get("ms_description",""))[0] in ("badge-expanded","badge-revised"))
        preserved_count = sum(1 for e in book_entries if diff_badge(e.get("ms_description",""))[0] == "badge-preserved")
        cards = "\n".join(card_html(e) for e in book_entries)
        book_sections += f"""
  <section class="book-section" id="book{b}">
    <div class="book-header">
      <h2>{book_name(b)}</h2>
      <span class="book-stats">
        {len(book_entries)} chapters &nbsp;|&nbsp;
        {new_count} new &nbsp;·&nbsp; {expanded_count} expanded &nbsp;·&nbsp; {preserved_count} preserved
      </span>
    </div>
    <div class="card-grid">{cards}</div>
  </section>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>De occulta philosophia — 1510 / 1533 Comparison</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header>
  <h1>De occulta philosophia libri tres</h1>
  <div class="subtitle">
    Würzburg draft (W, 1510) vs. Cologne edition (K, 1533) ·
    Data from V. Perrone Compagni's critical edition (Brill, 1992)
  </div>
  <nav>
    <a href="#book1">Book I</a>
    <a href="#book2">Book II</a>
    <a href="#book3">Book III</a>
    <a href="scholarship.html">Scholarship</a>
  </nav>
</header>
<main>
  <p style="margin-bottom:1.5rem; color:var(--text-muted); font-size:.9rem;">
    Each card represents a chapter or section of the 1533 edition. The badge shows
    its relationship to the 1510 Würzburg draft. Click a card for a chapter essay
    and full difference analysis.
  </p>
  <div class="filter-bar">
    <input id="search" type="text" placeholder="Search chapters…" />
    <select id="filter-status">
      <option value="">All statuses</option>
      <option value="badge-new">New in 1533</option>
      <option value="badge-mostly-new">Largely New</option>
      <option value="badge-expanded">Heavily Expanded</option>
      <option value="badge-revised">Revised &amp; Expanded</option>
      <option value="badge-preserved">Preserved from W</option>
    </select>
  </div>
  {epist_html}
  {book_sections}
</main>
<footer>
  Structured metadata extracted from V. Perrone Compagni (ed.),
  <em>De occulta philosophia libri tres</em> (Leiden: Brill, 1992).
  Short fair-use excerpts only; no continuous edition text reproduced.
</footer>
<script src="app.js"></script>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    entries = json.loads(COMP_JSON.read_text(encoding="utf-8"))
    titles_raw = json.loads(TITLES_JSON.read_text(encoding="utf-8"))
    titles_map: dict[tuple[int,int], str] = {
        (t["book"], t["chapter"]): t["title_latin"]
        for t in titles_raw
    }

    # Write CSS and JS
    (SITE_DIR / "style.css").write_text(CSS, encoding="utf-8")
    (SITE_DIR / "app.js").write_text(JS, encoding="utf-8")
    print(f"[build_site] Wrote style.css and app.js")

    # Write individual chapter pages
    n_chap = 0
    for entry in entries:
        slug = chapter_slug(entry)
        key = (entry["book_1533"], entry["chapter_1533"])
        title_lat = titles_map.get(key, "")
        page_html = chapter_page_html(entry, title_lat)
        out_path = CHAP_DIR / f"{slug}.html"
        out_path.write_text(page_html, encoding="utf-8")
        n_chap += 1

    print(f"[build_site] Wrote {n_chap} chapter pages")

    # Write index
    idx = index_html(entries, titles_map)
    (SITE_DIR / "index.html").write_text(idx, encoding="utf-8")
    print(f"[build_site] Wrote index.html")
    print(f"[build_site] Site ready at: {SITE_DIR}")


if __name__ == "__main__":
    main()
