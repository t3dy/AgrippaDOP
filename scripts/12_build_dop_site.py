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

# ─────────────────────────────────────────────────────────────────────────────
# Close readings of Agrippa's own argument, keyed by (book, chapter).
# These accompany the SCHOLARLY_NOTES and focus on what Agrippa is actually
# doing in each chapter: which tradition he draws on, what his distinctive
# move is, and how the chapter functions in his systematic architecture.
# ─────────────────────────────────────────────────────────────────────────────
CHAPTER_READINGS: dict[tuple[int, int], str] = {

    # ── Epistles ─────────────────────────────────────────────────────────────
    (0, -1): (
        "The prefatory letters establish the social and intellectual conditions of the "
        "work's legitimacy before its philosophical argument begins. By addressing "
        "Trithemius — the most respected scholar of occult subjects in the German-speaking "
        "world — Agrippa secures his credentials within a community of learned inquiry. "
        "His claim that magic has been 'perverted and defiled' by those who detach it from "
        "its philosophical foundations is not humility but a polemical positioning: <em>De "
        "occulta philosophia</em> will restore magic to its proper status as 'the most "
        "perfect accomplishment of the noblest philosophy' (<em>totius nobilissimae "
        "philosophiae absoluta consummatio</em>). The letters are the first move in "
        "Agrippa's rehabilitation project — drawing on the Neoplatonic tradition of "
        "esoteric writing that reserves true knowledge for prepared readers."
    ),

    # ── Book I ────────────────────────────────────────────────────────────────
    (1, 1): (
        "Agrippa's opening move is architectural: to establish three ontological registers "
        "— elemental, celestial, intellectual — as the framework within which all magical "
        "operations will be classified. Drawing on Ficino's graduated cosmos and Pico's "
        "hierarchical natural philosophy, he makes the crucial claim that these three levels "
        "are not merely descriptive categories but operative domains: the magician works "
        "differently at each level, using different instruments and different knowledge. "
        "This is Agrippa's most distinctive contribution relative to his predecessors — "
        "the strict structural mapping of philosophical cosmology onto a programme of "
        "practice. The chapter is load-bearing: without this tripartite scaffolding, the "
        "three books of the DOP have no unifying logic."
    ),
    (1, 2): (
        "Agrippa's definition of magic as <em>totius nobilissimae philosophiae absoluta "
        "consummatio</em> is a deliberate elevation beyond his sources. Where Pico called "
        "magic 'the most perfect accomplishment of natural philosophy,' Agrippa substitutes "
        "'noblest philosophy' — a term that encompasses all three registers "
        "(natural, celestial, divine) and not merely the elemental tier. The operative "
        "formula is 'uniting the virtues of things through the application of them one to "
        "the other': magic is the discipline of correspondence, of traversing the links "
        "that connect hierarchically ordered spheres. This makes the definition architecturally "
        "necessary for everything that follows — it is not a claim about magic as a craft "
        "but a philosophical proposition about the structure of reality and the cognitive "
        "activity appropriate to it. Agrippa draws on Neoplatonic sympathy theory, "
        "Hermetic correspondence, and Christian Kabbalah simultaneously, treating them as "
        "complementary articulations of a single cosmological truth."
    ),
    (1, 3): (
        "This chapter's argument turns on Platonic elemental theory: earth alone, among "
        "the four elements, resists fundamental transmutation — it is <em>intransmutabilis</em> "
        "(not convertible into other elements, only dissolved or mixed). Agrippa draws on "
        "Plato's <em>Timaeus</em> and the Neoplatonic commentary tradition, but his emphasis "
        "on earth's unique ontological stability is oriented toward an alchemical conclusion: "
        "a substance that persists through elemental change without being converted is a "
        "candidate for the <em>prima materia</em>, the universal substrate underlying "
        "elemental differentiation. The chapter belongs to the systematic argument of I:3–6 "
        "establishing the cosmological conditions for occult virtues, and specifically for "
        "the reception of celestial rays and the seminal virtues Agrippa will invoke throughout "
        "Book I's natural-magic programme."
    ),
    (1, 4): (
        "Agrippa here introduces a threefold hierarchy of elements — pure and incorruptible, "
        "compound but reducible, and decomposed and convertible — that mirrors the tripartite "
        "cosmological structure of the entire DOP. His most significant move is describing the "
        "third, derivative order as 'operative, as in magic natural, so divine,' achievable "
        "through 'certain numbers, degrees, and orders.' Where Trithemius (his primary source "
        "for this elemental doctrine) describes purification in explicitly alchemical terms "
        "emphasizing transformation of the operator, Agrippa deliberately keeps his language "
        "abstract and cosmological. He is drawing on the Trithemian tradition while opening "
        "it toward a more universal philosophical framework — one in which the operator's "
        "transformation and the material transformation are aspects of a single ontological "
        "movement back toward divine simplicity."
    ),
    (1, 5): (
        "The chapter's central claim — that earth, 'purged by the artifice of fire and reduced "
        "to its simplicity by an agreeable washing,' discloses its 'greatest secrets' — is "
        "Agrippa's most explicit engagement with alchemical doctrine in Book I. Drawing on "
        "Neoplatonic cosmology (earth as 'the object, subject, and receptacle of all celestial "
        "rays') and alchemical natural philosophy (earth as container of 'seeds and seminal "
        "virtues'), Agrippa argues that the elemental substrate of reality is not inert but "
        "actively receives and stores the downward flow of celestial influence. The purification "
        "claim orients this cosmological argument toward an operative conclusion: the secrets "
        "of matter are recoverable through a technique that removes impurity and restores "
        "original simplicity. This is not chrysopoeia (gold-making) but philosophical alchemy "
        "— the recovery of elemental purity as an epistemic and spiritual act."
    ),
    (1, 10): (
        "Agrippa uses an Aristotelian term — 'occult qualities' — to argue against Aristotelian "
        "epistemology. Occult qualities are called occult, he states, because 'their causes lie "
        "beyond the reach of human intellect': they cannot be known through rational demonstration "
        "from first principles. This move simultaneously acknowledges a limit of natural reason "
        "and elevates empirical experience as the appropriate alternative: since causes cannot "
        "be demonstrated, effects as reported by experience become the primary evidence. The "
        "chapter thus establishes the epistemological foundation of the entire natural-magic "
        "programme — not Aristotelian causal explanation but a form of experimental testimony "
        "that trusts the accumulated record of what things do over any theoretical account of "
        "why. This is Agrippa's characteristic anti-scholastic move: using the scholastic "
        "vocabulary of occult qualities to open a space that Aristotelian science cannot fill."
    ),
    (1, 11): (
        "The chapter's key philosophical move is the identification of the <em>spiritus mundi</em> "
        "with the alchemists' <em>quinta essentia</em>. Agrippa draws on Ficinian Neoplatonism "
        "(the <em>anima mundi</em> generating all stellar virtues and impressing them on "
        "sublunary matter) but adds the alchemical identification: the world-spirit that "
        "distributes cosmic qualities is the same substance that alchemists seek to isolate "
        "and concentrate. This fusion of Neoplatonic cosmology with alchemical natural "
        "philosophy is Agrippa's synthetic move — it opens his natural-magic system to "
        "alchemical interpretation while grounding it in a philosophically respectable "
        "Platonic framework. The <em>spiritus mundi</em> is the mechanism by which occult "
        "virtues descend from celestial causes into material receptacles — and therefore "
        "the ontological medium through which natural magic operates."
    ),
    (1, 14): (
        "Agrippa reports his own failed experimental attempt to multiply gold by weight beyond "
        "the quantity of the source material, then immediately qualifies the report: he does "
        "not deny such multiplication 'can be done by another artifice.' The combination is "
        "characteristic of Agrippa's philosophical style — empirical honesty about what he "
        "has and has not achieved, paired with principled openness to further possibilities "
        "he has not yet demonstrated. The chapter's discussion of extracting the <em>spiritus</em> "
        "from gold and silver reorients alchemical inquiry from external transmutation to the "
        "interior pneumatic dimension: the gold's <em>spiritus</em>, not the gold itself, "
        "is the object of philosophical alchemy. This is Agrippa's distinctive contribution "
        "to alchemical discourse — distinguishing vulgar chrysopoeia from a philosophical "
        "alchemy of spirit, grounded in the same <em>spiritus mundi</em> theory that "
        "underpins Book I's natural-magic programme."
    ),
    (1, 42): (
        "The chapter demonstrates the natural-magic programme at its most challenging: the "
        "same substance (menstrual blood, from Pliny's <em>Natural History</em>) simultaneously "
        "cures fevers, repels vermin, banishes serpents, and poisons everything it touches. "
        "Agrippa's argument is not that this is credible folk medicine but that the Plinian "
        "evidence illustrates the principle of occult virtues: a thing's power is irreducible "
        "to its observable material properties, and may work beneficially or destructively "
        "depending on what it is applied to. The explanatory formula — 'the power of this "
        "poison is so great that it is a poison even to poisonous creatures' — exemplifies "
        "Agrippa's empiricist epistemology: the cause (whatever makes menstrual blood "
        "efficacious) lies beyond reason's reach; the effects, as attested by Pliny and "
        "others, are the evidence. This same material will later be re-deployed in "
        "<em>De nobilitate</em> with its negative valence suppressed — evidence of "
        "deliberate rhetorical selection, not naive credulity."
    ),
    (1, 58): (
        "The chapter makes visible the epistemological consequence of the natural-magic "
        "programme's foundational commitment to empirical testimony over theoretical "
        "demonstration. Agrippa accepts the report of men revived from death because it is "
        "'certified abundantly by approved scholars' — he is not credulous but consistent: "
        "if causes lie beyond reason and experience is the only guide, then the weight of "
        "learned testimony constitutes the relevant epistemic standard. This is the same "
        "logic that governs the systematic collection of natural-magical correspondences "
        "throughout Book I. The chapter shows Agrippa's natural philosophy at its extreme "
        "boundary, where empiricism without theoretical constraint produces openness to "
        "marvels that reason would exclude — but which experience, properly understood, "
        "cannot rule out. Daniels's reading (that this is Agrippa's empiricism applied "
        "consistently) is more illuminating than treating it as a lapse of critical judgment."
    ),
    (1, 65): (
        "The chapter is the capstone of Book I's argument and the point where natural magic "
        "touches the celestial register. Agrippa's claim — that 'the mind is far more "
        "powerful, strong, fervent, and more prevalent by its motion than vapours exhaling "
        "out of bodies' — identifies mental intention as a natural force stronger than "
        "material ones. The philosophical framework is Neoplatonic: the tripartite human "
        "being (mind / reason / sensory faculty) mirrors the tripartite cosmos, and the "
        "mind's celestial portion can act on natural bodies by the same logic that governs "
        "stellar influence. Mental magic is therefore not transgression but the natural "
        "magic of the highest human faculty. Agrippa cites Apollonius and Pythagoras as "
        "practitioners — invoking the Hermetic and Pythagorean traditions to ground the "
        "claim. The chapter's closing deferral ('the virtues of the fantasy are "
        "subordinated to reason, and reason to mind') establishes the hierarchy that "
        "ceremonial magic in Book III will complete."
    ),
    (1, 67): (
        "The chapter makes self-knowledge a precondition of magical operation, drawing on "
        "the Platonic maxim 'know thyself' as interpreted through Neoplatonic psychology. "
        "Agrippa's argument is that the aspiring magician must 'know and understand the "
        "property, virtue, measure, order, and degree of his own soul among the powers in "
        "the universe itself' — the soul is not a private psychological entity but a "
        "microcosmic participant in the cosmic hierarchy, and knowing the soul is knowing "
        "one's position in the universal order. This grounds the magician's operations: "
        "he works as a precisely located node in the cosmic network, not as an external "
        "agent imposing will on matter. Agrippa draws on Ficino's Neoplatonic psychology "
        "and the Hermetic *microcosmus* tradition while tilting toward a practical "
        "epistemological conclusion: the magician who does not know himself cannot "
        "know which operations his soul's position in the hierarchy licenses."
    ),
    (1, 69): (
        "The chapter introduces Agrippa's philosophy of language by distinguishing between "
        "the internal word (mental conception) and the external word (uttered sound). "
        "Drawing on Stoic <em>logos</em> theory as mediated through Neoplatonic commentary, "
        "Agrippa locates natural magical efficacy in the physical medium of speech — breath, "
        "air, the organs of articulation — while locating meaning-bearing efficacy in the "
        "rational-interpretive function that requires a prepared receiver. The invocation of "
        "the Greek <em>logos</em> hints at an ideal 'perfect word' synthesizing all three "
        "registers (natural, celestial, divine). This is the theoretical hinge between "
        "Book I and Book II: language, as physical phenomenon, belongs to natural magic; "
        "as carrier of meaning, it crosses into the celestial; as divine name, it reaches "
        "the intellectual register. The chapter therefore establishes the graduated theory "
        "of linguistic efficacy that will underpin the entire sign theory of Books II–III."
    ),
    (1, 73): (
        "Agrippa's claim that 'writing is the last expression of the mind, and is the "
        "number of speech and voice' — absent from the 1510 draft, a deliberate mature "
        "addition — positions written inscription at the threshold between natural and "
        "celestial magic. Speech belongs to the natural order (it is air shaped by bodily "
        "organs); writing is further removed from the body and partakes more purely of "
        "the rational (celestial) register. Writing's capacity to embody meaning in a "
        "physical but non-temporal form — fixed, inspectable, transferable — makes it "
        "the appropriate medium for mathematical-celestial operations. This is why "
        "Book II's magical programme is primarily a programme of written characters, "
        "tables, and sigils: writing is not merely the record of thought but its "
        "closest material analogue in the natural world, and therefore the medium "
        "through which celestial mathematical structure can be impressed on matter."
    ),
    (1, 74): (
        "The chapter grounds written characters in cosmological necessity: the diverse "
        "alphabets of human languages received their 'characters of writing' from celestial "
        "bodies and divine virtues, not from human convention. Drawing on the Christian "
        "Kabbalistic tradition (Pico, Reuchlin, Ricius) and specifically on the claim that "
        "Hebrew characters correspond to stellar positions, Agrippa argues that sacred "
        "alphabets are simultaneously iconic (visually resembling their celestial referents), "
        "numerical (operating through gematria), and symbolic (authorized by divine "
        "institution). His distinctive move is to assimilate Hebrew to the 'strange/foreign "
        "words' (<em>barbara verba</em>) of ancient Neoplatonic theurgy — no human language, "
        "including Hebrew, has intrinsic privilege; efficacy comes from the cosmological "
        "anchoring and the faith of the practitioner. This completes the natural-magic "
        "book's sign theory and authorizes the practical written operations of Book II."
    ),

    # ── Book II ───────────────────────────────────────────────────────────────
    (2, 1): (
        "Book II opens with the Pythagorean-Neoplatonic claim that number is the "
        "structural principle of reality — not an abstract quantity imposed on things "
        "from outside but the form through which God created the cosmos. Agrippa draws "
        "on Iamblichus's <em>Theology of Arithmetic</em>, Nicomachus's <em>Introduction "
        "to Arithmetic</em>, and Boethius's <em>De musica</em> to ground his mathematical "
        "magic in a philosophical tradition that treats numbers as ontological causes "
        "rather than descriptive labels. This is the move that elevates Book II above "
        "a practical manual: the magic squares, planetary tables, and sigil-construction "
        "methods are not techniques for manipulating spirits but demonstrations of how "
        "the mathematical structure of the cosmos can be read and operated on by a "
        "trained intellect. The chapter establishes mathematical magic as the appropriate "
        "cognitive form for the celestial register."
    ),
    (2, 4): (
        "The chapter presents what Agrippa calls 'one thing created by God, the subject "
        "of every marvel on heaven and earth' — deliberately unnamed, described only by "
        "its properties (animal, vegetable, and mineral; found everywhere; known by very "
        "few) and identified in an accompanying diagram as 'the stone of the philosophers "
        "/ the one subject and instrument of all natural and trans-natural virtues.' "
        "Agrippa's argument traces unity's presence across all being-levels: God (as "
        "Archetype), the <em>anima mundi</em> (as intellectual principle), the Sun "
        "(as celestial unity), the heart (as the human centre), and Lucifer (as the "
        "inverted unity of hell). The philosopher's stone is the elemental instantiation "
        "of this universal principle of unity — not a material substance but the point "
        "at which the elemental world reconnects with the One from which it descended. "
        "Agrippa draws on a Trithemius letter interpreting the <em>Tabula Smaragdina</em> "
        "cosmologically, fusing Hermetic, Neoplatonic, and alchemical traditions into a "
        "single metaphysical claim: the unity underlying diversity is the object both of "
        "philosophical contemplation and of operative magical and alchemical practice."
    ),
    (2, 22): (
        "The chapter demonstrates Agrippa's mathematical-magic programme in technical "
        "detail: the planetary magic squares contain spirit-names encoded through Hebrew "
        "gematria, and the sigils derived from tracing the gematria values across the grid "
        "are simultaneously mnemonic devices and operative instruments. Agrippa appears "
        "to devise at least one original construction rule (for the solar square), "
        "showing that this is not mere compilation but active engagement with the "
        "mathematical tradition he inherits. The chapter is absent from the 1510 draft, "
        "indicating a mature deliberate addition. The philosophical point is that "
        "mathematical structure generates magical writing — the sigils are not "
        "arbitrary symbols but traces of the spirit's position in the cosmic grid, "
        "which is itself a projection of celestial numerical order onto a material surface. "
        "This is the fullest practical demonstration of Agrippa's claim that the "
        "celestial register operates through number and that number can be written."
    ),
    (2, 24): (
        "The chapter opens Agrippa's treatment of musical effectus with a bold "
        "cosmological claim: music is not merely a phenomenon that affects the soul "
        "but a structured expression of celestial harmony itself. Drawing on "
        "Tinctoris's <em>Complexus effectuum musices</em> as his immediate source, "
        "Agrippa reframes the late-medieval catalogue of musical effects as a "
        "demonstration of how celestial order operates through sound on embodied "
        "human beings. The move is to make music technology rather than merely art: "
        "understanding the celestial basis of musical harmony enables the practitioner "
        "to compose and deploy music that directs affective and somatic states "
        "deliberately. This is the positive pole of a diptych whose negative pole "
        "is Agrippa's devastating critique of degenerate contemporary music in "
        "<em>De incertitudine</em> — he attacks the degraded practice precisely "
        "because he holds the standard of what music at its best is and does."
    ),
    (2, 25): (
        "The chapter's claim that 'the heaven consists of harmonic composition and "
        "governs and effects all things through harmonic tones and movements' grounds "
        "musical magic in Pythagorean-Neoplatonic cosmology: celestial harmony is not "
        "a metaphor but the literal organizing structure of the cosmos, and terrestrial "
        "music participates in it. Agrippa draws on the <em>musica mundana</em> "
        "tradition from Plato's <em>Timaeus</em> through Boethius, but makes it "
        "operative: 'there is in sound a virtue for receiving celestial gifts.' "
        "This is the mechanism by which musical magic works — properly composed "
        "music in the right celestial conditions opens the soul to receive the "
        "influence corresponding to the prevailing planetary harmony. The chapter "
        "transforms music from a passive cultural product into an active instrument "
        "for aligning the human soul with the celestial order."
    ),
    (2, 26): (
        "The chapter states the operative principle of musical magic: 'no songs, sounds, "
        "or musical instruments are more powerful for moving the emotions and inducing "
        "magical impressions than those composed from numbers, measures, and proportions "
        "after the fashion of the celestial.' Mathematical composition is the key — music "
        "works magically not through emotional expressiveness but through the precision "
        "of its proportional correspondence to celestial harmonics. Agrippa grounds this "
        "in the quadrivial tradition (arithmetic, music as applied arithmetic, geometry, "
        "astronomy) that links musical proportion to celestial proportion. His argument "
        "explains why Book II's mathematical programme extends to music: the magic "
        "squares of the planets and the harmonic proportions of celestial music are "
        "different expressions of the same underlying numerical order, and the "
        "practitioner who understands one understands both."
    ),
    (2, 28): (
        "The chapter argues that music was introduced into divine worship by ancient "
        "prophets and patriarchs precisely because they 'knew these harmonic sacraments' "
        "(<em>haec harmonica sacramenta</em>) — that is, they understood the cosmological "
        "basis of music's power and deliberately harnessed it for the elevation of "
        "the worshipping community. Agrippa draws on the prophetic tradition of "
        "sacred song (David, the Levitical choir) and the Pythagorean tradition of "
        "musical healing (Pythagoras using music to cure psychological disorders) "
        "to establish that music has always been understood by the wise as a "
        "vehicle for spiritual and cosmological alignment. The ideal of rendering "
        "man 'entirely celestial' through music is the Book II equivalent of "
        "Book III's theurgic ascent — music is a kind of ceremonial magic operating "
        "through the celestial register of sound rather than through sacred words and "
        "ritual action."
    ),
    (2, 50): (
        "The chapter culminates the mathematical-magic programme with its most ambitious "
        "claim: that the magus who 'the elements being restrained, nature being overcome, "
        "the heavens being overpowered,' transcends even the angelic orders and comes to "
        "the Archetype itself, can 'give a soul to an image.' This is not conjuring "
        "but theurgic participation — the magus becomes a 'cooperator' of God, "
        "replicating through his own operations the divine creative act by which God "
        "gave soul to the cosmos. Agrippa draws on Neoplatonic theurgy (Iamblichus, "
        "Porphyry) and on Ficino's use of talisman-making as cosmological mediation. "
        "His distinctive move is to connect this to a clear hierarchy of three "
        "kinds of magic-image in the chapter: planetary images for specific effects, "
        "images for prophetic dreams, and images animated by divine cooperation. "
        "The third category establishes that mathematical magic has a theurgic "
        "culmination — it points toward Book III before Book III has begun."
    ),

    # ── Book III ──────────────────────────────────────────────────────────────
    (3, 1): (
        "The chapter establishes religion as the non-negotiable ethical prerequisite of "
        "all ceremonial magic. Agrippa's argument is structural, not merely prudential: "
        "since the operations of Book III involve genuine contact with higher spiritual "
        "powers, only a practitioner whose soul is rightly oriented toward God can "
        "perform them without deception by evil demons. 'Holy religion purifies the "
        "mind and makes it divine' — the phrase is not pious decoration but a claim "
        "about the epistemological conditions of divine contact. Agrippa draws on "
        "Neoplatonic theurgy (Iamblichus's insistence on ritual purity and divine "
        "orientation) and on the Christian three theological virtues (faith, hope, "
        "charity) as the content of the required piety. His synthesis is to treat "
        "the pagan theurgic requirement of ritual purity as identical with the "
        "Christian requirement of virtuous life — both are expressions of the "
        "same structural necessity: the soul must be aligned with what it seeks "
        "to contact."
    ),
    (3, 2): (
        "The chapter provides the hermeneutical frame for everything that follows in "
        "Book III. Agrippa's claim that 'divine powers detest public things and profane, "
        "and love secrecy; so every magical experiment fleeth the public, seeks to be hid, "
        "is strengthened by silence, but is destroyed by publication' is not a social "
        "precaution but an epistemological proposition: a magical sign achieves its "
        "effect only on a prepared receiver. The injunction to keep the 'holy determination' "
        "concealed maps the text's operative logic onto its reading protocol: the "
        "reader who proceeds through Books I and II without understanding the ascending "
        "structure will find Book III an incomprehensible collection of rituals. "
        "The prepared reader — who has internalized the sign theory of Books I–II "
        "and who approaches Book III in the right disposition — finds an initiation "
        "document. The chapter is absent from the 1510 draft, marking it as a "
        "deliberate mature addition that reframes the entire project's relationship "
        "to its audience."
    ),
    (3, 11): (
        "This chapter conceals what is arguably the most philosophically significant "
        "claim in the entire <em>De occulta philosophia</em>: that sacred words 'have "
        "not their power in Magical operations, from themselves, as they are words, "
        "but from the occult divine powers working by them in the minds of those who "
        "by faith adhere to them.' The claim is embedded between lengthy lists of "
        "divine names and diminishing spells — a reader attending to the lists "
        "will not notice the doctrinal statement that transforms their meaning. "
        "Agrippa draws on Augustinian sign theory (words as conventional signs "
        "whose efficacy depends on shared understanding) and Neoplatonic theurgy "
        "(divine power as the ultimate cause, mediated through the practitioner's "
        "faith). His move is to apply this anti-magical sign theory to magic itself, "
        "dissolving the apparent contradiction between a philosophy of language "
        "that denies inherent word-power and a practice that deploys words for "
        "operative ends. The resolution: the words work, but not for the reasons "
        "a naive reader would suppose."
    ),
    (3, 13): (
        "The chapter develops the <em>imago Dei</em> doctrine into an operative "
        "magical claim: God's members are 'the ideas and exemplars of our members,' "
        "and through rightful conformity of our members to those exemplars we are "
        "'translated into the same image' and made 'true sons of God.' Agrippa draws "
        "on the Kabbalistic tradition of <em>Shi'ur Komah</em> (the mystical account "
        "of the divine body's proportions) and on the Christian theological tradition "
        "of the imago Dei, synthesizing them into a claim that has both contemplative "
        "and operative dimensions. The operative dimension: the ritual invocation of "
        "divine names and angelic aspects is simultaneously a spiritual discipline "
        "through which the magician's body and soul are progressively conformed to "
        "the divine nature. Magic is not commanding God or spirits but conforming "
        "oneself to the divine image, which then — by the logic of Agrippa's "
        "entire cosmological system — draws higher powers to cooperate."
    ),
    (3, 23): (
        "The chapter establishes the upper limit of Agrippa's sign theory: angelic "
        "communication requires no sensory medium because angels impress their "
        "meaning directly on the minds of their interlocutors. This is not telepathy "
        "but the logical consequence of the tripartite sign theory — natural signs "
        "operate through matter, celestial signs through mathematical proportion "
        "(which can be written), and divine communication transcends both, leaving "
        "no gap between signifier and signified. Agrippa draws on Pseudo-Dionysian "
        "angelology and Neoplatonic theories of intellectual communication. His "
        "polemical move is against Pico's insistence on Hebrew's special privilege "
        "as the language of magic: if angelic communication bypasses all human "
        "language, then no particular tongue — not even the sacred Hebrew — has "
        "intrinsic authority at the highest magical register. Only the practitioner's "
        "spiritual elevation matters, not the language he speaks. The chapter "
        "is absent from the 1510 draft, marking a mature universalist development "
        "of the sign theory."
    ),
    (3, 24): (
        "The chapter handles the problem of magical nomenclature: if true spirit-names "
        "are known only to God, how can the magician use them? Agrippa's answer "
        "draws on the Genesis account of Adam naming the animals: Adam's naming "
        "was not cataloguing but a participation in the divine creative act, made "
        "possible by his pre-Fall closeness to God. The practitioner 'dignified "
        "and elevated to this virtue by some divine gift, or sacred authority' "
        "participates in the same capacity — naming spirits is an ontological act "
        "available only to one who has recovered something of the Adamic image "
        "through the triple process of natural perfection, moral merit, and "
        "godliness (<em>dignitas</em> / <em>dignitas meritoria</em> / <em>ars "
        "religiosa</em>). Agrippa draws on Neoplatonic theurgy (divine authorization "
        "of the *theurgos*) and Christian Kabbalah (the power of divinely instituted "
        "names) while shifting the emphasis from linguistic knowledge to spiritual "
        "qualification. The chapter is absent from the 1510 draft — it marks "
        "Agrippa's move away from Pico's Hebrew-centred Kabbalah toward a "
        "universalist theology of spiritual elevation."
    ),
    (3, 25): (
        "The chapter presents Agrippa's most technically demanding operation: "
        "the extraction of 72 angelic names from Exodus 14:19–21 through "
        "the boustrophedon arrangement of three consecutive verses, followed by "
        "a substitution cipher (<em>ziruph</em>) traceable to Trithemius's "
        "<em>Polygraphia</em>. The philosophical claim underlying the technique "
        "is that Scripture encodes angelic names in a form recoverable only by "
        "one who understands Hebrew letter-mysticism and cryptographic substitution "
        "simultaneously. Agrippa draws on Kabbalistic tradition (the 72-letter "
        "name of God from the <em>Zohar</em>) and on his intellectual inheritance "
        "from Trithemius (the cryptographic tradition of the <em>Polygraphia</em> "
        "and <em>Steganographia</em>). His move is to demonstrate that cryptography "
        "and Kabbalah are not separate disciplines but the same practice at "
        "different ontological levels: both conceal knowledge from the unprepared "
        "while preserving it for the initiate, and both derive their authority "
        "from the original act of divine inscription in Scripture."
    ),
    (3, 65): (
        "The chapter performs a double movement that enacts the philosophy of language "
        "it has been building. First, Agrippa addresses the 'sons of wisdom and learning' "
        "with an invitation to active interpretation: 'search diligently in this book, "
        "gathering together our dispersed intentions, which in divers places we have "
        "propounded, and what is hid in one place, we make manifest in another.' This "
        "is Agrippa's explicit acknowledgment that DOP is not a manual but an initiatory "
        "text requiring reconstruction. Then, in the appended <em>De vanitate</em> Censure, "
        "he formally retracts the three books — but his Latin formulation "
        "('<em>nunc cautior hac palinodia recantatum volo</em>') deploys a "
        "self-reflexive grammatical construction: the retraction retracts itself. "
        "Agrippa draws on the classical tradition of the <em>palinode</em> (the "
        "formal recantation-poem) and on the Liar paradox: a text that says 'I am "
        "retracted' is not retracted by its own saying. The result is what the "
        "entire DOP has been moving toward: a demonstration, in a single gesture, "
        "that human language can approach but never capture divine truth — and that "
        "the appropriate response is not silence but the active, faith-oriented, "
        "self-critical reading that the text has modeled throughout."
    ),
}


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
        "Lehrich (2003) treats De occulta philosophia I:2 as the foundational anchor for his "
        "entire reading of Agrippa's system, opening the analytical portion of his study by "
        "quoting the chapter's celebrated definition of magic at length and noting that the "
        "passage appears nearly verbatim in the Juvenile Draft, which establishes its centrality "
        "to Agrippa's mature project. For Lehrich, the operative phrase is the definition's "
        "insistence that magic works 'by uniting the virtues of things through the application "
        "of them one to the other': this articulates the semiotic infrastructure of the whole "
        "DOP, the principle that hierarchically ordered spheres — natural, celestial, and divine "
        "— are linked by correspondence and that the magician's art consists in traversing those "
        "links. Lehrich argues that this makes Agrippa's categorization more rigorous than the "
        "frameworks of Ficino or Trithemius, because where his predecessors tended to collapse "
        "the three registers into one another, I:2 insists on their structural distinctness while "
        "asserting their mutual implication. The chapter thus occupies an unusual position in "
        "historiographical debates about whether the DOP is a coherent system or an encyclopedic "
        "miscellany: Lehrich's reading uses I:2 as evidence that Agrippa's tripartite structure "
        "is architecturally intentional, with the definition of magic here functioning less as "
        "an introduction than as a load-bearing proposition for everything that follows."
    ),
    (1, 3): (
        "Newman's engagement with Book I, Chapter 3 offers one of the most philologically "
        "precise interventions in recent Agrippa scholarship. Newman (2004) cites DOP I.iii to "
        "establish Agrippa's adherence to a Platonic doctrine in which earth alone among the "
        "four elements resists fundamental transmutation, being only dissolved or mixed rather "
        "than converted into other elemental forms. The argument carries significant "
        "historiographical weight because Newman simultaneously exposes a textual corruption: "
        "the Lyon 1600 edition altered Agrippa's 'intransmutabilem' to 'transmutabilem,' "
        "inverting the philosophical claim entirely. Newman demonstrates that Müller-Jahncke's "
        "anti-alchemical reading of Agrippa was built, in part, on this corrupted text, "
        "rendering that interpretation methodologically unsound at its foundations. This "
        "philological recovery serves Newman's larger revisionist thesis — that Agrippa was not "
        "hostile to alchemy as such but rather distinguished a legitimate, philosophically "
        "grounded metallurgical alchemy from its vulgar counterfeits. Within that argument, "
        "Chapter 3's doctrine of terrestrial non-transmutability is load-bearing: earth's "
        "unique ontological stability makes it a plausible candidate for the alchemical prima "
        "materia, the undifferentiated substrate that precedes elemental differentiation."
    ),
    (1, 4): (
        "Lehrich (2003) gives this chapter extended treatment as a cornerstone of his argument "
        "that Agrippa constructs a coherent philosophical system rather than an encyclopedic "
        "compilation. The chapter's tripartite hierarchy of elements mirrors, for Lehrich, "
        "the tripartite structure of the universe at large, establishing the analogical "
        "correspondence he reads as the architectural principle of the entire DOP. Crucially, "
        "Lehrich notes that the third, derivative order is described as 'operative, as in magic "
        "natural, so divine,' and that its perfection is achievable through 'certain numbers, "
        "degrees, and orders' — language he contrasts with Trithemius's more explicitly "
        "alchemical rhetoric, which foregrounds the purification of the operator. Newman (2006) "
        "approaches the same chapter from the reception history of Agrippa's natural philosophy, "
        "documenting how Thomas Vaughan adopted precisely this threefold elemental schema in "
        "<em>Anthroposophia Theomagica</em> and mapped it onto a concentric cosmology tied to "
        "the persons of the Trinity. Newman's analysis extends Lehrich's point about Trithemian "
        "derivation — he traces the terms Binarius and Ternarius back through this chapter to "
        "Trithemius — while demonstrating that Vaughan's Trinitarian cosmology was a direct "
        "extrapolation of Agrippa's own text. Together, the two scholars situate Book I, "
        "Chapter 4 at the intersection of source criticism, systematic philosophy, and long "
        "reception, making it one of the most densely contested passages in Agrippan scholarship."
    ),
    (1, 5): (
        "Newman's reading of Book I, Chapter 5 has placed this brief but dense passage at the "
        "center of a significant historiographical reappraisal of Agrippa's relationship to "
        "alchemy. Newman (2004) identifies the chapter as 'a passage of key importance,' arguing "
        "that no modern scholar before him had recognized its language as explicitly alchemical. "
        "The passage's description of earth as 'the basis and foundation of all elements' and "
        "'the object, subject, and receptacle of all celestial rays,' containing 'the seeds and "
        "seminal virtues of all things,' deploys a technical vocabulary Newman traces through "
        "the Paracelsian and post-Paracelsian alchemical tradition. Most consequentially, "
        "Agrippa's closing injunction — that earth's 'greatest secrets' are disclosed when it "
        "is 'purged by the artifice of fire, and reduced to its simplicity by an agreeable "
        "washing' — signals, in Newman's reading, a non-metallurgical alchemy of elemental "
        "purification rather than the chrysopoeia (gold-making) that older scholarship took "
        "to be alchemy's defining concern. This rehabilitation of Agrippa as a knowing "
        "participant in alchemical discourse challenges the earlier consensus, represented by "
        "scholars such as Nauert, which treated the natural magic of the DOP as largely "
        "independent of operative alchemical traditions. Newman further uses the chapter to "
        "anchor a transmission history running from Trithemius through Sendivogius to Thomas "
        "Vaughan, whose claim that 'Cornelius Agrippa knew the first preparation' Newman reads "
        "as a precise and well-informed allusion to this very passage."
    ),

    (1, 10): (
        "Daniels (1966) treats Book I, Chapter 10 as the primary textual anchor for his "
        "reframing of Agrippa's epistemology. Drawing directly on the chapter's claim that "
        "occult qualities are so named precisely because their causes lie beyond the reach of "
        "human intellect, Daniels argues that Agrippa is not the arch-skeptic of the "
        "historiographical tradition but rather a committed empiricist: where reason cannot "
        "penetrate to causes, sensory experience of individual facts becomes the only legitimate "
        "instrument of knowledge. The chapter thus supports Daniels's larger fideist thesis, "
        "in which experience and faith operate in parallel jurisdictions — experience governing "
        "the domain of particular, observable fact, and faith governing the domain of universal "
        "essences — without collision or contradiction. On this reading, Agrippa's invocation "
        "of occult qualities is not a gesture toward irrationalism but a sober demarcation of "
        "reason's limits and a corresponding elevation of empirical inquiry. Daniels's "
        "intervention remains significant precisely because it redirects attention to these "
        "foundational epistemological chapters as evidence that Agrippa's project belongs, in "
        "part, to a tradition of Renaissance naturalism in which the boundaries of rational "
        "cognition are mapped carefully before magic is permitted to operate within them."
    ),
    (1, 11): (
        "Newman (2004) situates De occulta philosophia I.xi within the theoretical substructure "
        "that makes Agrippa's engagement with alchemical categories intelligible, noting that "
        "the chapter attributes the anima mundi and spiritus mundi theory to the 'Platonici' "
        "as a collective authority. For Newman, the pivotal move in this chapter is Agrippa's "
        "identification of the spiritus mundi with the alchemists' quinta essentia: by equating "
        "these two concepts, Agrippa fuses his Neoplatonic cosmological framework with operative "
        "alchemical doctrine, demonstrating that later readers such as Thomas Vaughan who drew "
        "alchemical conclusions from the DOP were following a trajectory already inscribed in "
        "Agrippa's own text rather than imposing a foreign reading upon it. The chapter's "
        "cosmological sequence — in which the spiritus mundi functions as the quasi-material "
        "vehicle by which occult properties descend to elemental earth — provides the ontological "
        "chain Newman identifies as essential for understanding how occult qualities could be "
        "thought to inhere in physical substances at all. This positions I.xi as the hinge on "
        "which Agrippa's system turns from cosmological description to natural-magical and "
        "proto-alchemical explanation, lending weight to those who emphasize the practical and "
        "chymical dimensions of the DOP over purely rhetorical or humanist interpretations."
    ),
    (1, 14): (
        "Newman (2004) places De occulta philosophia I.xiv at the centre of a significant "
        "historiographical dispute about the nature of Agrippa's relationship to alchemy. The "
        "chapter contains Agrippa's admission that he could not multiply the weight of gold "
        "beyond the quantity of the source material — a passage that Müller-Jahncke had "
        "previously cited as evidence of Agrippa's categorical rejection of alchemical claims. "
        "Newman corrects what he identifies as Müller-Jahncke's selective quotation, "
        "demonstrating that the passage continues with a crucial qualification: Agrippa "
        "explicitly states that he does not deny such multiplication 'can be done by another "
        "artifice.' Where Müller-Jahncke reads a blanket condemnation, Newman shows that "
        "Agrippa is making a narrower, economically grounded critique of one specific "
        "metallurgical procedure — not a philosophical repudiation of alchemy as a discipline. "
        "Newman argues that I.xiv reveals Agrippa as a thinker who rejected the vulgar, "
        "laboratory-bound ambitions of commercial transmutation while remaining genuinely open "
        "to a philosophical alchemy concerned with the deeper pneumatic and spiritus-based "
        "operations that animate matter. Newman sees this posture as consistent across "
        "Agrippa's corpus and aligns it with the interpretation associated with Vaughan, "
        "situating I.xiv as evidence that the historiographical consensus of Agrippa-as-sceptic "
        "rests on incomplete textual analysis rather than a full engagement with what Agrippa "
        "actually wrote."
    ),

    (1, 42): (
        "Chapter 42 of Book I, which catalogues the occult virtues and dangers of menstrual "
        "blood following Pliny's natural-historical framework, has attracted sustained scholarly "
        "attention precisely because of the interpretive pressure Agrippa places on this passage "
        "across his wider corpus. Newman (2002) provides the most detailed reading, demonstrating "
        "that Agrippa here preserves the full ambivalence of the Plinian tradition: menstrual "
        "blood holds curative power against fevers, vermin, and serpents, but Agrippa carefully "
        "explains that such efficacy operates because 'the power of this poison is so great that "
        "it is a poison even to poisonous creatures.' Newman's central contribution is to show "
        "what happens when Agrippa subsequently quarries this same material for <em>De nobilitate "
        "et praecellentia foeminei sexus</em>: the poison logic is silently suppressed, and only "
        "the apotropaic and quasi-miraculous properties survive. The comparison exposes a "
        "deliberate rhetorical strategy: <em>De nobilitate</em> is not a transparent record of "
        "Agrippa's esoteric convictions but a selectively shaped redeployment of his own occult "
        "philosophy. For Newman, DOP 1.42 is therefore the indispensable control text against "
        "which the feminist text's editorial decisions become legible, situating the chapter at "
        "the intersection of natural history, occult philosophy, and Agrippa's feminist rhetoric."
    ),
    (1, 58): (
        "Daniels (1966) places Book I, Chapter 58 at the center of his argument about Agrippa's "
        "epistemology, treating it as the chapter that most clearly exposes the logic underlying "
        "the entire collecting enterprise of <em>De occulta philosophia</em>. When Agrippa here "
        "accepts extraordinary reports — including accounts of men revived from death — on the "
        "grounds that they are 'certified abundantly by approved scholars,' Daniels argues he is "
        "not being naively credulous, nor fraudulent. He is acting with strict consistency from "
        "an empiricist premise: in the absence of universal laws of nature that could serve as a "
        "theoretical filter, the weight of accumulated testimony from respected authorities "
        "constitutes the only available warrant for accepting or rejecting a reported fact. "
        "Chapter 58, on this reading, is not an embarrassment to be explained away but a "
        "predictable and even necessary consequence of the same anti-Aristotelian stance that "
        "drives the skeptical arguments of <em>De vanitate</em>. The apparent contradiction "
        "between the two Agrippas — the cautious critic of scholastic overreach in one work and "
        "the uncritical collector of marvels in the other — dissolves once the shared "
        "epistemological root is identified. Both postures flow from a single commitment: "
        "trust the particular, the witnessed, the testified; distrust the universal, the "
        "theoretical, the systematized."
    ),
    (1, 65): (
        "Lehrich (2003) reads Book I, Chapter 65 as the culminating argument of Agrippa's case "
        "for mental magic, and the chapter's position at the close of the first book gives it "
        "particular structural weight in the historiographical debate about what kind of thinker "
        "Agrippa was. The chapter's central claim — that 'the body, and soul of one may in like "
        "manner be affected with the mind of another, seeing the mind is far more powerful, "
        "strong, fervent, and more prevalent by its motion than vapours exhaling out of bodies' "
        "— allows Lehrich to press a thesis against the influential reading offered by Frances "
        "Yates: where Yates's 'Man the operator' is a figure animated by quasi-religious "
        "Hermetic enthusiasm, Lehrich argues that Agrippa's operator has a philosophically "
        "rigorous, structurally necessary grounding. The chapter demonstrates that the threefold "
        "division of the world (elemental, celestial, intellectual) is replicated within the "
        "human being, so that the celestial portion of the mind can act upon natural bodies by "
        "the same logic that governs celestial influence over earthly matter. Mental magic is "
        "therefore not an exceptional intrusion but a consequence built into the system's "
        "architecture. Lehrich further emphasizes the chapter's function as a 'teaser,' "
        "in which the passions of the fantasy are subordinated to reason and reason to mind, "
        "with the miraculous works of Apollonius and Pythagoras invoked as evidence of what "
        "the higher faculties can achieve."
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
        "Daniels (1968) anchors his reading of Book I, Chapter 67 within his larger argument "
        "that <em>De occulta philosophia</em> operates as a form of Renaissance fideism — a "
        "position in which speculative cosmological claims are deliberately held at one remove "
        "from demonstrated knowledge. The chapter's prescription that the aspiring magician must "
        "'know and understand the property, virtue, measure, order, and degree of his own soul "
        "among the powers in the universe itself' is, for Daniels, one of the few moments in "
        "the entire treatise where Agrippa steps beyond taxonomic cataloguing and offers an "
        "explicit interpretive framework. Daniels reads this as the Neoplatonic microcosm-"
        "macrocosm doctrine asserting that self-knowledge and cosmological participation are "
        "inseparable. Yet Daniels is careful to note the tension this creates for his portrait "
        "of Agrippa as fundamentally empiricist in orientation: just as Hume could employ "
        "interpretive patterns while remaining epistemologically skeptical of their grounding, "
        "Agrippa could articulate a Platonic cosmological vision while acknowledging that such "
        "constructions were probably in error and could not be rationally secured. For Daniels, "
        "Chapter 67 is the 'conjecture' layer that floats above the empirical bedrock, sustained "
        "not by demonstration but by faith, placing the chapter at the center of the "
        "historiographical debate over whether Agrippa is best understood as a committed "
        "Neoplatonist, a skeptic, or — as Daniels insists — a fideist for whom speculative "
        "synthesis is legitimate precisely because it never claims the authority of knowledge."
    ),
    (1, 69): (
        "De occulta philosophia I.69 has attracted concentrated scholarly attention as the locus "
        "classicus of Agrippa's philosophy of language, becoming a testing ground for competing "
        "interpretations of what kind of epistemological project the DOP represents. Lehrich "
        "(2003) reads I.69 as the structural pivot between Books I and II, treating it as the "
        "passage where Agrippa draws the precise boundary between natural and celestial magic "
        "in the domain of language. Lehrich's reading turns on Agrippa's 'twofold' word — the "
        "internal conception and the uttered sound — arguing that while spoken language carries "
        "natural efficacy through its physical medium, the meaning-bearing function of language "
        "requires a rational interpreter and therefore crosses into the celestial register. "
        "Miles (2008) accepts Lehrich's premise that I.69 is conceptually central but presses "
        "the passage in a different direction. Where Lehrich is concerned with the architecture "
        "of Agrippa's magical taxonomy, Miles foregrounds the chapter's implications for the "
        "historiographical debate initiated by Brian Vickers, who charged Renaissance occult "
        "philosophy with a 'denotative fallacy' — an assumed identity between signifier and "
        "signified. Miles argues that I.69 directly refutes this charge: Agrippa's insistence "
        "that words are 'vehicula' whose power derives from the virtue of the speaker and the "
        "capacity of the hearer presents language as instrumental and community-dependent. On "
        "Miles's reading, this makes Agrippa's philosophy of language fundamentally relational, "
        "which in turn undermines the Vickers-Foucault binary between occult fixity and "
        "scientific fluidity that has long structured the historiography of early modern science "
        "and magic."
    ),
    (1, 73): (
        "Scholarship on Book I, Chapter 73 clusters around two interlocking debates: the "
        "structural architecture of <em>De occulta philosophia</em> as a whole, and the nature "
        "of Agrippa's theory of language. Lehrich (2003) treats the chapter as one of two "
        "transitional passages bridging natural and celestial magic, attaching particular weight "
        "to the chapter's opening claim that 'writing is the last expression of the mind, and "
        "is the number of speech and voice.' He observes that this formulation appears only in "
        "the final 1533 text and is absent from the Juvenile Draft, arguing that the fully "
        "developed theory of language as connective tissue across the three worlds was a late "
        "and deliberate elaboration. For Lehrich, I:73 is the structural hinge at which natural "
        "magic — having worked through mental intention and vocal speech — crosses into the "
        "celestial sphere of written inscription, confirming that Agrippa's natural magic is "
        "fundamentally a magic of logos. Miles (2008) approaches the same chapter from a "
        "sharply different angle, reading it alongside I:69 to substantiate his argument that "
        "Agrippa holds an explicitly instrumental and arbitrary theory of language. Where "
        "Lehrich emphasizes the chapter's place in a teleological semiotic architecture, Miles "
        "emphasizes its plain-stated communicative theory: words externalize mental content and "
        "declare the speaker's will, with no suggestion that signs are ontologically fused with "
        "the realities they name. Together the two scholars establish I:73 as a site where the "
        "tension between Agrippa's systematic occult architecture and his nominally anti-magical "
        "linguistic declarations is most sharply concentrated."
    ),
    (1, 74): (
        "Lehrich (2003) places De occulta philosophia I:74 at the structural center of his "
        "argument about 'analog signification' — the thesis that signs in Agrippa's system do "
        "not refer in a binary, arbitrary fashion but by degree, across multiple simultaneous "
        "registers. The chapter's claim that diverse human languages have received 'divers, and "
        "proper characters of writing' disposed 'from above, whereby they agree with the "
        "celestial, and divine bodies, and virtues' is, for Lehrich, the explicit warrant for "
        "treating written characters as cosmologically anchored rather than conventionally "
        "assigned. He observes that Hebrew letters in this chapter perform three distinct "
        "semiotic functions simultaneously: they operate iconically through their visual "
        "correspondence to stellar positions, numerically through the gematria system, and as "
        "divinely ordained symbols whose authority derives from their celestial origin. This "
        "triadic structure maps, Lehrich notes, onto all three of Peirce's sign modes at once "
        "— symbol, icon, and index — and it is precisely this overdetermination that grants "
        "Hebrew characters a higher degree of operative power than ordinary alphabetic signs. "
        "Lehrich further remarks that Agrippa's claim about the divine breath residing in the "
        "'joining together of letters' may refer obliquely to the Masoretic pointing system, "
        "situating the chapter's theoretical apparatus within a specific transmission from "
        "<em>Sefer Yetzirah</em>. He provides the full Latin text in Appendix I, treating "
        "I:74 alongside I:73 as a hinge passage: together these two chapters complete the "
        "semiotic groundwork that licenses the practical operations of Books II and III."
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
    (2, 4): (
        "Newman's treatment of this chapter stands as the most consequential intervention in "
        "recent Agrippa scholarship. Newman quotes De occulta philosophia II.iv's declaration "
        "that there exists 'one thing created by God, the subject of every marvel on heaven "
        "and earth; this itself is animal, vegetable, and mineral in act, found everywhere, "
        "known by very few, described by none under its proper name, but concealed with "
        "innumerable figures and enigmas, without which neither natural magic nor alchemy can "
        "attain their perfect end.' For Newman, this passage — together with the accompanying "
        "diagram's identification of this hidden 'unity' with 'the stone of the philosophers / "
        "the one subject and instrument of all natural and trans-natural virtues' — constitutes "
        "Agrippa's most explicit alignment of his own natural-philosophical system with "
        "alchemical doctrine. Newman argues that the longstanding historiographical tendency to "
        "cast Agrippa as an opponent or skeptic of alchemy is simply mistaken; the chapter's "
        "ironic and distancing rhetoric represents esoteric concealment rather than rejection. "
        "The chapter's afterlife further supports Newman's case: Thomas Vaughan explicitly "
        "invoked II.iv when claiming that Agrippa had 'clearly discovered' the first preparation "
        "of the philosopher's stone — evidence that early modern readers within the alchemical "
        "tradition recognized this chapter as a key disclosure, however veiled, of Agrippa's "
        "sympathies."
    ),

    (2, 22): (
        "Lehrich (2003) provides the most sustained technical engagement with this chapter, "
        "treating it as the primary demonstration of Agrippa's mathematical magic and as the "
        "foundational exemplum for his theory of analog signification in the DOP. Lehrich shows "
        "in careful detail how the planetary demonic sigils are generated by tracing the Hebrew "
        "gematria values of spirit-names across the magic squares, and how the planetary "
        "characters function as mnemotechnical instruments for reconstructing those squares from "
        "memory — a procedure that reflects deliberate editorial selection and at least one "
        "apparently original construction rule devised by Agrippa for the singly-even solar "
        "square. The chapter's absence from the Juvenile Draft and its projected table of "
        "contents, appearing only in the 1533 final redaction, reinforces Lehrich's claim that "
        "it represents a mature, considered addition rather than encyclopedic padding. The "
        "larger argumentative weight Lehrich places on II:22 is semiotic: the sigils exemplify "
        "what he calls a hieroglyphic mode of signification, in which signs are simultaneously "
        "transparent in structure and radically opaque to the uninitiated. This positions II:22 "
        "at the center of the historiographical debate about whether Agrippa is best understood "
        "as a compiler of Renaissance occult commonplaces or as an original systematic thinker. "
        "Against the encyclopedist reading implicit in earlier scholarship, Lehrich uses this "
        "chapter to insist on Agrippa's originality and on the internal coherence of DOP as a "
        "semiotic system whose full meaning is deliberately withheld from the uninstructed reader."
    ),

    (2, 24): (
        "Schipperges (2001) places De occulta philosophia II.24 at the center of his "
        "comparative study of Agrippa's two seemingly contradictory treatments of music, "
        "arguing that the chapter establishes the general rubric — that musical harmony "
        "'changes the affects, intentions, gestures, movements, acts, and customs of all "
        "listeners and suddenly provokes them to its own properties' — under which all "
        "subsequent specific effectus in II.24–28 are organized. By mapping this rubric against "
        "Tinctoris's <em>Complexus effectuum musices</em> in a parallel table, Schipperges "
        "demonstrates that Agrippa is working within and against a recognizable late-medieval "
        "music-theoretical tradition, selecting and reordering Tinctoris's twenty categories to "
        "serve his own occult-philosophical synthesis. The methodological stakes of this reading "
        "are considerable: Schipperges uses II.24 not merely as a source of content but as the "
        "positive pole of a deliberate compositional diptych, arguing that the notorious "
        "skeptical chapter in <em>De incertitudine et vanitate scientiarum</em> (ch. 17) should "
        "be read as a systematic negation of the effectus catalogue opened here, rather than as "
        "evidence of intellectual incoherence or a late change of heart. This positions Agrippa "
        "as a strategically self-aware author who structured his two major works in dialectical "
        "relation, and it situates II.24 historiographically as a pivotal text in the debate "
        "over Agrippa's unity of purpose."
    ),
    (2, 25): (
        "Schipperges (2001) offers the most sustained engagement with De occulta philosophia "
        "II.25, treating it as a pivotal node in Agrippa's cosmological theory of music. "
        "Drawing directly on the chapter's assertion that 'the heaven consists of harmonic "
        "composition and governs and effects all things through harmonic tones and movements,' "
        "Schipperges situates Agrippa within the long effectus musicae tradition while arguing "
        "that II.25 represents a decisive operational reformulation of that tradition. Where "
        "earlier theorists such as Tinctoris catalogued the effects of music in a list-based, "
        "largely descriptive manner, Agrippa recasts those effects as the mechanical consequence "
        "of a cosmological structure — a move that transforms music from a phenomenon to be "
        "admired into a technology to be deployed. The chapter's further claim that 'there is "
        "in sound a virtue for receiving celestial gifts' is, for Schipperges, the hinge on "
        "which this magical operationalization turns: it is no longer sufficient to note that "
        "music affects the soul; the chapter grounds that efficacy in the harmonic constitution "
        "of the heavens themselves. Schipperges extends this reading into the broader question "
        "of Agrippa's intellectual coherence, arguing that the two major works are related by "
        "the logic of paradox and the conventions of the declamatio genre — the serious and the "
        "ironic register presuppose each other, and neither can be read in isolation from the other."
    ),
    (2, 26): (
        "Schipperges (2001) situates De occulta philosophia II.26 at the center of a longstanding "
        "historiographical debate about whether Agrippa's natural magic constitutes a coherent "
        "philosophical system or a collection of opportunistic borrowings. The chapter's core "
        "claim — that no songs, sounds, or musical instruments are more powerful for moving the "
        "emotions and inducing magical impressions than those composed from numbers, measures, "
        "and proportions after the fashion of the celestial — is, for Schipperges, not merely "
        "an assertion of musical efficacy but a programmatic statement grounding that efficacy "
        "in the quadrivial tradition of musica mundana. Crucially, Schipperges uses II.26 to "
        "resolve the longstanding interpretive puzzle of how to reconcile the confident natural-"
        "magical program of <em>De occulta philosophia</em> with the apparent scepticism of "
        "<em>De incertitudine</em> chapter 17. Rather than reading <em>De incertitudine</em> as "
        "a recantation, Schipperges argues that its negative catalogue is a deliberate "
        "paradoxical inversion of the mathematical-cosmological ground laid out in II.26 — "
        "the sceptical text presupposes and depends upon the positive framework it appears to "
        "undercut. If Schipperges is correct, II.26 is not a local chapter on musical talismans "
        "but a structural node connecting Agrippa's cosmology, his mathematics of celestial "
        "proportion, and his theory of emotional influence into a single, if deliberately "
        "tensioned, philosophical architecture."
    ),
    (2, 28): (
        "Schipperges (2001) situates De occulta philosophia II.28 as the positive pole of what "
        "he describes as Agrippa's paradox regarding music. The chapter's claim that music was "
        "introduced into divine worship by the ancient prophets and patriarchs precisely because "
        "they 'knew these harmonic sacraments' (<em>haec harmonica sacramenta</em>), and that "
        "the ancient wise men employed musical tones to lead souls toward salutary customs, "
        "ultimately tempering man to celestial harmony and rendering him 'entirely celestial,' "
        "supplies for Schipperges the authoritative standard against which the bitter attack on "
        "contemporary liturgical music in <em>De incertitudine</em> chapter 17 becomes legible: "
        "Agrippa's mockery of debased musical practice presupposes, and indeed requires, the "
        "elevated theory articulated in II.28. Schipperges thus uses this chapter to argue that "
        "Agrippa was not a sceptic about music in itself but about its corrupt and degraded "
        "application in his own time. This reading positions II.28 within the larger "
        "historiographical debate about whether Agrippa's skeptical writings represent a "
        "repudiation of the occult philosophy or merely its mirror image: the continuity "
        "between the two works is one of critical contrast, not contradiction, and II.28 "
        "provides the normative horizon without which Agrippa's polemical voice in the later "
        "work would lack its philosophical grounding."
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

    (2, 50): (
        "Lehrich (2003) treats De occulta philosophia II:50, 'Of certain celestial observations "
        "and the practice of some images,' as one of the two pivotal practical exempla of "
        "mathematical magic in Book II, and reads its tripartite structure as the moment where "
        "his broader argument about the operative magus receives its fullest demonstration. "
        "Applying Panofsky's tripartite distinction of pre-iconography, iconography, and "
        "iconology, Lehrich argues that the magus-constructor does not merely interpret an "
        "image but predetermines its reference structure, thereby controlling the iconological "
        "content and fixing a sign that carries indexical power over the world. The chapter's "
        "climactic passage — that only the one who, 'the elements being restrained, nature being "
        "overcome, the heavens being overpowered,' transcends the progress of angels and comes "
        "to the Archetype itself can 'give a soul to an image' — is for Lehrich the crux of his "
        "semiotic reading: mathematical magic is about enacting rather than merely understanding "
        "the celestial hierarchy. He further observes that this passage connects II:50 forward "
        "to Book III's ceremonial magic, revealing that all three varieties of Agrippan magic "
        "share the same telos of divine cooperation, the magus becoming what the text calls 'a "
        "cooperator' of the Archetype. The chapter thus occupies a hinge position in the "
        "historiographical debate about whether Agrippa's system is primarily theoretical or "
        "operational: Lehrich's reading insists that II:50 is precisely where the speculative "
        "architecture resolves into a practical and theurgic programme continuous with the "
        "angelic and divine magic of Book III."
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
        "Van der Poel (1997) places De occulta philosophia III.1 — titled 'De necessitate, "
        "virtute et utilitate religionis' — at the center of his rehabilitation of Agrippa as "
        "a sincere humanist theologian rather than a cynical purveyor of occult fraud. Drawing "
        "directly on Agrippa's declaration that 'holy religion purifies the mind and makes it "
        "divine' and his warning that those who abandon religion are 'very frequently deceived "
        "by evil demons,' Van der Poel demonstrates that the chapter functions as an ethical "
        "threshold: legitimate magical practice is conditional upon faith and piety, not merely "
        "technical competence. The fact that this chapter remained textually stable across all "
        "revisions of the DOP — surviving the decades of manuscript circulation and printed "
        "recension alike — marks it as doctrinally non-negotiable for Agrippa, not an ornamental "
        "gesture toward orthodoxy. Van der Poel uses this stability to dismantle the 'charlatan "
        "reading,' the tradition running from sixteenth-century polemics through older "
        "scholarship, that treats Agrippa's religious professions as window-dressing over an "
        "essentially subversive or demonic project. For Van der Poel, III.1 is the structural "
        "proof that Agrippa's occultism was governed throughout by the same Neoplatonic-Christian "
        "ethics visible in his theological declamations and his defense of a woman accused of "
        "heresy, grounding the entire third book in an explicitly Christian framework of moral "
        "prerequisite rather than autonomous occult technique."
    ),
    (3, 2): (
        "Lehrich (2003) reads De occulta philosophia III:2 as the pivotal initiatory threshold "
        "of the entire work, arguing that the chapter's injunction to 'keep silent and constantly "
        "conceal within the secret closets of your religious breast, so holy a determination' is "
        "not merely a social precaution but an epistemological claim with structural consequences "
        "for the whole treatise. The chapter's declaration that 'divine powers detest public "
        "things and profane, and love secrecy; so every magical experiment fleeth the public, "
        "seeks to be hid, is strengthened by silence, but is destroyed by publication' encodes, "
        "for Lehrich, a theory of how signs work on minds: a magical sign achieves its effect "
        "only upon a prepared receiver. This situates III:2 as the hinge connecting the semiotic "
        "theory elaborated in Book II to the ritual practice of Book III — just as a magical "
        "image has power solely for one who already understands its analogical significance, so "
        "the ceremonies of Book III operate only for one who has been disciplined by the prior "
        "learning of Books I and II. Lehrich further notes that III:2 is absent from the Juvenile "
        "Draft, appearing only in the final redaction, which suggests Agrippa deliberately added "
        "this hermeneutical frame to govern the reader's approach to the most sensitive material. "
        "Lehrich firmly endorses the view that this rhetoric of secrecy reflects genuine esoteric "
        "commitment rather than prudential self-protection, treating III:2 as evidence that the "
        "text functions as an initiatory document in its own right."
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
        "The central historiographical dispute surrounding Book III, Chapter 11 concerns "
        "whether Agrippa's treatment of sacred language belongs to a tradition of autonomous "
        "sign-power — the view that occult names act by virtue of their inherent properties — "
        "or whether it encodes a more sophisticated theology of mediated divine action. Lehrich "
        "(2003) draws on this chapter twice, finding in it the clearest expression of what he "
        "calls the 'conduit pipe' theory: the chapter's explicit declaration that sacred words "
        "derive their power not from themselves as words but from 'the occult divine powers "
        "working by them in the minds of those who by faith adhere to them.' For Lehrich, this "
        "passage demonstrates that DOP's semiotic is not a theory of sign-autonomy but a "
        "theology in which the sign functions only as a vehicle for divine power channeled "
        "through the practitioner's faith and spiritual elevation. He further notes that both "
        "key passages appear only in the final 1533 draft, suggesting deliberate late-stage "
        "theological refinement. Miles (2008) converges with Lehrich on the import of the same "
        "quotation, but presses its implications further, arguing that Agrippa's position "
        "constitutes a 'remarkably modern' recognition of the arbitrariness of the sign — a "
        "direct refutation of the denotative fallacy that Brian Vickers had attributed to "
        "Renaissance occultism. Where Miles extends Lehrich's reading is in his attention to "
        "the chapter's structural rhetoric: the arbitrary-sign argument is deliberately embedded "
        "within densely compendious lists of Divine names, diminishing spells, and Hebrew seals, "
        "so that an inattentive reader might mistake Agrippa for asserting the very identity of "
        "signifier and signified that the chapter's doctrinal core explicitly denies. For Miles, "
        "the chapter thus enacts on a formal level the concealment it thematizes, making III:11 "
        "not merely a theoretical statement but a rhetorical performance of its own thesis."
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
    (3, 13): (
        "Lehrich (2003) reads Book III, Chapter 13 as the culmination of Agrippa's extended "
        "treatment of divine names and angelic hierarchies, identifying it as the locus of what "
        "the text itself calls the 'great and hidden mysteries' of man as imago Dei. The "
        "chapter's central claim — that God's members are the 'ideas and exemplars of our "
        "members,' and that through rightful conformity of our members we are 'translated into "
        "the same image' and made 'true sons of God' — is, for Lehrich, the positive program "
        "toward which the entire ceremonial magic system of Book III has been building. "
        "Situating the passage within the Kabbalistic tradition of Shi'ur Komah, the mystical "
        "speculation on the measure of God's body, Lehrich argues that the invocation of divine "
        "aspects is not reducible to technique for producing worldly effects; it is simultaneously "
        "a contemplative discipline through which the magician's body and soul are progressively "
        "conformed to the divine nature. This reading intervenes decisively in the historiographical "
        "debate over whether Agrippa's magic is instrumental or transformative in its ultimate "
        "orientation: against accounts that treat the angelic hierarchies of Book III as a "
        "mechanism for commanding spirits, Lehrich insists that the manipulation of names and "
        "seals is internally ordered toward spiritual ascent. The chapter appears only in the "
        "1533 final draft rather than the earlier circulated version, suggesting Agrippa himself "
        "sharpened this theurgic dimension in his mature redaction."
    ),

    (3, 23): (
        "Lehrich (2003) places De occulta philosophia III:23 at the apex of Agrippa's semiotic "
        "architecture, arguing that the chapter establishes the upper register of a three-tiered "
        "theory of signification in which speech belongs to the natural world, writing to the "
        "celestial, and direct mental impression to the divine. The chapter's central claim — "
        "that angels and demons communicate not through audible voice but by 'impressing the "
        "conception of the speech' immediately upon the minds of their interlocutors — "
        "instantiates, for Lehrich, the ideal of a perfectly transparent sign, one in which "
        "the gap between signifier and signified is entirely abolished. This reading situates "
        "III:23 as logically necessary to the whole argument of DOP: without it, the tripartite "
        "scheme of language would lack its culminating term. Lehrich further notes that the "
        "chapter carries a significant polemical charge, disagreeing explicitly with Pico della "
        "Mirandola's insistence that the efficacious names of magic must be Hebrew — because "
        "angelic communication bypasses human language altogether, the privilege of any "
        "particular tongue is rendered secondary at the highest level of operation. The absence "
        "of this chapter from the Juvenile Draft signals that this fully developed semiotic "
        "framework was a product of Agrippa's mature revision, not an early commitment, which "
        "bears directly on debates about the coherence and development of his magical theory."
    ),
    (3, 24): (
        "Lehrich (2003) draws on Book III, Chapter 24 more extensively than almost any other "
        "single chapter in the <em>De occulta philosophia</em>, returning to it on three "
        "distinct occasions to support his semiotic reading. The chapter's insistence that the "
        "'proper and true names' of spirits 'are known to God alone' might seem to foreclose "
        "the magician's access to spiritual power entirely, but Lehrich reads the qualification "
        "— that a man 'dignified, and elevated to this virtue by some divine gift, or sacred "
        "authority' may nonetheless impose names upon spirits — as the pivot on which Agrippa's "
        "entire system turns. For Lehrich, this is the semiotic correlate of spiritual elevation: "
        "naming is not an arbitrary or conventional act but an ontological one, available only "
        "to the practitioner who has ascended through the divine hierarchy and recovered "
        "something of the Adamic image, just as Adam's naming of the animals in Genesis was "
        "not cataloguing but constitutive participation in creation. Lehrich further notes that "
        "the chapter's absence from the Juvenile Draft signals a mature development marking a "
        "progressive shift away from the Hebrew-centric Kabbalah inherited from Pico toward a "
        "more universalist position in which divine dignification, rather than kabbalistic "
        "initiation alone, authorizes the magician's speech. This places the chapter at the "
        "center of ongoing historiographical debate about whether Agrippa's syncretism "
        "represents a coherent philosophical position or an eclectic accumulation."
    ),
    (3, 25): (
        "Lehrich (2003) provides the most sustained engagement with this chapter, offering a "
        "detailed reconstruction of Agrippa's Shemhamphoras technique, by which 72 angelic "
        "names are extracted from the three verses of Exodus 14:19–21 through the boustrophedon "
        "arrangement of their letters. Lehrich identifies the ziruph substitution table "
        "reproduced in this chapter as an instance of the Vigenère progressive-key cipher, "
        "tracing its direct descent from Trithemius's <em>Polygraphia</em> — a lineage that "
        "anchors Lehrich's most provocative interpretive claim: that the long-running scholarly "
        "debate over whether the <em>Steganographia</em> is cryptography or magic rests on a "
        "false dichotomy. For Lehrich, Agrippa's placement of a recognizably cryptographic "
        "apparatus within Book III's ceremonial-magical treatment of angelic nomenclature "
        "demonstrates that the two systems are, for Agrippa, identical in kind. The angelic "
        "names generated through ziruph carry operative power precisely because they are "
        "connected to Scripture by multiple, overlapping systems of reference — each "
        "substitution preserving a thread of analogical continuity back to the sacred source "
        "text. This reading has significant implications for the historiographical debate about "
        "how to situate Agrippa within Renaissance learned culture: where older scholarship "
        "tended to treat the technical apparatus of Book III as ornamental scaffolding around "
        "a core of Neoplatonic theology, Lehrich's analysis of III:25 insists that the "
        "machinery is the argument — Agrippa's epistemology of the sacred name cannot be "
        "separated from his theory of writing as such."
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
        "Chapter III.65 occupies a singular position in the historiographical debate about "
        "Agrippa's intentions in the <em>De occulta philosophia</em>, functioning simultaneously "
        "as authorial directive, structural frame, and self-canceling paradox. Miles (2008) "
        "treats the chapter's exhortation to the 'sons of wisdom and learning' — to 'search "
        "diligently in this book, gathering together our dispersed intentions, which in divers "
        "places we have propounded, and what is hid in one place, we make manifest in another' "
        "— as Agrippa's own warrant for a method of reading against the grain. In Miles's "
        "analysis, this passage establishes that the surface discourse of DOP is not to be "
        "taken at face value; the real argument about language and the sacred is deliberately "
        "distributed and occulted across the whole text, and III.65 is the authorial signal "
        "that licenses exactly this kind of reconstructive, active readership. Miles further "
        "argues that the chapter's status as an addition to the 1533 edition reinforces its "
        "function as a considered retrospective framing device. The chapter's second critical "
        "dimension lies in the embedded <em>De vanitate</em> Censure appended within III.65's "
        "concluding frame. Here Agrippa formally recants the three books of DOP, yet Miles "
        "points to the Latin construction 'nunc cautior hac palinodia recantatum volo' as a "
        "self-canceling gesture: the retraction recants itself along with the work it purports "
        "to disown. This creates what Miles calls a 'typical Epimenidian self-referential loop,' "
        "bracketing the entire DOP between the Ad Lectorem at its opening and the De vanitate "
        "Censure at its close. The Liar paradox thereby becomes, in Miles's reading, not mere "
        "irony but a deliberate rhetorical mechanism through which Agrippa delivers his deeper "
        "'instructional paradox' about the arbitrariness of human language and its incapacity "
        "to convey stable truth. Bowen (1972) connects this move to Erasmus's <em>Praise of "
        "Folly</em> and the tradition of paradoxical encomium."
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
    reading = CHAPTER_READINGS.get((book, chapter), "")
    if not reading and book == 0:
        reading = CHAPTER_READINGS.get((0, -1), "")

    note = ""
    if (book, chapter) in SCHOLARLY_NOTES:
        note = SCHOLARLY_NOTES[(book, chapter)]
    elif book == 0:
        note = SCHOLARLY_NOTES.get((0, -1), "")
    else:
        t = (title_en or "").lower()
        if book == 1:
            note = _book1_theme(t)
        elif book == 2:
            note = _book2_theme(t)
        elif book == 3:
            note = _book3_theme(t)

    if not reading and not note:
        return ""

    parts = ["\n<div class='scholarly-section'>"]
    if reading:
        parts.append(
            "<div class='argument-block'>"
            "<h3>Agrippa's Argument</h3>"
            f"<p>{reading}</p>"
            "</div>"
        )
    if note:
        parts.append(
            "<div class='debate-block'>"
            "<h3>Scholarly Perspectives</h3>"
            f"<p>{note}</p>"
            "</div>"
        )
    parts.append("</div>")
    return "\n".join(parts)


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
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-left: 4px solid var(--accent);
  border-radius: 0 var(--radius) var(--radius) 0;
  overflow: hidden;
}
.argument-block {
  padding: 1.2rem 1.4rem 1rem;
  border-bottom: 1px solid var(--border);
  border-left: 3px solid #8aad7a;
  margin-left: -4px;
}
.debate-block {
  padding: 1.2rem 1.4rem 1rem;
}
.scholarly-section h3 {
  font-size: .75rem; font-weight: 700; color: var(--accent);
  text-transform: uppercase; letter-spacing: .1em; margin-bottom: .65rem;
}
.argument-block h3 { color: #5a7a4a; }
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
