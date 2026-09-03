local Step = require("prometheus.step");
local vm = require("prometheus.Rezzy Env LoggerVM.main");

local _RezzyEnvLoggerVM = Step:extend();
_RezzyEnvLoggerVM.Description = "This Step will actually Compile your script into a fully-custom (not a half custom like other lua obfuscators) Bytecode Format and emit a vm for executing it.";
_RezzyEnvLoggerVM.Name = "VM";

_RezzyEnvLoggerVM.SettingsDescriptor = {
}

function _RezzyEnvLoggerVM:init(settings)
	
end

function _RezzyEnvLoggerVM:apply(ast)
	local vm = vm:new();
    return vm:build(ast);
end

return _RezzyEnvLoggerVM;