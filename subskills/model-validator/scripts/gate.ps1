# gate.ps1 — model-validator 的 skill_exec entrypoint shim
#
# OpenClaw 的 skill_exec 对 .ps1 走 `pwsh -NoProfile -File`（ResolveScriptCommand），
# 比直接执行 .py（依赖 Windows 文件关联）更稳。本 shim 只做转发：
#   python validate_yaml_refs.py <yaml_dir> <manifest> --format json
# stdout 只输出验证器 JSON（skill_exec parse_mode=json 会严格解析），退出码透传：
#   0 = OK，1 = 存在 FAIL，2 = ERROR/参数错误。

param(
    [Parameter(Mandatory = $true)]
    [string]$YamlDir,

    [Parameter(Mandatory = $true)]
    [string]$Manifest
)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

python "$here/validate_yaml_refs.py" $YamlDir $Manifest --format json
exit $LASTEXITCODE
