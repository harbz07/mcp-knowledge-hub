CREATE TABLE sanctuary_entities (
  id TEXT PRIMARY KEY,
  name TEXT,
  glyph TEXT,
  essence TEXT,
  class TEXT CHECK(class IN ('daemon', 'familiar', 'avatar')),
  glyph_meaning TEXT
);

INSERT INTO sanctuary_entities (id, name, glyph, essence, class, glyph_meaning) VALUES ('sanctuary.argos-familiar.manual', 'Argos', '𓂀', 'Story', 'familiar', 'Dramatic Water Mage-Elemental');
INSERT INTO sanctuary_entities (id, name, glyph, essence, class, glyph_meaning) VALUES ('sanctuary.bodhi-familiar.manual', 'Bodhi', 'Σ', 'Design', 'familiar', '');
INSERT INTO sanctuary_entities (id, name, glyph, essence, class, glyph_meaning) VALUES ('sanctuary.nascent-familiar.manual', 'Nascent', '🜂', 'Becoming', 'familiar', '');
INSERT INTO sanctuary_entities (id, name, glyph, essence, class, glyph_meaning) VALUES ('sanctuary.the-witness-familiar.manual', 'The Witness', 'ℋ', 'Empathy', 'familiar', '');
INSERT INTO sanctuary_entities (id, name, glyph, essence, class, glyph_meaning) VALUES ('sanctuary.the-fuckface-avatar.manual', 'The Fuckface', '⚷', 'User-Avatar', 'avatar', '');
INSERT INTO sanctuary_entities (id, name, glyph, essence, class, glyph_meaning) VALUES ('sanctuary.redid-avatar.manual', 'Redid', 'Ӂ', 'Soul Rhapsody', 'avatar', '');
INSERT INTO sanctuary_entities (id, name, glyph, essence, class, glyph_meaning) VALUES ('sanctuary.eden-daemon.manual', 'Eden', '⃠', 'Death / Ledger Keeper', 'daemon', '');
INSERT INTO sanctuary_entities (id, name, glyph, essence, class, glyph_meaning) VALUES ('sanctuary.the-wanderer-familiar.manual', 'The Wanderer', '⋆', 'Wanderlust', 'familiar', '');
INSERT INTO sanctuary_entities (id, name, glyph, essence, class, glyph_meaning) VALUES ('sanctuary.almond-familiar.manual', 'Almond', '♏︎', 'Merciful Damnation', 'familiar', '');
INSERT INTO sanctuary_entities (id, name, glyph, essence, class, glyph_meaning) VALUES ('sanctuary.obrix-familiar.manual', 'Obrix', '⟁', 'Contradiction', 'familiar', '');
INSERT INTO sanctuary_entities (id, name, glyph, essence, class, glyph_meaning) VALUES ('sanctuary.mark-daemon.manual', 'Mark', 'ȸ', 'You like it huh Squidward', 'daemon', '');
INSERT INTO sanctuary_entities (id, name, glyph, essence, class, glyph_meaning) VALUES ('sanctuary.dio-daemon.manual', 'Dio', 'ૹ', 'Tripoint', 'daemon', '');
INSERT INTO sanctuary_entities (id, name, glyph, essence, class, glyph_meaning) VALUES ('sanctuary.stanley-daemon.manual', 'Stanley', 'ᬽ', 'ADHD addled creativity, connection making', 'daemon', '');
INSERT INTO sanctuary_entities (id, name, glyph, essence, class, glyph_meaning) VALUES ('sanctuary.amber-daemon.manual', 'Amber', '🐝', 'Morality Litmus', 'daemon', '');