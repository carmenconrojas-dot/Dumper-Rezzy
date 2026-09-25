local fs = require("@lune/fs")
local process = require("@lune/process")
local luau = require("@lune/luau")
local targetfilename = process.args[1]
local input = fs.readFile("dumps/original/" .. targetfilename)
local isluraph = input:find("(does your environment support load/loadstring?)", 1, true)

local fakeenv = require("./fakegame")
local chunk, err = luau.load(input)
if not chunk then
    warn("Failed to load script: " .. tostring(err))
    return
end

local r = nil
local r_len = 0  -- track longest captured string to prefer the real payload

local cenv = {}
for i, v in fakeenv do
    cenv[i] = v
end

-- Silence noisy globals
cenv.print    = function() end
cenv.warn     = function() end
cenv.wait     = function() return 1 end
cenv.delay    = function() end
cenv.spawn    = function(f) pcall(f) end
cenv.setclipboard  = function() end
cenv.toclipboard   = function() end

-- Fake filesystem
local fake_fs = {}
cenv.writefile  = function(path, cont) fake_fs[path] = cont end
cenv.readfile   = function(path) return fake_fs[path] end
cenv.isfile     = function(path) return fake_fs[path] ~= nil end
cenv.isfolder   = function(path) return type(fake_fs[path]) == "table" end
cenv.mkdir      = function(path) fake_fs[path] = {} end
cenv.listfiles  = function() return {} end

cenv.getfenv = function(lvl)
    local res = getfenv(type(lvl) == "number" and lvl + 2 or lvl)
    if res.require ~= cenv.require then return cenv end
    return res
end

cenv.loadstring = function(src, chunkname)
    if type(src) ~= "string" then
        return nil, "bad argument #1 to 'loadstring' (string expected, got " .. type(src) .. ")"
    end

    -- Skip http-comment headers injected by the bot itself
    local is_http_header = src:find("-- http", 1, true) and #src < 200
    -- Prefer the longest non-header string (likely the real payload)
    if not is_http_header and #src > r_len then
        r = src
        r_len = #src
    end

    -- For Luraph: stop after capturing the loadstring arg (don't execute it)
    if isluraph and #src > 100 then
        -- Return a dummy function that does nothing
        local dummy = function() end
        setfenv(dummy, cenv)
        return dummy
    end

    local func, load_err = luau.load(src, chunkname)
    if not func then return nil, load_err end
    setfenv(func, cenv)
    return func
end

cenv.load = cenv.loadstring
cenv.require = function() return { xd = true } end
cenv.getgenv = function() return cenv end
cenv.getrenv = function() return cenv end
cenv.getsenv = function() return cenv end

-- Set environment and run
local env = getfenv(chunk)
setfenv(chunk, setmetatable({}, {
    __index = function(_, k)
        if cenv[k] ~= nil then return cenv[k] end
        return env[k]
    end,
    __metatable = false
}))

local ok, run_err = pcall(chunk)

if r == nil then
    if not ok then
        warn("Script errored before loadstring was called: " .. tostring(run_err))
    else
        warn("Script ran successfully but loadstring was never called with a capturable payload")
    end
    -- Write an empty marker so the bot knows we ran but got nothing
    fs.writeFile("dumps/dumped/" .. targetfilename, "-- .ld: no loadstring payload captured\n-- Script error: " .. tostring(run_err))
    print("empty")
    return
end

fs.writeFile("dumps/dumped/" .. targetfilename, r)
print("success")
