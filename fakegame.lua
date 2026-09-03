-- fakegame.lua
-- Minimal Roblox executor environment stubs.
-- Returns a flat table of global stubs used by httplog.lua / loadstringlog.lua
-- as a base environment for analysing obfuscated scripts.

local exec_env = require("./exec_env.lua")

local env = {}

-- Stub every function name listed in exec_env
for _, name in exec_env["function"] do
    env[name] = function() return nil end
end

-- Stub every table name listed in exec_env
for _, name in exec_env["table"] do
    env[name] = setmetatable({}, {__index = function() return function() return nil end end})
end

-- Stub Instance globals (game / workspace) as basic proxy tables
for _, name in exec_env["Instance"] do
    env[name] = setmetatable({}, {
        __index = function(_, key)
            return setmetatable({}, {__index = function(_, k)
                return function() return nil end
            end})
        end,
        __call = function() return nil end,
    })
end

-- Common globals expected by most executor scripts
env.game = setmetatable({}, {
    __index = function(_, key)
        return setmetatable({}, {__index = function() return function() return nil end end})
    end
})
env.workspace = env.game
env.script     = setmetatable({}, {__index = function() return nil end})
env.Enum       = setmetatable({}, {__index = function(_, k)
    return setmetatable({}, {__index = function(_, v)
        return {Name = v, Value = 0}
    end})
end})
env.Vector3    = {new = function(x,y,z) return {X=x or 0,Y=y or 0,Z=z or 0} end}
env.Vector2    = {new = function(x,y)   return {X=x or 0,Y=y or 0}           end}
env.CFrame     = {new = function(...)   return {}                              end}
env.Color3     = {new = function(r,g,b) return {R=r or 0,G=g or 0,B=b or 0} end,
                  fromRGB = function(r,g,b) return {R=(r or 0)/255,G=(g or 0)/255,B=(b or 0)/255} end}
env.UDim2      = {new = function(...)   return {}                              end}
env.UDim       = {new = function(...)   return {}                              end}
env.TweenInfo  = {new = function(...)   return {}                              end}
env.Instance   = {new = function(cls)
    return setmetatable({ClassName=cls or ""},{__index=function()return function()return nil end end})
end}
env.tick        = function() return 0 end
env.time        = function() return 0 end
env.wait        = function(n) return n or 0 end
env.spawn       = function(f) end
env.delay       = function(t,f) end
env.warn        = function(...) end
env.error       = error
env.print       = print
env.pairs       = pairs
env.ipairs      = ipairs
env.next        = next
env.select      = select
env.unpack      = table.unpack or unpack
env.type        = type
env.tostring    = tostring
env.tonumber    = tonumber
env.rawget      = rawget
env.rawset      = rawset
env.rawequal    = rawequal
env.setmetatable = setmetatable
env.getmetatable = getmetatable
env.pcall       = pcall
env.xpcall      = xpcall
env.assert      = assert
env.collectgarbage = function() return 0 end
env.string      = string
env.table       = table
env.math        = math
env.os          = os
env.coroutine   = coroutine
env.io          = io

return env, env
