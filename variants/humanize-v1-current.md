---
name: humanize
description: Scan blog posts for AI writing tics and missed opportunities for human voice. Reports subtractions (AI patterns to remove) and additions (wordplay, arc, and claims to strengthen).
argument-hint: <file_path>
allowed-tools: Read, Edit, Grep, AskUserQuestion
---

# Humanize: AI Pattern Scan for Blog Posts

Scan a post for AI writing tics and missed opportunities for human voice. Do not fix anything until the user approves.

## Process

1. Read the file
2. **Subtract:** Scan for every AI pattern below. Report each instance as: `L{line}: {pattern name} — "{quoted text}"`
3. **Add:** Scan for wordplay opportunities, arc issues, and unsubstantiated claims. Report each as: `L{line}: {opportunity name} — "{quoted text}" → {suggestion}`
4. Present both lists. Wait for the user to say which to fix.
5. Apply fixes. Preserve the argument; cut the padding; add the voice. Balance flow and punch: longer sentences build momentum, short ones land the point. A post that's all short sentences reads like a telegram. A post that's all long ones reads like a textbook.
6. Re-read the result. If anything still reads as AI or feels flat, report it.

## Patterns

**Em dash overuse.** More than 1 per post is a tell. Replace with periods, commas, colons, or restructure. Count every `—` in the file.

**Negative parallelisms.** "Not X but Y", "Not X. Y.", "It's not just X, it's Y", "isn't X; it's Y", "not an X but a Y", "can't X. But it can Y." Define things by what they are. The negation half is almost always dead weight. Alternatives: "More than X", "Beyond X", or just state Y directly. This pattern was fine pre-AI but readers have sensitized to it — even legitimate uses now read as generated.

**Restated points.** The same idea said 2-3 different ways across consecutive sentences or paragraphs. One of them is usually the best. Kill the rest.

**Rule of three.** Three-item lists or three parallel phrases used for rhetorical effect. Three parallel items are a tell. Check whether the list is honest or performative.

**AI vocabulary.** Additionally, crucial, delve, enhance, fostering, garner, highlight (verb), interplay, intricate, key (adj), landscape (abstract), pivotal, showcase, tapestry (abstract), testament, underscore (verb), valuable, vibrant. Flag any occurrence.

**Copula avoidance.** "Serves as", "stands as", "represents", "functions as", "is a property of" instead of "is", "has", or a direct verb. Just say what it is. "X is a property of Y" → "Y requires X". "Serves as the filter" → "is the filter". "Functions as a gate" → "gates".

**Synonym cycling.** Calling the same thing by a different name every sentence to avoid repetition. Just use the same word.

**Superficial -ing clauses.** Participial phrases tacked onto sentences for fake depth: "highlighting...", "underscoring...", "showcasing...", "ensuring...", "reflecting..."

**Filler.** "In order to" (→ "to"), "it is important to note that" (→ delete), "has the ability to" (→ "can"), "due to the fact that" (→ "because").

**Inflated significance.** "Pivotal moment", "setting the stage", "marks a shift", "indelible mark", "evolving landscape". If the sentence works without the inflation, cut it.

**Monotonous rhythm.** Flag any run of 3+ sentences with the same structure (e.g., all starting with "The X does Y").

**Stock metaphors.** Dead metaphors that add no meaning the sentence doesn't already carry: "shaky ground", "solid ground", "paves the way", "opens the door", "at the end of the day", "tip of the iceberg", "game changer", "double-edged sword", "level the playing field", "move the needle". If the sentence works without the metaphor, replace it with the specific claim.

## Additions

**Wordplay.** Scan for missed opportunities: terms with double meanings that fit the argument, section titles that could land harder, closing lines that could echo an earlier phrase with a twist. Flag opportunities; suggest specific rewrites. Puns, double entendres, and repurposed jargon all count. Don't force it.

**Arc (foreshadow/recall).** Check whether the opening and closing connect. The last line should recall the first, reframe the title, or close a loop the reader didn't notice was open. If the post ends with a generic summary or a new thought that doesn't tie back, flag it. Also check: does the title earn its meaning by the end? If the title is a metaphor, does the post deliver the payoff?

**Prosody.** Read sentences aloud in your head. Flag where stress patterns clash between consecutive phrases or where an added/removed syllable would make the rhythm land. Short phrases need downbeats aligned. Parallel structures need matching meter. A function word ("either", "the", "a") can fix a stress collision without changing meaning. The ear catches what the eye skips.

**Unsubstantiated claims.** Flag any factual or causal claim that lacks a citation, a link, or a concrete example. Opinions and arguments are fine without sourcing. Empirical claims ("X% of Y do Z", "studies show", "the data suggests") need a link or a qualifier like "in my experience." If a claim is presented as fact but is actually the author's hypothesis, flag it for reframing.

## Reference

Based on [Wikipedia:Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) and the [humanizer](https://github.com/blader/humanizer) skill by @blader.
