--[[
  list_item_figures.lua — demote Figure AST nodes inside list items to
  plain inline images.

  Why:
    Pandoc's LaTeX writer renders a Figure block as
      \begin{figure}\centering\includegraphics...\caption{...}\end{figure}
    That is a LaTeX float. When a float lives inside an \item, even with
    \floatplacement{figure}{H}, LaTeX reserves the full float height
    within the item and pushes subsequent items down by that amount,
    producing big visible gaps between steps.

    In-line \includegraphics inside an \item behaves like any other
    content: it takes its natural vertical space and the next item
    follows immediately. That is what we want for tutorial workflows.

  What the filter does:
    - For every OrderedList / BulletList / DefinitionList, walk each
      item's blocks.
    - Any Figure descendant becomes a Plain block containing just the
      first Image inside it. Caption is rendered as a following emphasis
      paragraph so the reader still sees what the figure represents.

    - Figures OUTSIDE list items are left alone.
--]]

local function first_image(node)
  local found
  pandoc.walk_block(pandoc.Div(node), {
    Image = function(img)
      if not found then
        found = img
      end
    end,
  })
  return found
end

local function caption_text(fig)
  -- Pandoc 3.x Figure has .caption.long (list of Blocks). Flatten to
  -- inlines for rendering as a paragraph.
  if fig.caption and fig.caption.long then
    local inlines = {}
    for _, block in ipairs(fig.caption.long) do
      if block.t == "Plain" or block.t == "Para" then
        for _, i in ipairs(block.content) do
          table.insert(inlines, i)
        end
      end
    end
    if #inlines > 0 then
      return inlines
    end
  end
  return nil
end

local function demote_figures(blocks)
  local out = {}
  for _, block in ipairs(blocks) do
    if block.t == "Figure" then
      local img = first_image(block)
      if img then
        table.insert(out, pandoc.Plain({img}))
        local cap = caption_text(block)
        if cap then
          table.insert(out, pandoc.Para({pandoc.Emph(cap)}))
        end
      else
        table.insert(out, block)
      end
    else
      -- Nested lists and divs: recurse.
      if block.t == "OrderedList" or block.t == "BulletList" then
        for i, item in ipairs(block.content) do
          block.content[i] = demote_figures(item)
        end
      elseif block.t == "Div" or block.t == "BlockQuote" then
        block.content = demote_figures(block.content)
      end
      table.insert(out, block)
    end
  end
  return out
end

function OrderedList(list)
  for i, item in ipairs(list.content) do
    list.content[i] = demote_figures(item)
  end
  return list
end

function BulletList(list)
  for i, item in ipairs(list.content) do
    list.content[i] = demote_figures(item)
  end
  return list
end

function DefinitionList(list)
  for i, entry in ipairs(list.content) do
    local _, defs = entry[1], entry[2]
    for j, def in ipairs(defs) do
      defs[j] = demote_figures(def)
    end
  end
  return list
end
