"""The shop at runtime: XS that offers boons on the Wonder after each wave.

Python writes a data block (boon tech ids, rarities, which categories each boon is in, the config) ahead of a
hand-written runtime, shop.xs:

  crucibleShopOpen()   called when a wave is defeated: grants the config's choices. Each choice picks two categories
                       that still have boons to offer, names the choice buttons ("Stable boons (4)") and enables
                       them; after a pick, the next choice shows on the same buttons until none are left.
  rule (choosing)      a click locks in: the other choice is disabled.
  rule (picked)        when the pick finishes, puts a boon of that category on each row-1 slot, stacking on the boons
                       already there (the one on top researches, then the next shows): rarity drawn by points, never
                       a boon offered already.
"""
