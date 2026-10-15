-- fx_include: splice a generated HTML fragment into a page at render time.
--
--   ::: {.fx-include file="_generated/stats.html"}
--   :::
--
-- Why a filter and not `{{< include >}}`: Quarto expands include shortcodes
-- while it scans the project's input files, BEFORE it runs the pre-render
-- scripts, so an include of a file that a pre-render script writes fails on
-- a clean checkout (tried 2026-10-15, Quarto 1.9.38). A Lua filter runs
-- inside pandoc, after pre-render, so the fragment exists by then. The
-- fragment is inserted as a raw HTML block, unparsed.
--
-- The path is relative to the project root. A missing file is an error, not
-- an empty block: a page that silently lost its stat strip or its matrix
-- would pass every other check.

local function project_root()
  if quarto and quarto.project and quarto.project.directory then
    return quarto.project.directory
  end
  return "."
end

function Div(el)
  if not el.classes:includes("fx-include") then
    return nil
  end
  local rel = el.attributes["file"]
  if not rel then
    error("fx-include: the div has no file= attribute")
  end
  local path = project_root() .. "/" .. rel
  local f = io.open(path, "r")
  if not f then
    error("fx-include: cannot read " .. path .. " (did the pre-render scripts in _quarto.yml run?)")
  end
  local html = f:read("a")
  f:close()
  return pandoc.RawBlock("html", html)
end
