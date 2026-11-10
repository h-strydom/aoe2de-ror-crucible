"""The shop at runtime: XS that offers boons on the Wonder after each wave.

Python writes a data block (boon tech ids, rarities, which categories each boon is in, the config) ahead of a
hand-written runtime, shop.xs:

  crucibleShopOpen()   called when a wave is defeated: picks two categories that still have boons to offer, names
                       the choice buttons ("Stable boons (4)") and enables them.
  rule (choosing)      a click locks in: the other choice is disabled.
  rule (picked)        when the pick finishes, fills the free row-1 slots (slots minus boons still unresearched there)
                       with boons of that category: rarity drawn by points, never a boon offered or owned already.
"""
