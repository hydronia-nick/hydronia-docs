--[[
  table_widths.lua — assign sensible column widths to Pandoc tables that
  arrive without explicit widths.

  Why:
    Pipe tables in MkDocs source carry no width hints. Pandoc's LaTeX
    writer then defaults to equal-width columns, which wastes horizontal
    space on short "name" columns and starves wide "description" columns.
    The Dialog Controls tables (the manual's most common pattern) need
    ~25% for Control, ~15% for Type, ~60% for Description so Description
    text doesn't wrap awkwardly.

  Heuristic:
    - 2 columns -> 30 / 70 (favour second column)
    - 3 columns -> 25 / 15 / 60 (name / type / description)
    - 4 columns -> 20 / 15 / 15 / 50
    - Other counts -> unchanged

    Tables that already have explicit widths set are left alone.

  Pandoc API:
    `pandoc.Table.colspecs` is a list of {alignment, width} pairs where
    width is a number in [0,1] (fraction of text width) or 0 for
    "default / computed". We set width when the current value is 0 or
    nil.
--]]

local DEFAULTS = {
  [2] = { 0.30, 0.70 },
  [3] = { 0.25, 0.25, 0.50 },
  [4] = { 0.20, 0.15, 0.15, 0.50 },
}

-- Is any column width meaningfully different from the equal-fraction
-- default Pandoc assigns by default for pipe tables with no explicit
-- widths? A genuinely author-sized table would have unequal widths.
local function has_author_widths(colspecs)
  local ncols = #colspecs
  if ncols == 0 then
    return false
  end
  local equal = 1.0 / ncols
  for _, cs in ipairs(colspecs) do
    local w = cs[2]
    if type(w) == "number" and w > 0 and math.abs(w - equal) > 1e-4 then
      return true
    end
  end
  return false
end

function Table(tbl)
  local ncols = #tbl.colspecs
  local defaults = DEFAULTS[ncols]
  if not defaults then
    return nil -- column count we don't handle; leave alone
  end
  if has_author_widths(tbl.colspecs) then
    return nil -- table was intentionally sized in the markdown; respect it
  end
  for i = 1, ncols do
    tbl.colspecs[i][2] = defaults[i]
  end
  return tbl
end
